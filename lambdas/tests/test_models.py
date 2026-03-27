"""Tests for Pydantic models."""

import pytest
from pydantic import ValidationError

from api.models import (
    IpResponse,
    DnsUpdateRequest,
    DnsUpdateResponse,
    ErrorResponse,
)


class TestIpResponse:
    """Test suite for IpResponse model."""

    def test_ip_response_serialization(self):
        """Test IpResponse model creates and serializes correctly."""
        response = IpResponse(ip="192.168.1.1")

        assert response.ip == "192.168.1.1"
        assert response.model_dump() == {"ip": "192.168.1.1"}

    def test_ip_response_json_serialization(self):
        """Test IpResponse serializes to JSON correctly."""
        response = IpResponse(ip="10.0.0.1")

        json_str = response.model_dump_json()
        assert '"ip":"10.0.0.1"' in json_str.replace(" ", "")


class TestDnsUpdateRequest:
    """Test suite for DnsUpdateRequest model."""

    def test_valid_domain_with_trailing_dot(self):
        """Test DnsUpdateRequest accepts valid domain with trailing dot."""
        request = DnsUpdateRequest(
            domain="johnsosoka.com.",
            ip="192.168.1.1",
        )

        assert request.domain == "johnsosoka.com."
        assert request.ip == "192.168.1.1"

    def test_valid_subdomain_with_trailing_dot(self):
        """Test DnsUpdateRequest accepts subdomain with trailing dot."""
        request = DnsUpdateRequest(
            domain="sub.johnsosoka.com.",
            ip="192.168.1.1",
        )

        assert request.domain == "sub.johnsosoka.com."
        assert request.ip == "192.168.1.1"

    def test_invalid_domain_without_trailing_dot(self):
        """Test DnsUpdateRequest raises ValidationError for domain without trailing dot."""
        with pytest.raises(ValidationError) as exc_info:
            DnsUpdateRequest(
                domain="johnsosoka.com",
                ip="192.168.1.1",
            )

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("domain",)
        assert "trailing dot" in errors[0]["msg"].lower()

    def test_valid_ipv4_address(self):
        """Test DnsUpdateRequest accepts valid IPv4 address."""
        request = DnsUpdateRequest(
            domain="test.com.",
            ip="192.168.1.100",
        )

        assert request.ip == "192.168.1.100"

    def test_valid_ipv4_edge_cases(self):
        """Test DnsUpdateRequest accepts IPv4 addresses at valid boundaries."""
        # Test 0.0.0.0
        request = DnsUpdateRequest(domain="test.com.", ip="0.0.0.0")
        assert request.ip == "0.0.0.0"

        # Test 255.255.255.255
        request = DnsUpdateRequest(domain="test.com.", ip="255.255.255.255")
        assert request.ip == "255.255.255.255"

        # Test 127.0.0.1
        request = DnsUpdateRequest(domain="test.com.", ip="127.0.0.1")
        assert request.ip == "127.0.0.1"

    def test_invalid_ipv4_not_enough_octets(self):
        """Test DnsUpdateRequest raises ValidationError for incomplete IPv4."""
        with pytest.raises(ValidationError) as exc_info:
            DnsUpdateRequest(
                domain="test.com.",
                ip="192.168.1",
            )

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("ip",)
        assert "valid IPv4" in errors[0]["msg"]

    def test_invalid_ipv4_too_many_octets(self):
        """Test DnsUpdateRequest raises ValidationError for too many octets."""
        with pytest.raises(ValidationError) as exc_info:
            DnsUpdateRequest(
                domain="test.com.",
                ip="192.168.1.1.1",
            )

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("ip",)
        assert "valid IPv4" in errors[0]["msg"]

    def test_invalid_ipv4_octet_exceeds_255(self):
        """Test DnsUpdateRequest raises ValidationError when octet exceeds 255."""
        with pytest.raises(ValidationError) as exc_info:
            DnsUpdateRequest(
                domain="test.com.",
                ip="192.168.1.256",
            )

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("ip",)
        assert "0 and 255" in errors[0]["msg"]

    def test_invalid_ipv4_octet_way_over_255(self):
        """Test DnsUpdateRequest raises ValidationError when octet is much larger."""
        with pytest.raises(ValidationError) as exc_info:
            DnsUpdateRequest(
                domain="test.com.",
                ip="999.999.999.999",
            )

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("ip",)
        assert "0 and 255" in errors[0]["msg"]

    def test_invalid_ipv4_non_numeric(self):
        """Test DnsUpdateRequest raises ValidationError for non-numeric octets."""
        with pytest.raises(ValidationError) as exc_info:
            DnsUpdateRequest(
                domain="test.com.",
                ip="192.168.one.1",
            )

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("ip",)
        assert "valid IPv4" in errors[0]["msg"]

    def test_invalid_ipv4_empty_string(self):
        """Test DnsUpdateRequest raises ValidationError for empty IP."""
        with pytest.raises(ValidationError) as exc_info:
            DnsUpdateRequest(
                domain="test.com.",
                ip="",
            )

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("ip",)

    def test_invalid_domain_invalid_characters(self):
        """Test DnsUpdateRequest raises ValidationError for invalid domain characters."""
        with pytest.raises(ValidationError) as exc_info:
            DnsUpdateRequest(
                domain="test_invalid.com.",
                ip="192.168.1.1",
            )

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("domain",)
        assert "valid DNS characters" in errors[0]["msg"]

    def test_valid_domain_with_hyphens(self):
        """Test DnsUpdateRequest accepts domain with hyphens."""
        request = DnsUpdateRequest(
            domain="my-test-domain.com.",
            ip="192.168.1.1",
        )

        assert request.domain == "my-test-domain.com."

    def test_model_serialization(self):
        """Test DnsUpdateRequest serializes correctly."""
        request = DnsUpdateRequest(
            domain="test.com.",
            ip="192.168.1.1",
        )

        data = request.model_dump()
        assert data == {
            "domain": "test.com.",
            "ip": "192.168.1.1",
        }


