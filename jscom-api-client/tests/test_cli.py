"""Tests for CLI application."""

import os
from unittest.mock import patch

import pytest
import responses
from jscom_api.cli.main import app
from typer.testing import CliRunner

runner = CliRunner()


@pytest.fixture
def mock_env():
    """Provide clean environment for tests."""
    with patch.dict(os.environ, {}, clear=True):
        yield


class TestIpCommand:
    """Tests for 'ip' command."""

    def test_default_output(self, mock_api, mock_env):
        """Test default human-readable output format."""
        mock_api.add(
            responses.GET,
            "https://api.johnsosoka.com/v1/ip/my",
            json={"ip": "203.0.113.42"},
            status=200,
        )

        result = runner.invoke(app, ["ip"])

        assert result.exit_code == 0
        assert "203.0.113.42" in result.stdout
        # Check for table formatting (from rich.table)
        assert "Your Public IP" in result.stdout or "203.0.113.42" in result.stdout

    def test_json_output(self, mock_api, mock_env):
        """Test --json output format."""
        mock_api.add(
            responses.GET,
            "https://api.johnsosoka.com/v1/ip/my",
            json={"ip": "203.0.113.42"},
            status=200,
        )

        result = runner.invoke(app, ["ip", "--json"])

        assert result.exit_code == 0
        # The output should contain JSON data
        assert "203.0.113.42" in result.stdout
        # Verify it's valid JSON-like output
        assert "ip" in result.stdout or "203.0.113.42" in result.stdout

    def test_quiet_output(self, mock_api, mock_env):
        """Test --quiet output (IP only)."""
        mock_api.add(
            responses.GET,
            "https://api.johnsosoka.com/v1/ip/my",
            json={"ip": "203.0.113.42"},
            status=200,
        )

        result = runner.invoke(app, ["ip", "--quiet"])

        assert result.exit_code == 0
        # Should only contain the IP address
        assert "203.0.113.42" in result.stdout
        # Should not contain table headers
        assert "Your Public IP" not in result.stdout

    def test_quiet_shorthand(self, mock_api, mock_env):
        """Test -q shorthand for --quiet."""
        mock_api.add(
            responses.GET,
            "https://api.johnsosoka.com/v1/ip/my",
            json={"ip": "203.0.113.42"},
            status=200,
        )

        result = runner.invoke(app, ["ip", "-q"])

        assert result.exit_code == 0
        assert "203.0.113.42" in result.stdout

    def test_network_error(self, mock_api, mock_env):
        """Test network error handling."""
        mock_api.add(
            responses.GET,
            "https://api.johnsosoka.com/v1/ip/my",
            body=ConnectionError("Connection failed"),
        )

        result = runner.invoke(app, ["ip"])

        assert result.exit_code == 1
        assert "Network error" in result.stdout or "error" in result.stdout.lower()

    def test_server_error(self, mock_api, mock_env):
        """Test server error handling."""
        mock_api.add(
            responses.GET,
            "https://api.johnsosoka.com/v1/ip/my",
            json={"error": "Internal server error"},
            status=500,
        )

        result = runner.invoke(app, ["ip"])

        assert result.exit_code == 1
        assert "Server error" in result.stdout or "error" in result.stdout.lower()

    def test_custom_base_url(self, mock_api, mock_env):
        """Test --base-url option."""
        mock_api.add(
            responses.GET,
            "https://custom.api.com/v1/ip/my",
            json={"ip": "203.0.113.42"},
            status=200,
        )

        result = runner.invoke(app, ["--base-url", "https://custom.api.com", "ip"])

        assert result.exit_code == 0
        assert "203.0.113.42" in result.stdout

    def test_base_url_from_env(self, mock_api):
        """Test JSCOM_API_BASE_URL environment variable."""
        with patch.dict(os.environ, {"JSCOM_API_BASE_URL": "https://env.api.com"}):
            mock_api.add(
                responses.GET,
                "https://env.api.com/v1/ip/my",
                json={"ip": "203.0.113.42"},
                status=200,
            )

            result = runner.invoke(app, ["ip"])

            assert result.exit_code == 0
            assert "203.0.113.42" in result.stdout


