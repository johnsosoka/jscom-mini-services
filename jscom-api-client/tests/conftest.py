"""Pytest fixtures for jscom-api tests."""

import pytest
import responses
from jscom_api import JscomApiClient


@pytest.fixture
def mock_api():
    """Provide a responses mock context for HTTP mocking.

    Yields:
        RequestsMock instance for registering mock responses
    """
    with responses.RequestsMock() as rsps:
        yield rsps


@pytest.fixture
def client():
    """Create a JscomApiClient instance with test configuration.

    Returns:
        JscomApiClient configured with test base URL and token
    """
    return JscomApiClient(
        base_url="https://api.test.com",
        auth_token="test-token-12345",
        timeout=10.0,
    )


@pytest.fixture
def client_no_auth():
    """Create a JscomApiClient instance without authentication.

    Returns:
        JscomApiClient configured with test base URL but no token
    """
    return JscomApiClient(
        base_url="https://api.test.com",
        auth_token=None,
        timeout=10.0,
    )
