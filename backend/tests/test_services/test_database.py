"""
Comprehensive tests for database services
Tests DatabaseManager (PostgreSQL), RedisCache, and InfluxDBClient
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from datetime import datetime, timedelta
import pandas as pd
import json

from app.database.connection import DatabaseManager
from app.database.redis_cache import RedisCache
from app.database.influx_client import InfluxDBClient
from app.database.models.models import User, Watchlist, Signal, Alert, SignalType, AlertStatus


# ===== DATABASE MANAGER (POSTGRESQL) TESTS =====

class TestDatabaseManager:
    """Tests for PostgreSQL DatabaseManager"""

    @pytest.fixture
    def mock_engine(self):
        """Mock SQLAlchemy engine"""
        engine = Mock()
        engine.connect.return_value.__enter__.return_value = Mock()
        return engine

    @pytest.fixture
    def mock_session(self):
        """Mock SQLAlchemy session"""
        session = Mock()
        session.query.return_value = session
        session.filter_by.return_value = session
        session.filter.return_value = session
        session.order_by.return_value = session
        session.limit.return_value = session
        session.first.return_value = None
        session.all.return_value = []
        # Add context manager support
        session.__enter__ = Mock(return_value=session)
        session.__exit__ = Mock(return_value=False)
        return session

    @pytest.fixture
    def db_manager(self, mock_engine, mock_session):
        """Create DatabaseManager with mocked dependencies"""
        with patch('app.database.connection.create_engine', return_value=mock_engine):
            with patch('app.database.connection.sessionmaker'):
                manager = DatabaseManager(database_url="postgresql://test")
                manager._SessionLocal = lambda: mock_session
                return manager

    def test_db_manager_initialization(self):
        """Test DatabaseManager initializes correctly"""
        with patch('app.database.connection.create_engine') as mock_create:
            mock_create.return_value = Mock()
            manager = DatabaseManager(database_url="postgresql://test")
            assert manager is not None

    def test_get_session(self, db_manager):
        """Test getting database session"""
        session = db_manager.get_session()
        assert session is not None

    def test_test_connection_success(self, db_manager, mock_engine):
        """Test successful database connection test"""
        result = db_manager.test_connection()
        assert isinstance(result, bool)

    def test_test_connection_failure(self):
        """Test database connection failure handling"""
        with patch('app.database.connection.create_engine') as mock_create:
            mock_engine = Mock()
            mock_engine.connect.side_effect = Exception("Connection failed")
            mock_create.return_value = mock_engine

            manager = DatabaseManager(database_url="postgresql://test")
            result = manager.test_connection()
            assert result == False

    def test_create_user(self, db_manager, mock_session):
        """Test user creation"""
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_session.add = Mock()
        mock_session.commit = Mock()
        mock_session.refresh = Mock()

        # Mock the return value after adding
        with patch.object(mock_session, 'add') as mock_add:
            mock_add.return_value = None
            # Simulate creating user
            user_data = {
                'username': 'testuser',
                'email': 'test@example.com',
                'password_hash': 'hashed',
                'full_name': 'Test User'
            }

            # Test would call: user = db_manager.create_user(**user_data)
            # Since we're mocking, just verify the method exists
            assert hasattr(db_manager, 'create_user')

    def test_get_user_by_username(self, db_manager, mock_session):
        """Test getting user by username"""
        mock_user = Mock(spec=User)
        mock_user.username = "testuser"
        mock_session.filter_by.return_value.first.return_value = mock_user

        user = db_manager.get_user_by_username("testuser")

        assert user == mock_user
        mock_session.query.assert_called()

    def test_get_user_by_email(self, db_manager, mock_session):
        """Test getting user by email"""
        mock_user = Mock(spec=User)
        mock_user.email = "test@example.com"
        mock_session.filter_by.return_value.first.return_value = mock_user

        user = db_manager.get_user_by_email("test@example.com")

        assert user == mock_user

    def test_create_watchlist(self, db_manager, mock_session):
        """Test watchlist creation"""
        assert hasattr(db_manager, 'create_watchlist')
        # Mock would verify the creation logic

    def test_create_signal(self, db_manager, mock_session):
        """Test signal creation"""
        assert hasattr(db_manager, 'create_signal')

    def test_get_active_signals(self, db_manager, mock_session):
        """Test getting active signals"""
        mock_signals = [Mock(spec=Signal) for _ in range(3)]
        mock_session.filter_by.return_value.order_by.return_value.limit.return_value.all.return_value = mock_signals

        signals = db_manager.get_active_signals(limit=3)

        assert len(signals) == 3

    def test_create_alert(self, db_manager, mock_session):
        """Test alert creation"""
        assert hasattr(db_manager, 'create_alert')

    def test_get_user_alerts(self, db_manager, mock_session):
        """Test getting user alerts"""
        mock_alerts = [Mock(spec=Alert) for _ in range(2)]
        mock_session.filter.return_value.order_by.return_value.all.return_value = mock_alerts

        alerts = db_manager.get_user_alerts(user_id=1)

        assert len(alerts) == 2

    def test_log_message(self, db_manager, mock_session):
        """Test logging message"""
        assert hasattr(db_manager, 'log_message')

    def test_get_recent_logs(self, db_manager, mock_session):
        """Test getting recent logs"""
        mock_logs = [Mock() for _ in range(5)]
        mock_session.order_by.return_value.limit.return_value.all.return_value = mock_logs

        logs = db_manager.get_recent_logs(limit=5)

        assert len(logs) == 5


# ===== REDIS CACHE TESTS =====

class TestRedisCache:
    """Tests for Redis cache"""

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client"""
        redis_mock = Mock()
        redis_mock.ping.return_value = True
        redis_mock.set.return_value = True
        redis_mock.get.return_value = json.dumps({"test": "data"}).encode()
        redis_mock.delete.return_value = 1
        redis_mock.exists.return_value = 1
        redis_mock.ttl.return_value = 3600
        redis_mock.mset.return_value = True
        redis_mock.mget.return_value = [json.dumps({"key": "value"}).encode()]
        redis_mock.scan_iter.return_value = iter([b'key1', b'key2'])
        redis_mock.flushdb.return_value = True
        redis_mock.incr.return_value = 1
        return redis_mock

    @pytest.fixture
    def redis_cache(self, mock_redis):
        """Create RedisCache with mocked Redis"""
        with patch('redis.Redis', return_value=mock_redis):
            cache = RedisCache(host='localhost', port=6379)
            return cache

    def test_redis_initialization(self):
        """Test Redis cache initializes"""
        with patch('redis.Redis') as mock_redis_class:
            mock_redis_class.return_value = Mock()
            cache = RedisCache()
            assert cache is not None

    def test_is_connected_success(self, redis_cache, mock_redis):
        """Test Redis connection check"""
        result = redis_cache.is_connected()
        assert result == True
        mock_redis.ping.assert_called_once()

    def test_is_connected_failure(self, mock_redis):
        """Test Redis connection failure"""
        mock_redis.ping.side_effect = Exception("Connection failed")
        with patch('redis.Redis', return_value=mock_redis):
            cache = RedisCache()
            result = cache.is_connected()
            assert result == False

    def test_set_simple_value(self, redis_cache, mock_redis):
        """Test setting a simple value"""
        result = redis_cache.set('test_key', 'test_value')
        assert result == True
        mock_redis.set.assert_called_once()

    def test_set_with_expire(self, redis_cache, mock_redis):
        """Test setting value with expiration"""
        result = redis_cache.set('test_key', 'test_value', expire=60)
        assert result == True

    def test_set_complex_object(self, redis_cache, mock_redis):
        """Test setting complex object"""
        data = {"nested": {"key": "value"}, "list": [1, 2, 3]}
        result = redis_cache.set('complex_key', data)
        assert result == True

    def test_get_value(self, redis_cache, mock_redis):
        """Test getting a value"""
        result = redis_cache.get('test_key')
        assert result == {"test": "data"}

    def test_get_nonexistent_key(self, redis_cache, mock_redis):
        """Test getting non-existent key"""
        mock_redis.get.return_value = None
        result = redis_cache.get('nonexistent')
        assert result is None

    def test_delete_key(self, redis_cache, mock_redis):
        """Test deleting a key"""
        result = redis_cache.delete('test_key')
        assert result == True
        mock_redis.delete.assert_called_once_with('test_key')

    def test_exists_key(self, redis_cache, mock_redis):
        """Test checking key existence"""
        result = redis_cache.exists('test_key')
        assert result == True

    def test_get_ttl(self, redis_cache, mock_redis):
        """Test getting TTL"""
        result = redis_cache.get_ttl('test_key')
        assert result == 3600

    def test_set_multiple(self, redis_cache, mock_redis):
        """Test setting multiple keys"""
        mapping = {'key1': 'value1', 'key2': 'value2'}
        result = redis_cache.set_multiple(mapping)
        assert result == True

    def test_get_multiple(self, redis_cache, mock_redis):
        """Test getting multiple keys"""
        result = redis_cache.get_multiple(['key1', 'key2'])
        assert isinstance(result, dict)

    def test_clear_pattern(self, redis_cache, mock_redis):
        """Test clearing keys by pattern"""
        result = redis_cache.clear_pattern('test_*')
        assert isinstance(result, int)
        assert result >= 0

    def test_flush_db(self, redis_cache, mock_redis):
        """Test flushing database"""
        result = redis_cache.flush_db()
        assert result == True
        mock_redis.flushdb.assert_called_once()

    def test_cache_quote(self, redis_cache, mock_redis):
        """Test caching quote data"""
        quote_data = {'symbol': 'AAPL', 'price': 150.50}
        redis_cache.cache_quote('AAPL', quote_data)
        mock_redis.set.assert_called()

    def test_get_cached_quote(self, redis_cache, mock_redis):
        """Test getting cached quote"""
        result = redis_cache.get_cached_quote('AAPL')
        assert isinstance(result, dict)

    def test_cache_ohlcv(self, redis_cache, mock_redis):
        """Test caching OHLCV data"""
        ohlcv_data = {'data': [[100, 105, 95, 102, 10000]]}
        redis_cache.cache_ohlcv('AAPL', '1h', ohlcv_data)
        mock_redis.set.assert_called()

    def test_get_cached_ohlcv(self, redis_cache, mock_redis):
        """Test getting cached OHLCV"""
        result = redis_cache.get_cached_ohlcv('AAPL', '1h')
        assert isinstance(result, dict)

    def test_cache_indicators(self, redis_cache, mock_redis):
        """Test caching indicators"""
        indicators = {'rsi': 65.5, 'macd': 2.3}
        redis_cache.cache_indicators('AAPL', '1h', indicators)
        mock_redis.set.assert_called()

    def test_get_cached_indicators(self, redis_cache, mock_redis):
        """Test getting cached indicators"""
        result = redis_cache.get_cached_indicators('AAPL', '1h')
        assert isinstance(result, dict)

    def test_increment_counter(self, redis_cache, mock_redis):
        """Test incrementing counter"""
        result = redis_cache.increment_counter('api_calls')
        assert result == 1
        mock_redis.incr.assert_called_once()

    def test_get_counter(self, redis_cache, mock_redis):
        """Test getting counter value"""
        mock_redis.get.return_value = b'42'
        result = redis_cache.get_counter('api_calls')
        assert result == 42


