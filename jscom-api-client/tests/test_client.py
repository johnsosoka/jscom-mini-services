"""Tests for JscomApiClient."""

import pytest
import responses
from jscom_api import JscomApiClient
from jscom_api.exceptions import (
    AuthenticationError,
    NetworkError,
    ServerError,
    ValidationError,
)
from jscom_api.models import DnsUpdateResponse, IpResponse
from requests.exceptions import ConnectionError, Timeout


class TestGetMyIp:
    """Tests for JscomApiClient.get_my_ip()."""

    def test_success(self, mock_api, client):
        """Test successful IP retrieval."""
        mock_api.add(
            responses.GET,
            "https://api.test.com/v1/ip/my",
            json={"ip": "203.0.113.42"},
            status=200,
        )

        result = client.get_my_ip()

        assert isinstance(result, IpResponse)
        assert result.ip == "203.0.113.42"
        assert len(mock_api.calls) == 1
        assert mock_api.calls[0].request.url == "https://api.test.com/v1/ip/my"

    def test_network_error_connection_failure(self, mock_api, client):
        """Test network error on connection failure."""
        mock_api.add(
            responses.GET,
            "https://api.test.com/v1/ip/my",
            body=ConnectionError("Failed to establish connection"),
        )

        with pytest.raises(NetworkError) as exc_info:
            client.get_my_ip()

        assert "Failed to connect to API" in str(exc_info.value)

    def test_network_error_timeout(self, mock_api, client):
        """Test network error on timeout."""
        mock_api.add(
            responses.GET,
            "https://api.test.com/v1/ip/my",
            body=Timeout("Request timed out"),
        )

        with pytest.raises(NetworkError) as exc_info:
            client.get_my_ip()

        assert "Failed to connect to API" in str(exc_info.value)

    def test_server_error_500(self, mock_api, client):
        """Test server error on 500 response."""
        mock_api.add(
            responses.GET,
            "https://api.test.com/v1/ip/my",
            json={"error": "Internal server error", "message": "Database unavailable"},
            status=500,
        )

        with pytest.raises(ServerError) as exc_info:
            client.get_my_ip()

        assert "Server error" in str(exc_info.value)
        assert "Internal server error" in str(exc_info.value)

    def test_server_error_503(self, mock_api, client):
        """Test server error on 503 response."""
        mock_api.add(
            responses.GET,
            "https://api.test.com/v1/ip/my",
            json={"error": "Service unavailable"},
            status=503,
        )

        with pytest.raises(ServerError) as exc_info:
            client.get_my_ip()

        assert "Server error" in str(exc_info.value)

    def test_unexpected_status_code(self, mock_api, client):
        """Test handling of unexpected status code."""
        mock_api.add(
            responses.GET,
            "https://api.test.com/v1/ip/my",
            json={"error": "Not found"},
            status=404,
        )

        with pytest.raises(NetworkError) as exc_info:
            client.get_my_ip()

        assert "Unexpected status 404" in str(exc_info.value)

    def test_invalid_json_response(self, mock_api, client):
        """Test handling of invalid JSON response."""
        mock_api.add(
            responses.GET,
            "https://api.test.com/v1/ip/my",
            body="not valid json",
            status=200,
        )

        with pytest.raises(NetworkError) as exc_info:
            client.get_my_ip()

        assert "Invalid JSON response" in str(exc_info.value)

    def test_missing_ip_field(self, mock_api, client):
        """Test handling of response missing required 'ip' field."""
        mock_api.add(
            responses.GET,
            "https://api.test.com/v1/ip/my",
            json={"address": "203.0.113.42"},  # Wrong field name
            status=200,
        )

        with pytest.raises(ValidationError) as exc_info:
            client.get_my_ip()

        assert "missing required field" in str(exc_info.value)


