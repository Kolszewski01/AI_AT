"""
WebSocket client for real-time data
"""
import asyncio
import json
import websockets
from typing import Callable, Optional
from PyQt6.QtCore import QThread, pyqtSignal
from src.utils.logger import get_logger

logger = get_logger("websocket")


class WebSocketClient(QThread):
    """
    WebSocket client thread for real-time data streaming

    Signals:
        message_received: Emitted when a message is received
        connected: Emitted when connection is established
        disconnected: Emitted when connection is closed
        error: Emitted when an error occurs
    """

    message_received = pyqtSignal(dict)
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, ws_url: str):
        """
        Initialize WebSocket client

        Args:
            ws_url: WebSocket URL (e.g., ws://localhost:8000/ws/market/BTC-USD)
        """
        super().__init__()
        self.ws_url = ws_url
        self.running = False
        self.websocket = None
        logger.debug(f"WebSocketClient created for: {ws_url}")

    def run(self):
        """Run WebSocket client in thread"""
        self.running = True
        logger.info(f"Starting WebSocket connection to: {self.ws_url}")
        asyncio.run(self._connect())

    async def _connect(self):
        """Connect to WebSocket and receive messages"""
        try:
            async with websockets.connect(self.ws_url) as websocket:
                self.websocket = websocket
                logger.info(f"WebSocket connected: {self.ws_url}")
                self.connected.emit()

                while self.running:
                    try:
                        message = await asyncio.wait_for(
                            websocket.recv(),
                            timeout=1.0
                        )
                        data = json.loads(message)
                        logger.debug(f"WS message received: {str(data)[:100]}")
                        self.message_received.emit(data)
                    except asyncio.TimeoutError:
                        continue
                    except websockets.exceptions.ConnectionClosed as e:
                        logger.warning(f"WebSocket connection closed: {e}")
                        break

        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            self.error.emit(str(e))
        finally:
            logger.info(f"WebSocket disconnected: {self.ws_url}")
            self.disconnected.emit()
            self.websocket = None

    def stop(self):
        """Stop WebSocket client"""
        logger.info(f"Stopping WebSocket client: {self.ws_url}")
        self.running = False
        self.wait()


class MarketDataStream(WebSocketClient):
    """WebSocket stream for market data"""

    def __init__(self, base_url: str, symbol: str):
        """
        Initialize market data stream

        Args:
            base_url: WebSocket base URL
            symbol: Ticker symbol
        """
        ws_url = f"{base_url}/ws/market/{symbol}"
        super().__init__(ws_url)
        self.symbol = symbol


class AlertsStream(WebSocketClient):
    """WebSocket stream for alerts"""

    def __init__(self, base_url: str):
        """
        Initialize alerts stream

        Args:
            base_url: WebSocket base URL
        """
        ws_url = f"{base_url}/ws/alerts"
        super().__init__(ws_url)


class AnalysisStream(WebSocketClient):
    """WebSocket stream for technical analysis updates"""

    def __init__(self, base_url: str, symbol: str):
        """
        Initialize analysis stream

        Args:
            base_url: WebSocket base URL
            symbol: Ticker symbol
        """
        ws_url = f"{base_url}/ws/analysis/{symbol}"
        super().__init__(ws_url)
        self.symbol = symbol
