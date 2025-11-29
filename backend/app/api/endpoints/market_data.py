"""
Market data endpoints - OHLCV, symbols, etc.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
import time
import threading
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class AdaptiveRateLimitedCache:
    """
    In-memory cache with adaptive rate limiting for Yahoo Finance API.

    - Normal mode: requests every 30 seconds
    - Backoff mode (after 429): requests every 5 minutes, then gradually recovers
    """

    # Rate limit settings
    NORMAL_INTERVAL = 30.0        # 30 seconds between requests normally
    BACKOFF_INTERVAL = 300.0      # 5 minutes after hitting rate limit
    RECOVERY_STEP = 30.0          # Reduce interval by 30s after each successful request
    MIN_INTERVAL = 30.0           # Never go below 30 seconds

    def __init__(self, cache_ttl: int = 300):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = cache_ttl  # seconds
        self._current_interval = self.NORMAL_INTERVAL
        self._last_request_time = 0.0
        self._lock = threading.Lock()
        self._in_backoff = False

    def _trigger_backoff(self):
        """Called when we hit a 429 rate limit"""
        with self._lock:
            self._in_backoff = True
            self._current_interval = self.BACKOFF_INTERVAL
            logger.warning(f"🚨 Rate limit hit! Switching to backoff mode: {self._current_interval}s between requests")

    def _on_success(self):
        """Called after a successful request - gradually recover from backoff"""
        with self._lock:
            if self._in_backoff:
                old_interval = self._current_interval
                self._current_interval = max(
                    self.MIN_INTERVAL,
                    self._current_interval - self.RECOVERY_STEP
                )
                if self._current_interval <= self.MIN_INTERVAL:
                    self._in_backoff = False
                    logger.info(f"✅ Recovered from backoff, back to normal interval: {self._current_interval}s")
                else:
                    logger.info(f"📈 Recovering from backoff: {old_interval}s -> {self._current_interval}s")

    def _wait_for_rate_limit(self):
        """Ensure minimum interval between requests"""
        with self._lock:
            now = time.time()
            elapsed = now - self._last_request_time
            if elapsed < self._current_interval:
                sleep_time = self._current_interval - elapsed
                logger.debug(f"Rate limiting: waiting {sleep_time:.1f}s (interval: {self._current_interval}s)")
                time.sleep(sleep_time)
            self._last_request_time = time.time()

    def get_status(self) -> Dict[str, Any]:
        """Get current rate limiter status"""
        return {
            "in_backoff": self._in_backoff,
            "current_interval": self._current_interval,
            "cache_size": len(self._cache),
            "cache_ttl": self._cache_ttl
        }

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached value if not expired"""
        if key in self._cache:
            entry = self._cache[key]
            if time.time() - entry["timestamp"] < self._cache_ttl:
                logger.debug(f"Cache HIT for {key}")
                return entry["data"]
            else:
                del self._cache[key]
        return None

    def set(self, key: str, data: Any):
        """Store value in cache"""
        self._cache[key] = {
            "data": data,
            "timestamp": time.time()
        }

    def get_ticker_info(self, symbol: str, max_retries: int = 3) -> Dict:
        """Get ticker info with caching and adaptive rate limiting"""
        cache_key = f"info:{symbol}"
        cached = self.get(cache_key)
        if cached is not None:
            return cached

        last_error = None
        for attempt in range(max_retries):
            try:
                self._wait_for_rate_limit()
                ticker = yf.Ticker(symbol)
                info = ticker.info
                # Check if we got valid data (not just empty or error response)
                if info and info.get("regularMarketPrice") is not None:
                    self._on_success()  # Successful request - recover from backoff
                    self.set(cache_key, info)
                    return info
                elif info and info.get("currentPrice") is not None:
                    self._on_success()  # Successful request - recover from backoff
                    self.set(cache_key, info)
                    return info
                # If no price data, might be rate limited
                self._trigger_backoff()
                logger.warning(f"No valid data for {symbol} (attempt {attempt + 1}/{max_retries})")
            except Exception as e:
                last_error = e
                error_str = str(e)
                if "429" in error_str or "Too Many Requests" in error_str:
                    self._trigger_backoff()
                    logger.warning(f"Rate limited on {symbol} (attempt {attempt + 1}/{max_retries})")
                else:
                    logger.error(f"Error fetching info for {symbol}: {e}")
                    if attempt == max_retries - 1:
                        raise

        # Return empty dict if all retries failed
        logger.warning(f"All retries failed for {symbol}, last error: {last_error}")
        return {}

    def get_ticker_history(
        self,
        symbol: str,
        interval: str,
        period: str = None,
        start: str = None,
        end: str = None,
        max_retries: int = 3
    ) -> pd.DataFrame:
        """Get ticker history with caching and adaptive rate limiting"""
        cache_key = f"ohlcv:{symbol}:{interval}:{period}:{start}:{end}"
        cached = self.get(cache_key)
        if cached is not None:
            return cached

        for attempt in range(max_retries):
            try:
                self._wait_for_rate_limit()
                ticker = yf.Ticker(symbol)

                if start and end:
                    df = ticker.history(interval=interval, start=start, end=end)
                else:
                    df = ticker.history(period=period, interval=interval)

                if not df.empty:
                    self._on_success()  # Successful request - recover from backoff
                    self.set(cache_key, df)
                    return df
                else:
                    # Empty data might mean rate limiting
                    self._trigger_backoff()
                    logger.warning(f"No history data for {symbol} (attempt {attempt + 1}/{max_retries})")

            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "Too Many Requests" in error_str:
                    self._trigger_backoff()
                    logger.warning(f"Rate limited on {symbol} history (attempt {attempt + 1}/{max_retries})")
                else:
                    logger.error(f"Error fetching history for {symbol}: {e}")
                    raise

        return pd.DataFrame()