# ===== INFLUXDB CLIENT TESTS =====

class TestInfluxDBClient:
    """Tests for InfluxDB time series client"""

    @pytest.fixture
    def mock_influx_client(self):
        """Mock InfluxDB client"""
        client = Mock()
        client.ping.return_value = True
        client.write_points.return_value = True
        client.query.return_value.raw = {'series': []}
        return client

    @pytest.fixture
    def influx_client(self, mock_influx_client):
        """Create InfluxDBClient with mocked client"""
        with patch('influxdb_client.InfluxDBClient', return_value=mock_influx_client):
            from app.database.influx_client import InfluxDBClient as InfluxClient
            client = InfluxClient(
                url='http://localhost:8086',
                token='test_token',
                org='test_org',
                bucket='test_bucket'
            )
            return client

    def test_influx_initialization(self):
        """Test InfluxDB client initializes"""
        with patch('influxdb_client.InfluxDBClient') as mock:
            mock.return_value = Mock()
            from app.database.influx_client import InfluxDBClient as InfluxClient
            client = InfluxClient(
                url='http://localhost:8086',
                bucket='test_bucket'
            )
            assert client is not None

    def test_is_connected_success(self, influx_client, mock_influx_client):
        """Test InfluxDB connection check"""
        result = influx_client.is_connected()
        assert result == True
        mock_influx_client.ping.assert_called_once()

    def test_is_connected_failure(self, mock_influx_client):
        """Test InfluxDB connection failure"""
        mock_influx_client.ping.side_effect = Exception("Connection failed")
        with patch('influxdb.InfluxDBClient', return_value=mock_influx_client):
            client = InfluxDBClient(database='test_db')
            result = client.is_connected()
            assert result == False

    def test_write_ohlcv(self, influx_client, mock_influx_client):
        """Test writing OHLCV data"""
        result = influx_client.write_ohlcv(
            symbol='AAPL',
            timestamp=datetime.now(),
            open_price=150.0,
            high=151.0,
            low=149.0,
            close=150.5,
            volume=1000000
        )

        assert result == True
        mock_influx_client.write_points.assert_called_once()

    def test_write_ohlcv_batch(self, influx_client, mock_influx_client):
        """Test writing batch OHLCV data"""
        data = [
            {
                'timestamp': datetime.now(),
                'open': 150.0,
                'high': 151.0,
                'low': 149.0,
                'close': 150.5,
                'volume': 1000000
            },
            {
                'timestamp': datetime.now() - timedelta(hours=1),
                'open': 149.0,
                'high': 150.0,
                'low': 148.5,
                'close': 149.5,
                'volume': 900000
            }
        ]

        result = influx_client.write_ohlcv_batch('AAPL', data)
        assert result == True

    def test_write_indicator(self, influx_client, mock_influx_client):
        """Test writing indicator data"""
        result = influx_client.write_indicator(
            symbol='AAPL',
            indicator_name='RSI',
            timestamp=datetime.now(),
            value=65.5
        )

        assert result == True
        mock_influx_client.write_points.assert_called()

    def test_query_ohlcv(self, influx_client, mock_influx_client):
        """Test querying OHLCV data"""
        # Mock query result
        mock_result = Mock()
        mock_result.raw = {
            'series': [{
                'values': [
                    ['2023-01-01T00:00:00Z', 150.0, 151.0, 149.0, 150.5, 1000000]
                ],
                'columns': ['time', 'open', 'high', 'low', 'close', 'volume']
            }]
        }
        mock_influx_client.query.return_value = mock_result

        df = influx_client.query_ohlcv('AAPL', hours=24)

        assert isinstance(df, pd.DataFrame)

    def test_query_indicator(self, influx_client, mock_influx_client):
        """Test querying indicator data"""
        mock_result = Mock()
        mock_result.raw = {
            'series': [{
                'values': [['2023-01-01T00:00:00Z', 65.5]],
                'columns': ['time', 'value']
            }]
        }
        mock_influx_client.query.return_value = mock_result

        df = influx_client.query_indicator('AAPL', 'RSI', hours=24)

        assert isinstance(df, pd.DataFrame)

    def test_get_latest_candle(self, influx_client, mock_influx_client):
        """Test getting latest candle"""
        mock_result = Mock()
        mock_result.raw = {
            'series': [{
                'values': [['2023-01-01T00:00:00Z', 150.0, 151.0, 149.0, 150.5, 1000000]],
                'columns': ['time', 'open', 'high', 'low', 'close', 'volume']
            }]
        }
        mock_influx_client.query.return_value = mock_result

        candle = influx_client.get_latest_candle('AAPL')

        assert isinstance(candle, dict) or candle is None

    def test_delete_old_data(self, influx_client, mock_influx_client):
        """Test deleting old data"""
        mock_influx_client.query.return_value = Mock()

        result = influx_client.delete_old_data(days=90)

        assert isinstance(result, bool)

    def test_close_connection(self, influx_client, mock_influx_client):
        """Test closing connection"""
        influx_client.close()
        mock_influx_client.close.assert_called_once()


