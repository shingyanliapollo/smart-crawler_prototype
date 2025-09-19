"""Tests for configuration module."""

import os
import pytest
from unittest.mock import patch

from src.common.config import Settings


class TestSettings:
    """Test cases for Settings class."""
    
    def test_default_settings(self):
        """Test default settings values."""
        settings = Settings()
        
        assert settings.env == "development"
        assert settings.debug is True
        assert settings.app_name == "smart_crawl"
        assert settings.log_level == "INFO"
        assert settings.batch_max_workers == 4
        assert settings.batch_retry_count == 3
        assert settings.batch_timeout_seconds == 300
    
    def test_environment_override(self):
        """Test that environment variables override defaults."""
        with patch.dict(os.environ, {
            "ENV": "production",
            "DEBUG": "False",
            "LOG_LEVEL": "ERROR",
            "BATCH_MAX_WORKERS": "8"
        }):
            settings = Settings()
            
            assert settings.env == "production"
            assert settings.debug is False
            assert settings.log_level == "ERROR"
            assert settings.batch_max_workers == 8
    
    def test_is_production(self):
        """Test is_production property."""
        with patch.dict(os.environ, {"ENV": "production"}):
            settings = Settings()
            assert settings.is_production is True
            assert settings.is_development is False
        
        with patch.dict(os.environ, {"ENV": "development"}):
            settings = Settings()
            assert settings.is_production is False
            assert settings.is_development is True
    
    def test_database_url(self):
        """Test database URL generation."""
        with patch.dict(os.environ, {
            "DB_HOST": "localhost",
            "DB_PORT": "5432",
            "DB_NAME": "testdb",
            "DB_USER": "testuser",
            "DB_PASSWORD": "testpass"
        }):
            settings = Settings()
            expected = "postgresql://testuser:testpass@localhost:5432/testdb"
            assert settings.database_url == expected
    
    def test_database_url_missing_values(self):
        """Test database URL when values are missing."""
        settings = Settings()
        assert settings.database_url is None
    
    def test_redis_url(self):
        """Test Redis URL generation."""
        with patch.dict(os.environ, {
            "REDIS_HOST": "localhost",
            "REDIS_PORT": "6379",
            "REDIS_DB": "1"
        }):
            settings = Settings()
            expected = "redis://localhost:6379/1"
            assert settings.redis_url == expected
    
    def test_redis_url_missing(self):
        """Test Redis URL when host is missing."""
        settings = Settings()
        assert settings.redis_url is None