# Global cache instance with adaptive rate limiting
# - Normal: 30s between requests
# - After 429: 5 min between requests, then gradually recovers
_cache = AdaptiveRateLimitedCache(cache_ttl=300)


@router.get("/status")
async def get_rate_limit_status():
    """
    Get current rate limiter status (for debugging)
    """
    status = _cache.get_status()
    return {
        "rate_limiter": status,
        "mode": "backoff" if status["in_backoff"] else "normal",
        "next_request_interval": f"{status['current_interval']}s"
    }


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
        df = _cache.get_ticker_history(
            symbol=symbol,
            interval=interval,
            period=period,
            start=start,
            end=end
        )

        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")

        # Convert to JSON-friendly format
        df = df.copy()
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

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching OHLCV for {symbol}: {e}")
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
        info = _cache.get_ticker_info(symbol)

        if not info:
            raise HTTPException(
                status_code=503,
                detail=f"Market data temporarily unavailable for {symbol}. Yahoo Finance rate limit may be active. Try again in a few minutes.",
                headers={"Retry-After": "60"}
            )

        current_price = info.get("currentPrice") or info.get("regularMarketPrice")
        if current_price is None:
            raise HTTPException(
                status_code=503,
                detail=f"No price data available for {symbol}. Data provider may be rate limiting requests.",
                headers={"Retry-After": "60"}
            )

        quote = {
            "symbol": symbol,
            "current_price": current_price,
            "previous_close": info.get("previousClose"),
            "open": info.get("open") or info.get("regularMarketOpen"),
            "day_high": info.get("dayHigh") or info.get("regularMarketDayHigh"),
            "day_low": info.get("dayLow") or info.get("regularMarketDayLow"),
            "volume": info.get("volume") or info.get("regularMarketVolume"),
            "market_cap": info.get("marketCap"),
            "name": info.get("longName") or info.get("shortName"),
        }

        return quote

    except HTTPException:
        raise
    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "Too Many Requests" in error_str:
            logger.warning(f"Rate limited fetching quote for {symbol}")
            raise HTTPException(
                status_code=503,
                detail="Yahoo Finance rate limit exceeded. Please wait a few minutes before retrying.",
                headers={"Retry-After": "120"}
            )
        logger.error(f"Error fetching quote for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching quote: {str(e)}")


@router.get("/info/{symbol}")
async def get_symbol_info(symbol: str):
    """
    Get detailed information about a symbol
    """
    try:
        info = _cache.get_ticker_info(symbol)

        if not info:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")

        return {
            "symbol": symbol,
            "info": info
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching info for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching info: {str(e)}")
