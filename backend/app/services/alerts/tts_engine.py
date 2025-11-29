"""
Text-to-Speech engine for voice alerts
"""
import logging
from typing import Optional
import os

logger = logging.getLogger(__name__)

# Try to import TTS libraries
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    logger.warning("pyttsx3 not available. Voice alerts will be limited.")

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False
    logger.warning("gTTS not available. Google TTS will not work.")


class TTSEngine:
    """
    Text-to-Speech engine for voice alerts
    Supports both offline (pyttsx3) and online (gTTS)
    """

    def __init__(self, engine: str = "pyttsx3"):
        """
        Initialize TTS engine

        Args:
            engine: 'pyttsx3' (offline) or 'gtts' (online)
        """
        self.engine_name = engine

        if engine == "pyttsx3" and PYTTSX3_AVAILABLE:
            self.engine = pyttsx3.init()
            self._configure_pyttsx3()
        elif engine == "gtts" and not GTTS_AVAILABLE:
            raise ValueError("gTTS not available. Install with: pip install gtts")
        elif not PYTTSX3_AVAILABLE:
            raise ValueError("pyttsx3 not available. Install with: pip install pyttsx3")

    def _configure_pyttsx3(self):
        """Configure pyttsx3 engine settings"""
        try:
            # Set rate (speed of speech)
            self.engine.setProperty('rate', 150)  # Normal speed

            # Set volume (0.0 to 1.0)
            self.engine.setProperty('volume', 1.0)

            # Set voice (optional - male/female)
            voices = self.engine.getProperty('voices')
            if voices:
                # Use first available voice
                self.engine.setProperty('voice', voices[0].id)

        except Exception as e:
            logger.error(f"Error configuring pyttsx3: {e}")

    def speak(self, text: str, async_mode: bool = False) -> bool:
        """
        Speak text using TTS

        Args:
            text: Text to speak
            async_mode: If True, speak asynchronously (non-blocking)

        Returns:
            True if successful
        """
        try:
            if self.engine_name == "pyttsx3" and PYTTSX3_AVAILABLE:
                self.engine.say(text)
                if not async_mode:
                    self.engine.runAndWait()
                return True

            elif self.engine_name == "gtts" and GTTS_AVAILABLE:
                # Generate audio file
                tts = gTTS(text=text, lang='en', slow=False)
                filename = "/tmp/tts_alert.mp3"
                tts.save(filename)

                # Play audio (requires system audio player)
                if os.name == 'posix':  # Linux/Mac
                    os.system(f"mpg123 {filename} >/dev/null 2>&1 &" if async_mode else f"mpg123 {filename}")
                elif os.name == 'nt':  # Windows
                    os.system(f"start {filename}")

                return True

            else:
                logger.error("No TTS engine available")
                return False

        except Exception as e:
            logger.error(f"TTS speak error: {e}")
            return False

    def alert(
        self,
        symbol: str,
        signal: str,
        price: Optional[float] = None,
        pattern: Optional[str] = None,
        rsi: Optional[float] = None
    ) -> bool:
        """
        Speak trading alert

        Args:
            symbol: Trading symbol
            signal: BUY/SELL/NEUTRAL
            price: Current price
            pattern: Candlestick pattern
            rsi: RSI value

        Returns:
            True if successful
        """
        # Build alert message
        message_parts = ["Alert!"]

        if pattern:
            message_parts.append(f"{pattern} pattern detected on")

        message_parts.append(symbol)

        if signal:
            message_parts.append(f"Signal: {signal}")

        if price:
            message_parts.append(f"Price: {price:.2f}")

        if rsi:
            if rsi < 30:
                message_parts.append(f"RSI oversold at {rsi:.1f}")
            elif rsi > 70:
                message_parts.append(f"RSI overbought at {rsi:.1f}")
            else:
                message_parts.append(f"RSI at {rsi:.1f}")

        message = ". ".join(message_parts)

        logger.info(f"TTS Alert: {message}")
        return self.speak(message, async_mode=True)

    def simple_alert(self, message: str) -> bool:
        """
        Speak simple alert message

        Args:
            message: Message to speak

        Returns:
            True if successful
        """
        return self.speak(message, async_mode=True)


# Example usage and testing
if __name__ == "__main__":
    # Test pyttsx3 (offline)
    if PYTTSX3_AVAILABLE:
        print("Testing pyttsx3 (offline TTS)...")
        tts = TTSEngine(engine="pyttsx3")
        tts.alert(
            symbol="DAX",
            signal="SELL",
            pattern="Shooting Star",
            price=16150.50,
            rsi=68.5
        )
        print("TTS alert sent!")

    # Test gTTS (online)
    if GTTS_AVAILABLE:
        print("\nTesting gTTS (online TTS)...")
        tts_online = TTSEngine(engine="gtts")
        tts_online.simple_alert("This is a test alert for gTTS")
        print("gTTS alert sent!")