class TestUpdateDns:
    """Tests for JscomApiClient.update_dns()."""

    def test_success(self, mock_api, client):
        """Test successful DNS update."""
        mock_api.add(
            responses.POST,
            "https://api.test.com/v1/dns/update",
            json={
                "message": "DNS record updated successfully",
                "change_info": {
                    "id": "C1234567890ABC",
                    "status": "PENDING",
                    "submitted_at": "2025-11-27T12:00:00Z",
                },
            },
            status=200,
        )

        result = client.update_dns(domain="mc.example.com.", ip="203.0.113.42")

        assert isinstance(result, DnsUpdateResponse)
        assert result.message == "DNS record updated successfully"
        assert result.change_info["id"] == "C1234567890ABC"
        assert result.change_info["status"] == "PENDING"

        # Verify request
        assert len(mock_api.calls) == 1
        request = mock_api.calls[0].request
        assert request.url == "https://api.test.com/v1/dns/update"
        assert request.headers["x-auth-token"] == "test-token-12345"
        assert request.headers["Content-Type"] == "application/json"

        # Parse request body
        import json

        body = json.loads(request.body)
        assert body["domain"] == "mc.example.com."
        assert body["ip"] == "203.0.113.42"

    def test_success_no_auth_token(self, mock_api, client_no_auth):
        """Test DNS update without auth token in headers."""
        mock_api.add(
            responses.POST,
            "https://api.test.com/v1/dns/update",
            json={
                "message": "DNS record updated",
                "change_info": {},
            },
            status=200,
        )

        result = client_no_auth.update_dns(domain="test.com.", ip="1.2.3.4")

        assert isinstance(result, DnsUpdateResponse)
        request = mock_api.calls[0].request
        assert "x-auth-token" not in request.headers

    def test_authentication_error_403(self, mock_api, client):
        """Test authentication error on 403 response."""
        mock_api.add(
            responses.POST,
            "https://api.test.com/v1/dns/update",
            json={"error": "Forbidden", "message": "Invalid or missing authentication token"},
            status=403,
        )

        with pytest.raises(AuthenticationError) as exc_info:
            client.update_dns(domain="mc.example.com.", ip="203.0.113.42")

        assert "Authentication failed" in str(exc_info.value)
        assert "Forbidden" in str(exc_info.value)

    def test_validation_error_400_invalid_json(self, mock_api, client):
        """Test validation error on 400 response with invalid JSON."""
        mock_api.add(
            responses.POST,
            "https://api.test.com/v1/dns/update",
            json={
                "error": "Bad Request",
                "message": "Invalid JSON format",
            },
            status=400,
        )

        with pytest.raises(ValidationError) as exc_info:
            client.update_dns(domain="mc.example.com.", ip="203.0.113.42")

        assert "Validation error" in str(exc_info.value)
        assert "Bad Request" in str(exc_info.value)

    def test_validation_error_400_missing_params(self, mock_api, client):
        """Test validation error on 400 response with missing parameters."""
        mock_api.add(
            responses.POST,
            "https://api.test.com/v1/dns/update",
            json={
                "error": "Bad Request",
                "message": "Missing required field: domain",
            },
            status=400,
        )

        with pytest.raises(ValidationError) as exc_info:
            client.update_dns(domain="", ip="203.0.113.42")

        assert "Validation error" in str(exc_info.value)
        assert "Missing required field" in str(exc_info.value)

    def test_validation_error_400_invalid_domain(self, mock_api, client):
        """Test validation error for invalid domain format."""
        mock_api.add(
            responses.POST,
            "https://api.test.com/v1/dns/update",
            json={
                "error": "Bad Request",
                "message": "Domain must include trailing dot",
            },
            status=400,
        )

        with pytest.raises(ValidationError) as exc_info:
            client.update_dns(domain="mc.example.com", ip="203.0.113.42")

        assert "Validation error" in str(exc_info.value)
        assert "trailing dot" in str(exc_info.value)

    def test_server_error_500(self, mock_api, client):
        """Test server error on 500 response."""
        mock_api.add(
            responses.POST,
            "https://api.test.com/v1/dns/update",
            json={"error": "Internal server error", "message": "Route53 API failure"},
            status=500,
        )

        with pytest.raises(ServerError) as exc_info:
            client.update_dns(domain="mc.example.com.", ip="203.0.113.42")

        assert "Server error" in str(exc_info.value)
        assert "Internal server error" in str(exc_info.value)

    def test_server_error_502(self, mock_api, client):
        """Test server error on 502 response."""
        mock_api.add(
            responses.POST,
            "https://api.test.com/v1/dns/update",
            json={"error": "Bad Gateway"},
            status=502,
        )

        with pytest.raises(ServerError) as exc_info:
            client.update_dns(domain="mc.example.com.", ip="203.0.113.42")

        assert "Server error" in str(exc_info.value)

    def test_network_error_connection_failure(self, mock_api, client):
        """Test network error on connection failure."""
        mock_api.add(
            responses.POST,
            "https://api.test.com/v1/dns/update",
            body=ConnectionError("Connection refused"),
        )

        with pytest.raises(NetworkError) as exc_info:
            client.update_dns(domain="mc.example.com.", ip="203.0.113.42")

        assert "Failed to connect to API" in str(exc_info.value)

    def test_network_error_timeout(self, mock_api, client):
        """Test network error on timeout."""
        mock_api.add(
            responses.POST,
            "https://api.test.com/v1/dns/update",
            body=Timeout("Request timed out after 30 seconds"),
        )

        with pytest.raises(NetworkError) as exc_info:
            client.update_dns(domain="mc.example.com.", ip="203.0.113.42")

        assert "Failed to connect to API" in str(exc_info.value)

    def test_invalid_json_response(self, mock_api, client):
        """Test handling of invalid JSON response."""
        mock_api.add(
            responses.POST,
            "https://api.test.com/v1/dns/update",
            body="<html>Server Error</html>",
            status=200,
        )

        with pytest.raises(NetworkError) as exc_info:
            client.update_dns(domain="mc.example.com.", ip="203.0.113.42")

        assert "Invalid JSON response" in str(exc_info.value)

    def test_unexpected_status_code(self, mock_api, client):
        """Test handling of unexpected status code."""
        mock_api.add(
            responses.POST,
            "https://api.test.com/v1/dns/update",
            json={"error": "Not found"},
            status=404,
        )

        with pytest.raises(NetworkError) as exc_info:
            client.update_dns(domain="mc.example.com.", ip="203.0.113.42")

        assert "Unexpected status 404" in str(exc_info.value)


