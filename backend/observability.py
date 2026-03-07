"""
Structured logging and request tracing.

Every log line is newline-delimited JSON, suitable for:
  - Shipping to Datadog / Logtail / CloudWatch
  - Parsing by any SIEM
  - SOC 2 CC7.2 — monitoring system activity

Request IDs follow the W3C Trace-Context format (X-Request-ID header).
"""

import json
import logging
import os
import sys
import time
import uuid
from contextvars import ContextVar
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# ---------------------------------------------------------------------------
# Context var so request_id is available anywhere in the call stack
# ---------------------------------------------------------------------------
request_id_var: ContextVar[str] = ContextVar("request_id", default="")


# ---------------------------------------------------------------------------
# JSON log formatter
# ---------------------------------------------------------------------------
class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "request_id": request_id_var.get(""),
            "env": os.getenv("ENVIRONMENT", "development"),
            "version": os.getenv("APP_VERSION", "unknown"),
        }
        if record.exc_info:
            log["exc"] = self.formatException(record.exc_info)
        # Merge any extra fields passed via extra={}
        for key, val in record.__dict__.items():
            if key not in {
                "msg", "args", "levelname", "levelno", "pathname", "filename",
                "module", "exc_info", "exc_text", "stack_info", "lineno",
                "funcName", "created", "msecs", "relativeCreated", "thread",
                "threadName", "processName", "process", "name", "message",
            }:
                log[key] = val
        return json.dumps(log)


def setup_logging() -> logging.Logger:
    level = getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO)
    root = logging.getLogger()
    root.setLevel(level)
    # Remove any existing handlers
    root.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)
    # Silence noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    return logging.getLogger("seques")


logger = setup_logging()


# ---------------------------------------------------------------------------
# Request tracing middleware
# ---------------------------------------------------------------------------
class RequestTracingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request_id_var.set(rid)

        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception as exc:
            logger.error(
                "unhandled_exception",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "error": str(exc),
                },
            )
            raise
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 1)

        response.headers["X-Request-ID"] = rid
        logger.info(
            "http_request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": duration_ms,
                "ip": request.client.host if request.client else "unknown",
                "ua": request.headers.get("user-agent", ""),
            },
        )
        return response
