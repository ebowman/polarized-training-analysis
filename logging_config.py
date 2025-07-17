"""
Logging configuration for PolarFlow application.

This module provides consistent logging setup across all modules,
including proper formatting, log levels, and rotation policies.
"""

import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path


class PolarFlowLogFormatter(logging.Formatter):
    """Custom formatter with enhanced error information."""
    
    def format(self, record):
        # Add additional context for errors
        if record.levelno >= logging.ERROR:
            record.msg = f"[{record.module}:{record.funcName}] {record.msg}"
        return super().format(record)


def setup_logging(
    app_name: str = "polarflow",
    log_level: str = "INFO",
    log_dir: str = "logs",
    enable_file_logging: bool = True,
    enable_console_logging: bool = True,
    max_bytes: int = 10_485_760,  # 10MB
    backup_count: int = 5
):
    """
    Set up consistent logging configuration for the application.
    
    Args:
        app_name: Name of the application for log files
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files
        enable_file_logging: Whether to log to files
        enable_console_logging: Whether to log to console
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup files to keep
    
    Returns:
        The root logger configured with handlers
    """
    # Create logs directory if needed
    if enable_file_logging:
        log_path = Path(log_dir)
        log_path.mkdir(exist_ok=True)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = PolarFlowLogFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    
    # Console handler
    if enable_console_logging:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        root_logger.addHandler(console_handler)
    
    # File handlers
    if enable_file_logging:
        # Main log file with rotation
        main_log_file = log_path / f"{app_name}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            main_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(file_handler)
        
        # Error log file
        error_log_file = log_path / f"{app_name}_errors.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(error_handler)
    
    # Log initial setup
    root_logger.info(f"Logging initialized for {app_name} at level {log_level}")
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Name of the module (usually __name__)
    
    Returns:
        Logger instance configured for the module
    """
    return logging.getLogger(name)


# Custom exception classes for better error handling
class PolarFlowError(Exception):
    """Base exception class for PolarFlow application."""
    pass


class ConfigurationError(PolarFlowError):
    """Raised when there's an error in configuration."""
    pass


class StravaAPIError(PolarFlowError):
    """Raised when there's an error communicating with Strava API."""
    pass


class DataValidationError(PolarFlowError):
    """Raised when data validation fails."""
    pass


class CacheError(PolarFlowError):
    """Raised when there's an error with cache operations."""
    pass


class AnalysisError(PolarFlowError):
    """Raised when there's an error during analysis."""
    pass


class AIProviderError(PolarFlowError):
    """Raised when there's an error with AI provider operations."""
    pass


# Initialize logging on import if running as main application
if __name__ != "__main__":
    # Set up default logging configuration
    setup_logging(
        log_level=os.getenv("POLARFLOW_LOG_LEVEL", "INFO"),
        enable_file_logging=os.getenv("POLARFLOW_ENABLE_FILE_LOGGING", "true").lower() == "true"
    )