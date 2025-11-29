"""
YFinance client for fetching stock and index data
"""
import yfinance as yf
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class YFinanceClient:
    """Client for fetching data from Yahoo Finance"""

    def __init__(self):
        """Initialize YFinance client"""
        self.cache = {}
        self.cache_timeout = 60  # seconds

    def get_ohlcv(
        self,
        symbol: str,
        interval: str = "1h",
        period: str = "7d",
        start: Optional[str] = None,
        end: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get OHLCV data for a symbol

        Args:
            symbol: Ticker symbol (e.g., ^GDAXI, AAPL, BTC-USD)
            interval: Candle interval (1m, 5m, 15m, 30m, 1h, 4h, 1d, 1wk, 1mo)
            period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            start: Start date (YYYY-MM-DD)
            end: End date (YYYY-MM-DD)

        Returns:
            DataFrame with OHLCV data
        """
        try:
            ticker = yf.Ticker(symbol)

            if start and end:
                df = ticker.history(interval=interval, start=start, end=end)
            else:
                df = ticker.history(period=period, interval=interval)

            if df.empty:
                logger.warning(f"No data found for {symbol}")
                return pd.DataFrame()

            # Standardize column names
            df.columns = [col.lower() for col in df.columns]

            return df

        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            return pd.DataFrame()

    def get_quote(self, symbol: str) -> Dict:
        """
        Get current quote for a symbol

        Args:
            symbol: Ticker symbol

        Returns:
            Dictionary with current price data
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
                "currency": info.get("currency"),
                "exchange": info.get("exchange"),
            }

            return quote

        except Exception as e:
            logger.error(f"Error fetching quote for {symbol}: {str(e)}")
            return {}

    def get_info(self, symbol: str) -> Dict:
        """
        Get detailed information about a symbol

        Args:
            symbol: Ticker symbol

        Returns:
            Dictionary with symbol information
        """
        try:
            ticker = yf.Ticker(symbol)
            return ticker.info

        except Exception as e:
            logger.error(f"Error fetching info for {symbol}: {str(e)}")
            return {}

    def get_multiple_quotes(self, symbols: List[str]) -> List[Dict]:
        """
        Get quotes for multiple symbols

        Args:
            symbols: List of ticker symbols

        Returns:
            List of quote dictionaries
        """
        quotes = []
        for symbol in symbols:
            quote = self.get_quote(symbol)
            if quote:
                quotes.append(quote)

        return quotes

    def search_symbols(self, query: str) -> List[Dict]:
        """
        Search for symbols by name or ticker

        Args:
            query: Search query

        Returns:
            List of matching symbols
        """
        try:
            # Use yfinance Ticker search (limited functionality)
            ticker = yf.Ticker(query)
            info = ticker.info

            if info:
                return [{
                    "symbol": query,
                    "name": info.get("longName") or info.get("shortName"),
                    "exchange": info.get("exchange"),
                    "type": info.get("quoteType"),
                }]

            return []

        except Exception as e:
            logger.error(f"Error searching for {query}: {str(e)}")
            return []

    def get_dividends(self, symbol: str) -> pd.DataFrame:
        """
        Get dividend history for a symbol

        Args:
            symbol: Ticker symbol

        Returns:
            DataFrame with dividend data
        """
        try:
            ticker = yf.Ticker(symbol)
            return ticker.dividends

        except Exception as e:
            logger.error(f"Error fetching dividends for {symbol}: {str(e)}")
            return pd.DataFrame()

    def get_splits(self, symbol: str) -> pd.DataFrame:
        """
        Get stock split history for a symbol

        Args:
            symbol: Ticker symbol

        Returns:
            DataFrame with split data
        """
        try:
            ticker = yf.Ticker(symbol)
            return ticker.splits

        except Exception as e:
            logger.error(f"Error fetching splits for {symbol}: {str(e)}")
            return pd.DataFrame()
