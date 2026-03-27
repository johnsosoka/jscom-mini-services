"""Custom exceptions for the consolidated Lambda API."""


class ApiException(Exception):
    """Base exception for API errors with HTTP status codes."""

    def __init__(self, message: str, status_code: int):
        """
        Initialize API exception.

        Args:
            message: Human-readable error message
            status_code: HTTP status code
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class UnauthorizedError(ApiException):
    """Raised when authentication credentials are missing."""

    def __init__(self, message: str = "Authentication required"):
        """Initialize with 401 status code."""
        super().__init__(message, status_code=401)


class ForbiddenError(ApiException):
    """Raised when authentication credentials are invalid."""

    def __init__(self, message: str = "Invalid authentication credentials"):
        """Initialize with 403 status code."""
        super().__init__(message, status_code=403)


class ValidationError(ApiException):
    """Raised when request validation fails."""

    def __init__(self, message: str):
        """Initialize with 400 status code."""
        super().__init__(message, status_code=400)


class DomainNotAllowedError(ApiException):
    """Raised when a domain is not in the allowed zones list."""

    def __init__(self, domain: str):
        """
        Initialize with 403 status code.

        Args:
            domain: The domain that was not allowed
        """
        message = f"Domain '{domain}' is not in the allowed zones list"
        super().__init__(message, status_code=403)


class DnsUpdateError(ApiException):
    """Raised when DNS record update fails."""

    def __init__(self, message: str):
        """Initialize with 500 status code."""
        super().__init__(message, status_code=500)
