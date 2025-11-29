"""
Pytest configuration and fixtures
"""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client (lazy import to avoid loading all dependencies)"""
    from app.main import app
    return TestClient(app)


@pytest.fixture
def sample_symbol():
    """Sample ticker symbol for testing"""
    return "AAPL"


@pytest.fixture
def sample_ohlcv_data():
    """Sample OHLCV data for testing"""
    import pandas as pd
    from datetime import datetime, timedelta

    dates = pd.date_range(end=datetime.now(), periods=100, freq='1h')
    data = {
        'Open': range(100, 200),
        'High': range(105, 205),
        'Low': range(95, 195),
        'Close': range(100, 200),
        'Volume': [1000000] * 100
    }

    return pd.DataFrame(data, index=dates)
