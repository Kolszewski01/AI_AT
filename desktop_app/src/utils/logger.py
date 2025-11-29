"""
Logging configuration for desktop application.

Features:
- Rotating log files (app.log, errors.log)
- Remote error reporting to backend
- Structured logging with context
"""
import logging
import os
import sys
import traceback
import threading
import platform
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional
from queue import Queue

# App version (should match main app version)
APP_VERSION = "1.0.0"

# Log format with function context
LOG_FORMAT = '%(asctime)s | %(levelname)-8s | %(name)-25s | %(funcName)-15s:%(lineno)-4d | %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Log directory
LOG_DIR = Path(__file__).parent.parent.parent / 'logs'
LOG_DIR.mkdir(exist_ok=True)

# Log files
APP_LOG_FILE = LOG_DIR / "app.log"
ERROR_LOG_FILE = LOG_DIR / "errors.log"

# Queue for async error reporting
_error_queue: Queue = Queue()
_error_reporter_started = False


class ErrorOnlyFilter(logging.Filter):
    """Filter that only allows ERROR and CRITICAL level logs."""
    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno >= logging.ERROR


class RemoteErrorHandler(logging.Handler):
    """
    Handler that sends ERROR and CRITICAL logs to the backend.
    Uses a background thread to avoid blocking.
    """

    def __init__(self, api_base_url: str = "http://localhost:8000/api/v1"):
        super().__init__(level=logging.ERROR)
        self.api_url = f"{api_base_url}/errors/report"
        self._start_reporter()

    def _start_reporter(self):
        """Start background thread for error reporting."""
        global _error_reporter_started
        if not _error_reporter_started:
            _error_reporter_started = True
            thread = threading.Thread(target=self._report_errors, daemon=True)
            thread.start()

    def _report_errors(self):
        """Background thread that sends errors to backend."""
        import requests

        while True:
            try:
                error_data = _error_queue.get()
                if error_data is None:
                    break

                try:
                    requests.post(
                        self.api_url,
                        json=error_data,
                        timeout=5
                    )
                except Exception:
                    # Silently fail - don't log errors about logging
                    pass

            except Exception:
                pass

    def emit(self, record: logging.LogRecord):
        """Send error record to backend via queue."""
        try:
            error_data = {
                "client_type": "desktop",
                "client_version": APP_VERSION,
                "error_level": record.levelname,
                "error_message": record.getMessage(),
                "error_type": getattr(record, 'exc_info', (None,))[0].__name__ if record.exc_info and record.exc_info[0] else None,
                "stack_trace": self._format_exception(record),
                "module": record.name,
                "function": record.funcName,
                "line_number": record.lineno,
                "timestamp": datetime.utcnow().isoformat(),
                "device_info": {
                    "os": platform.system(),
                    "os_version": platform.version(),
                    "python": platform.python_version(),
                    "machine": platform.machine()
                }
            }
            _error_queue.put(error_data)
        except Exception:
            pass

    def _format_exception(self, record: logging.LogRecord) -> Optional[str]:
        """Format exception info if present."""
        if record.exc_info:
            return ''.join(traceback.format_exception(*record.exc_info))
        return None


def setup_logger(
    name: str = "ai_trading",
    level: int = logging.DEBUG,
    log_to_file: bool = True,
    log_to_console: bool = True,
    remote_errors: bool = True
) -> logging.Logger:
    """
    Setup and configure application logger.

    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Enable file logging
        log_to_console: Enable console logging
        remote_errors: Enable sending errors to backend

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    logger.setLevel(level)

    formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT)

    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # Main app log file (rotating)
    if log_to_file:
        app_handler = RotatingFileHandler(
            APP_LOG_FILE,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )
        app_handler.setLevel(level)
        app_handler.setFormatter(formatter)
        logger.addHandler(app_handler)

        # Separate errors-only log file
        error_handler = RotatingFileHandler(
            ERROR_LOG_FILE,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=10,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        error_handler.addFilter(ErrorOnlyFilter())
        logger.addHandler(error_handler)

    # Remote error reporting
    if remote_errors:
        try:
            from src.utils.config import Config
            config = Config()
            remote_handler = RemoteErrorHandler(api_base_url=config.API_BASE_URL)
            remote_handler.setFormatter(formatter)
            logger.addHandler(remote_handler)
        except Exception:
            # Config not available yet, use default URL
            remote_handler = RemoteErrorHandler()
            remote_handler.setFormatter(formatter)
            logger.addHandler(remote_handler)

    return logger


def get_logger(module_name: str) -> logging.Logger:
    """
    Get a child logger for a specific module.

    Args:
        module_name: Name of the module (e.g., 'api_client', 'chart_widget')

    Returns:
        Child logger instance
    """
    # Ensure parent logger is configured
    parent = logging.getLogger("ai_trading")
    if not parent.handlers:
        setup_logger()

    child_logger = logging.getLogger(f"ai_trading.{module_name}")
    child_logger.setLevel(logging.DEBUG)
    return child_logger


def log_exception(
    logger: logging.Logger,
    message: str,
    exc: Optional[Exception] = None,
    context: Optional[dict] = None
) -> None:
    """
    Log an exception with full context.

    Args:
        logger: Logger instance
        message: Error message
        exc: Exception (optional)
        context: Additional context dict
    """
    context_str = ""
    if context:
        context_str = " | " + ", ".join(f"{k}={v}" for k, v in context.items())

    if exc:
        logger.error(f"{message}{context_str}", exc_info=exc)
    else:
        logger.error(f"{message}{context_str}", exc_info=True)


# Create default logger on import
logger = setup_logger()
