"""Pytest configuration and fixtures."""

import os
import sys
from pathlib import Path
import pytest
from unittest.mock import Mock, patch

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set test environment
os.environ["ENV"] = "test"
os.environ["LOG_LEVEL"] = "DEBUG"


@pytest.fixture
def mock_settings():
    """Mock application settings."""
    with patch("src.common.config.settings") as mock:
        mock.env = "test"
        mock.debug = True
        mock.app_name = "smart_crawl_test"
        mock.log_level = "DEBUG"
        mock.batch_max_workers = 2
        mock.batch_retry_count = 1
        mock.batch_timeout_seconds = 60
        mock.is_production = False
        mock.is_development = False
        yield mock


@pytest.fixture
def mock_logger():
    """Mock logger for testing."""
    logger = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    logger.debug = Mock()
    return logger


@pytest.fixture
def sample_job_context():
    """Sample context for batch job testing."""
    return {
        "job_name": "TestJob",
        "params": {
            "param1": "value1",
            "param2": 123
        },
        "metadata": {
            "triggered_by": "test",
            "priority": "normal"
        }
    }


@pytest.fixture
def temp_data_dir(tmp_path):
    """Create temporary data directory for tests."""
    data_dir = tmp_path / "test_data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment variables after each test."""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)