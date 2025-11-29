"""
API Client for backend communication
"""
import requests
from typing import Dict, List, Optional
from datetime import datetime
from src.utils.logger import get_logger

logger = get_logger("api_client")


class APIClient:
    """Client for trading system API"""

    def __init__(self, base_url: str):
        """
        Initialize API client

        Args:
            base_url: Base URL for API (e.g., http://localhost:8000/api/v1)
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        logger.info(f"APIClient initialized with base_url: {self.base_url}")

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """
        Make HTTP request

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            **kwargs: Additional arguments for requests

        Returns:
            Response JSON
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        logger.debug(f"API Request: {method} {url}")
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            logger.debug(f"API Response: {response.status_code} OK")
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP Error: {e.response.status_code} - {e.response.text[:200]}")
            raise
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection Error: {e}")
            raise
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout Error: {e}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected API error: {e}")
            raise

    # Market Data
    def get_symbols(self) -> Dict:
        """Get list of available symbols"""
        return self._request('GET', '/market/symbols')

    def get_ohlcv(
        self,
        symbol: str,
        interval: str = '1h',
        period: str = '7d',
        start: Optional[str] = None,
        end: Optional[str] = None
    ) -> Dict:
        """
        Get OHLCV data

        Args:
            symbol: Ticker symbol
            interval: Candle interval (1m, 5m, 15m, 1h, 4h, 1d)
            period: Time period (1d, 5d, 1mo, 3mo, 1y)
            start: Start date (YYYY-MM-DD)
            end: End date (YYYY-MM-DD)

        Returns:
            OHLCV data
        """
        params = {'interval': interval}
        if start and end:
            params['start'] = start
            params['end'] = end
        else:
            params['period'] = period

        return self._request('GET', f'/market/ohlcv/{symbol}', params=params)

    def get_quote(self, symbol: str) -> Dict:
        """Get current quote for symbol"""
        return self._request('GET', f'/market/quote/{symbol}')

    # Technical Analysis
    def get_indicators(
        self,
        symbol: str,
        interval: str = '1h',
        period: str = '7d'
    ) -> Dict:
        """Get technical indicators"""
        params = {'interval': interval, 'period': period}
        return self._request('GET', f'/analysis/indicators/{symbol}', params=params)

    def get_patterns(
        self,
        symbol: str,
        interval: str = '1h',
        period: str = '7d'
    ) -> Dict:
        """Detect candlestick patterns"""
        params = {'interval': interval, 'period': period}
        return self._request('GET', f'/analysis/patterns/{symbol}', params=params)

    def get_signal(
        self,
        symbol: str,
        interval: str = '1h',
        period: str = '7d'
    ) -> Dict:
        """Get trading signal"""
        params = {'interval': interval, 'period': period}
        return self._request('GET', f'/analysis/signal/{symbol}', params=params)

    # Alerts
    def get_alerts(self, status: Optional[str] = None) -> Dict:
        """Get all alerts"""
        params = {}
        if status:
            params['status'] = status
        return self._request('GET', '/alerts', params=params)

    def create_alert(self, alert_data: Dict) -> Dict:
        """Create a new alert"""
        return self._request('POST', '/alerts/create', json=alert_data)

    def delete_alert(self, alert_id: str) -> Dict:
        """Delete an alert"""
        return self._request('DELETE', f'/alerts/{alert_id}')

    # News & Sentiment
    def get_news(
        self,
        symbol: str,
        days: int = 7,
        max_items: int = 20
    ) -> Dict:
        """Get news for symbol"""
        params = {'days': days, 'max_items': max_items}
        return self._request('GET', f'/news/{symbol}', params=params)

    def get_sentiment(self, symbol: str, days: int = 7) -> Dict:
        """Get sentiment analysis for symbol"""
        params = {'days': days}
        return self._request('GET', f'/news/sentiment/{symbol}', params=params)

    # Backtesting
    def run_backtest(self, backtest_config: Dict) -> Dict:
        """Run a backtest"""
        return self._request('POST', '/backtest/run', json=backtest_config)

    def get_strategies(self) -> Dict:
        """Get available backtest strategies"""
        return self._request('GET', '/backtest/strategies')

    def compare_strategies(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        initial_capital: float = 10000.0
    ) -> Dict:
        """Compare strategies"""
        params = {
            'symbol': symbol,
            'start_date': start_date,
            'end_date': end_date,
            'initial_capital': initial_capital
        }
        return self._request('POST', '/backtest/compare', params=params)

    def health_check(self) -> Dict:
        """Check API health"""
        # Remove /api/v1 from base_url for health endpoint
        base = self.base_url.replace('/api/v1', '')
        url = f"{base}/health"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
