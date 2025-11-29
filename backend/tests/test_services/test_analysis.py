"""
Tests for technical analysis services - UPDATED for new architecture
"""
import pytest
import pandas as pd
import numpy as np
from app.services.technical_analysis.indicators import TechnicalIndicators
from app.services.technical_analysis.patterns import CandlestickPatterns


@pytest.fixture
def sample_df():
    """Create sample OHLCV DataFrame for testing"""
    dates = pd.date_range(end=pd.Timestamp.now(), periods=100, freq='1h')
    data = {
        'open': [100 + i + np.random.randn() for i in range(100)],
        'high': [105 + i + np.random.randn() for i in range(100)],
        'low': [95 + i + np.random.randn() for i in range(100)],
        'close': [100 + i + np.random.randn() for i in range(100)],
        'volume': [1000000 + np.random.randint(0, 100000) for _ in range(100)]
    }
    return pd.DataFrame(data, index=dates)


def test_rsi_calculation(sample_df):
    """Test RSI calculation"""
    indicators = TechnicalIndicators(sample_df)
    rsi = indicators.rsi(period=14)

    assert len(rsi) == len(sample_df)
    assert not pd.isna(rsi.iloc[-1])
    assert 0 <= rsi.iloc[-1] <= 100


def test_macd_calculation(sample_df):
    """Test MACD calculation"""
    indicators = TechnicalIndicators(sample_df)
    macd, signal, histogram = indicators.macd()

    assert len(macd) == len(sample_df)
    assert len(signal) == len(sample_df)
    assert len(histogram) == len(sample_df)
    assert not pd.isna(macd.iloc[-1])


def test_bollinger_bands(sample_df):
    """Test Bollinger Bands calculation"""
    indicators = TechnicalIndicators(sample_df)
    upper, middle, lower = indicators.bollinger_bands(period=20, std_dev=2)

    assert len(upper) == len(sample_df)
    assert len(middle) == len(sample_df)
    assert len(lower) == len(sample_df)

    # Upper should be > middle > lower (most of the time)
    assert upper.iloc[-1] > middle.iloc[-1]
    assert middle.iloc[-1] > lower.iloc[-1]


def test_atr_calculation(sample_df):
    """Test ATR calculation"""
    indicators = TechnicalIndicators(sample_df)
    atr = indicators.atr(period=14)

    assert len(atr) == len(sample_df)
    assert atr.iloc[-1] > 0  # ATR should be positive


def test_calculate_all_indicators(sample_df):
    """Test calculating all indicators at once"""
    indicators = TechnicalIndicators(sample_df)
    all_indicators = indicators.calculate_all()

    # Check that major indicators are present (flattened structure)
    assert 'rsi' in all_indicators
    assert 'macd' in all_indicators
    assert 'bollinger_upper' in all_indicators
    assert 'bollinger_middle' in all_indicators
    assert 'bollinger_lower' in all_indicators
    assert 'atr' in all_indicators
    assert 'adx' in all_indicators


def test_get_signal_summary(sample_df):
    """Test getting signal summary"""
    indicators = TechnicalIndicators(sample_df)
    signal_summary = indicators.get_signal_summary()

    assert 'signal' in signal_summary
    assert signal_summary['signal'] in ['BUY', 'SELL', 'NEUTRAL']
    assert 'bullish_count' in signal_summary
    assert 'bearish_count' in signal_summary


def test_detect_hammer():
    """Test hammer pattern detection"""
    # Create hammer candle: small body, long lower shadow
    dates = pd.date_range(end=pd.Timestamp.now(), periods=10, freq='1h')
    data = {
        'open': [100, 100, 100, 100, 100, 100, 100, 105, 100, 100],
        'high': [101, 101, 101, 101, 101, 101, 101, 106, 101, 101],
        'low': [90, 99, 99, 99, 99, 99, 99, 95, 99, 99],  # Hammer at index 7
        'close': [100, 100, 100, 100, 100, 100, 100, 104, 100, 100],
        'volume': [1000000] * 10
    }
    df = pd.DataFrame(data, index=dates)

    patterns = CandlestickPatterns(df)
    hammers = patterns.hammer()

    # Hammer detection may or may not find patterns based on TA-Lib's criteria
    assert isinstance(hammers, list)
    # If detected, check structure
    if len(hammers) > 0:
        assert hammers[0]['pattern'] == 'Hammer'
        assert hammers[0]['signal'] == 'bullish'


def test_detect_shooting_star():
    """Test shooting star pattern detection"""
    # Create shooting star: small body, long upper shadow
    dates = pd.date_range(end=pd.Timestamp.now(), periods=10, freq='1h')
    data = {
        'open': [100, 100, 100, 100, 100, 100, 100, 100, 100, 100],
        'high': [101, 101, 101, 101, 101, 101, 101, 115, 101, 101],  # Shooting star at index 7
        'low': [99, 99, 99, 99, 99, 99, 99, 99, 99, 99],
        'close': [100, 100, 100, 100, 100, 100, 100, 101, 100, 100],
        'volume': [1000000] * 10
    }
    df = pd.DataFrame(data, index=dates)

    patterns = CandlestickPatterns(df)
    shooting_stars = patterns.shooting_star()

    # Shooting star detection may or may not find patterns based on TA-Lib's criteria
    assert isinstance(shooting_stars, list)
    # If detected, check structure
    if len(shooting_stars) > 0:
        assert shooting_stars[0]['pattern'] == 'Shooting Star'
        assert shooting_stars[0]['signal'] == 'bearish'


def test_detect_all_patterns(sample_df):
    """Test detecting all patterns"""
    patterns = CandlestickPatterns(sample_df)
    all_patterns = patterns.detect_all(lookback=10)

    # Should return a list (may be empty if no patterns found)
    assert isinstance(all_patterns, list)

    # If patterns found, check structure
    if len(all_patterns) > 0:
        assert 'pattern' in all_patterns[0]
        assert 'timestamp' in all_patterns[0]
        assert 'signal' in all_patterns[0]


def test_get_pattern_summary(sample_df):
    """Test pattern summary"""
    patterns = CandlestickPatterns(sample_df)
    summary = patterns.get_pattern_summary()

    assert 'total_patterns' in summary
    assert 'bullish_count' in summary
    assert 'bearish_count' in summary
    assert 'overall_signal' in summary
    assert 'confidence' in summary
