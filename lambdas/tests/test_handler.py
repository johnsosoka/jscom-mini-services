"""Integration tests for Lambda handler."""

import json
import pytest
from unittest.mock import MagicMock, patch

from api.handler import app, lambda_handler
from api.models import ErrorResponse


def create_http_api_event(
    method: str,
    path: str,
    body: str | None = None,
    headers: dict | None = None,
    source_ip: str = "203.0.113.42",
) -> dict:
    """Create a properly formatted HTTP API v2 event."""
    return {
        "version": "2.0",
        "routeKey": f"{method} {path}",
        "rawPath": path,
        "rawQueryString": "",
        "headers": headers or {},
        "requestContext": {
            "accountId": "123456789012",
            "apiId": "test-api-id",
            "domainName": "api.johnsosoka.com",
            "domainPrefix": "api",
            "http": {
                "method": method,
                "path": path,
                "protocol": "HTTP/1.1",
                "sourceIp": source_ip,
                "userAgent": "test-agent",
            },
            "requestId": "test-request-id",
            "routeKey": f"{method} {path}",
            "stage": "$default",
            "time": "22/Dec/2025:12:00:00 +0000",
            "timeEpoch": 1734868800000,
        },
        "body": body,
        "isBase64Encoded": False,
    }


class TestGetMyIp:
    """Test suite for GET /v1/ip/my endpoint."""

    def test_get_my_ip_returns_source_ip(self, mock_lambda_context):
        """Test that /v1/ip/my returns IP from request context."""
        event = create_http_api_event("GET", "/v1/ip/my", source_ip="203.0.113.42")

        response = lambda_handler(event, mock_lambda_context)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["ip"] == "203.0.113.42"

    def test_get_my_ip_with_different_source_ip(self, mock_lambda_context):
        """Test that endpoint returns different IP addresses correctly."""
        event = create_http_api_event("GET", "/v1/ip/my", source_ip="198.51.100.99")

        response = lambda_handler(event, mock_lambda_context)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["ip"] == "198.51.100.99"


