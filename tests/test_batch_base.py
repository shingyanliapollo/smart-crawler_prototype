"""Tests for batch job base class."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from src.batch.base import BaseBatchJob


class TestBatchJob(BaseBatchJob):
    """Test implementation of BaseBatchJob."""
    
    def execute(self):
        return {"test": "result"}


class FailingBatchJob(BaseBatchJob):
    """Test implementation that always fails."""
    
    def execute(self):
        raise ValueError("Test error")


class TestBaseBatchJob:
    """Test cases for BaseBatchJob."""
    
    def test_batch_job_initialization(self):
        """Test batch job initialization."""
        job = TestBatchJob("TestJob")
        assert job.job_name == "TestJob"
        assert job.start_time is None
        assert job.end_time is None
        assert job.context == {}
    
    def test_batch_job_default_name(self):
        """Test batch job with default name."""
        job = TestBatchJob()
        assert job.job_name == "TestBatchJob"
    
    @patch("src.batch.base.get_logger")
    def test_successful_execution(self, mock_get_logger):
        """Test successful batch job execution."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        job = TestBatchJob()
        result = job.run()
        
        assert result["status"] == "success"
        assert result["job_name"] == "TestBatchJob"
        assert "start_time" in result
        assert "end_time" in result
        assert "duration_seconds" in result
        assert result["result"] == {"test": "result"}
        
        # Check that logger was called
        assert mock_logger.info.called
    
    @patch("src.batch.base.get_logger")
    def test_failed_execution(self, mock_get_logger):
        """Test failed batch job execution."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        job = FailingBatchJob()
        result = job.run()
        
        assert result["status"] == "failed"
        assert result["job_name"] == "FailingBatchJob"
        assert "start_time" in result
        assert "end_time" in result
        assert "duration_seconds" in result
        assert "error" in result
        assert "Test error" in result["error"]
        
        # Check that logger was called
        assert mock_logger.error.called
    
    @patch("src.batch.base.get_logger")
    def test_hooks_called(self, mock_get_logger):
        """Test that hooks are called during execution."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        class HookedJob(BaseBatchJob):
            def __init__(self):
                super().__init__()
                self.before_called = False
                self.after_called = False
                self.error_called = False
            
            def execute(self):
                return {"result": "success"}
            
            def before_execute(self):
                self.before_called = True
            
            def after_execute(self, result):
                self.after_called = True
                assert result == {"result": "success"}
            
            def on_error(self, error):
                self.error_called = True
        
        job = HookedJob()
        result = job.run()
        
        assert job.before_called
        assert job.after_called
        assert not job.error_called
        assert result["status"] == "success"
    
    @patch("src.batch.base.get_logger")
    def test_error_hook_called_on_failure(self, mock_get_logger):
        """Test that error hook is called on failure."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        class HookedFailingJob(BaseBatchJob):
            def __init__(self):
                super().__init__()
                self.error_called = False
                self.error_message = None
            
            def execute(self):
                raise RuntimeError("Intentional error")
            
            def on_error(self, error):
                self.error_called = True
                self.error_message = str(error)
        
        job = HookedFailingJob()
        result = job.run()
        
        assert job.error_called
        assert job.error_message == "Intentional error"
        assert result["status"] == "failed"