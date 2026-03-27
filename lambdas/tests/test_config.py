"""Tests for AppConfig configuration management."""

import os
import pytest
from unittest.mock import patch

from api.config import AppConfig, ZoneConfig


class TestAppConfig:
    """Test suite for AppConfig class."""

    def test_from_env_valid_single_zone(self):
        """Test loading configuration with a single zone."""
        env_vars = {
            "AUTH_TOKEN": "test-token",
            "ALLOWED_ZONES": "johnsosoka.com.:Z123456",
            "DEFAULT_TTL": "300",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = AppConfig.from_env()

            assert config.auth_token == "test-token"
            assert len(config.allowed_zones) == 1
            assert config.allowed_zones[0].domain == "johnsosoka.com."
            assert config.allowed_zones[0].zone_id == "Z123456"
            assert config.default_ttl == 300

    def test_from_env_valid_multiple_zones(self):
        """Test loading configuration with multiple zones."""
        env_vars = {
            "AUTH_TOKEN": "test-token",
            "ALLOWED_ZONES": "johnsosoka.com.:Z123,example.com.:Z456,test.org.:Z789",
            "DEFAULT_TTL": "600",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = AppConfig.from_env()

            assert config.auth_token == "test-token"
            assert len(config.allowed_zones) == 3
            assert config.allowed_zones[0].domain == "johnsosoka.com."
            assert config.allowed_zones[0].zone_id == "Z123"
            assert config.allowed_zones[1].domain == "example.com."
            assert config.allowed_zones[1].zone_id == "Z456"
            assert config.allowed_zones[2].domain == "test.org."
            assert config.allowed_zones[2].zone_id == "Z789"
            assert config.default_ttl == 600

    def test_from_env_with_whitespace(self):
        """Test parsing zones with extra whitespace."""
        env_vars = {
            "AUTH_TOKEN": "test-token",
            "ALLOWED_ZONES": "  johnsosoka.com. : Z123  ,  example.com. : Z456  ",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = AppConfig.from_env()

            assert len(config.allowed_zones) == 2
            assert config.allowed_zones[0].domain == "johnsosoka.com."
            assert config.allowed_zones[0].zone_id == "Z123"
            assert config.allowed_zones[1].domain == "example.com."
            assert config.allowed_zones[1].zone_id == "Z456"

    def test_from_env_default_ttl_when_not_specified(self):
        """Test DEFAULT_TTL defaults to 300 when not specified."""
        env_vars = {
            "AUTH_TOKEN": "test-token",
            "ALLOWED_ZONES": "johnsosoka.com.:Z123",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = AppConfig.from_env()

            assert config.default_ttl == 300

    def test_from_env_missing_auth_token_raises_error(self):
        """Test ValueError is raised when AUTH_TOKEN is missing."""
        env_vars = {
            "ALLOWED_ZONES": "johnsosoka.com.:Z123",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValueError, match="AUTH_TOKEN environment variable is required"):
                AppConfig.from_env()

    def test_from_env_missing_allowed_zones_raises_error(self):
        """Test ValueError is raised when ALLOWED_ZONES is missing."""
        env_vars = {
            "AUTH_TOKEN": "test-token",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValueError, match="ALLOWED_ZONES environment variable is required"):
                AppConfig.from_env()

    def test_from_env_invalid_zone_format_missing_colon(self):
        """Test ValueError is raised when zone format is invalid (missing colon)."""
        env_vars = {
            "AUTH_TOKEN": "test-token",
            "ALLOWED_ZONES": "johnsosoka.com.Z123",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValueError, match="Invalid ALLOWED_ZONES format"):
                AppConfig.from_env()

    def test_from_env_invalid_zone_format_too_many_colons(self):
        """Test ValueError is raised when zone has too many colons."""
        env_vars = {
            "AUTH_TOKEN": "test-token",
            "ALLOWED_ZONES": "johnsosoka.com.:Z123:extra",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValueError, match="Invalid ALLOWED_ZONES format"):
                AppConfig.from_env()

    def test_from_env_empty_allowed_zones_raises_error(self):
        """Test ValueError is raised when ALLOWED_ZONES is empty or only whitespace."""
        env_vars = {
            "AUTH_TOKEN": "test-token",
            "ALLOWED_ZONES": "   ,  ,  ",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValueError, match="At least one zone must be configured"):
                AppConfig.from_env()

    def test_from_env_invalid_ttl_raises_error(self):
        """Test ValueError is raised when DEFAULT_TTL is not an integer."""
        env_vars = {
            "AUTH_TOKEN": "test-token",
            "ALLOWED_ZONES": "johnsosoka.com.:Z123",
            "DEFAULT_TTL": "not-a-number",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValueError, match="DEFAULT_TTL must be an integer"):
                AppConfig.from_env()

    def test_get_zone_for_domain_exact_match(self):
        """Test get_zone_for_domain returns correct zone for exact domain match."""
        config = AppConfig(
            auth_token="test-token",
            allowed_zones=[
                ZoneConfig(domain="johnsosoka.com.", zone_id="Z123"),
                ZoneConfig(domain="example.com.", zone_id="Z456"),
            ],
        )

        zone = config.get_zone_for_domain("johnsosoka.com.")
        assert zone is not None
        assert zone.domain == "johnsosoka.com."
        assert zone.zone_id == "Z123"

    def test_get_zone_for_domain_subdomain_match(self):
        """Test get_zone_for_domain matches subdomain to parent zone."""
        config = AppConfig(
            auth_token="test-token",
            allowed_zones=[
                ZoneConfig(domain="johnsosoka.com.", zone_id="Z123"),
            ],
        )

        zone = config.get_zone_for_domain("sub.johnsosoka.com.")
        assert zone is not None
        assert zone.domain == "johnsosoka.com."
        assert zone.zone_id == "Z123"

    def test_get_zone_for_domain_deep_subdomain_match(self):
        """Test get_zone_for_domain matches deeply nested subdomain."""
        config = AppConfig(
            auth_token="test-token",
            allowed_zones=[
                ZoneConfig(domain="johnsosoka.com.", zone_id="Z123"),
            ],
        )

        zone = config.get_zone_for_domain("a.b.c.johnsosoka.com.")
        assert zone is not None
        assert zone.domain == "johnsosoka.com."
        assert zone.zone_id == "Z123"

    def test_get_zone_for_domain_without_trailing_dot(self):
        """Test get_zone_for_domain works with domains missing trailing dot."""
        config = AppConfig(
            auth_token="test-token",
            allowed_zones=[
                ZoneConfig(domain="johnsosoka.com.", zone_id="Z123"),
            ],
        )

        zone = config.get_zone_for_domain("sub.johnsosoka.com")
        assert zone is not None
        assert zone.domain == "johnsosoka.com."
        assert zone.zone_id == "Z123"

    def test_get_zone_for_domain_no_match_returns_none(self):
        """Test get_zone_for_domain returns None when domain is not allowed."""
        config = AppConfig(
            auth_token="test-token",
            allowed_zones=[
                ZoneConfig(domain="johnsosoka.com.", zone_id="Z123"),
            ],
        )

        zone = config.get_zone_for_domain("unknown.com.")
        assert zone is None

    def test_get_zone_for_domain_partial_match_returns_none(self):
        """Test get_zone_for_domain doesn't match partial domain strings."""
        config = AppConfig(
            auth_token="test-token",
            allowed_zones=[
                ZoneConfig(domain="johnsosoka.com.", zone_id="Z123"),
            ],
        )

        # "notjohnsosoka.com" should not match "johnsosoka.com"
        zone = config.get_zone_for_domain("notjohnsosoka.com.")
        assert zone is None
