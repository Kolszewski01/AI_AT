"""
WebSocket endpoints for real-time data streaming
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict
import asyncio
import json
import yfinance as yf
from datetime import datetime

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections"""

    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, channel: str):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        if channel not in self.active_connections:
            self.active_connections[channel] = []
        self.active_connections[channel].append(websocket)

    def disconnect(self, websocket: WebSocket, channel: str):
        """Remove a WebSocket connection"""
        if channel in self.active_connections:
            if websocket in self.active_connections[channel]:
                self.active_connections[channel].remove(websocket)
            if not self.active_connections[channel]:
                del self.active_connections[channel]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific client"""
        await websocket.send_text(message)

    async def broadcast(self, message: str, channel: str):
        """Broadcast a message to all clients in a channel"""
        if channel in self.active_connections:
            disconnected = []
            for connection in self.active_connections[channel]:
                try:
                    await connection.send_text(message)
                except:
                    disconnected.append(connection)

            # Remove disconnected clients
            for conn in disconnected:
                self.disconnect(conn, channel)


# Global connection manager
manager = ConnectionManager()


async def get_market_data(symbol: str) -> dict:
    """Fetch current market data for a symbol"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        data = {
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat(),
            "price": info.get("currentPrice") or info.get("regularMarketPrice"),
            "change": info.get("regularMarketChange"),
            "change_percent": info.get("regularMarketChangePercent"),
            "volume": info.get("volume") or info.get("regularMarketVolume"),
            "bid": info.get("bid"),
            "ask": info.get("ask"),
            "open": info.get("open") or info.get("regularMarketOpen"),
            "high": info.get("dayHigh") or info.get("regularMarketDayHigh"),
            "low": info.get("dayLow") or info.get("regularMarketDayLow"),
        }
        return data
    except Exception as e:
        return {
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }


@router.websocket("/ws/market/{symbol}")
async def websocket_market_data(websocket: WebSocket, symbol: str):
    """
    WebSocket endpoint for real-time market data

    Args:
        symbol: Ticker symbol (e.g., ^GDAXI, BTC-USD)

    Sends market data updates every 5 seconds
    """
    channel = f"market:{symbol}"
    await manager.connect(websocket, channel)

    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Main loop - send data every 5 seconds
        while True:
            data = await get_market_data(symbol)
            data["type"] = "market_data"

            await websocket.send_json(data)
            await asyncio.sleep(5)  # Update every 5 seconds

    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)
        print(f"Client disconnected from {channel}")
    except Exception as e:
        print(f"Error in WebSocket {channel}: {e}")
        manager.disconnect(websocket, channel)


@router.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """
    WebSocket endpoint for real-time alerts

    Broadcasts trading alerts as they are generated
    """
    channel = "alerts"
    await manager.connect(websocket, channel)

    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "channel": "alerts",
            "timestamp": datetime.utcnow().isoformat()
        })

        # Keep connection alive and wait for broadcasts
        while True:
            # Wait for client messages (ping/pong for keepalive)
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                # Echo back to confirm connection is alive
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                })
            except asyncio.TimeoutError:
                # Send keepalive ping
                await websocket.send_json({
                    "type": "ping",
                    "timestamp": datetime.utcnow().isoformat()
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)
        print(f"Client disconnected from alerts channel")
    except Exception as e:
        print(f"Error in alerts WebSocket: {e}")
        manager.disconnect(websocket, channel)


@router.websocket("/ws/analysis/{symbol}")
async def websocket_analysis(websocket: WebSocket, symbol: str):
    """
    WebSocket endpoint for real-time technical analysis updates

    Args:
        symbol: Ticker symbol

    Sends updated technical indicators every 30 seconds
    """
    channel = f"analysis:{symbol}"
    await manager.connect(websocket, channel)

    try:
        from app.api.endpoints.analysis import calculate_rsi, calculate_macd
        import pandas as pd

        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat()
        })

        while True:
            try:
                # Fetch recent data
                ticker = yf.Ticker(symbol)
                df = ticker.history(period="5d", interval="5m")

                if not df.empty:
                    # Calculate indicators
                    df['RSI'] = calculate_rsi(df['Close'])
                    macd, signal, histogram = calculate_macd(df['Close'])

                    latest = df.iloc[-1]

                    analysis_data = {
                        "type": "analysis",
                        "symbol": symbol,
                        "timestamp": datetime.utcnow().isoformat(),
                        "price": float(latest['Close']),
                        "volume": int(latest['Volume']),
                        "indicators": {
                            "rsi": float(latest['RSI']) if not pd.isna(latest['RSI']) else None,
                            "macd": {
                                "value": float(macd.iloc[-1]) if not pd.isna(macd.iloc[-1]) else None,
                                "signal": float(signal.iloc[-1]) if not pd.isna(signal.iloc[-1]) else None,
                                "histogram": float(histogram.iloc[-1]) if not pd.isna(histogram.iloc[-1]) else None
                            }
                        }
                    }

                    await websocket.send_json(analysis_data)

            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "message": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                })

            await asyncio.sleep(30)  # Update every 30 seconds

    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)
        print(f"Client disconnected from {channel}")
    except Exception as e:
        print(f"Error in analysis WebSocket: {e}")
        manager.disconnect(websocket, channel)


# Helper function to broadcast alerts (called from alert engine)
async def broadcast_alert(alert: dict):
    """
    Broadcast an alert to all connected clients on the alerts channel

    Args:
        alert: Alert dictionary with details
    """
    message = {
        "type": "alert",
        "timestamp": datetime.utcnow().isoformat(),
        **alert
    }
    await manager.broadcast(json.dumps(message), "alerts")
