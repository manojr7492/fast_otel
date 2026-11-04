import json
import logging
import sys
import traceback
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from opentelemetry import trace
from app.core.config import settings

SENSITIVE_KEYS = {
    "password", "secret", "token", "access_token", "refresh_token",
    "authorization", "hashed_password", "credit_card", "card_number", "cvv"
}


def sanitize_data(data: Any) -> Any:
    """Recursively redact sensitive keys from dictionaries or lists."""
    if isinstance(data, dict):
        sanitized = {}
        for k, v in data.items():
            if any(sens in str(k).lower() for sens in SENSITIVE_KEYS):
                sanitized[k] = "[REDACTED]"
            else:
                sanitized[k] = sanitize_data(v)
        return sanitized
    elif isinstance(data, (list, tuple, set)):
        return [sanitize_data(item) for item in data]
    return data


class JSONLogFormatter(logging.Formatter):
    """
    Production-grade structured JSON log formatter that correlates log records
    with active OpenTelemetry trace_id and span_id, and redacts sensitive data.
    """

    def format(self, record: logging.LogRecord) -> str:
        # Extract active OpenTelemetry span context
        span = trace.get_current_span()
        span_ctx = span.get_span_context() if span else None

        trace_id: Optional[str] = None
        span_id: Optional[str] = None
        if span_ctx and span_ctx.is_valid:
            trace_id = f"{span_ctx.trace_id:032x}"
            span_id = f"{span_ctx.span_id:016x}"

        log_payload: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service_name": settings.SERVICE_NAME,
            "environment": settings.ENVIRONMENT,
            "logger": record.name,
            "message": record.getMessage(),
            "trace_id": trace_id,
            "span_id": span_id,
            "process_id": record.process,
            "thread_name": record.threadName,
        }

        # Include source code location for errors
        if record.levelno >= logging.ERROR:
            log_payload["location"] = f"{record.pathname}:{record.lineno}"

        # Capture exception details safely
        if record.exc_info:
            exc_type, exc_value, exc_tb = record.exc_info
            log_payload["exception"] = {
                "type": exc_type.__name__ if exc_type else "Exception",
                "message": str(exc_value) if exc_value else "",
                "stacktrace": traceback.format_exception(exc_type, exc_value, exc_tb),
            }

        # Support extra context passed to logger
        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            log_payload["extra"] = sanitize_data(record.extra_data)

        return json.dumps(log_payload, default=str)


def setup_logging():
    """Initializes structured logging based on configuration."""
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO

    handler = logging.StreamHandler(sys.stdout)
    if settings.LOG_FORMAT.lower() == "json":
        handler.setFormatter(JSONLogFormatter())
    else:
        text_format = (
            "[%(asctime)s] [%(process)d] [%(levelname)s] "
            "[%(name)s:%(lineno)d] - %(message)s"
        )
        handler.setFormatter(logging.Formatter(text_format))

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers = [handler]

    # Silence noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("asyncmy").setLevel(logging.WARNING)
    logging.getLogger("opentelemetry").setLevel(logging.WARNING)

    service_logger = logging.getLogger(settings.SERVICE_NAME)
    service_logger.info(
        "Structured logging initialized for %s in %s mode (Format: %s).",
        settings.SERVICE_NAME,
        settings.ENVIRONMENT,
        settings.LOG_FORMAT,
    )
    return service_logger


logger = logging.getLogger(settings.SERVICE_NAME)
