"""Data models for jscom-api client."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class IpResponse:
    """Response from GET /v1/ip/my."""

    ip: str


@dataclass(frozen=True)
class DnsUpdateResponse:
    """Response from POST /v1/dns/update."""

    message: str
    change_info: dict[str, Any]
