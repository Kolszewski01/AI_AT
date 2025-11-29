"""
SMS alerts using Twilio
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Try to import Twilio
try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    logger.warning("Twilio not available. SMS alerts will not work.")


class SMSAlerter:
    """
    Send SMS alerts using Twilio
    """

    def __init__(
        self,
        account_sid: str,
        auth_token: str,
        from_number: str,
        to_number: str
    ):
        """
        Initialize Twilio SMS client

        Args:
            account_sid: Twilio Account SID
            auth_token: Twilio Auth Token
            from_number: Twilio phone number (sender)
            to_number: Recipient phone number
        """
        if not TWILIO_AVAILABLE:
            raise ValueError("Twilio not available. Install with: pip install twilio")

        self.client = Client(account_sid, auth_token)
        self.from_number = from_number
        self.to_number = to_number

    def send_alert(
        self,
        symbol: str,
        signal: str,
        price: float,
        pattern: Optional[str] = None,
        severity: str = "medium"
    ) -> bool:
        """
        Send SMS trading alert

        Args:
            symbol: Trading symbol
            signal: BUY/SELL/NEUTRAL
            price: Current price
            pattern: Candlestick pattern
            severity: Alert severity

        Returns:
            True if sent successfully
        """
        try:
            # Build SMS message (max 160 characters for single SMS)
            message_parts = [
                f"🚨 {signal} ALERT"
            ]

            if severity == "critical":
                message_parts[0] = f"⚠️ CRITICAL: {signal}"

            message_parts.append(f"{symbol}: ${price:.2f}")

            if pattern:
                message_parts.append(f"Pattern: {pattern}")

            message = "\n".join(message_parts)

            # Send SMS
            twilio_message = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=self.to_number
            )

            logger.info(f"SMS alert sent for {symbol}. SID: {twilio_message.sid}")
            return True

        except Exception as e:
            logger.error(f"Failed to send SMS alert: {e}")
            return False

    def send_simple_message(self, message: str) -> bool:
        """
        Send simple SMS message

        Args:
            message: Message text (max 1600 chars for concatenated SMS)

        Returns:
            True if sent successfully
        """
        try:
            twilio_message = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=self.to_number
            )

            logger.info(f"SMS sent. SID: {twilio_message.sid}")
            return True

        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
            return False

    def send_critical_alert(
        self,
        symbol: str,
        message: str
    ) -> bool:
        """
        Send critical alert (short, urgent)

        Args:
            symbol: Trading symbol
            message: Alert message

        Returns:
            True if sent successfully
        """
        alert_text = f"⚠️ CRITICAL ALERT ⚠️\n{symbol}: {message}"
        return self.send_simple_message(alert_text)


# Example usage
if __name__ == "__main__":
    import os

    if TWILIO_AVAILABLE:
        # Load from environment variables
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        from_number = os.getenv('TWILIO_FROM_NUMBER')
        to_number = os.getenv('TWILIO_TO_NUMBER')

        if all([account_sid, auth_token, from_number, to_number]):
            sms = SMSAlerter(account_sid, auth_token, from_number, to_number)
            sms.send_alert(
                symbol="DAX",
                signal="SELL",
                price=16150.50,
                pattern="Shooting Star",
                severity="critical"
            )
            print("SMS alert sent!")
        else:
            print("Twilio credentials not configured in environment")
    else:
        print("Twilio not available")
