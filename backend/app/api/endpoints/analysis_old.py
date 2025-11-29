"""
Technical analysis endpoints - indicators, patterns, signals
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import yfinance as yf
import pandas as pd
import numpy as np

router = APIRouter()


def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
    """Calculate RSI indicator"""
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """Calculate MACD indicator"""
    ema_fast = data.ewm(span=fast, adjust=False).mean()
    ema_slow = data.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def detect_hammer(row) -> bool:
    """Detect hammer candlestick pattern"""
    body = abs(row['Close'] - row['Open'])
    lower_shadow = min(row['Open'], row['Close']) - row['Low']
    upper_shadow = row['High'] - max(row['Open'], row['Close'])

    # Hammer: small body, long lower shadow, small/no upper shadow
    if body > 0 and lower_shadow > 2 * body and upper_shadow < body:
        return True
    return False


def detect_shooting_star(row) -> bool:
    """Detect shooting star candlestick pattern"""
    body = abs(row['Close'] - row['Open'])
    upper_shadow = row['High'] - max(row['Open'], row['Close'])
    lower_shadow = min(row['Open'], row['Close']) - row['Low']

    # Shooting star: small body, long upper shadow, small/no lower shadow
    if body > 0 and upper_shadow > 2 * body and lower_shadow < body:
        return True
    return False


@router.get("/indicators/{symbol}")
async def get_indicators(
    symbol: str,
    interval: str = Query(default="1h", description="Interval: 1m, 5m, 15m, 1h, 4h, 1d"),
    period: str = Query(default="7d", description="Period: 1d, 5d, 1mo, 3mo, 1y")
):
    """
    Calculate technical indicators for a symbol

    Returns: RSI, MACD, Moving Averages, etc.
    """
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)

        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")

        # Calculate indicators
        df['RSI'] = calculate_rsi(df['Close'], period=14)
        macd, signal, histogram = calculate_macd(df['Close'])
        df['MACD'] = macd
        df['MACD_Signal'] = signal
        df['MACD_Histogram'] = histogram

        # Moving averages
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        df['EMA_12'] = df['Close'].ewm(span=12, adjust=False).mean()
        df['EMA_26'] = df['Close'].ewm(span=26, adjust=False).mean()

        # Get latest values
        latest = df.iloc[-1]

        indicators = {
            "symbol": symbol,
            "timestamp": str(df.index[-1]),
            "price": float(latest['Close']),
            "rsi": float(latest['RSI']) if not pd.isna(latest['RSI']) else None,
            "macd": {
                "macd": float(latest['MACD']) if not pd.isna(latest['MACD']) else None,
                "signal": float(latest['MACD_Signal']) if not pd.isna(latest['MACD_Signal']) else None,
                "histogram": float(latest['MACD_Histogram']) if not pd.isna(latest['MACD_Histogram']) else None
            },
            "moving_averages": {
                "sma_20": float(latest['SMA_20']) if not pd.isna(latest['SMA_20']) else None,
                "sma_50": float(latest['SMA_50']) if not pd.isna(latest['SMA_50']) else None,
                "ema_12": float(latest['EMA_12']) if not pd.isna(latest['EMA_12']) else None,
                "ema_26": float(latest['EMA_26']) if not pd.isna(latest['EMA_26']) else None
            },
            "volume": int(latest['Volume'])
        }

        return indicators

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating indicators: {str(e)}")


@router.get("/patterns/{symbol}")
async def detect_patterns(
    symbol: str,
    interval: str = Query(default="1h", description="Interval"),
    period: str = Query(default="7d", description="Period")
):
    """
    Detect candlestick patterns

    Returns: List of detected patterns with timestamps
    """
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)

        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")

        patterns = []

        # Check last few candles for patterns
        for i in range(max(0, len(df) - 10), len(df)):
            row = df.iloc[i]
            timestamp = str(df.index[i])

            if detect_hammer(row):
                patterns.append({
                    "timestamp": timestamp,
                    "pattern": "Hammer",
                    "signal": "bullish",
                    "confidence": "medium"
                })

            if detect_shooting_star(row):
                patterns.append({
                    "timestamp": timestamp,
                    "pattern": "Shooting Star",
                    "signal": "bearish",
                    "confidence": "medium"
                })

        return {
            "symbol": symbol,
            "patterns": patterns,
            "total_found": len(patterns)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detecting patterns: {str(e)}")


@router.get("/signal/{symbol}")
async def get_trading_signal(
    symbol: str,
    interval: str = Query(default="1h", description="Interval"),
    period: str = Query(default="7d", description="Period")
):
    """
    Generate a trading signal based on technical analysis

    Combines multiple indicators to produce buy/sell/neutral signal
    """
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)

        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")

        # Calculate indicators
        df['RSI'] = calculate_rsi(df['Close'])
        macd, signal_line, _ = calculate_macd(df['Close'])
        df['MACD'] = macd
        df['MACD_Signal'] = signal_line

        latest = df.iloc[-1]

        # Signal logic
        signals = []

        # RSI signals
        if latest['RSI'] < 30:
            signals.append(("RSI oversold", "bullish", 2))
        elif latest['RSI'] > 70:
            signals.append(("RSI overbought", "bearish", 2))
        else:
            signals.append(("RSI neutral", "neutral", 0))

        # MACD signals
        if latest['MACD'] > latest['MACD_Signal']:
            signals.append(("MACD bullish cross", "bullish", 1))
        else:
            signals.append(("MACD bearish", "bearish", 1))

        # Pattern detection
        if detect_hammer(latest):
            signals.append(("Hammer pattern", "bullish", 2))
        if detect_shooting_star(latest):
            signals.append(("Shooting star pattern", "bearish", 2))

        # Calculate overall signal
        bullish_score = sum(score for _, signal_type, score in signals if signal_type == "bullish")
        bearish_score = sum(score for _, signal_type, score in signals if signal_type == "bearish")

        if bullish_score > bearish_score + 1:
            overall = "BUY"
            strength = min(100, int((bullish_score / (bullish_score + bearish_score)) * 100))
        elif bearish_score > bullish_score + 1:
            overall = "SELL"
            strength = min(100, int((bearish_score / (bullish_score + bearish_score)) * 100))
        else:
            overall = "NEUTRAL"
            strength = 50

        return {
            "symbol": symbol,
            "timestamp": str(df.index[-1]),
            "signal": overall,
            "strength": strength,
            "price": float(latest['Close']),
            "indicators": {
                "rsi": float(latest['RSI']),
                "macd": float(latest['MACD']),
                "macd_signal": float(latest['MACD_Signal'])
            },
            "reasoning": [
                {"indicator": reason, "signal": sig, "weight": score}
                for reason, sig, score in signals
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating signal: {str(e)}")


@router.get("/support-resistance/{symbol}")
async def get_support_resistance(
    symbol: str,
    interval: str = Query(default="1h", description="Interval"),
    period: str = Query(default="3mo", description="Period"),
    method: str = Query(default="all", description="Method: all, fractals, pivots, volume")
):
    """
    Detect support and resistance zones

    Returns: Support and resistance levels with strength
    """
    try:
        from app.services.technical_analysis.support_resistance import SupportResistanceDetector

        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)

        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")

        # Normalize column names
        df.columns = [col.lower() for col in df.columns]

        detector = SupportResistanceDetector(sensitivity=0.02)
        current_price = float(df['close'].iloc[-1])

        zones = detector.detect_zones(df, current_price, lookback=200)

        return {
            "symbol": symbol,
            "current_price": current_price,
            "support": zones['support'],
            "resistance": zones['resistance'],
            "pivots": zones['pivots'],
            "volume_profile": {
                "poc": zones['volume_profile'].get('poc'),
                "value_area_count": len(zones['volume_profile'].get('value_area', []))
            },
            "timestamp": str(df.index[-1])
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detecting S/R: {str(e)}")


@router.get("/order-blocks/{symbol}")
async def get_order_blocks(
    symbol: str,
    interval: str = Query(default="1h", description="Interval"),
    period: str = Query(default="1mo", description="Period")
):
    """
    Detect institutional order blocks

    Returns: Bullish and bearish order blocks
    """
    try:
        from app.services.technical_analysis.support_resistance import SupportResistanceDetector

        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)

        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")

        # Normalize column names
        df.columns = [col.lower() for col in df.columns]

        detector = SupportResistanceDetector()
        order_blocks = detector.detect_order_blocks(df, lookback=100)

        bullish_blocks = [b for b in order_blocks if b['type'] == 'bullish']
        bearish_blocks = [b for b in order_blocks if b['type'] == 'bearish']

        return {
            "symbol": symbol,
            "order_blocks": order_blocks,
            "bullish_count": len(bullish_blocks),
            "bearish_count": len(bearish_blocks),
            "timestamp": str(df.index[-1])
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detecting order blocks: {str(e)}")
