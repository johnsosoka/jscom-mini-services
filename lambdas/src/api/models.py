"""Pydantic models for request and response validation."""

import re
from pydantic import BaseModel, field_validator


class IpResponse(BaseModel):
    """Response model for IP lookup endpoint."""

    ip: str


class DnsUpdateRequest(BaseModel):
    """Request model for DNS update endpoint."""

    domain: str
    ip: str

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, v: str) -> str:
        """
        Validate domain format.

        Domain must end with a trailing dot and contain valid DNS characters.

        Args:
            v: Domain string to validate

        Returns:
            Validated domain string

        Raises:
            ValueError: If domain format is invalid
        """
        if not v.endswith("."):
            raise ValueError("Domain must end with a trailing dot (.)")

        # Basic DNS name validation (allows subdomains)
        # Pattern: alphanumeric and hyphens, separated by dots, ending with dot
        pattern = r"^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+$"
        if not re.match(pattern, v):
            raise ValueError(
                "Domain must contain valid DNS characters (alphanumeric and hyphens)"
            )

        return v

    @field_validator("ip")
    @classmethod
    def validate_ip(cls, v: str) -> str:
        """
        Validate IPv4 address format.

        Args:
            v: IP address string to validate

        Returns:
            Validated IP address string

        Raises:
            ValueError: If IP address format is invalid
        """
        # IPv4 validation pattern
        pattern = r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$"
        match = re.match(pattern, v)

        if not match:
            raise ValueError("IP must be a valid IPv4 address")

        # Verify each octet is 0-255
        for octet in match.groups():
            if int(octet) > 255:
                raise ValueError("IP address octets must be between 0 and 255")

        return v


class DnsUpdateResponse(BaseModel):
    """Response model for DNS update endpoint."""

    message: str
    domain: str
    ip: str
    change_id: str
    status: str


class ErrorResponse(BaseModel):
    """Generic error response model."""

    error: str
    message: str
