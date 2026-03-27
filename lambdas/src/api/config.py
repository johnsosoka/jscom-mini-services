"""Configuration management for the consolidated Lambda API."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ZoneConfig:
    """Route53 hosted zone configuration."""

    domain: str
    zone_id: str


@dataclass
class AppConfig:
    """Application configuration loaded from environment variables."""

    auth_token: str
    allowed_zones: list[ZoneConfig]
    default_ttl: int = 300

    @classmethod
    def from_env(cls) -> "AppConfig":
        """
        Load configuration from environment variables.

        Environment Variables:
            AUTH_TOKEN: Authentication token for protected endpoints
            ALLOWED_ZONES: Comma-separated domain:zone_id pairs
            DEFAULT_TTL: Optional TTL for DNS records (default: 300)

        Returns:
            AppConfig: Configured application instance

        Raises:
            ValueError: If required environment variables are missing or invalid
        """
        auth_token = os.environ.get("AUTH_TOKEN")
        if not auth_token:
            raise ValueError("AUTH_TOKEN environment variable is required")

        zones_str = os.environ.get("ALLOWED_ZONES")
        if not zones_str:
            raise ValueError("ALLOWED_ZONES environment variable is required")

        # Parse ALLOWED_ZONES format: "domain:zone_id,domain:zone_id,..."
        allowed_zones = []
        for entry in zones_str.split(","):
            entry = entry.strip()
            if not entry:
                continue

            parts = entry.split(":")
            if len(parts) != 2:
                raise ValueError(
                    f"Invalid ALLOWED_ZONES format: '{entry}'. Expected 'domain:zone_id'"
                )

            domain, zone_id = parts
            allowed_zones.append(ZoneConfig(domain=domain.strip(), zone_id=zone_id.strip()))

        if not allowed_zones:
            raise ValueError("At least one zone must be configured in ALLOWED_ZONES")

        # Parse optional DEFAULT_TTL
        default_ttl = 300
        ttl_str = os.environ.get("DEFAULT_TTL")
        if ttl_str:
            try:
                default_ttl = int(ttl_str)
            except ValueError:
                raise ValueError(f"DEFAULT_TTL must be an integer, got: '{ttl_str}'")

        return cls(
            auth_token=auth_token,
            allowed_zones=allowed_zones,
            default_ttl=default_ttl,
        )

    def get_zone_for_domain(self, domain: str) -> ZoneConfig | None:
        """
        Find the appropriate zone configuration for a given domain.

        Matches by checking if the domain equals the zone domain or is a subdomain.
        Prevents partial matches (e.g., "notexample.com" won't match "example.com").

        Args:
            domain: Fully qualified domain name (e.g., "subdomain.example.com.")

        Returns:
            ZoneConfig if a matching zone is found, None otherwise
        """
        # Normalize by removing trailing dot
        normalized_domain = domain.rstrip(".")

        for zone in self.allowed_zones:
            normalized_zone = zone.domain.rstrip(".")

            # Exact match
            if normalized_domain == normalized_zone:
                return zone

            # Subdomain match: domain must end with ".{zone_domain}"
            if normalized_domain.endswith(f".{normalized_zone}"):
                return zone

        return None
