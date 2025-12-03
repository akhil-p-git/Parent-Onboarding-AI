"""
Structured Logging Configuration.

Provides JSON-formatted logging with correlation IDs and contextual information.
"""

import contextvars
import json
import logging
import sys
import uuid
from datetime import datetime, timezone
from typing import Any

from app.core.config import settings

# Context variables for request-scoped data
request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)
trace_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "trace_id", default=None
)
user_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "user_id", default=None
)
api_key_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "api_key_id", default=None
)


def get_request_id() -> str | None:
    """Get the current request ID from context."""
    return request_id_var.get()


def set_request_id(request_id: str | None) -> None:
    """Set the request ID in context."""
    request_id_var.set(request_id)


def get_trace_id() -> str | None:
    """Get the current trace ID from context."""
    return trace_id_var.get()


def set_trace_id(trace_id: str | None) -> None:
    """Set the trace ID in context."""
    trace_id_var.set(trace_id)


def get_user_id() -> str | None:
    """Get the current user ID from context."""
    return user_id_var.get()


def set_user_id(user_id: str | None) -> None:
    """Set the user ID in context."""
    user_id_var.set(user_id)


def get_api_key_id() -> str | None:
    """Get the current API key ID from context."""
    return api_key_id_var.get()


def set_api_key_id(api_key_id: str | None) -> None:
    """Set the API key ID in context."""
    api_key_id_var.set(api_key_id)


def generate_request_id() -> str:
    """Generate a unique request ID."""
    return str(uuid.uuid4())


class JSONFormatter(logging.Formatter):
    """
    Custom JSON log formatter.

    Outputs logs in structured JSON format for easy parsing by log aggregators.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.default_fields = {
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.APP_ENV,
        }

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            **self.default_fields,
        }

        # Add context variables
        request_id = get_request_id()
        if request_id:
            log_data["request_id"] = request_id

        trace_id = get_trace_id()
        if trace_id:
            log_data["trace_id"] = trace_id

        user_id = get_user_id()
        if user_id:
            log_data["user_id"] = user_id

        api_key_id = get_api_key_id()
        if api_key_id:
            log_data["api_key_id"] = api_key_id

        # Add source location
        log_data["source"] = {
            "file": record.filename,
            "line": record.lineno,
            "function": record.funcName,
        }

        # Add extra fields from the record
        if hasattr(record, "__dict__"):
            for key, value in record.__dict__.items():
                if key not in (
                    "name",
                    "msg",
                    "args",
                    "created",
                    "filename",
                    "funcName",
                    "levelname",
                    "levelno",
                    "lineno",
                    "module",
                    "msecs",
                    "pathname",
                    "process",
                    "processName",
                    "relativeCreated",
                    "stack_info",
                    "exc_info",
                    "exc_text",
                    "thread",
                    "threadName",
                    "message",
                    "taskName",
                ):
                    try:
                        # Ensure the value is JSON serializable
                        json.dumps(value)
                        log_data[key] = value
                    except (TypeError, ValueError):
                        log_data[key] = str(value)

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info),
            }

        return json.dumps(log_data, default=str)


class DevelopmentFormatter(logging.Formatter):
    """
    Human-readable formatter for development.

    Provides colored, readable output for local development.
    """

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors and context."""
        color = self.COLORS.get(record.levelname, self.RESET)

        # Build prefix with context
        prefix_parts = []
        request_id = get_request_id()
        if request_id:
            prefix_parts.append(f"req={request_id[:8]}")

        api_key_id = get_api_key_id()
        if api_key_id:
            prefix_parts.append(f"key={api_key_id[:8]}")

        prefix = f"[{' '.join(prefix_parts)}] " if prefix_parts else ""

        # Format the base message
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        message = (
            f"{timestamp} | {color}{record.levelname:8}{self.RESET} | "
            f"{record.name:30} | {prefix}{record.getMessage()}"
        )

        # Add extra fields
        extra_fields = {}
        if hasattr(record, "__dict__"):
            for key, value in record.__dict__.items():
                if key not in (
                    "name",
                    "msg",
                    "args",
                    "created",
                    "filename",
                    "funcName",
                    "levelname",
                    "levelno",
                    "lineno",
                    "module",
                    "msecs",
                    "pathname",
                    "process",
                    "processName",
                    "relativeCreated",
                    "stack_info",
                    "exc_info",
                    "exc_text",
                    "thread",
                    "threadName",
                    "message",
                    "taskName",
                ):
                    extra_fields[key] = value

        if extra_fields:
            message += f"\n    {color}→{self.RESET} {extra_fields}"

        # Add exception info
        if record.exc_info:
            message += f"\n{self.formatException(record.exc_info)}"

        return message


class ContextFilter(logging.Filter):
    """Filter that adds context variables to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Add context to the record."""
        record.request_id = get_request_id()
        record.trace_id = get_trace_id()
        record.user_id = get_user_id()
        record.api_key_id = get_api_key_id()
        return True


def setup_logging() -> None:
    """
    Configure application logging.

    Sets up structured JSON logging for production and readable
    colored output for development.
    """
    # Determine log level
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)

    # Choose formatter based on environment
    if settings.is_production:
        formatter = JSONFormatter()
    else:
        formatter = DevelopmentFormatter()

    handler.setFormatter(formatter)

    # Add context filter
    handler.addFilter(ContextFilter())

    # Add handler to root logger
    root_logger.addHandler(handler)

    # Set levels for noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.WARNING if settings.is_production else logging.INFO
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    # Log startup
    logger = logging.getLogger(__name__)
    logger.info(
        f"Logging configured",
        extra={
            "log_level": settings.LOG_LEVEL,
            "format": "json" if settings.is_production else "development",
        },
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


# Convenience function for adding extra context to log calls
def log_with_context(
    logger: logging.Logger,
    level: int,
    message: str,
    **extra: Any,
) -> None:
    """
    Log a message with additional context.

    Args:
        logger: Logger instance
        level: Log level (e.g., logging.INFO)
        message: Log message
        **extra: Additional fields to include in the log
    """
    logger.log(level, message, extra=extra)
