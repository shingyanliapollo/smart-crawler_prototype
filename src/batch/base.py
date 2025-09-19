"""Base class for batch jobs."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from src.common.config import settings
from src.common.logging import get_logger


class BaseBatchJob(ABC):
    """Base class for all batch jobs."""

    def __init__(self, job_name: Optional[str] = None):
        """Initialize batch job.
        
        Args:
            job_name: Name of the job. If not provided, uses class name.
        """
        self.job_name = job_name or self.__class__.__name__
        self.logger = get_logger(self.job_name)
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.context: Dict[str, Any] = {}
        
    def run(self) -> Dict[str, Any]:
        """Execute the batch job with error handling and metrics."""
        self.start_time = datetime.now()
        self.logger.info(
            "batch_job_started",
            job_name=self.job_name,
            start_time=self.start_time.isoformat()
        )
        
        try:
            # Pre-processing hook
            self.before_execute()
            
            # Main execution
            result = self._execute_with_retry()
            
            # Post-processing hook
            self.after_execute(result)
            
            self.end_time = datetime.now()
            duration = (self.end_time - self.start_time).total_seconds()
            
            self.logger.info(
                "batch_job_completed",
                job_name=self.job_name,
                duration_seconds=duration,
                result=result
            )
            
            return {
                "status": "success",
                "job_name": self.job_name,
                "start_time": self.start_time.isoformat(),
                "end_time": self.end_time.isoformat(),
                "duration_seconds": duration,
                "result": result
            }
            
        except Exception as e:
            self.end_time = datetime.now()
            duration = (self.end_time - self.start_time).total_seconds()
            
            self.logger.error(
                "batch_job_failed",
                job_name=self.job_name,
                duration_seconds=duration,
                error=str(e),
                exc_info=True
            )
            
            self.on_error(e)
            
            return {
                "status": "failed",
                "job_name": self.job_name,
                "start_time": self.start_time.isoformat(),
                "end_time": self.end_time.isoformat(),
                "duration_seconds": duration,
                "error": str(e)
            }
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    def _execute_with_retry(self) -> Any:
        """Execute the job with retry logic."""
        return self.execute()
    
    @abstractmethod
    def execute(self) -> Any:
        """Main job logic to be implemented by subclasses.
        
        Returns:
            Result of the job execution.
        """
        pass
    
    def before_execute(self):
        """Hook called before job execution. Override in subclasses if needed."""
        pass
    
    def after_execute(self, result: Any):
        """Hook called after successful job execution.
        
        Args:
            result: Result from the execute method.
        """
        pass
    
    def on_error(self, error: Exception):
        """Hook called when job fails.
        
        Args:
            error: The exception that caused the failure.
        """
        pass