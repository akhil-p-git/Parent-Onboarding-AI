"""
Request/Response Logging Middleware.

Provides comprehensive logging for all API requests and responses.
"""

import logging
import time
from typing import Callable
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.config import settings
from app.core.logging import (
    generate_request_id,
    set_api_key_id,
    set_request_id,
    set_trace_id,
    set_user_id,
)

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging HTTP requests and responses.

    Features:
    - Assigns unique request IDs
    - Logs request details (method, path, headers)
    - Logs response details (status code, timing)
    - Adds request ID to response headers
    - Supports trace ID propagation
    """

    # Paths to exclude from detailed logging
    EXCLUDE_PATHS = {
        "/",
        "/health",
        "/ready",
        "/live",
        "/metrics",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/health",
        "/api/v1/health/ready",
        "/api/v1/health/live",
        "/api/v1/health/metrics",
        "/api/v1/health/metrics/prometheus",
        "/favicon.ico",
    }

    # Headers to redact in logs
    REDACT_HEADERS = {
        "authorization",
        "x-api-key",
        "cookie",
        "set-cookie",
    }

    def __init__(
        self,
        app: ASGIApp,
        log_request_body: bool = False,
        log_response_body: bool = False,
        max_body_log_size: int = 1000,
    ) -> None:
        super().__init__(app)
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.max_body_log_size = max_body_log_size

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Process the request and log details."""
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID") or generate_request_id()

        # Extract trace ID for distributed tracing
        trace_id = request.headers.get("X-Trace-ID") or request.headers.get(
            "traceparent"
        )

        # Set context variables
        set_request_id(request_id)
        set_trace_id(trace_id)

        # Store request ID in state for access in handlers
        request.state.request_id = request_id
        request.state.trace_id = trace_id

        # Record start time
        start_time = time.perf_counter()

        # Check if this is a health check or excluded path
        is_health_check = request.url.path in self.EXCLUDE_PATHS

        # Log incoming request (unless excluded)
        if not is_health_check:
            await self._log_request(request)

        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Log exception
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"Request failed with exception",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "duration_ms": round(duration_ms, 2),
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )
            raise

        # Calculate duration
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Add headers to response
        response.headers["X-Request-ID"] = request_id
        if trace_id:
            response.headers["X-Trace-ID"] = trace_id
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

        # Log response (unless excluded)
        if not is_health_check:
            self._log_response(request, response, duration_ms)

        # Clear context variables
        set_request_id(None)
        set_trace_id(None)
        set_user_id(None)
        set_api_key_id(None)

        return response

    async def _log_request(self, request: Request) -> None:
        """Log incoming request details."""
        # Get safe headers
        headers = self._get_safe_headers(dict(request.headers))

        # Extract client info
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")

        log_data = {
            "event": "request_started",
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params) if request.query_params else None,
            "client_ip": client_ip,
            "user_agent": user_agent,
            "content_type": request.headers.get("content-type"),
            "content_length": request.headers.get("content-length"),
        }

        # Add headers in debug mode
        if settings.DEBUG:
            log_data["headers"] = headers

        logger.info(f"→ {request.method} {request.url.path}", extra=log_data)

    def _log_response(
        self, request: Request, response: Response, duration_ms: float
    ) -> None:
        """Log outgoing response details."""
        # Determine log level based on status code
        status_code = response.status_code

        log_data = {
            "event": "request_completed",
            "method": request.method,
            "path": request.url.path,
            "status_code": status_code,
            "duration_ms": round(duration_ms, 2),
            "content_type": response.headers.get("content-type"),
            "content_length": response.headers.get("content-length"),
        }

        # Format message
        message = f"← {request.method} {request.url.path} {status_code} ({duration_ms:.2f}ms)"

        if status_code >= 500:
            logger.error(message, extra=log_data)
        elif status_code >= 400:
            logger.warning(message, extra=log_data)
        else:
            logger.info(message, extra=log_data)

    def _get_safe_headers(self, headers: dict[str, str]) -> dict[str, str]:
        """Get headers with sensitive values redacted."""
        safe_headers = {}
        for key, value in headers.items():
            if key.lower() in self.REDACT_HEADERS:
                safe_headers[key] = "[REDACTED]"
            else:
                safe_headers[key] = value
        return safe_headers

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request, considering proxies."""
        # Check X-Forwarded-For header (for load balancers/proxies)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Get the first IP in the chain (original client)
            return forwarded_for.split(",")[0].strip()

        # Check X-Real-IP header
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fall back to direct client IP
        if request.client:
            return request.client.host

        return "unknown"


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """
    Simple middleware that only handles correlation IDs.

    Use this if you want minimal overhead and only need request IDs.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add correlation ID to request and response."""
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid4())

        # Set in context
        set_request_id(request_id)
        request.state.request_id = request_id

        # Process request
        response = await call_next(request)

        # Add to response
        response.headers["X-Request-ID"] = request_id

        # Clear context
        set_request_id(None)

        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to responses.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response."""
        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Add HSTS in production
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        return response


class SlowRequestMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log slow requests.
    """

    def __init__(self, app: ASGIApp, threshold_ms: float = 1000.0) -> None:
        super().__init__(app)
        self.threshold_ms = threshold_ms

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log requests that exceed the threshold."""
        start_time = time.perf_counter()

        response = await call_next(request)

        duration_ms = (time.perf_counter() - start_time) * 1000

        if duration_ms > self.threshold_ms:
            logger.warning(
                f"Slow request detected",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "duration_ms": round(duration_ms, 2),
                    "threshold_ms": self.threshold_ms,
                    "status_code": response.status_code,
                },
            )

        return response