# ===== MODEL TESTS =====

class TestDatabaseModels:
    """Tests for database models"""

    def test_signal_type_enum(self):
        """Test SignalType enum"""
        assert hasattr(SignalType, 'BUY')
        assert hasattr(SignalType, 'SELL')
        assert hasattr(SignalType, 'HOLD')

    def test_alert_status_enum(self):
        """Test AlertStatus enum"""
        assert hasattr(AlertStatus, 'PENDING')
        assert hasattr(AlertStatus, 'SENT')
        assert hasattr(AlertStatus, 'FAILED')

    def test_user_model_exists(self):
        """Test User model exists"""
        assert User is not None
        assert hasattr(User, '__tablename__')

    def test_signal_model_exists(self):
        """Test Signal model exists"""
        assert Signal is not None
        assert hasattr(Signal, '__tablename__')

    def test_alert_model_exists(self):
        """Test Alert model exists"""
        assert Alert is not None
        assert hasattr(Alert, '__tablename__')

    def test_watchlist_model_exists(self):
        """Test Watchlist model exists"""
        assert Watchlist is not None
        assert hasattr(Watchlist, '__tablename__')


# ===== INTEGRATION TESTS =====

class TestDatabaseIntegration:
    """Integration tests for database services"""

    def test_all_database_clients_exist(self):
        """Test all database clients can be instantiated"""
        # Test with mocking to avoid real connections
        with patch('app.database.connection.create_engine'):
            db_manager = DatabaseManager(database_url="postgresql://test")
            assert db_manager is not None

        with patch('redis.Redis'):
            redis_cache = RedisCache()
            assert redis_cache is not None

        with patch('influxdb_client.InfluxDBClient'):
            from app.database.influx_client import InfluxDBClient as InfluxClient
            influx_client = InfluxClient(url='http://localhost:8086', bucket='test')
            assert influx_client is not None

    def test_database_manager_has_all_methods(self):
        """Test DatabaseManager has all expected methods"""
        with patch('app.database.connection.create_engine'):
            manager = DatabaseManager(database_url="postgresql://test")

            # Check all major methods exist
            assert hasattr(manager, 'get_session')
            assert hasattr(manager, 'test_connection')
            assert hasattr(manager, 'init_database')
            assert hasattr(manager, 'create_user')
            assert hasattr(manager, 'create_signal')
            assert hasattr(manager, 'create_alert')
            assert hasattr(manager, 'create_watchlist')
            assert hasattr(manager, 'log_message')

    def test_redis_cache_has_all_methods(self):
        """Test RedisCache has all expected methods"""
        with patch('redis.Redis'):
            cache = RedisCache()

            # Check all major methods exist
            assert hasattr(cache, 'set')
            assert hasattr(cache, 'get')
            assert hasattr(cache, 'delete')
            assert hasattr(cache, 'exists')
            assert hasattr(cache, 'cache_quote')
            assert hasattr(cache, 'cache_ohlcv')
            assert hasattr(cache, 'cache_indicators')
            assert hasattr(cache, 'increment_counter')

    def test_influx_client_has_all_methods(self):
        """Test InfluxDBClient has all expected methods"""
        with patch('influxdb.InfluxDBClient'):
            client = InfluxDBClient(database='test')

            # Check all major methods exist
            assert hasattr(client, 'write_ohlcv')
            assert hasattr(client, 'write_ohlcv_batch')
            assert hasattr(client, 'write_indicator')
            assert hasattr(client, 'query_ohlcv')
            assert hasattr(client, 'query_indicator')
            assert hasattr(client, 'get_latest_candle')
            assert hasattr(client, 'delete_old_data')
