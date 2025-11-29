"""
Alerts endpoints - create, list, delete alerts
"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from enum import Enum

router = APIRouter()

# In-memory storage for now (in production, use database)
alerts_db = []


class AlertType(str, Enum):
    TECHNICAL = "technical"
    PRICE = "price"
    CUSTOM = "custom"


class AlertSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertCreate(BaseModel):
    symbol: str
    alert_type: AlertType
    severity: AlertSeverity
    message: str
    conditions: dict
    channels: List[str] = ["telegram"]


class Alert(BaseModel):
    id: str
    symbol: str
    alert_type: AlertType
    severity: AlertSeverity
    message: str
    conditions: dict
    channels: List[str]
    created_at: datetime
    triggered_at: Optional[datetime] = None
    status: str = "active"  # active, triggered, dismissed


@router.post("/create")
async def create_alert(alert: AlertCreate):
    """
    Create a new alert
    """
    import uuid

    new_alert = Alert(
        id=str(uuid.uuid4()),
        symbol=alert.symbol,
        alert_type=alert.alert_type,
        severity=alert.severity,
        message=alert.message,
        conditions=alert.conditions,
        channels=alert.channels,
        created_at=datetime.utcnow()
    )

    alerts_db.append(new_alert.dict())

    return {
        "success": True,
        "alert_id": new_alert.id,
        "message": f"Alert created for {alert.symbol}"
    }


@router.get("/")
async def get_alerts(
    status: Optional[str] = None,
    symbol: Optional[str] = None
):
    """
    Get all alerts, optionally filtered by status or symbol
    """
    filtered_alerts = alerts_db

    if status:
        filtered_alerts = [a for a in filtered_alerts if a["status"] == status]

    if symbol:
        filtered_alerts = [a for a in filtered_alerts if a["symbol"] == symbol]

    return {
        "total": len(filtered_alerts),
        "alerts": filtered_alerts
    }


@router.get("/{alert_id}")
async def get_alert(alert_id: str):
    """
    Get a specific alert by ID
    """
    alert = next((a for a in alerts_db if a["id"] == alert_id), None)

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    return alert


@router.delete("/{alert_id}")
async def delete_alert(alert_id: str):
    """
    Delete an alert
    """
    global alerts_db

    alert = next((a for a in alerts_db if a["id"] == alert_id), None)

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alerts_db = [a for a in alerts_db if a["id"] != alert_id]

    return {
        "success": True,
        "message": f"Alert {alert_id} deleted"
    }


@router.post("/test")
async def test_alert():
    """
    Send a test alert through all configured channels
    """
    test_message = "🧪 Test alert from AI Trading System"

    # In production, this would actually send to Telegram, Discord, etc.
    return {
        "success": True,
        "message": "Test alert sent (not implemented yet - requires credentials)",
        "channels_tested": ["telegram", "discord", "push"]
    }
