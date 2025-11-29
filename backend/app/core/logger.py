"""
Centralized logging configuration for AI Trading System Backend.

Usage:
    from app.core.logger import get_logger
    logger = get_logger(__name__)
    logger.error("Something went wrong", exc_info=True)
"""
import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from app.core.config import settings


# Log format with detailed context
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-30s | %(funcName)-20s:%(lineno)-4d | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Ensure logs directory exists
LOGS_DIR = Path(settings.LOG_FILE_PATH).parent
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Separate log files for different purposes
ERROR_LOG_FILE = LOGS_DIR / "errors.log"
APP_LOG_FILE = LOGS_DIR / "app.log"

# Track configured loggers to avoid duplicate handlers
_configured_loggers: set = set()


class ErrorOnlyFilter(logging.Filter):
    """Filter that only allows ERROR and CRITICAL level logs."""

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno >= logging.ERROR


def setup_root_logger() -> None:
    """Configure the root logger with handlers for console and file output."""
    root_logger = logging.getLogger()

    # Avoid duplicate setup
    if "root" in _configured_loggers:
        return

    # Set root level based on config
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    root_logger.setLevel(log_level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler (all levels based on config)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    root_logger.addHandler(console_handler)

    # App log file handler (all levels, rotating)
    app_file_handler = RotatingFileHandler(
        APP_LOG_FILE,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8"
    )
    app_file_handler.setLevel(log_level)
    app_file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    root_logger.addHandler(app_file_handler)

    # Error-only log file (separate file for easy error tracking)
    error_file_handler = RotatingFileHandler(
        ERROR_LOG_FILE,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=10,  # Keep more error logs
        encoding="utf-8"
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    error_file_handler.addFilter(ErrorOnlyFilter())
    root_logger.addHandler(error_file_handler)

    _configured_loggers.add("root")

    # Suppress noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("yfinance").setLevel(logging.WARNING)
    logging.getLogger("peewee").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name (typically __name__ of the calling module)

    Returns:
        Configured logger instance
    """
    # Ensure root logger is configured
    if "root" not in _configured_loggers:
        setup_root_logger()

    return logging.getLogger(name)


def log_exception(
    logger: logging.Logger,
    message: str,
    exc: Optional[Exception] = None,
    extra_context: Optional[dict] = None
) -> None:
    """
    Log an exception with full context.

    Args:
        logger: Logger instance to use
        message: Error message
        exc: Exception instance (optional, will use exc_info if not provided)
        extra_context: Additional context to include in log
    """
    context_str = ""
    if extra_context:
        context_str = " | Context: " + ", ".join(f"{k}={v}" for k, v in extra_context.items())

    if exc:
        logger.error(f"{message}{context_str}", exc_info=exc)
    else:
        logger.error(f"{message}{context_str}", exc_info=True)


# Initialize logging on module import
setup_root_logger()