class TestUpdateDns:
    """Test suite for POST /v1/dns/update endpoint."""

    def test_update_dns_without_auth_returns_401(self, mock_lambda_context):
        """Test POST /v1/dns/update without auth token returns 401."""
        event = create_http_api_event(
            "POST",
            "/v1/dns/update",
            body=json.dumps({"domain": "test.johnsosoka.com.", "ip": "192.168.1.100"}),
        )

        response = lambda_handler(event, mock_lambda_context)

        assert response["statusCode"] == 401
        body = json.loads(response["body"])
        assert body["error"] == "UnauthorizedError"

    def test_update_dns_with_invalid_auth_returns_403(self, mock_lambda_context):
        """Test POST /v1/dns/update with invalid auth token returns 403."""
        event = create_http_api_event(
            "POST",
            "/v1/dns/update",
            body=json.dumps({"domain": "test.johnsosoka.com.", "ip": "192.168.1.100"}),
            headers={"x-auth-token": "wrong-token"},
        )

        response = lambda_handler(event, mock_lambda_context)

        assert response["statusCode"] == 403
        body = json.loads(response["body"])
        assert body["error"] == "ForbiddenError"

    def test_update_dns_with_valid_auth_succeeds(self, mock_lambda_context):
        """Test POST /v1/dns/update with valid auth succeeds."""
        event = create_http_api_event(
            "POST",
            "/v1/dns/update",
            body=json.dumps({"domain": "test.johnsosoka.com.", "ip": "192.168.1.100"}),
            headers={"x-auth-token": "test-token-12345"},
        )

        mock_route53 = MagicMock()
        mock_route53.change_resource_record_sets.return_value = {
            "ChangeInfo": {
                "Id": "/change/C123456",
                "Status": "PENDING",
            }
        }

        # Patch the already-instantiated dns_service's client
        from api.handler import dns_service
        with patch.object(dns_service, "route53_client", mock_route53):
            response = lambda_handler(event, mock_lambda_context)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["message"] == "DNS record updated successfully"
        assert body["domain"] == "test.johnsosoka.com."
        assert body["ip"] == "192.168.1.100"
        assert body["change_id"] == "C123456"
        assert body["status"] == "PENDING"

    def test_update_dns_with_case_insensitive_auth_header(self, mock_lambda_context):
        """Test auth header is case-insensitive."""
        event = create_http_api_event(
            "POST",
            "/v1/dns/update",
            body=json.dumps({"domain": "test.johnsosoka.com.", "ip": "192.168.1.100"}),
            headers={"X-Auth-Token": "test-token-12345"},
        )

        mock_route53 = MagicMock()
        mock_route53.change_resource_record_sets.return_value = {
            "ChangeInfo": {
                "Id": "/change/C123456",
                "Status": "PENDING",
            }
        }

        # Patch the already-instantiated dns_service's client
        from api.handler import dns_service
        with patch.object(dns_service, "route53_client", mock_route53):
            response = lambda_handler(event, mock_lambda_context)

        assert response["statusCode"] == 200

    def test_update_dns_invalid_json_returns_400(self, mock_lambda_context):
        """Test invalid JSON body returns 400."""
        event = create_http_api_event(
            "POST",
            "/v1/dns/update",
            body="invalid json {{",
            headers={"x-auth-token": "test-token-12345"},
        )

        response = lambda_handler(event, mock_lambda_context)

        assert response["statusCode"] == 400

    def test_update_dns_missing_domain_returns_400(self, mock_lambda_context):
        """Test request with missing domain field returns 400."""
        event = create_http_api_event(
            "POST",
            "/v1/dns/update",
            body=json.dumps({"ip": "192.168.1.1"}),
            headers={"x-auth-token": "test-token-12345"},
        )

        response = lambda_handler(event, mock_lambda_context)

        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error"] == "ValidationError"

    def test_update_dns_missing_ip_returns_400(self, mock_lambda_context):
        """Test request with missing ip field returns 400."""
        event = create_http_api_event(
            "POST",
            "/v1/dns/update",
            body=json.dumps({"domain": "test.johnsosoka.com."}),
            headers={"x-auth-token": "test-token-12345"},
        )

        response = lambda_handler(event, mock_lambda_context)

        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error"] == "ValidationError"

    def test_update_dns_domain_without_trailing_dot_returns_400(self, mock_lambda_context):
        """Test domain without trailing dot returns 400."""
        event = create_http_api_event(
            "POST",
            "/v1/dns/update",
            body=json.dumps({"domain": "test.johnsosoka.com", "ip": "192.168.1.1"}),
            headers={"x-auth-token": "test-token-12345"},
        )

        response = lambda_handler(event, mock_lambda_context)

        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error"] == "ValidationError"
        assert "trailing dot" in body["message"].lower()

    def test_update_dns_invalid_ipv4_returns_400(self, mock_lambda_context):
        """Test invalid IPv4 address returns 400."""
        event = create_http_api_event(
            "POST",
            "/v1/dns/update",
            body=json.dumps({"domain": "test.johnsosoka.com.", "ip": "999.999.999.999"}),
            headers={"x-auth-token": "test-token-12345"},
        )

        response = lambda_handler(event, mock_lambda_context)

        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error"] == "ValidationError"
        assert "255" in body["message"]

    def test_update_dns_domain_not_in_allowed_zones_returns_403(self, mock_lambda_context):
        """Test domain not in allowed zones returns 403."""
        event = create_http_api_event(
            "POST",
            "/v1/dns/update",
            body=json.dumps({"domain": "notallowed.com.", "ip": "192.168.1.1"}),
            headers={"x-auth-token": "test-token-12345"},
        )

        response = lambda_handler(event, mock_lambda_context)

        assert response["statusCode"] == 403
        body = json.loads(response["body"])
        assert body["error"] == "DomainNotAllowedError"

    def test_update_dns_route53_error_returns_500(self, mock_lambda_context):
        """Test Route53 error returns 500."""
        event = create_http_api_event(
            "POST",
            "/v1/dns/update",
            body=json.dumps({"domain": "test.johnsosoka.com.", "ip": "192.168.1.100"}),
            headers={"x-auth-token": "test-token-12345"},
        )

        from botocore.exceptions import ClientError

        mock_route53 = MagicMock()
        mock_route53.change_resource_record_sets.side_effect = ClientError(
            {"Error": {"Code": "InvalidChangeBatch", "Message": "Invalid request"}},
            "ChangeResourceRecordSets",
        )

        # Patch the already-instantiated dns_service's client
        from api.handler import dns_service
        with patch.object(dns_service, "route53_client", mock_route53):
            response = lambda_handler(event, mock_lambda_context)

        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert body["error"] == "DnsUpdateError"
        assert "Failed to update DNS record" in body["message"]


class TestExceptionHandlers:
    """Test suite for exception handlers."""

    def test_validation_error_handler_formats_errors(self, mock_lambda_context):
        """Test validation error handler formats Pydantic errors correctly."""
        event = create_http_api_event(
            "POST",
            "/v1/dns/update",
            body=json.dumps({"domain": "missing-trailing-dot.com", "ip": "not-an-ip"}),
            headers={"x-auth-token": "test-token-12345"},
        )

        response = lambda_handler(event, mock_lambda_context)

        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error"] == "ValidationError"
        # Should have formatted error messages
        assert "domain" in body["message"].lower() or "ip" in body["message"].lower()

    def test_unexpected_exception_returns_500(self, mock_lambda_context):
        """Test unexpected exceptions return generic 500 error."""
        event = create_http_api_event(
            "POST",
            "/v1/dns/update",
            body=json.dumps({"domain": "test.johnsosoka.com.", "ip": "192.168.1.1"}),
            headers={"x-auth-token": "test-token-12345"},
        )

        mock_route53 = MagicMock()
        mock_route53.change_resource_record_sets.side_effect = Exception("Unexpected error")

        # Patch the already-instantiated dns_service's client
        from api.handler import dns_service
        with patch.object(dns_service, "route53_client", mock_route53):
            response = lambda_handler(event, mock_lambda_context)

        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert body["error"] == "DnsUpdateError"
