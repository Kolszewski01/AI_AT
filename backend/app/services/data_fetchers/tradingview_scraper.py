"""
TradingView scraper for fetching market data and indicators
"""
import requests
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
import logging
import json
import time

logger = logging.getLogger(__name__)


class TradingViewScraper:
    """
    Scraper for TradingView data

    Note: This uses TradingView's unofficial API endpoints.
    For production, consider using official data providers or
    TradingView's official API when available.
    """

    def __init__(self):
        """Initialize TradingView scraper"""
        self.base_url = "https://scanner.tradingview.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Origin': 'https://www.tradingview.com',
        })

    def get_scanner_data(
        self,
        market: str = "america",
        symbols_type: str = "stock",
        columns: Optional[List[str]] = None,
        filter_query: Optional[Dict] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get data from TradingView scanner

        Args:
            market: Market region (america, germany, crypto, forex, etc.)
            symbols_type: Type of symbols (stock, crypto, forex, cfd, index)
            columns: List of columns to fetch (default: name, close, volume, change)
            filter_query: Filter conditions (optional)
            limit: Maximum number of results

        Returns:
            List of dictionaries with scanner data
        """
        if columns is None:
            columns = [
                "name",
                "close",
                "change",
                "change_abs",
                "volume",
                "Recommend.All",
                "RSI",
                "Stoch.K",
                "MACD.macd",
                "ADX",
                "market_cap_basic",
            ]

        url = f"{self.base_url}/{market}/scan"

        payload = {
            "symbols": {
                "query": {"types": [symbols_type]},
                "tickers": []
            },
            "columns": columns,
            "sort": {
                "sortBy": "volume",
                "sortOrder": "desc"
            },
            "range": [0, limit]
        }

        if filter_query:
            payload["filter"] = filter_query

        try:
            response = self.session.post(url, json=payload, timeout=10)
            response.raise_for_status()

            data = response.json()
            results = []

            for item in data.get("data", []):
                row_data = {}
                row_data["symbol"] = item.get("s", "")

                # Map column values
                for i, col in enumerate(columns):
                    if i < len(item.get("d", [])):
                        row_data[col] = item["d"][i]

                results.append(row_data)

            return results

        except Exception as e:
            logger.error(f"Error fetching scanner data: {str(e)}")
            return []

    def get_symbol_data(
        self,
        symbol: str,
        exchange: str = "NASDAQ",
        interval: str = "1D"
    ) -> Dict:
        """
        Get data for a specific symbol

        Args:
            symbol: Symbol ticker (e.g., AAPL, BTCUSD)
            exchange: Exchange name
            interval: Time interval (1, 5, 15, 30, 60, 240, 1D, 1W, 1M)

        Returns:
            Dictionary with symbol data
        """
        columns = [
            "close",
            "volume",
            "change",
            "change_abs",
            "Recommend.All",
            "Recommend.MA",
            "Recommend.Other",
            "RSI",
            "RSI[1]",
            "Stoch.K",
            "Stoch.D",
            "MACD.macd",
            "MACD.signal",
            "ADX",
            "ADX+DI",
            "ADX-DI",
            "AO",
            "Mom",
            "CCI20",
            "BBPower",
            "UO",
            "EMA10",
            "SMA10",
            "EMA20",
            "SMA20",
            "EMA50",
            "SMA50",
            "EMA100",
            "SMA100",
            "EMA200",
            "SMA200",
        ]

        url = f"{self.base_url}/america/scan"

        payload = {
            "symbols": {
                "tickers": [f"{exchange}:{symbol}"]
            },
            "columns": columns
        }

        try:
            response = self.session.post(url, json=payload, timeout=10)
            response.raise_for_status()

            data = response.json()

            if data.get("data") and len(data["data"]) > 0:
                item = data["data"][0]
                result = {"symbol": symbol, "exchange": exchange}

                for i, col in enumerate(columns):
                    if i < len(item.get("d", [])):
                        result[col] = item["d"][i]

                return result

            return {}

        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            return {}

    def get_top_movers(
        self,
        market: str = "america",
        direction: str = "gainers",
        limit: int = 20
    ) -> List[Dict]:
        """
        Get top gaining or losing stocks

        Args:
            market: Market region
            direction: "gainers" or "losers"
            limit: Number of results

        Returns:
            List of top movers
        """
        filter_query = None

        if direction == "gainers":
            # Filter for positive change
            filter_query = {
                "left": "change",
                "operation": "greater",
                "right": 0
            }
        elif direction == "losers":
            # Filter for negative change
            filter_query = {
                "left": "change",
                "operation": "less",
                "right": 0
            }

        results = self.get_scanner_data(
            market=market,
            symbols_type="stock",
            filter_query=filter_query,
            limit=limit
        )

        # Sort by change
        results.sort(
            key=lambda x: abs(x.get("change", 0)),
            reverse=True
        )

        return results[:limit]

    def get_technical_ratings(
        self,
        symbol: str,
        exchange: str = "NASDAQ"
    ) -> Dict:
        """
        Get technical analysis ratings for a symbol

        Args:
            symbol: Symbol ticker
            exchange: Exchange name

        Returns:
            Dictionary with ratings (BUY, SELL, NEUTRAL)
        """
        data = self.get_symbol_data(symbol, exchange)

        if not data:
            return {}

        return {
            "symbol": symbol,
            "overall": data.get("Recommend.All"),
            "moving_averages": data.get("Recommend.MA"),
            "oscillators": data.get("Recommend.Other"),
            "rsi": data.get("RSI"),
            "macd": data.get("MACD.macd"),
            "adx": data.get("ADX"),
            "interpretation": self._interpret_rating(data.get("Recommend.All", 0))
        }

    def _interpret_rating(self, rating: float) -> str:
        """
        Interpret numerical rating as text

        Args:
            rating: Numerical rating (-1 to 1)

        Returns:
            Text interpretation
        """
        if rating >= 0.5:
            return "STRONG_BUY"
        elif rating >= 0.1:
            return "BUY"
        elif rating <= -0.5:
            return "STRONG_SELL"
        elif rating <= -0.1:
            return "SELL"
        else:
            return "NEUTRAL"

    def get_crypto_screener(
        self,
        sort_by: str = "volume",
        limit: int = 50
    ) -> List[Dict]:
        """
        Get cryptocurrency screener data

        Args:
            sort_by: Sort field (volume, change, close)
            limit: Number of results

        Returns:
            List of crypto data
        """
        return self.get_scanner_data(
            market="crypto",
            symbols_type="crypto",
            limit=limit
        )

    def get_forex_screener(
        self,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get forex screener data

        Args:
            limit: Number of results

        Returns:
            List of forex pairs
        """
        return self.get_scanner_data(
            market="forex",
            symbols_type="forex",
            limit=limit
        )

    def search_symbols(
        self,
        query: str,
        market: str = "america",
        symbols_type: str = "stock"
    ) -> List[Dict]:
        """
        Search for symbols

        Args:
            query: Search query
            market: Market region
            symbols_type: Type of symbols

        Returns:
            List of matching symbols
        """
        url = "https://symbol-search.tradingview.com/symbol_search/"

        params = {
            "text": query,
            "type": symbols_type,
            "exchange": market,
        }

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            return [
                {
                    "symbol": item.get("symbol"),
                    "description": item.get("description"),
                    "exchange": item.get("exchange"),
                    "type": item.get("type"),
                }
                for item in data
            ]

        except Exception as e:
            logger.error(f"Error searching symbols: {str(e)}")
            return []

    def get_market_heatmap(
        self,
        market: str = "america",
        limit: int = 100
    ) -> List[Dict]:
        """
        Get market heatmap data (top stocks by volume and change)

        Args:
            market: Market region
            limit: Number of stocks

        Returns:
            List of stocks with performance data
        """
        columns = [
            "name",
            "close",
            "change",
            "volume",
            "market_cap_basic",
            "sector",
        ]

        return self.get_scanner_data(
            market=market,
            symbols_type="stock",
            columns=columns,
            limit=limit
        )