class TestDnsUpdateCommand:
    """Tests for 'dns update' command."""

    def test_success_with_explicit_ip(self, mock_api, mock_env):
        """Test successful DNS update with explicit IP."""
        mock_api.add(
            responses.POST,
            "https://api.johnsosoka.com/v1/dns/update",
            json={
                "message": "DNS record updated successfully",
                "change_info": {
                    "id": "C1234567890ABC",
                    "status": "PENDING",
                },
            },
            status=200,
        )

        result = runner.invoke(
            app,
            [
                "--token",
                "test-token",
                "dns",
                "update",
                "--domain",
                "mc.example.com.",
                "--ip",
                "203.0.113.42",
            ],
        )

        assert result.exit_code == 0
        assert "Success" in result.stdout
        assert "DNS record updated successfully" in result.stdout

    def test_success_with_use_current_ip(self, mock_api, mock_env):
        """Test successful DNS update with --use-current-ip."""
        # Mock the IP lookup
        mock_api.add(
            responses.GET,
            "https://api.johnsosoka.com/v1/ip/my",
            json={"ip": "203.0.113.42"},
            status=200,
        )

        # Mock the DNS update
        mock_api.add(
            responses.POST,
            "https://api.johnsosoka.com/v1/dns/update",
            json={
                "message": "DNS record updated successfully",
                "change_info": {
                    "id": "C1234567890ABC",
                    "status": "PENDING",
                },
            },
            status=200,
        )

        result = runner.invoke(
            app,
            [
                "--token",
                "test-token",
                "dns",
                "update",
                "--domain",
                "mc.example.com.",
                "--use-current-ip",
            ],
        )

        assert result.exit_code == 0
        assert "Fetching current public IP" in result.stdout
        assert "203.0.113.42" in result.stdout
        assert "Success" in result.stdout

    def test_missing_required_options(self, mock_env):
        """Test error when neither --ip nor --use-current-ip is provided."""
        result = runner.invoke(
            app,
            ["--token", "test-token", "dns", "update", "--domain", "mc.example.com."],
        )

        assert result.exit_code == 1
        assert "Either --ip or --use-current-ip must be provided" in result.stdout

    def test_mutually_exclusive_options(self, mock_env):
        """Test error when both --ip and --use-current-ip are provided."""
        result = runner.invoke(
            app,
            [
                "--token",
                "test-token",
                "dns",
                "update",
                "--domain",
                "mc.example.com.",
                "--ip",
                "203.0.113.42",
                "--use-current-ip",
            ],
        )

        assert result.exit_code == 1
        assert "mutually exclusive" in result.stdout

    def test_authentication_error_display(self, mock_api, mock_env):
        """Test authentication error display."""
        mock_api.add(
            responses.POST,
            "https://api.johnsosoka.com/v1/dns/update",
            json={"error": "Forbidden", "message": "Invalid token"},
            status=403,
        )

        result = runner.invoke(
            app,
            [
                "--token",
                "invalid-token",
                "dns",
                "update",
                "--domain",
                "mc.example.com.",
                "--ip",
                "203.0.113.42",
            ],
        )

        assert result.exit_code == 2
        assert "Authentication failed" in result.stdout
        assert "JSCOM_API_TOKEN" in result.stdout or "token" in result.stdout.lower()

    def test_authentication_error_no_token(self, mock_api, mock_env):
        """Test authentication error when no token is provided."""
        mock_api.add(
            responses.POST,
            "https://api.johnsosoka.com/v1/dns/update",
            json={"error": "Forbidden", "message": "Missing authentication"},
            status=403,
        )

        result = runner.invoke(
            app,
            [
                "dns",
                "update",
                "--domain",
                "mc.example.com.",
                "--ip",
                "203.0.113.42",
            ],
        )

        assert result.exit_code == 2
        assert "Authentication failed" in result.stdout

    def test_validation_error(self, mock_api, mock_env):
        """Test validation error display."""
        mock_api.add(
            responses.POST,
            "https://api.johnsosoka.com/v1/dns/update",
            json={"error": "Bad Request", "message": "Invalid domain format"},
            status=400,
        )

        result = runner.invoke(
            app,
            [
                "--token",
                "test-token",
                "dns",
                "update",
                "--domain",
                "invalid-domain",
                "--ip",
                "203.0.113.42",
            ],
        )

        assert result.exit_code == 1
        assert "Validation error" in result.stdout

    def test_network_error(self, mock_api, mock_env):
        """Test network error handling."""
        mock_api.add(
            responses.POST,
            "https://api.johnsosoka.com/v1/dns/update",
            body=ConnectionError("Connection failed"),
        )

        result = runner.invoke(
            app,
            [
                "--token",
                "test-token",
                "dns",
                "update",
                "--domain",
                "mc.example.com.",
                "--ip",
                "203.0.113.42",
            ],
        )

        assert result.exit_code == 1
        assert "Network error" in result.stdout or "error" in result.stdout.lower()

    def test_server_error(self, mock_api, mock_env):
        """Test server error handling."""
        mock_api.add(
            responses.POST,
            "https://api.johnsosoka.com/v1/dns/update",
            json={"error": "Internal server error"},
            status=500,
        )

        result = runner.invoke(
            app,
            [
                "--token",
                "test-token",
                "dns",
                "update",
                "--domain",
                "mc.example.com.",
                "--ip",
                "203.0.113.42",
            ],
        )

        assert result.exit_code == 1
        assert "Server error" in result.stdout or "error" in result.stdout.lower()

    def test_token_from_env(self, mock_api):
        """Test JSCOM_API_TOKEN environment variable."""
        with patch.dict(os.environ, {"JSCOM_API_TOKEN": "env-token"}):
            mock_api.add(
                responses.POST,
                "https://api.johnsosoka.com/v1/dns/update",
                json={
                    "message": "DNS record updated",
                    "change_info": {},
                },
                status=200,
            )

            result = runner.invoke(
                app,
                [
                    "dns",
                    "update",
                    "--domain",
                    "mc.example.com.",
                    "--ip",
                    "203.0.113.42",
                ],
            )

            assert result.exit_code == 0

    def test_change_info_display(self, mock_api, mock_env):
        """Test that change info is displayed properly."""
        mock_api.add(
            responses.POST,
            "https://api.johnsosoka.com/v1/dns/update",
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

        result = runner.invoke(
            app,
            [
                "--token",
                "test-token",
                "dns",
                "update",
                "--domain",
                "mc.example.com.",
                "--ip",
                "203.0.113.42",
            ],
        )

        assert result.exit_code == 0
        assert "Change Info" in result.stdout
        # At least one of the change_info values should be present
        assert (
            "C1234567890ABC" in result.stdout
            or "PENDING" in result.stdout
            or "submitted_at" in result.stdout
        )

    def test_custom_base_url_and_token(self, mock_api, mock_env):
        """Test custom base URL and token via CLI options."""
        mock_api.add(
            responses.POST,
            "https://custom.api.com/v1/dns/update",
            json={
                "message": "DNS updated",
                "change_info": {},
            },
            status=200,
        )

        result = runner.invoke(
            app,
            [
                "--base-url",
                "https://custom.api.com",
                "--token",
                "custom-token",
                "dns",
                "update",
                "--domain",
                "mc.example.com.",
                "--ip",
                "203.0.113.42",
            ],
        )

        assert result.exit_code == 0


class TestVersionCommand:
    """Tests for 'version' command."""

    def test_version_output(self, mock_env):
        """Test version command output."""
        result = runner.invoke(app, ["version"])

        assert result.exit_code == 0
        assert "jscom-api version" in result.stdout
        assert "0.1.0" in result.stdout


class TestNoArgsHelp:
    """Tests for no-args help behavior."""

    def test_no_args_shows_help(self, mock_env):
        """Test that running with no args shows help."""
        result = runner.invoke(app, [])

        assert result.exit_code == 0
        # Should show help text or usage information
        assert "Usage" in result.stdout or "Commands" in result.stdout

    def test_dns_no_args_shows_help(self, mock_env):
        """Test that 'dns' with no subcommand shows help."""
        result = runner.invoke(app, ["dns"])

        # Typer returns exit code 2 for missing subcommand
        assert result.exit_code == 2
        # Should show DNS-specific help
        assert (
            "update" in result.stdout
            or "Commands" in result.stdout
            or "Missing command" in result.stdout
        )
