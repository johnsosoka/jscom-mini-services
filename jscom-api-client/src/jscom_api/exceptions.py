"""Exceptions for jscom-api client."""


class JscomApiError(Exception):
    """Base exception for all API errors."""


class AuthenticationError(JscomApiError):
    """Raised when authentication fails (403)."""


class ValidationError(JscomApiError):
    """Raised when request validation fails (400)."""


class ServerError(JscomApiError):
    """Raised when server returns 5xx error."""


class NetworkError(JscomApiError):
    """Raised when network request fails."""
