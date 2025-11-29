"""
Alert notification system for critical errors.

This module provides infrastructure for sending alerts via various channels
(Telegram, Discord, SMS, etc.) when critical errors occur.

Currently prepared for future implementation. To enable:
1. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env
2. Set DISCORD_WEBHOOK_URL in .env

Usage:
    from app.core.alert_notifier import AlertNotifier, AlertLevel

    notifier = AlertNotifier()
    await notifier.send_alert(
        level=AlertLevel.CRITICAL,
        title="Database Connection Lost",
        message="PostgreSQL connection failed after 5 retries",
        source="database.connection"
    )
"""
import asyncio
from datetime import datetime
from enum import Enum
from typing import Optional, List
from abc import ABC, abstractmethod

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AlertChannel(ABC):
    """Base class for alert notification channels."""

    @abstractmethod
    async def send(self, level: AlertLevel, title: str, message: str, source: str) -> bool:
        """Send alert through this channel. Returns True if successful."""
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """Check if this channel is properly configured."""
        pass


class TelegramChannel(AlertChannel):
    """Telegram notification channel."""

    def __init__(self):
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID

    def is_configured(self) -> bool:
        return bool(self.bot_token and self.chat_id)

    async def send(self, level: AlertLevel, title: str, message: str, source: str) -> bool:
        if not self.is_configured():
            return False

        try:
            import httpx

            emoji = {
                AlertLevel.INFO: "ℹ️",
                AlertLevel.WARNING: "⚠️",
                AlertLevel.ERROR: "❌",
                AlertLevel.CRITICAL: "🚨"
            }.get(level, "📢")

            text = (
                f"{emoji} *{level.value}: {title}*\n\n"
                f"📍 Source: `{source}`\n"
                f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"```\n{message[:3000]}\n```"
            )

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://api.telegram.org/bot{self.bot_token}/sendMessage",
                    json={
                        "chat_id": self.chat_id,
                        "text": text,
                        "parse_mode": "Markdown"
                    },
                    timeout=10.0
                )
                return response.status_code == 200

        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")
            return False


class DiscordChannel(AlertChannel):
    """Discord webhook notification channel."""

    def __init__(self):
        self.webhook_url = settings.DISCORD_WEBHOOK_URL

    def is_configured(self) -> bool:
        return bool(self.webhook_url)

    async def send(self, level: AlertLevel, title: str, message: str, source: str) -> bool:
        if not self.is_configured():
            return False

        try:
            import httpx

            color = {
                AlertLevel.INFO: 0x3498DB,      # Blue
                AlertLevel.WARNING: 0xF39C12,   # Orange
                AlertLevel.ERROR: 0xE74C3C,     # Red
                AlertLevel.CRITICAL: 0x9B59B6   # Purple
            }.get(level, 0x95A5A6)

            embed = {
                "title": f"{level.value}: {title}",
                "description": message[:4000],
                "color": color,
                "fields": [
                    {"name": "Source", "value": f"`{source}`", "inline": True},
                    {"name": "Time", "value": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "inline": True}
                ],
                "footer": {"text": "AI Trading System Alert"}
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json={"embeds": [embed]},
                    timeout=10.0
                )
                return response.status_code in (200, 204)

        except Exception as e:
            logger.error(f"Failed to send Discord alert: {e}")
            return False


class ConsoleChannel(AlertChannel):
    """Console/log notification channel (always enabled)."""

    def is_configured(self) -> bool:
        return True

    async def send(self, level: AlertLevel, title: str, message: str, source: str) -> bool:
        log_msg = f"[ALERT] {level.value} | {title} | Source: {source} | {message}"

        if level == AlertLevel.CRITICAL:
            logger.critical(log_msg)
        elif level == AlertLevel.ERROR:
            logger.error(log_msg)
        elif level == AlertLevel.WARNING:
            logger.warning(log_msg)
        else:
            logger.info(log_msg)

        return True


class AlertNotifier:
    """
    Main alert notification manager.

    Sends alerts through all configured channels.
    """

    def __init__(self):
        self.channels: List[AlertChannel] = [
            ConsoleChannel(),  # Always enabled
            TelegramChannel(),
            DiscordChannel(),
        ]

        # Log which channels are configured
        configured = [c.__class__.__name__ for c in self.channels if c.is_configured()]
        logger.info(f"AlertNotifier initialized with channels: {configured}")

    async def send_alert(
        self,
        level: AlertLevel,
        title: str,
        message: str,
        source: str = "unknown"
    ) -> dict:
        """
        Send alert through all configured channels.

        Args:
            level: Alert severity level
            title: Short alert title
            message: Detailed message
            source: Source module/component

        Returns:
            Dict with results per channel
        """
        results = {}

        for channel in self.channels:
            if channel.is_configured():
                channel_name = channel.__class__.__name__
                try:
                    success = await channel.send(level, title, message, source)
                    results[channel_name] = "sent" if success else "failed"
                except Exception as e:
                    results[channel_name] = f"error: {str(e)}"
                    logger.error(f"Alert channel {channel_name} failed: {e}")

        return results

    def send_alert_sync(
        self,
        level: AlertLevel,
        title: str,
        message: str,
        source: str = "unknown"
    ) -> None:
        """
        Synchronous wrapper for send_alert.
        Runs in background, doesn't block.
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.send_alert(level, title, message, source))
            else:
                loop.run_until_complete(self.send_alert(level, title, message, source))
        except RuntimeError:
            # No event loop, create new one
            asyncio.run(self.send_alert(level, title, message, source))


# Global notifier instance
_notifier: Optional[AlertNotifier] = None


def get_notifier() -> AlertNotifier:
    """Get global AlertNotifier instance."""
    global _notifier
    if _notifier is None:
        _notifier = AlertNotifier()
    return _notifier


async def send_critical_alert(title: str, message: str, source: str = "unknown") -> dict:
    """Convenience function for sending critical alerts."""
    return await get_notifier().send_alert(AlertLevel.CRITICAL, title, message, source)


async def send_error_alert(title: str, message: str, source: str = "unknown") -> dict:
    """Convenience function for sending error alerts."""
    return await get_notifier().send_alert(AlertLevel.ERROR, title, message, source)
