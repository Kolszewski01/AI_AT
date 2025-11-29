"""
CCXT client for fetching cryptocurrency data
"""
import ccxt
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class CCXTClient:
    """Client for fetching cryptocurrency data from exchanges"""

    def __init__(self, exchange_name: str = "binance"):
        """
        Initialize CCXT client

        Args:
            exchange_name: Name of the exchange (binance, coinbase, kraken, etc.)
        """
        self.exchange_name = exchange_name
        self.exchange = self._get_exchange(exchange_name)

    def _get_exchange(self, exchange_name: str):
        """Get exchange instance"""
        try:
            exchange_class = getattr(ccxt, exchange_name)
            return exchange_class({
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot',
                }
            })
        except Exception as e:
            logger.error(f"Error initializing exchange {exchange_name}: {str(e)}")
            return None

    def get_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1h",
        limit: int = 500,
        since: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Get OHLCV data for a cryptocurrency pair

        Args:
            symbol: Trading pair (e.g., BTC/USDT, ETH/BTC)
            timeframe: Timeframe (1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w)
            limit: Number of candles to fetch
            since: Timestamp in milliseconds

        Returns:
            DataFrame with OHLCV data
        """
        try:
            if not self.exchange:
                logger.error("Exchange not initialized")
                return pd.DataFrame()

            # Fetch OHLCV data
            ohlcv = self.exchange.fetch_ohlcv(
                symbol=symbol,
                timeframe=timeframe,
                limit=limit,
                since=since
            )

            if not ohlcv:
                logger.warning(f"No data found for {symbol}")
                return pd.DataFrame()

            # Convert to DataFrame
            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )

            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)

            return df

        except Exception as e:
            logger.error(f"Error fetching OHLCV for {symbol}: {str(e)}")
            return pd.DataFrame()

    def get_ticker(self, symbol: str) -> Dict:
        """
        Get current ticker data for a symbol

        Args:
            symbol: Trading pair (e.g., BTC/USDT)

        Returns:
            Dictionary with ticker data
        """
        try:
            if not self.exchange:
                logger.error("Exchange not initialized")
                return {}

            ticker = self.exchange.fetch_ticker(symbol)

            return {
                "symbol": symbol,
                "exchange": self.exchange_name,
                "last": ticker.get("last"),
                "bid": ticker.get("bid"),
                "ask": ticker.get("ask"),
                "open": ticker.get("open"),
                "high": ticker.get("high"),
                "low": ticker.get("low"),
                "close": ticker.get("close"),
                "volume": ticker.get("baseVolume"),
                "quote_volume": ticker.get("quoteVolume"),
                "change": ticker.get("change"),
                "percentage": ticker.get("percentage"),
                "timestamp": ticker.get("timestamp"),
            }

        except Exception as e:
            logger.error(f"Error fetching ticker for {symbol}: {str(e)}")
            return {}

    def get_order_book(self, symbol: str, limit: int = 20) -> Dict:
        """
        Get order book for a symbol

        Args:
            symbol: Trading pair
            limit: Number of order book entries

        Returns:
            Dictionary with bids and asks
        """
        try:
            if not self.exchange:
                logger.error("Exchange not initialized")
                return {}

            order_book = self.exchange.fetch_order_book(symbol, limit=limit)

            return {
                "symbol": symbol,
                "bids": order_book.get("bids", []),
                "asks": order_book.get("asks", []),
                "timestamp": order_book.get("timestamp"),
            }

        except Exception as e:
            logger.error(f"Error fetching order book for {symbol}: {str(e)}")
            return {}

    def get_markets(self) -> List[Dict]:
        """
        Get list of all available markets on the exchange

        Returns:
            List of market dictionaries
        """
        try:
            if not self.exchange:
                logger.error("Exchange not initialized")
                return []

            markets = self.exchange.load_markets()

            return [
                {
                    "symbol": market_id,
                    "base": market.get("base"),
                    "quote": market.get("quote"),
                    "active": market.get("active"),
                    "type": market.get("type"),
                }
                for market_id, market in markets.items()
            ]

        except Exception as e:
            logger.error(f"Error fetching markets: {str(e)}")
            return []

    def get_trades(self, symbol: str, limit: int = 100) -> List[Dict]:
        """
        Get recent trades for a symbol

        Args:
            symbol: Trading pair
            limit: Number of trades

        Returns:
            List of trade dictionaries
        """
        try:
            if not self.exchange:
                logger.error("Exchange not initialized")
                return []

            trades = self.exchange.fetch_trades(symbol, limit=limit)

            return [
                {
                    "id": trade.get("id"),
                    "timestamp": trade.get("timestamp"),
                    "price": trade.get("price"),
                    "amount": trade.get("amount"),
                    "side": trade.get("side"),
                }
                for trade in trades
            ]

        except Exception as e:
            logger.error(f"Error fetching trades for {symbol}: {str(e)}")
            return []

    def get_24h_volume(self, symbol: str) -> float:
        """
        Get 24-hour trading volume for a symbol

        Args:
            symbol: Trading pair

        Returns:
            24-hour volume
        """
        try:
            ticker = self.get_ticker(symbol)
            return ticker.get("volume", 0.0)

        except Exception as e:
            logger.error(f"Error fetching 24h volume for {symbol}: {str(e)}")
            return 0.0

    def search_symbols(self, query: str) -> List[Dict]:
        """
        Search for symbols containing query

        Args:
            query: Search query

        Returns:
            List of matching symbols
        """
        try:
            markets = self.get_markets()
            query_upper = query.upper()

            return [
                market for market in markets
                if query_upper in market["symbol"].upper()
            ]

        except Exception as e:
            logger.error(f"Error searching symbols: {str(e)}")
            return []
