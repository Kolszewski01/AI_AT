"""
Comprehensive tests for all data fetchers
Tests YFinanceClient, CCXTClient, and TradingViewScraper
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from app.services.data_fetchers.yfinance_client import YFinanceClient
from app.services.data_fetchers.ccxt_client import CCXTClient
from app.services.data_fetchers.tradingview_scraper import TradingViewScraper


# ===== YFINANCE CLIENT TESTS =====

class TestYFinanceClient:
    """Tests for YFinance client"""

    @pytest.fixture
    def client(self):
        """Create YFinance client instance"""
        return YFinanceClient()

    @pytest.fixture
    def sample_ohlcv_data(self):
        """Sample OHLCV data"""
        dates = pd.date_range(end=datetime.now(), periods=100, freq='1h')
        return pd.DataFrame({
            'Open': [100 + i for i in range(100)],
            'High': [105 + i for i in range(100)],
            'Low': [95 + i for i in range(100)],
            'Close': [100 + i for i in range(100)],
            'Volume': [1000000] * 100
        }, index=dates)

    @pytest.fixture
    def sample_ticker_info(self):
        """Sample ticker info"""
        return {
            'currentPrice': 150.50,
            'previousClose': 149.00,
            'open': 148.50,
            'dayHigh': 151.00,
            'dayLow': 147.50,
            'volume': 5000000,
            'marketCap': 1000000000,
            'longName': 'Test Company Inc',
            'currency': 'USD',
            'exchange': 'NASDAQ'
        }

    def test_client_initialization(self, client):
        """Test YFinance client initializes correctly"""
        assert client is not None
        assert hasattr(client, 'cache')
        assert hasattr(client, 'cache_timeout')
        assert client.cache_timeout == 60

    @patch('yfinance.Ticker')
    def test_get_ohlcv_success(self, mock_ticker, client, sample_ohlcv_data):
        """Test successful OHLCV data fetch"""
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = sample_ohlcv_data
        mock_ticker.return_value = mock_ticker_instance

        result = client.get_ohlcv('AAPL', interval='1h', period='7d')

        assert isinstance(result, pd.DataFrame)
        assert not result.empty
        assert len(result) == 100
        # Check columns are lowercased
        assert 'open' in result.columns
        assert 'close' in result.columns

    @patch('yfinance.Ticker')
    def test_get_ohlcv_with_date_range(self, mock_ticker, client, sample_ohlcv_data):
        """Test OHLCV fetch with custom date range"""
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = sample_ohlcv_data
        mock_ticker.return_value = mock_ticker_instance

        result = client.get_ohlcv(
            'AAPL',
            interval='1d',
            start='2023-01-01',
            end='2023-12-31'
        )

        assert isinstance(result, pd.DataFrame)
        mock_ticker_instance.history.assert_called_once_with(
            interval='1d',
            start='2023-01-01',
            end='2023-12-31'
        )

    @patch('yfinance.Ticker')
    def test_get_ohlcv_empty_data(self, mock_ticker, client):
        """Test OHLCV fetch with no data"""
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = pd.DataFrame()
        mock_ticker.return_value = mock_ticker_instance

        result = client.get_ohlcv('INVALID')

        assert isinstance(result, pd.DataFrame)
        assert result.empty

    @patch('yfinance.Ticker')
    def test_get_ohlcv_exception(self, mock_ticker, client):
        """Test OHLCV fetch handles exceptions"""
        mock_ticker.side_effect = Exception("Network error")

        result = client.get_ohlcv('AAPL')

        assert isinstance(result, pd.DataFrame)
        assert result.empty

    @patch('yfinance.Ticker')
    def test_get_quote_success(self, mock_ticker, client, sample_ticker_info):
        """Test successful quote fetch"""
        mock_ticker_instance = Mock()
        mock_ticker_instance.info = sample_ticker_info
        mock_ticker.return_value = mock_ticker_instance

        result = client.get_quote('AAPL')

        assert isinstance(result, dict)
        assert result['symbol'] == 'AAPL'
        assert result['current_price'] == 150.50
        assert result['previous_close'] == 149.00
        assert result['name'] == 'Test Company Inc'

    @patch('yfinance.Ticker')
    def test_get_quote_exception(self, mock_ticker, client):
        """Test quote fetch handles exceptions"""
        mock_ticker.side_effect = Exception("API error")

        result = client.get_quote('AAPL')

        assert isinstance(result, dict)
        assert result == {}

    @patch('yfinance.Ticker')
    def test_get_info_success(self, mock_ticker, client, sample_ticker_info):
        """Test successful info fetch"""
        mock_ticker_instance = Mock()
        mock_ticker_instance.info = sample_ticker_info
        mock_ticker.return_value = mock_ticker_instance

        result = client.get_info('AAPL')

        assert isinstance(result, dict)
        assert result == sample_ticker_info

    @patch('yfinance.Ticker')
    def test_get_multiple_quotes(self, mock_ticker, client, sample_ticker_info):
        """Test fetching multiple quotes"""
        mock_ticker_instance = Mock()
        mock_ticker_instance.info = sample_ticker_info
        mock_ticker.return_value = mock_ticker_instance

        symbols = ['AAPL', 'GOOGL', 'MSFT']
        result = client.get_multiple_quotes(symbols)

        assert isinstance(result, list)
        assert len(result) == 3
        for quote in result:
            assert 'symbol' in quote
            assert 'current_price' in quote

    @patch('yfinance.Ticker')
    def test_get_dividends(self, mock_ticker, client):
        """Test dividend fetch"""
        mock_ticker_instance = Mock()
        mock_ticker_instance.dividends = pd.Series([0.5, 0.52, 0.55])
        mock_ticker.return_value = mock_ticker_instance

        result = client.get_dividends('AAPL')

        assert isinstance(result, pd.Series)
        assert len(result) == 3

    @patch('yfinance.Ticker')
    def test_get_splits(self, mock_ticker, client):
        """Test stock split fetch"""
        mock_ticker_instance = Mock()
        mock_ticker_instance.splits = pd.Series([2.0, 4.0])
        mock_ticker.return_value = mock_ticker_instance

        result = client.get_splits('AAPL')

        assert isinstance(result, pd.Series)
        assert len(result) == 2

    @patch('yfinance.Ticker')
    def test_search_symbols(self, mock_ticker, client, sample_ticker_info):
        """Test symbol search"""
        mock_ticker_instance = Mock()
        mock_ticker_instance.info = sample_ticker_info
        mock_ticker.return_value = mock_ticker_instance

        result = client.search_symbols('AAPL')

        assert isinstance(result, list)
        if result:
            assert 'symbol' in result[0]
            assert 'name' in result[0]


# ===== CCXT CLIENT TESTS =====

class TestCCXTClient:
    """Tests for CCXT client"""

    @pytest.fixture
    def mock_exchange(self):
        """Mock CCXT exchange"""
        exchange = Mock()
        exchange.fetch_ohlcv.return_value = [
            [1609459200000, 29000, 29500, 28800, 29200, 1000],
            [1609462800000, 29200, 29600, 29100, 29400, 1200],
        ]
        exchange.fetch_ticker.return_value = {
            'last': 29400,
            'bid': 29390,
            'ask': 29410,
            'open': 29000,
            'high': 29600,
            'low': 28800,
            'close': 29400,
            'baseVolume': 1200,
            'quoteVolume': 35000000,
            'change': 400,
            'percentage': 1.38,
            'timestamp': 1609462800000
        }
        exchange.fetch_order_book.return_value = {
            'bids': [[29390, 1.5], [29380, 2.0]],
            'asks': [[29410, 1.2], [29420, 1.8]],
            'timestamp': 1609462800000
        }
        exchange.load_markets.return_value = {
            'BTC/USDT': {
                'base': 'BTC',
                'quote': 'USDT',
                'active': True,
                'type': 'spot'
            },
            'ETH/USDT': {
                'base': 'ETH',
                'quote': 'USDT',
                'active': True,
                'type': 'spot'
            }
        }
        exchange.fetch_trades.return_value = [
            {
                'id': '123',
                'timestamp': 1609462800000,
                'price': 29400,
                'amount': 0.5,
                'side': 'buy'
            }
        ]
        return exchange

    @pytest.fixture
    def client(self, mock_exchange):
        """Create CCXT client with mocked exchange"""
        with patch('ccxt.binance') as mock_binance:
            mock_binance.return_value = mock_exchange
            return CCXTClient('binance')

    def test_client_initialization(self):
        """Test CCXT client initializes"""
        with patch('ccxt.binance') as mock_binance:
            mock_binance.return_value = Mock()
            client = CCXTClient('binance')
            assert client is not None
            assert client.exchange_name == 'binance'

    def test_get_ohlcv_success(self, client):
        """Test successful OHLCV fetch"""
        result = client.get_ohlcv('BTC/USDT', timeframe='1h', limit=500)

        assert isinstance(result, pd.DataFrame)
        assert not result.empty
        assert 'open' in result.columns
        assert 'high' in result.columns
        assert 'low' in result.columns
        assert 'close' in result.columns
        assert 'volume' in result.columns

    def test_get_ohlcv_with_since(self, client):
        """Test OHLCV fetch with since parameter"""
        since = int(datetime(2021, 1, 1).timestamp() * 1000)
        result = client.get_ohlcv('BTC/USDT', since=since)

        assert isinstance(result, pd.DataFrame)

    def test_get_ohlcv_no_exchange(self):
        """Test OHLCV fetch when exchange not initialized"""
        client = CCXTClient.__new__(CCXTClient)
        client.exchange = None
        client.exchange_name = 'test'

        result = client.get_ohlcv('BTC/USDT')

        assert isinstance(result, pd.DataFrame)
        assert result.empty

    def test_get_ticker_success(self, client):
        """Test successful ticker fetch"""
        result = client.get_ticker('BTC/USDT')

        assert isinstance(result, dict)
        assert result['symbol'] == 'BTC/USDT'
        assert result['exchange'] == 'binance'
        assert result['last'] == 29400
        assert result['volume'] == 1200

    def test_get_ticker_no_exchange(self):
        """Test ticker fetch when exchange not initialized"""
        client = CCXTClient.__new__(CCXTClient)
        client.exchange = None
        client.exchange_name = 'test'

        result = client.get_ticker('BTC/USDT')

        assert isinstance(result, dict)
        assert result == {}

    def test_get_order_book_success(self, client):
        """Test successful order book fetch"""
        result = client.get_order_book('BTC/USDT', limit=20)

        assert isinstance(result, dict)
        assert 'symbol' in result
        assert 'bids' in result
        assert 'asks' in result
        assert len(result['bids']) == 2
        assert len(result['asks']) == 2

    def test_get_markets_success(self, client):
        """Test successful markets fetch"""
        result = client.get_markets()

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]['symbol'] == 'BTC/USDT'
        assert result[0]['base'] == 'BTC'
        assert result[0]['quote'] == 'USDT'

    def test_get_trades_success(self, client):
        """Test successful trades fetch"""
        result = client.get_trades('BTC/USDT', limit=100)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]['id'] == '123'
        assert result[0]['price'] == 29400

    def test_get_24h_volume(self, client):
        """Test 24h volume fetch"""
        result = client.get_24h_volume('BTC/USDT')

        assert isinstance(result, (int, float))
        assert result == 1200

    def test_search_symbols(self, client):
        """Test symbol search"""
        result = client.search_symbols('BTC')

        assert isinstance(result, list)
        assert len(result) == 1
        assert 'BTC' in result[0]['symbol']

    def test_exchange_initialization_failure(self):
        """Test handling of exchange initialization failure"""
        with patch('builtins.getattr', side_effect=AttributeError):
            client = CCXTClient('invalid_exchange')
            assert client.exchange is None


# ===== TRADINGVIEW SCRAPER TESTS =====

class TestTradingViewScraper:
    """Tests for TradingView scraper"""

    @pytest.fixture
    def scraper(self):
        """Create TradingView scraper instance"""
        return TradingViewScraper()

    @pytest.fixture
    def sample_scanner_response(self):
        """Sample scanner API response"""
        return {
            'data': [
                {
                    's': 'NASDAQ:AAPL',
                    'd': ['AAPL', 150.50, 2.5, 3.75, 50000000, 0.8, 65, 80, 0.5, 25, 2500000000]
                },
                {
                    's': 'NASDAQ:GOOGL',
                    'd': ['GOOGL', 2800.00, 1.2, 33.60, 25000000, 0.7, 58, 75, 0.3, 22, 1800000000]
                }
            ]
        }

    def test_scraper_initialization(self, scraper):
        """Test TradingView scraper initializes correctly"""
        assert scraper is not None
        assert hasattr(scraper, 'base_url')
        assert hasattr(scraper, 'session')
        assert scraper.base_url == "https://scanner.tradingview.com"

    def test_session_headers(self, scraper):
        """Test session has proper headers"""
        headers = scraper.session.headers
        assert 'User-Agent' in headers
        assert 'Accept' in headers
        assert 'Origin' in headers

    @patch('requests.Session.post')
    def test_get_scanner_data_success(self, mock_post, scraper, sample_scanner_response):
        """Test successful scanner data fetch"""
        mock_response = Mock()
        mock_response.json.return_value = sample_scanner_response
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = scraper.get_scanner_data(market='america', limit=50)

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]['symbol'] == 'NASDAQ:AAPL'

    @patch('requests.Session.post')
    def test_get_scanner_data_with_custom_columns(self, mock_post, scraper, sample_scanner_response):
        """Test scanner data with custom columns"""
        mock_response = Mock()
        mock_response.json.return_value = sample_scanner_response
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        columns = ['name', 'close', 'volume']
        result = scraper.get_scanner_data(columns=columns)

        assert isinstance(result, list)
        # Check that post was called with correct columns
        call_args = mock_post.call_args
        assert call_args is not None

    @patch('requests.Session.post')
    def test_get_scanner_data_exception(self, mock_post, scraper):
        """Test scanner data handles exceptions"""
        mock_post.side_effect = Exception("Network error")

        result = scraper.get_scanner_data()

        # Should return empty list on error
        assert isinstance(result, list)
        assert result == []

    @patch('requests.Session.post')
    def test_get_symbol_data(self, mock_post, scraper):
        """Test get symbol data"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'data': [{'s': 'NASDAQ:AAPL', 'd': ['AAPL', 150.50]}]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = scraper.get_symbol_data('AAPL')

        assert isinstance(result, dict)

    @patch('requests.Session.post')
    def test_get_top_movers(self, mock_post, scraper, sample_scanner_response):
        """Test get top movers"""
        mock_response = Mock()
        mock_response.json.return_value = sample_scanner_response
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = scraper.get_top_movers(market='america', limit=20)

        # get_top_movers returns a list, not a dict
        assert isinstance(result, list)

    @patch('requests.Session.post')
    def test_get_technical_ratings(self, mock_post, scraper):
        """Test get technical ratings"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'data': [{'s': 'NASDAQ:AAPL', 'd': ['AAPL', 0.8, 0.6, 0.7]}]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = scraper.get_technical_ratings('AAPL')

        assert isinstance(result, dict)

    def test_interpret_rating(self, scraper):
        """Test rating interpretation"""
        # rating >= 0.5 = STRONG_BUY
        assert scraper._interpret_rating(0.8) == 'STRONG_BUY'
        assert scraper._interpret_rating(0.6) == 'STRONG_BUY'
        # rating >= 0.1 = BUY
        assert scraper._interpret_rating(0.2) == 'BUY'
        # rating between -0.1 and 0.1 = NEUTRAL
        assert scraper._interpret_rating(0.0) == 'NEUTRAL'
        # rating <= -0.1 = SELL
        assert scraper._interpret_rating(-0.2) == 'SELL'
        # rating <= -0.5 = STRONG_SELL
        assert scraper._interpret_rating(-0.6) == 'STRONG_SELL'
        assert scraper._interpret_rating(-0.8) == 'STRONG_SELL'

    @patch('requests.Session.post')
    def test_get_crypto_screener(self, mock_post, scraper, sample_scanner_response):
        """Test crypto screener"""
        mock_response = Mock()
        mock_response.json.return_value = sample_scanner_response
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = scraper.get_crypto_screener(limit=20)

        assert isinstance(result, list)

    @patch('requests.Session.post')
    def test_get_forex_screener(self, mock_post, scraper, sample_scanner_response):
        """Test forex screener"""
        mock_response = Mock()
        mock_response.json.return_value = sample_scanner_response
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = scraper.get_forex_screener(limit=20)

        assert isinstance(result, list)

    @patch('requests.Session.post')
    def test_search_symbols(self, mock_post, scraper):
        """Test symbol search"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'data': [{'s': 'NASDAQ:AAPL', 'd': ['AAPL', 150.50]}]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = scraper.search_symbols('AAPL', market='america')

        assert isinstance(result, list)

    @patch('requests.Session.post')
    def test_get_market_heatmap(self, mock_post, scraper, sample_scanner_response):
        """Test market heatmap"""
        mock_response = Mock()
        mock_response.json.return_value = sample_scanner_response
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = scraper.get_market_heatmap(market='america', limit=100)

        assert isinstance(result, list)