class TestDnsUpdateResponse:
    """Test suite for DnsUpdateResponse model."""

    def test_dns_update_response_serialization(self):
        """Test DnsUpdateResponse creates and serializes correctly."""
        response = DnsUpdateResponse(
            message="DNS record updated successfully",
            domain="test.com.",
            ip="192.168.1.1",
            change_id="C123456",
            status="PENDING",
        )

        assert response.message == "DNS record updated successfully"
        assert response.domain == "test.com."
        assert response.ip == "192.168.1.1"
        assert response.change_id == "C123456"
        assert response.status == "PENDING"

    def test_dns_update_response_to_dict(self):
        """Test DnsUpdateResponse converts to dictionary correctly."""
        response = DnsUpdateResponse(
            message="Success",
            domain="example.com.",
            ip="10.0.0.1",
            change_id="C999",
            status="INSYNC",
        )

        data = response.model_dump()
        assert data == {
            "message": "Success",
            "domain": "example.com.",
            "ip": "10.0.0.1",
            "change_id": "C999",
            "status": "INSYNC",
        }


class TestErrorResponse:
    """Test suite for ErrorResponse model."""

    def test_error_response_serialization(self):
        """Test ErrorResponse creates and serializes correctly."""
        response = ErrorResponse(
            error="ValidationError",
            message="Invalid input provided",
        )

        assert response.error == "ValidationError"
        assert response.message == "Invalid input provided"

    def test_error_response_to_dict(self):
        """Test ErrorResponse converts to dictionary correctly."""
        response = ErrorResponse(
            error="NotFoundError",
            message="Resource not found",
        )

        data = response.model_dump()
        assert data == {
            "error": "NotFoundError",
            "message": "Resource not found",
        }

    def test_error_response_json_serialization(self):
        """Test ErrorResponse serializes to JSON correctly."""
        response = ErrorResponse(
            error="ServerError",
            message="Internal server error",
        )

        json_str = response.model_dump_json()
        assert '"error":"ServerError"' in json_str
        assert '"message":"Internal server error"' in json_str
