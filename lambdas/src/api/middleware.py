"""Middleware decorators for request processing."""

import secrets
from functools import wraps
from typing import Callable, Any

from .config import AppConfig
from .exceptions import UnauthorizedError, ForbiddenError


def require_auth(config: AppConfig) -> Callable:
    """
    Decorator factory for authentication requirement.

    Checks the x-auth-token header against the configured auth token.
    Returns appropriate error responses for missing or invalid tokens.

    Args:
        config: Application configuration containing the auth token

    Returns:
        Decorator function that enforces authentication

    Example:
        @app.post("/protected")
        @require_auth(config)
        def protected_endpoint():
            return {"message": "success"}
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Import app here to avoid circular import
            from .handler import app

            # Get headers from current event (case-insensitive lookup)
            headers = app.current_event.headers or {}

            # Look for x-auth-token header (case-insensitive)
            auth_token = None
            for key, value in headers.items():
                if key.lower() == "x-auth-token":
                    auth_token = value
                    break

            # Check if token is present
            if not auth_token:
                raise UnauthorizedError("Missing authentication token")

            # Verify token matches (constant-time comparison to prevent timing attacks)
            if not secrets.compare_digest(auth_token, config.auth_token):
                raise ForbiddenError("Invalid authentication token")

            # Token is valid, proceed with the request
            return func(*args, **kwargs)

        return wrapper

    return decorator
