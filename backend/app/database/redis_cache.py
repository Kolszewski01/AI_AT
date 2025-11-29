"""
Redis caching layer for the trading system
"""
import redis
import json
import logging
from typing import Any, Optional, List
from datetime import timedelta
import os
import pickle

logger = logging.getLogger(__name__)


class RedisCache:
    """
    Redis cache manager for caching market data, quotes, and API responses
    """

    def __init__(
        self,
        host: str = None,
        port: int = None,
        db: int = 0,
        password: str = None,
        decode_responses: bool = True
    ):
        """
        Initialize Redis cache

        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Redis password
            decode_responses: Whether to decode responses to strings
        """
        self.host = host or os.getenv("REDIS_HOST", "localhost")
        self.port = port or int(os.getenv("REDIS_PORT", 6379))
        self.db = db
        self.password = password or os.getenv("REDIS_PASSWORD")

        try:
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=decode_responses,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.client.ping()
            logger.info(f"Redis connection established: {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Redis connection failed: {str(e)}")
            self.client = None

    def is_connected(self) -> bool:
        """
        Check if Redis is connected

        Returns:
            True if connected, False otherwise
        """
        if not self.client:
            return False

        try:
            self.client.ping()
            return True
        except Exception:
            return False

    def set(
        self,
        key: str,
        value: Any,
        expire: int = None
    ) -> bool:
        """
        Set a value in cache

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            expire: Expiration time in seconds

        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            return False

        try:
            # Serialize value to JSON
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value)
            else:
                serialized_value = str(value)

            if expire:
                return self.client.setex(key, expire, serialized_value)
            else:
                return self.client.set(key, serialized_value)

        except Exception as e:
            logger.error(f"Error setting cache key {key}: {str(e)}")
            return False

    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        if not self.client:
            return None

        try:
            value = self.client.get(key)

            if value is None:
                return None

            # Try to deserialize JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value

        except Exception as e:
            logger.error(f"Error getting cache key {key}: {str(e)}")
            return None

    def delete(self, key: str) -> bool:
        """
        Delete a key from cache

        Args:
            key: Cache key

        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            return False

        try:
            return self.client.delete(key) > 0
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {str(e)}")
            return False

    def exists(self, key: str) -> bool:
        """
        Check if a key exists in cache

        Args:
            key: Cache key

        Returns:
            True if exists, False otherwise
        """
        if not self.client:
            return False

        try:
            return self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"Error checking cache key {key}: {str(e)}")
            return False

    def get_ttl(self, key: str) -> int:
        """
        Get time-to-live for a key

        Args:
            key: Cache key

        Returns:
            TTL in seconds, -1 if no expiration, -2 if key doesn't exist
        """
        if not self.client:
            return -2

        try:
            return self.client.ttl(key)
        except Exception as e:
            logger.error(f"Error getting TTL for key {key}: {str(e)}")
            return -2

    def set_multiple(self, mapping: dict, expire: int = None) -> bool:
        """
        Set multiple key-value pairs

        Args:
            mapping: Dictionary of key-value pairs
            expire: Expiration time in seconds

        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            return False

        try:
            # Serialize all values
            serialized_mapping = {}
            for key, value in mapping.items():
                if isinstance(value, (dict, list)):
                    serialized_mapping[key] = json.dumps(value)
                else:
                    serialized_mapping[key] = str(value)

            # Set all values
            self.client.mset(serialized_mapping)

            # Set expiration if specified
            if expire:
                for key in mapping.keys():
                    self.client.expire(key, expire)

            return True

        except Exception as e:
            logger.error(f"Error setting multiple cache keys: {str(e)}")
            return False

    def get_multiple(self, keys: List[str]) -> dict:
        """
        Get multiple values from cache

        Args:
            keys: List of cache keys

        Returns:
            Dictionary of key-value pairs
        """
        if not self.client:
            return {}

        try:
            values = self.client.mget(keys)
            result = {}

            for key, value in zip(keys, values):
                if value is not None:
                    try:
                        result[key] = json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        result[key] = value

            return result

        except Exception as e:
            logger.error(f"Error getting multiple cache keys: {str(e)}")
            return {}

    def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching a pattern

        Args:
            pattern: Pattern to match (e.g., "quotes:*")

        Returns:
            Number of keys deleted
        """
        if not self.client:
            return 0

        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0

        except Exception as e:
            logger.error(f"Error clearing pattern {pattern}: {str(e)}")
            return 0

    def flush_db(self) -> bool:
        """
        Flush entire database (use with caution!)

        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            return False

        try:
            self.client.flushdb()
            logger.warning("Redis database flushed")
            return True
        except Exception as e:
            logger.error(f"Error flushing database: {str(e)}")
            return False

    # Trading-specific cache methods

    def cache_quote(self, symbol: str, quote_data: dict, expire: int = 60):
        """Cache quote data for a symbol"""
        key = f"quote:{symbol}"
        return self.set(key, quote_data, expire=expire)

    def get_cached_quote(self, symbol: str) -> Optional[dict]:
        """Get cached quote for a symbol"""
        key = f"quote:{symbol}"
        return self.get(key)

    def cache_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        ohlcv_data: dict,
        expire: int = 300
    ):
        """Cache OHLCV data for a symbol"""
        key = f"ohlcv:{symbol}:{timeframe}"
        return self.set(key, ohlcv_data, expire=expire)

    def get_cached_ohlcv(self, symbol: str, timeframe: str) -> Optional[dict]:
        """Get cached OHLCV for a symbol"""
        key = f"ohlcv:{symbol}:{timeframe}"
        return self.get(key)

    def cache_indicators(
        self,
        symbol: str,
        timeframe: str,
        indicators_data: dict,
        expire: int = 300
    ):
        """Cache technical indicators for a symbol"""
        key = f"indicators:{symbol}:{timeframe}"
        return self.set(key, indicators_data, expire=expire)

    def get_cached_indicators(
        self,
        symbol: str,
        timeframe: str
    ) -> Optional[dict]:
        """Get cached indicators for a symbol"""
        key = f"indicators:{symbol}:{timeframe}"
        return self.get(key)

    def cache_signals(self, symbol: str, signals_data: list, expire: int = 300):
        """Cache trading signals for a symbol"""
        key = f"signals:{symbol}"
        return self.set(key, signals_data, expire=expire)

    def get_cached_signals(self, symbol: str) -> Optional[list]:
        """Get cached signals for a symbol"""
        key = f"signals:{symbol}"
        return self.get(key)

    def cache_news(self, symbol: str, news_data: list, expire: int = 1800):
        """Cache news for a symbol (30 min expiry)"""
        key = f"news:{symbol}"
        return self.set(key, news_data, expire=expire)

    def get_cached_news(self, symbol: str) -> Optional[list]:
        """Get cached news for a symbol"""
        key = f"news:{symbol}"
        return self.get(key)

    def cache_sentiment(
        self,
        symbol: str,
        sentiment_data: dict,
        expire: int = 1800
    ):
        """Cache sentiment data for a symbol"""
        key = f"sentiment:{symbol}"
        return self.set(key, sentiment_data, expire=expire)

    def get_cached_sentiment(self, symbol: str) -> Optional[dict]:
        """Get cached sentiment for a symbol"""
        key = f"sentiment:{symbol}"
        return self.get(key)

    def increment_counter(self, key: str, amount: int = 1) -> int:
        """
        Increment a counter

        Args:
            key: Counter key
            amount: Amount to increment

        Returns:
            New counter value
        """
        if not self.client:
            return 0

        try:
            return self.client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Error incrementing counter {key}: {str(e)}")
            return 0

    def get_counter(self, key: str) -> int:
        """Get counter value"""
        value = self.get(key)
        try:
            return int(value) if value else 0
        except (ValueError, TypeError):
            return 0
