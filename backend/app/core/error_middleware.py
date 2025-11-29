"""
Error handling middleware for FastAPI.

Catches unhandled exceptions and logs them with full context.
"""
import time
import traceback
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logger import get_logger

logger = get_logger(__name__)


class ErrorLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that logs all errors with request context."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        request_id = f"{int(start_time * 1000)}"

        # Build request context for logging
        request_context = {
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "client_ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown")[:100],
        }

        try:
            response = await call_next(request)
            duration = time.time() - start_time

            # Log slow requests (>5s) as warnings
            if duration > 5.0:
                logger.warning(
                    f"Slow request: {request.method} {request.url.path} "
                    f"took {duration:.2f}s | {request_context}"
                )

            # Log 5xx errors
            if response.status_code >= 500:
                logger.error(
                    f"Server error response: {response.status_code} | "
                    f"{request.method} {request.url.path} | {request_context}"
                )

            return response

        except Exception as exc:
            duration = time.time() - start_time

            # Log the full exception with traceback
            logger.error(
                f"Unhandled exception in request | "
                f"{request.method} {request.url.path} | "
                f"Duration: {duration:.2f}s | "
                f"Context: {request_context}",
                exc_info=True
            )

            # Return generic error response
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error",
                    "request_id": request_id
                }
            )