class TestClientContextManager:
    """Tests for JscomApiClient context manager functionality."""

    def test_context_manager_usage(self, mock_api):
        """Test client as context manager."""
        mock_api.add(
            responses.GET,
            "https://api.test.com/v1/ip/my",
            json={"ip": "203.0.113.42"},
            status=200,
        )

        with JscomApiClient(base_url="https://api.test.com") as client:
            result = client.get_my_ip()
            assert result.ip == "203.0.113.42"

        # Session should be closed after exiting context
        assert client._session is not None  # Session object still exists

    def test_manual_close(self, client):
        """Test manual close method."""
        assert client._session is not None
        client.close()
        # Session should remain accessible but closed
        assert client._session is not None


class TestClientConfiguration:
    """Tests for JscomApiClient configuration."""

    def test_default_configuration(self):
        """Test client with default configuration."""
        client = JscomApiClient()
        assert client.base_url == "https://api.johnsosoka.com"
        assert client.auth_token is None
        assert client.timeout == 30.0

    def test_custom_configuration(self):
        """Test client with custom configuration."""
        client = JscomApiClient(
            base_url="https://custom.api.com",
            auth_token="custom-token",
            timeout=60.0,
        )
        assert client.base_url == "https://custom.api.com"
        assert client.auth_token == "custom-token"
        assert client.timeout == 60.0

    def test_base_url_trailing_slash_removal(self):
        """Test that trailing slash is removed from base URL."""
        client = JscomApiClient(base_url="https://api.test.com/")
        assert client.base_url == "https://api.test.com"

    def test_base_url_multiple_trailing_slashes(self):
        """Test that multiple trailing slashes are removed."""
        client = JscomApiClient(base_url="https://api.test.com///")
        assert client.base_url == "https://api.test.com"


class TestErrorResponseParsing:
    """Tests for error response parsing."""

    def test_error_with_message(self, mock_api, client):
        """Test parsing error response with both error and message fields."""
        mock_api.add(
            responses.GET,
            "https://api.test.com/v1/ip/my",
            json={"error": "InternalError", "message": "Database connection failed"},
            status=500,
        )

        with pytest.raises(ServerError) as exc_info:
            client.get_my_ip()

        error_msg = str(exc_info.value)
        assert "InternalError" in error_msg
        assert "Database connection failed" in error_msg

    def test_error_without_message(self, mock_api, client):
        """Test parsing error response with only error field."""
        mock_api.add(
            responses.GET,
            "https://api.test.com/v1/ip/my",
            json={"error": "ServiceUnavailable"},
            status=503,
        )

        with pytest.raises(ServerError) as exc_info:
            client.get_my_ip()

        assert "ServiceUnavailable" in str(exc_info.value)

    def test_error_non_json_response(self, mock_api, client):
        """Test parsing non-JSON error response."""
        mock_api.add(
            responses.GET,
            "https://api.test.com/v1/ip/my",
            body="Plain text error message",
            status=500,
        )

        with pytest.raises(ServerError) as exc_info:
            client.get_my_ip()

        assert "Plain text error message" in str(exc_info.value)

    def test_error_empty_response(self, mock_api, client):
        """Test parsing empty error response."""
        mock_api.add(
            responses.GET,
            "https://api.test.com/v1/ip/my",
            body="",
            status=500,
        )

        with pytest.raises(ServerError) as exc_info:
            client.get_my_ip()

        assert "HTTP 500" in str(exc_info.value)
