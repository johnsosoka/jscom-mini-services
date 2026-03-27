"""Main Lambda handler with route definitions."""

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import APIGatewayHttpResolver, Response
from aws_lambda_powertools.event_handler.exceptions import (
    BadRequestError,
)
from aws_lambda_powertools.event_handler.openapi.exceptions import RequestValidationError
from pydantic import ValidationError as PydanticValidationError

from .config import AppConfig
from .models import IpResponse, DnsUpdateRequest, DnsUpdateResponse, ErrorResponse
from .exceptions import ApiException
from .middleware import require_auth
from .services import DnsService

# Initialize Powertools
# Using APIGatewayHttpResolver for API Gateway HTTP API (v2) with payload format 2.0
logger = Logger(service="jscom-mini-services")
tracer = Tracer(service="jscom-mini-services")
app = APIGatewayHttpResolver(enable_validation=True)

# Load configuration at module level for Lambda warm starts
config = AppConfig.from_env()
dns_service = DnsService(config)


@app.exception_handler(RequestValidationError)
def handle_request_validation_error(ex: RequestValidationError):
    """
    Handle Powertools request validation errors.

    Args:
        ex: Powertools request validation exception

    Returns:
        Error response with 400 status code
    """
    logger.warning("Request validation failed", extra={"errors": str(ex.errors())})

    # Format validation errors into a readable message
    error_messages = []
    for error in ex.errors():
        loc = error.get("loc", ())
        # Skip 'body' prefix from location
        field_parts = [str(p) for p in loc if p != "body"]
        field = ".".join(field_parts) if field_parts else "request"
        message = error.get("msg", "Validation error")
        error_messages.append(f"{field}: {message}")

    return Response(
        status_code=400,
        content_type="application/json",
        body=ErrorResponse(
            error="ValidationError",
            message="; ".join(error_messages),
        ).model_dump(),
    )


@app.exception_handler(PydanticValidationError)
def handle_pydantic_validation_error(ex: PydanticValidationError):
    """
    Handle Pydantic validation errors (fallback).

    Args:
        ex: Pydantic validation exception

    Returns:
        Error response with 400 status code
    """
    logger.warning("Pydantic validation failed", extra={"errors": str(ex.errors())})

    # Format validation errors into a readable message
    error_messages = []
    for error in ex.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        message = error["msg"]
        error_messages.append(f"{field}: {message}")

    return Response(
        status_code=400,
        content_type="application/json",
        body=ErrorResponse(
            error="ValidationError",
            message="; ".join(error_messages),
        ).model_dump(),
    )


@app.exception_handler(ApiException)
def handle_api_exception(ex: ApiException):
    """
    Handle custom API exceptions.

    Args:
        ex: API exception with status code

    Returns:
        Error response with appropriate status code
    """
    logger.warning(
        "API exception",
        extra={
            "exception_type": type(ex).__name__,
            "error_message": ex.message,
            "status_code": ex.status_code,
        },
    )

    return Response(
        status_code=ex.status_code,
        content_type="application/json",
        body=ErrorResponse(
            error=type(ex).__name__,
            message=ex.message,
        ).model_dump(),
    )


@app.exception_handler(Exception)
def handle_generic_exception(ex: Exception):
    """
    Handle unexpected exceptions.

    Args:
        ex: Unhandled exception

    Returns:
        Error response with 500 status code
    """
    logger.exception("Unexpected error", extra={"error": str(ex)})

    return Response(
        status_code=500,
        content_type="application/json",
        body=ErrorResponse(
            error="InternalServerError",
            message="An unexpected error occurred",
        ).model_dump(),
    )


@app.get("/v1/ip/my")
@tracer.capture_method
def get_my_ip() -> IpResponse:
    """
    Get the client's public IP address.

    Returns:
        IpResponse with the client's IP address
    """
    # Extract IP from API Gateway request context
    source_ip = app.current_event.request_context.http.source_ip

    logger.info("IP lookup request", extra={"ip": source_ip})

    return IpResponse(ip=source_ip)


@app.post("/v1/dns/update")
@tracer.capture_method
@require_auth(config)
def update_dns(request: DnsUpdateRequest) -> DnsUpdateResponse:
    """
    Update a DNS A record in Route53.

    Protected endpoint requiring authentication via x-auth-token header.

    Args:
        request: DNS update request with domain and IP

    Returns:
        DnsUpdateResponse with update details
    """
    logger.info(
        "DNS update request",
        extra={"domain": request.domain, "ip": request.ip},
    )

    response = dns_service.update_record(request)

    return response


@logger.inject_lambda_context(log_event=True)
@tracer.capture_lambda_handler
def lambda_handler(event: dict, context) -> dict:
    """
    Main Lambda handler for the consolidated API.

    Handles routing for multiple endpoints:
    - GET /v1/ip/my: Returns client IP address
    - POST /v1/dns/update: Updates Route53 DNS records (authenticated)

    Args:
        event: API Gateway proxy event
        context: Lambda context object

    Returns:
        API Gateway proxy response
    """
    return app.resolve(event, context)