# ===== INTEGRATION TESTS =====

class TestDataFetcherIntegration:
    """Integration tests for data fetchers"""

    def test_yfinance_client_exists(self):
        """Test YFinance client can be instantiated"""
        client = YFinanceClient()
        assert client is not None

    def test_ccxt_client_exists(self):
        """Test CCXT client can be instantiated"""
        with patch('ccxt.binance'):
            client = CCXTClient('binance')
            assert client is not None

    def test_tradingview_scraper_exists(self):
        """Test TradingView scraper can be instantiated"""
        scraper = TradingViewScraper()
        assert scraper is not None

    def test_all_clients_have_required_methods(self):
        """Test all clients have expected methods"""
        # YFinance
        yf_client = YFinanceClient()
        assert hasattr(yf_client, 'get_ohlcv')
        assert hasattr(yf_client, 'get_quote')
        assert hasattr(yf_client, 'get_info')

        # CCXT
        with patch('ccxt.binance') as mock:
            mock.return_value = Mock()
            ccxt_client = CCXTClient('binance')
            assert hasattr(ccxt_client, 'get_ohlcv')
            assert hasattr(ccxt_client, 'get_ticker')
            assert hasattr(ccxt_client, 'get_markets')

        # TradingView
        tv_scraper = TradingViewScraper()
        assert hasattr(tv_scraper, 'get_scanner_data')
        assert hasattr(tv_scraper, 'get_symbol_data')
        assert hasattr(tv_scraper, 'get_technical_ratings')
