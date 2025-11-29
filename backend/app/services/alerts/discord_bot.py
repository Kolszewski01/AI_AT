"""
Discord webhook integration for trading alerts
"""
import logging
import requests
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class DiscordAlerter:
    """
    Send trading alerts to Discord via webhook
    """

    def __init__(self, webhook_url: str):
        """
        Initialize Discord webhook

        Args:
            webhook_url: Discord webhook URL
        """
        self.webhook_url = webhook_url

    def send_alert(
        self,
        symbol: str,
        signal: str,
        price: float,
        details: Dict,
        severity: str = "medium"
    ) -> bool:
        """
        Send trading alert to Discord

        Args:
            symbol: Trading symbol
            signal: BUY/SELL/NEUTRAL
            price: Current price
            details: Additional details (RSI, MACD, etc.)
            severity: low, medium, high, critical

        Returns:
            True if sent successfully
        """
        try:
            # Map severity to color
            color_map = {
                "low": 0x808080,      # Gray
                "medium": 0xFFFF00,   # Yellow
                "high": 0xFFA500,     # Orange
                "critical": 0xFF0000  # Red
            }

            # Map signal to emoji
            signal_emoji = {
                "BUY": "📈 🟢",
                "SELL": "📉 🔴",
                "NEUTRAL": "⚪"
            }

            embed = {
                "title": f"{signal_emoji.get(signal, '')} {signal} SIGNAL - {symbol}",
                "description": f"New trading signal detected for **{symbol}**",
                "color": color_map.get(severity, 0xFFFF00),
                "fields": [
                    {
                        "name": "💰 Price",
                        "value": f"${price:,.2f}",
                        "inline": True
                    },
                    {
                        "name": "📊 Signal",
                        "value": signal,
                        "inline": True
                    },
                    {
                        "name": "⚠️ Severity",
                        "value": severity.upper(),
                        "inline": True
                    }
                ],
                "footer": {
                    "text": f"AI Trading System • {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
                },
                "timestamp": datetime.utcnow().isoformat()
            }

            # Add technical details
            if details.get('rsi'):
                embed["fields"].append({
                    "name": "📈 RSI",
                    "value": f"{details['rsi']:.2f}",
                    "inline": True
                })

            if details.get('macd'):
                embed["fields"].append({
                    "name": "📊 MACD",
                    "value": f"{details['macd']:.4f}",
                    "inline": True
                })

            if details.get('pattern'):
                embed["fields"].append({
                    "name": "🕯️ Pattern",
                    "value": details['pattern'],
                    "inline": True
                })

            if details.get('entry_price'):
                embed["fields"].append({
                    "name": "🎯 Entry",
                    "value": f"${details['entry_price']:.2f}",
                    "inline": True
                })

            if details.get('stop_loss'):
                embed["fields"].append({
                    "name": "🛑 Stop Loss",
                    "value": f"${details['stop_loss']:.2f}",
                    "inline": True
                })

            if details.get('take_profit'):
                embed["fields"].append({
                    "name": "✅ Take Profit",
                    "value": f"${details['take_profit']:.2f}",
                    "inline": True
                })

            if details.get('description'):
                embed["fields"].append({
                    "name": "📝 Analysis",
                    "value": details['description'][:1024],  # Discord limit
                    "inline": False
                })

            payload = {
                "username": "AI Trading Bot",
                "avatar_url": "https://i.imgur.com/4M34hi2.png",  # Optional bot avatar
                "embeds": [embed]
            }

            response = requests.post(self.webhook_url, json=payload)
            response.raise_for_status()

            logger.info(f"Discord alert sent for {symbol}: {signal}")
            return True

        except Exception as e:
            logger.error(f"Failed to send Discord alert: {e}")
            return False

    def send_simple_message(self, message: str) -> bool:
        """
        Send simple text message to Discord

        Args:
            message: Message text

        Returns:
            True if sent successfully
        """
        try:
            payload = {
                "content": message
            }

            response = requests.post(self.webhook_url, json=payload)
            response.raise_for_status()

            logger.info("Simple Discord message sent")
            return True

        except Exception as e:
            logger.error(f"Failed to send Discord message: {e}")
            return False

    def send_chart_screenshot(
        self,
        symbol: str,
        image_url: str,
        caption: Optional[str] = None
    ) -> bool:
        """
        Send chart screenshot to Discord

        Args:
            symbol: Trading symbol
            image_url: URL of chart image
            caption: Optional caption

        Returns:
            True if sent successfully
        """
        try:
            embed = {
                "title": f"📊 Chart: {symbol}",
                "description": caption or f"Chart analysis for {symbol}",
                "image": {
                    "url": image_url
                },
                "color": 0x1E90FF,  # Blue
                "timestamp": datetime.utcnow().isoformat()
            }

            payload = {
                "embeds": [embed]
            }

            response = requests.post(self.webhook_url, json=payload)
            response.raise_for_status()

            logger.info(f"Discord chart sent for {symbol}")
            return True

        except Exception as e:
            logger.error(f"Failed to send Discord chart: {e}")
            return False
