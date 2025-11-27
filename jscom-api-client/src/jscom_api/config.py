"""Configuration management for jscom-api client."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    """Configuration for jscom-api client."""

    base_url: str = "https://api.johnsosoka.com"
    auth_token: str | None = None
    timeout: float = 30.0


def load_config(
    base_url: str | None = None,
    auth_token: str | None = None,
    timeout: float | None = None,
) -> Config:
    """Load configuration with priority: args > env > defaults.

    Args:
        base_url: API base URL (overrides JSCOM_API_BASE_URL env var)
        auth_token: Authentication token (overrides JSCOM_API_TOKEN env var)
        timeout: Request timeout in seconds (overrides JSCOM_API_TIMEOUT env var)

    Returns:
        Config instance with resolved settings
    """
    default_config = Config()

    resolved_base_url = (
        base_url or os.getenv("JSCOM_API_BASE_URL") or default_config.base_url
    )

    resolved_auth_token = auth_token or os.getenv("JSCOM_API_TOKEN")

    resolved_timeout = timeout
    if resolved_timeout is None:
        env_timeout = os.getenv("JSCOM_API_TIMEOUT")
        if env_timeout:
            try:
                resolved_timeout = float(env_timeout)
            except ValueError:
                resolved_timeout = default_config.timeout
        else:
            resolved_timeout = default_config.timeout

    return Config(
        base_url=resolved_base_url,
        auth_token=resolved_auth_token,
        timeout=resolved_timeout,
    )
