"""Data models for jscom-api client."""

from dataclasses import dataclass


@dataclass(frozen=True)
class IpResponse:
    """Response from GET /v1/ip/my."""

    ip: str


@dataclass(frozen=True)
class DnsUpdateResponse:
    """Response from POST /v1/dns/update."""

    message: str
    domain: str
    ip: str
    change_id: str
    status: str
