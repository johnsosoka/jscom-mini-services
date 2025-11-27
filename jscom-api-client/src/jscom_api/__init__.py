"""jscom-api: CLI and Python client for jscom-mini-services API."""

from jscom_api.client import JscomApiClient
from jscom_api.config import Config, load_config
from jscom_api.exceptions import (
    AuthenticationError,
    JscomApiError,
    NetworkError,
    ServerError,
    ValidationError,
)
from jscom_api.models import DnsUpdateResponse, IpResponse

__all__ = [
    "JscomApiClient",
    "Config",
    "load_config",
    "JscomApiError",
    "AuthenticationError",
    "ValidationError",
    "ServerError",
    "NetworkError",
    "IpResponse",
    "DnsUpdateResponse",
]

__version__ = "0.1.0"
