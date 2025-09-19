"""Custom exceptions for the application."""


class SmartCrawlException(Exception):
    """Base exception for the application."""
    pass


class BatchJobException(SmartCrawlException):
    """Exception raised during batch job execution."""
    pass


class ConfigurationException(SmartCrawlException):
    """Exception raised for configuration issues."""
    pass


class ValidationException(SmartCrawlException):
    """Exception raised for validation errors."""
    pass


class ExternalAPIException(SmartCrawlException):
    """Exception raised when external API calls fail."""
    pass


class RetryableException(SmartCrawlException):
    """Exception that indicates the operation can be retried."""
    pass