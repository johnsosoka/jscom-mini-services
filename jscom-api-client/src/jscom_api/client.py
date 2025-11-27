"""API client for jscom-mini-services."""

import requests
from requests.exceptions import RequestException

from jscom_api.exceptions import (
    AuthenticationError,
    NetworkError,
    ServerError,
    ValidationError,
)
from jscom_api.models import DnsUpdateResponse, IpResponse


class JscomApiClient:
    """Synchronous client for jscom-mini-services API."""

    def __init__(
        self,
        base_url: str = "https://api.johnsosoka.com",
        auth_token: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        """Initialize the API client.

        Args:
            base_url: Base URL for the API
            auth_token: Authentication token for protected endpoints
            timeout: Request timeout in seconds

        Raises:
            ValueError: If timeout is not positive
        """
        if timeout <= 0:
            raise ValueError(f"timeout must be positive, got {timeout}")
        self.base_url = base_url.rstrip("/")
        self.auth_token = auth_token
        self.timeout = timeout
        self._session = requests.Session()

    def get_my_ip(self) -> IpResponse:
        """Retrieve the client's public IP address.

        Returns:
            IpResponse with the client's public IP

        Raises:
            NetworkError: If the request fails
            ServerError: If the server returns 5xx
        """
        url = f"{self.base_url}/v1/ip/my"

        try:
            response = self._session.get(url, timeout=self.timeout)
        except RequestException as e:
            raise NetworkError(f"Failed to connect to API: {e}") from e

        if response.status_code >= 500:
            error_data = self._parse_error_response(response)
            raise ServerError(f"Server error: {error_data}") from None

        if response.status_code != 200:
            error_data = self._parse_error_response(response)
            raise NetworkError(f"Unexpected status {response.status_code}: {error_data}") from None

        try:
            data = response.json()
        except ValueError as e:
            raise NetworkError(f"Invalid JSON response: {e}") from e

        try:
            return IpResponse(ip=data["ip"])
        except KeyError as e:
            raise ValidationError(f"API response missing required field: {e}") from e

    def update_dns(self, domain: str, ip: str) -> DnsUpdateResponse:
        """Update a DNS A record in Route53.

        Args:
            domain: The domain name (must include trailing dot, e.g., "mc.example.com.")
            ip: The IP address to set

        Returns:
            DnsUpdateResponse with success message and change info

        Raises:
            AuthenticationError: If token is invalid (403)
            ValidationError: If request is invalid (400)
            ServerError: If server error occurs (500)
            NetworkError: If the request fails
        """
        url = f"{self.base_url}/v1/dns/update"
        headers = {
            "Content-Type": "application/json",
        }

        if self.auth_token:
            headers["x-auth-token"] = self.auth_token

        payload = {
            "domain": domain,
            "ip": ip,
        }

        try:
            response = self._session.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
        except RequestException as e:
            raise NetworkError(f"Failed to connect to API: {e}") from e

        if response.status_code == 403:
            error_data = self._parse_error_response(response)
            raise AuthenticationError(f"Authentication failed: {error_data}") from None

        if response.status_code == 400:
            error_data = self._parse_error_response(response)
            raise ValidationError(f"Validation error: {error_data}") from None

        if response.status_code >= 500:
            error_data = self._parse_error_response(response)
            raise ServerError(f"Server error: {error_data}") from None

        if response.status_code != 200:
            error_data = self._parse_error_response(response)
            raise NetworkError(f"Unexpected status {response.status_code}: {error_data}") from None

        try:
            data = response.json()
        except ValueError as e:
            raise NetworkError(f"Invalid JSON response: {e}") from e

        try:
            return DnsUpdateResponse(
                message=data["message"],
                change_info=data["change_info"],
            )
        except KeyError as e:
            raise ValidationError(f"API response missing required field: {e}") from e

    def _parse_error_response(self, response: requests.Response) -> str:
        """Parse error response from API.

        Args:
            response: The HTTP response object

        Returns:
            Error message string
        """
        try:
            error_data = response.json()
            if "error" in error_data:
                if "message" in error_data:
                    return f"{error_data['error']}: {error_data['message']}"
                return str(error_data["error"])
            return str(error_data)
        except ValueError:
            return response.text or f"HTTP {response.status_code}"

    def close(self) -> None:
        """Close the HTTP session."""
        self._session.close()

    def __enter__(self) -> "JscomApiClient":
        """Context manager entry."""
        return self

    def __exit__(self, *args: object) -> None:
        """Context manager exit."""
        self.close()
