"""Logging configuration using structlog."""

import sys
import logging
from typing import Any, Dict
import structlog
from structlog.processors import CallsiteParameter

from src.common.config import settings


def setup_logging():
    """Configure structured logging for the application."""
    
    # Set up standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper(), logging.INFO)
    )
    
    # Configure structlog processors
    processors = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.CallsiteParameterAdder(
            parameters=[
                CallsiteParameter.FILENAME,
                CallsiteParameter.LINENO,
                CallsiteParameter.FUNC_NAME,
            ]
        ),
    ]
    
    # Add different renderers based on environment
    if settings.is_development:
        # Use colored output for development
        processors.append(
            structlog.dev.ConsoleRenderer(
                colors=True,
                exception_formatter=structlog.dev.plain_traceback
            )
        )
    else:
        # Use JSON output for production
        processors.append(structlog.processors.JSONRenderer())
    
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name).bind(
        app=settings.app_name,
        env=settings.env
    )


def log_context(**kwargs: Any) -> Dict[str, Any]:
    """Create a logging context dictionary.
    
    Args:
        **kwargs: Key-value pairs to include in the context
    
    Returns:
        Context dictionary for logging
    """
    return kwargs