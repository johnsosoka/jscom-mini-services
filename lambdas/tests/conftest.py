"""Pytest fixtures for jscom-mini-services Lambda API tests."""

import os

# Set environment variables BEFORE any imports that might trigger module-level config loading
# This is necessary because handler.py loads config at import time
os.environ.setdefault("AUTH_TOKEN", "test-token-12345")
os.environ.setdefault("ALLOWED_ZONES", "johnsosoka.com:Z1234567890ABC,example.com:Z9876543210DEF")
os.environ.setdefault("DEFAULT_TTL", "300")

import pytest
from unittest.mock import MagicMock, patch


class MockLambdaContext:
    """Mock Lambda context for testing."""

    def __init__(self):
        self.function_name = "jscom-api-lambda"
        self.function_version = "$LATEST"
        self.invoked_function_arn = "arn:aws:lambda:us-west-2:123456789012:function:jscom-api-lambda"
        self.memory_limit_in_mb = 256
        self.aws_request_id = "test-request-id-12345"
        self.log_group_name = "/aws/lambda/jscom-api-lambda"
        self.log_stream_name = "2025/12/22/[$LATEST]test"

    def get_remaining_time_in_millis(self):
        return 30000


@pytest.fixture
def mock_lambda_context():
    """Fixture to provide a mock Lambda context."""
    return MockLambdaContext()


@pytest.fixture
def mock_env_vars():
    """
    Fixture to mock environment variables.

    Sets up valid AUTH_TOKEN, ALLOWED_ZONES, and DEFAULT_TTL values.
    Cleans up after the test.

    Yields:
        dict: Environment variables that were set
    """
    env_vars = {
        "AUTH_TOKEN": "test-token-12345",
        "ALLOWED_ZONES": "johnsosoka.com:Z1234567890ABC,example.com:Z9876543210DEF",
        "DEFAULT_TTL": "300",
    }

    with patch.dict(os.environ, env_vars, clear=False):
        yield env_vars


@pytest.fixture
def mock_env_vars_minimal():
    """
    Fixture with minimal required environment variables.

    Only sets AUTH_TOKEN and ALLOWED_ZONES without DEFAULT_TTL.

    Yields:
        dict: Minimal environment variables
    """
    env_vars = {
        "AUTH_TOKEN": "test-token-12345",
        "ALLOWED_ZONES": "johnsosoka.com:Z1234567890ABC",
    }

    with patch.dict(os.environ, env_vars, clear=False):
        yield env_vars


@pytest.fixture
def mock_route53_client():
    """
    Fixture to mock boto3 Route53 client.

    Returns:
        MagicMock: Mocked Route53 client with default successful response
    """
    mock_client = MagicMock()

    # Default successful response
    mock_client.change_resource_record_sets.return_value = {
        "ChangeInfo": {
            "Id": "/change/C1234567890ABC",
            "Status": "PENDING",
            "SubmittedAt": "2025-12-22T12:00:00.000Z",
        }
    }

    return mock_client


@pytest.fixture
def app_config(mock_env_vars):
    """
    Fixture to create an AppConfig instance with mocked environment.

    Args:
        mock_env_vars: Environment variables fixture

    Returns:
        AppConfig: Configured application instance
    """
    from api.config import AppConfig

    return AppConfig.from_env()


@pytest.fixture
def dns_service(app_config, mock_route53_client):
    """
    Fixture to create a DnsService instance with mocked Route53 client.

    Args:
        app_config: Application configuration fixture
        mock_route53_client: Mocked Route53 client fixture

    Returns:
        DnsService: DNS service instance with mocked client
    """
    from api.services.dns_service import DnsService

    with patch("api.services.dns_service.boto3.client", return_value=mock_route53_client):
        service = DnsService(app_config)
        service.route53_client = mock_route53_client
        return service
