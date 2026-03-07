"""
Security middleware and utilities.

SOC 2 CC6.7  — data transmission controls (security headers)
SOC 2 CC6.1  — logical access (rate limiting)
ISO 27001 A.13.1 — network security management
OWASP Top 10 — A05 Security Misconfiguration
"""

from __future__ import annotations

import os
import time
from collections import defaultdict
from typing import Callable

from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from observability import logger


# ---------------------------------------------------------------------------
# Security headers middleware
# ---------------------------------------------------------------------------
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        env = os.getenv("ENVIRONMENT", "development")

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        # Prevent MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        # XSS protection (legacy browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # Permissions policy — deny everything not needed
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        # Remove server fingerprint
        try:
            del response.headers["server"]
        except KeyError:
            pass

        if env == "production":
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data:; "
                "connect-src 'self' https://api.groq.com https://generativelanguage.googleapis.com https://api.anthropic.com"
            )

        return response


# ---------------------------------------------------------------------------
# In-memory rate limiter (swap for Redis in production)
# ---------------------------------------------------------------------------
_rate_store: dict[str, list[float]] = defaultdict(list)
_RATE_LIMIT = int(os.getenv("RATE_LIMIT_PER_MINUTE", "30"))
_WINDOW = 60  # seconds


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Only rate-limit mutating API calls
        if not request.url.path.startswith("/api") or request.method not in ("POST", "PATCH", "PUT", "DELETE"):
            return await call_next(request)

        ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - _WINDOW

        # Prune old entries
        _rate_store[ip] = [t for t in _rate_store[ip] if t > window_start]

        if len(_rate_store[ip]) >= _RATE_LIMIT:
            logger.warning(
                "rate_limit_exceeded",
                extra={"ip": ip, "path": request.url.path, "count": len(_rate_store[ip])},
            )
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {_RATE_LIMIT} requests per minute",
            )

        _rate_store[ip].append(now)
        return await call_next(request)
