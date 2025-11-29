"""
Market data endpoints - OHLCV, symbols, etc.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd

router = APIRouter()


@router.get("/symbols")
async def get_symbols():
    """
    Get list of available symbols
    """
    # Hardcoded for now - in production, this would come from database
    symbols = {
        "indices": [
            {"symbol": "^GDAXI", "name": "DAX", "exchange": "XETRA"},
            {"symbol": "^GSPC", "name": "S&P 500", "exchange": "NYSE"},
            {"symbol": "^DJI", "name": "Dow Jones", "exchange": "NYSE"},
        ],
        "forex": [
            {"symbol": "EURUSD=X", "name": "EUR/USD", "exchange": "FOREX"},
            {"symbol": "GBPUSD=X", "name": "GBP/USD", "exchange": "FOREX"},
        ],
        "crypto": [
            {"symbol": "BTC-USD", "name": "Bitcoin", "exchange": "CRYPTO"},
            {"symbol": "ETH-USD", "name": "Ethereum", "exchange": "CRYPTO"},
        ]
    }
    return symbols


@router.get("/ohlcv/{symbol}")
async def get_ohlcv(
    symbol: str,
    interval: str = Query(default="1h", description="Interval: 1m, 5m, 15m, 1h, 4h, 1d"),
    period: str = Query(default="7d", description="Period: 1d, 5d, 1mo, 3mo, 1y, max"),
    start: Optional[str] = Query(default=None, description="Start date YYYY-MM-DD"),
    end: Optional[str] = Query(default=None, description="End date YYYY-MM-DD")
):
    """
    Get OHLCV data for a symbol

    Args:
        symbol: Ticker symbol (e.g., ^GDAXI, BTC-USD)
        interval: Candle interval
        period: Time period (used if start/end not provided)
        start: Start date (optional)
        end: End date (optional)

    Returns:
        OHLCV data with timestamps
    """
    try:
        ticker = yf.Ticker(symbol)

        if start and end:
            df = ticker.history(interval=interval, start=start, end=end)
        else:
            df = ticker.history(period=period, interval=interval)

        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")

        # Convert to JSON-friendly format
        df.reset_index(inplace=True)

        # Handle different column names from yfinance
        if 'Datetime' in df.columns:
            df.rename(columns={'Datetime': 'Date'}, inplace=True)

        if 'Date' in df.columns:
            df['Date'] = df['Date'].astype(str)

        data = {
            "symbol": symbol,
            "interval": interval,
            "data": df.to_dict(orient="records")
        }

        return data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data: {str(e)}")


@router.get("/quote/{symbol}")
async def get_quote(symbol: str):
    """
    Get current quote for a symbol

    Args:
        symbol: Ticker symbol

    Returns:
        Current price, change, volume, etc.
    """
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        quote = {
            "symbol": symbol,
            "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
            "previous_close": info.get("previousClose"),
            "open": info.get("open") or info.get("regularMarketOpen"),
            "day_high": info.get("dayHigh") or info.get("regularMarketDayHigh"),
            "day_low": info.get("dayLow") or info.get("regularMarketDayLow"),
            "volume": info.get("volume") or info.get("regularMarketVolume"),
            "market_cap": info.get("marketCap"),
            "name": info.get("longName") or info.get("shortName"),
        }

        return quote

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching quote: {str(e)}")


@router.get("/info/{symbol}")
async def get_symbol_info(symbol: str):
    """
    Get detailed information about a symbol
    """
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        return {
            "symbol": symbol,
            "info": info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching info: {str(e)}")
