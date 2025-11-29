"""
Endpoint for receiving error logs from client applications (desktop, mobile).

This allows centralized error tracking from all parts of the system.
"""
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


class ClientErrorReport(BaseModel):
    """Schema for error reports from client applications."""

    client_type: str = Field(..., description="Client type: 'desktop' or 'mobile'")
    client_version: str = Field(..., description="Client application version")
    error_level: str = Field(default="ERROR", description="ERROR, CRITICAL, WARNING")
    error_message: str = Field(..., description="Error message")
    error_type: Optional[str] = Field(None, description="Exception type/class name")
    stack_trace: Optional[str] = Field(None, description="Full stack trace")
    module: Optional[str] = Field(None, description="Module where error occurred")
    function: Optional[str] = Field(None, description="Function where error occurred")
    line_number: Optional[int] = Field(None, description="Line number")
    timestamp: Optional[datetime] = Field(None, description="When error occurred on client")
    device_info: Optional[dict] = Field(None, description="Device/OS information")
    user_context: Optional[dict] = Field(None, description="User action context")

    class Config:
        json_schema_extra = {
            "example": {
                "client_type": "desktop",
                "client_version": "1.0.0",
                "error_level": "ERROR",
                "error_message": "Failed to connect to WebSocket",
                "error_type": "ConnectionError",
                "stack_trace": "Traceback (most recent call last):\n  ...",
                "module": "websocket_client",
                "function": "connect",
                "line_number": 42,
                "timestamp": "2025-01-15T10:30:00Z",
                "device_info": {"os": "Windows 11", "python": "3.11.5"},
                "user_context": {"action": "connecting_to_stream", "symbol": "BTC-USD"}
            }
        }


class ClientErrorResponse(BaseModel):
    """Response after receiving error report."""
    received: bool = True
    error_id: str
    message: str = "Error logged successfully"


class ErrorStats(BaseModel):
    """Statistics about client errors."""
    total_errors: int
    errors_by_client: dict
    errors_by_level: dict
    recent_errors: List[dict]


# In-memory storage for recent errors (for quick access)
# In production, this would be stored in a database
_recent_client_errors: List[dict] = []
MAX_STORED_ERRORS = 1000


@router.post("/report", response_model=ClientErrorResponse)
async def report_client_error(error: ClientErrorReport):
    """
    Receive error report from client application.

    This endpoint allows desktop and mobile apps to report errors
    to the central backend for unified error tracking.
    """
    error_id = f"{error.client_type}_{int(datetime.utcnow().timestamp() * 1000)}"

    # Build log message with full context
    log_parts = [
        f"CLIENT ERROR [{error.client_type.upper()}]",
        f"v{error.client_version}",
        f"| {error.error_type or 'Unknown'}: {error.error_message}",
    ]

    if error.module:
        log_parts.append(f"| Module: {error.module}")
    if error.function:
        log_parts.append(f"| Function: {error.function}:{error.line_number or '?'}")

    log_message = " ".join(log_parts)

    # Log based on error level
    if error.error_level == "CRITICAL":
        logger.critical(log_message)
    elif error.error_level == "WARNING":
        logger.warning(log_message)
    else:
        logger.error(log_message)

    # Log stack trace separately if present
    if error.stack_trace:
        logger.error(f"Stack trace for {error_id}:\n{error.stack_trace}")

    # Store in memory for recent errors endpoint
    error_record = {
        "error_id": error_id,
        "client_type": error.client_type,
        "client_version": error.client_version,
        "error_level": error.error_level,
        "error_message": error.error_message,
        "error_type": error.error_type,
        "module": error.module,
        "function": error.function,
        "timestamp": error.timestamp or datetime.utcnow(),
        "device_info": error.device_info,
        "received_at": datetime.utcnow()
    }

    _recent_client_errors.insert(0, error_record)

    # Keep only last N errors
    if len(_recent_client_errors) > MAX_STORED_ERRORS:
        _recent_client_errors.pop()

    return ClientErrorResponse(
        error_id=error_id,
        message=f"Error logged successfully from {error.client_type}"
    )


@router.get("/stats", response_model=ErrorStats)
async def get_error_stats():
    """
    Get statistics about recent client errors.

    Useful for monitoring error trends across clients.
    """
    errors_by_client = {}
    errors_by_level = {}

    for error in _recent_client_errors:
        # Count by client type
        client = error["client_type"]
        errors_by_client[client] = errors_by_client.get(client, 0) + 1

        # Count by level
        level = error["error_level"]
        errors_by_level[level] = errors_by_level.get(level, 0) + 1

    return ErrorStats(
        total_errors=len(_recent_client_errors),
        errors_by_client=errors_by_client,
        errors_by_level=errors_by_level,
        recent_errors=_recent_client_errors[:20]  # Last 20 errors
    )


@router.get("/recent")
async def get_recent_errors(
    client_type: Optional[str] = None,
    error_level: Optional[str] = None,
    limit: int = 50
):
    """
    Get recent client errors with optional filtering.

    Args:
        client_type: Filter by 'desktop' or 'mobile'
        error_level: Filter by ERROR, CRITICAL, WARNING
        limit: Maximum number of errors to return
    """
    filtered = _recent_client_errors

    if client_type:
        filtered = [e for e in filtered if e["client_type"] == client_type]

    if error_level:
        filtered = [e for e in filtered if e["error_level"] == error_level]

    return {
        "count": len(filtered[:limit]),
        "errors": filtered[:limit]
    }


@router.delete("/clear")
async def clear_error_logs():
    """
    Clear all stored client error logs.

    Use with caution - this removes all error history from memory.
    """
    global _recent_client_errors
    count = len(_recent_client_errors)
    _recent_client_errors = []
    logger.info(f"Cleared {count} client error records")
    return {"message": f"Cleared {count} error records"}
