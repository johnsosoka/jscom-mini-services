"""Tests for DnsService."""

import pytest
from unittest.mock import MagicMock, patch
from botocore.exceptions import ClientError

from api.config import AppConfig, ZoneConfig
from api.models import DnsUpdateRequest, DnsUpdateResponse
from api.services.dns_service import DnsService
from api.exceptions import DomainNotAllowedError, DnsUpdateError


class TestDnsService:
    """Test suite for DnsService class."""

    @pytest.fixture
    def app_config(self):
        """Create test AppConfig instance."""
        return AppConfig(
            auth_token="test-token",
            allowed_zones=[
                ZoneConfig(domain="johnsosoka.com.", zone_id="Z123456"),
                ZoneConfig(domain="example.com.", zone_id="Z789012"),
            ],
            default_ttl=300,
        )

    @pytest.fixture
    def mock_route53(self):
        """Create mock Route53 client."""
        mock_client = MagicMock()
        mock_client.change_resource_record_sets.return_value = {
            "ChangeInfo": {
                "Id": "/change/C1234567890ABC",
                "Status": "PENDING",
                "SubmittedAt": "2025-12-22T12:00:00.000Z",
            }
        }
        return mock_client

    @pytest.fixture
    def dns_service(self, app_config, mock_route53):
        """Create DnsService instance with mocked Route53 client."""
        with patch("api.services.dns_service.boto3.client", return_value=mock_route53):
            service = DnsService(app_config)
            service.route53_client = mock_route53
            return service

    def test_update_record_success(self, dns_service, mock_route53):
        """Test successful DNS record update returns correct response."""
        request = DnsUpdateRequest(
            domain="test.johnsosoka.com.",
            ip="192.168.1.100",
        )

        response = dns_service.update_record(request)

        # Verify response
        assert isinstance(response, DnsUpdateResponse)
        assert response.message == "DNS record updated successfully"
        assert response.domain == "test.johnsosoka.com."
        assert response.ip == "192.168.1.100"
        assert response.change_id == "C1234567890ABC"
        assert response.status == "PENDING"

        # Verify Route53 was called with correct parameters
        mock_route53.change_resource_record_sets.assert_called_once()
        call_args = mock_route53.change_resource_record_sets.call_args

        assert call_args.kwargs["HostedZoneId"] == "Z123456"
        assert call_args.kwargs["ChangeBatch"]["Changes"][0]["Action"] == "UPSERT"
        assert call_args.kwargs["ChangeBatch"]["Changes"][0]["ResourceRecordSet"]["Name"] == "test.johnsosoka.com."
        assert call_args.kwargs["ChangeBatch"]["Changes"][0]["ResourceRecordSet"]["Type"] == "A"
        assert call_args.kwargs["ChangeBatch"]["Changes"][0]["ResourceRecordSet"]["TTL"] == 300
        assert call_args.kwargs["ChangeBatch"]["Changes"][0]["ResourceRecordSet"]["ResourceRecords"][0]["Value"] == "192.168.1.100"

    def test_update_record_with_exact_domain_match(self, dns_service, mock_route53):
        """Test update with exact domain match uses correct zone."""
        request = DnsUpdateRequest(
            domain="johnsosoka.com.",
            ip="10.0.0.1",
        )

        response = dns_service.update_record(request)

        assert response.domain == "johnsosoka.com."
        mock_route53.change_resource_record_sets.assert_called_once()
        call_args = mock_route53.change_resource_record_sets.call_args
        assert call_args.kwargs["HostedZoneId"] == "Z123456"

    def test_update_record_with_different_zone(self, dns_service, mock_route53):
        """Test update with different allowed zone."""
        request = DnsUpdateRequest(
            domain="test.example.com.",
            ip="172.16.0.1",
        )

        response = dns_service.update_record(request)

        assert response.domain == "test.example.com."
        mock_route53.change_resource_record_sets.assert_called_once()
        call_args = mock_route53.change_resource_record_sets.call_args
        assert call_args.kwargs["HostedZoneId"] == "Z789012"

    def test_update_record_custom_ttl(self):
        """Test DNS update uses custom TTL from config."""
        config = AppConfig(
            auth_token="test-token",
            allowed_zones=[
                ZoneConfig(domain="johnsosoka.com.", zone_id="Z123456"),
            ],
            default_ttl=600,
        )

        mock_route53 = MagicMock()
        mock_route53.change_resource_record_sets.return_value = {
            "ChangeInfo": {
                "Id": "/change/C999",
                "Status": "INSYNC",
            }
        }

        with patch("api.services.dns_service.boto3.client", return_value=mock_route53):
            service = DnsService(config)
            service.route53_client = mock_route53

            request = DnsUpdateRequest(
                domain="johnsosoka.com.",
                ip="192.168.1.1",
            )

            service.update_record(request)

            call_args = mock_route53.change_resource_record_sets.call_args
            assert call_args.kwargs["ChangeBatch"]["Changes"][0]["ResourceRecordSet"]["TTL"] == 600

    def test_update_record_domain_not_allowed(self, dns_service):
        """Test DomainNotAllowedError is raised for domain not in allowed zones."""
        request = DnsUpdateRequest(
            domain="notallowed.com.",
            ip="192.168.1.1",
        )

        with pytest.raises(DomainNotAllowedError) as exc_info:
            dns_service.update_record(request)

        assert exc_info.value.status_code == 403
        assert "notallowed.com." in exc_info.value.message
        assert "not in the allowed zones list" in exc_info.value.message

    def test_update_record_route53_client_error(self, dns_service, mock_route53):
        """Test DnsUpdateError is raised when Route53 API call fails."""
        # Mock Route53 to raise ClientError
        error_response = {
            "Error": {
                "Code": "InvalidChangeBatch",
                "Message": "Invalid DNS record",
            }
        }
        mock_route53.change_resource_record_sets.side_effect = ClientError(
            error_response, "ChangeResourceRecordSets"
        )

        request = DnsUpdateRequest(
            domain="test.johnsosoka.com.",
            ip="192.168.1.1",
        )

        with pytest.raises(DnsUpdateError) as exc_info:
            dns_service.update_record(request)

        assert exc_info.value.status_code == 500
        assert "Failed to update DNS record" in exc_info.value.message
        assert "Invalid DNS record" in exc_info.value.message

    def test_update_record_route53_access_denied(self, dns_service, mock_route53):
        """Test DnsUpdateError is raised for Route53 access denied."""
        error_response = {
            "Error": {
                "Code": "AccessDenied",
                "Message": "User is not authorized to perform: route53:ChangeResourceRecordSets",
            }
        }
        mock_route53.change_resource_record_sets.side_effect = ClientError(
            error_response, "ChangeResourceRecordSets"
        )

        request = DnsUpdateRequest(
            domain="johnsosoka.com.",
            ip="192.168.1.1",
        )

        with pytest.raises(DnsUpdateError) as exc_info:
            dns_service.update_record(request)

        assert exc_info.value.status_code == 500
        assert "not authorized" in exc_info.value.message

    def test_update_record_unexpected_exception(self, dns_service, mock_route53):
        """Test DnsUpdateError is raised for unexpected exceptions."""
        mock_route53.change_resource_record_sets.side_effect = Exception("Unexpected error")

        request = DnsUpdateRequest(
            domain="johnsosoka.com.",
            ip="192.168.1.1",
        )

        with pytest.raises(DnsUpdateError) as exc_info:
            dns_service.update_record(request)

        assert exc_info.value.status_code == 500
        assert "Unexpected error updating DNS record" in exc_info.value.message
        assert "Unexpected error" in exc_info.value.message

    def test_update_record_extracts_change_id_from_arn(self, dns_service, mock_route53):
        """Test that change ID is correctly extracted from ARN-style ID."""
        mock_route53.change_resource_record_sets.return_value = {
            "ChangeInfo": {
                "Id": "/change/C1234567890ABC",
                "Status": "PENDING",
            }
        }

        request = DnsUpdateRequest(
            domain="johnsosoka.com.",
            ip="192.168.1.1",
        )

        response = dns_service.update_record(request)

        # Should extract just the ID part after the last /
        assert response.change_id == "C1234567890ABC"

    def test_update_record_handles_change_id_without_arn(self, dns_service, mock_route53):
        """Test that change ID is handled correctly when already in simple format."""
        mock_route53.change_resource_record_sets.return_value = {
            "ChangeInfo": {
                "Id": "C1234567890ABC",
                "Status": "INSYNC",
            }
        }

        request = DnsUpdateRequest(
            domain="johnsosoka.com.",
            ip="192.168.1.1",
        )

        response = dns_service.update_record(request)

        assert response.change_id == "C1234567890ABC"
        assert response.status == "INSYNC"

    def test_update_record_handles_missing_change_info(self, dns_service, mock_route53):
        """Test graceful handling when ChangeInfo is missing from response."""
        mock_route53.change_resource_record_sets.return_value = {}

        request = DnsUpdateRequest(
            domain="johnsosoka.com.",
            ip="192.168.1.1",
        )

        response = dns_service.update_record(request)

        # Should handle missing fields gracefully
        assert response.change_id == ""
        assert response.status == "UNKNOWN"
