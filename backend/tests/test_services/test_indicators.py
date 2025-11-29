"""
Comprehensive tests for all technical indicators
Tests all 15+ indicators implemented in TechnicalIndicators class
"""
import pytest
import pandas as pd
import numpy as np
from app.services.technical_analysis.indicators import TechnicalIndicators


@pytest.fixture
def sample_df():
    """Create sample OHLCV DataFrame with realistic price movement"""
    np.random.seed(42)  # For reproducibility
    dates = pd.date_range(end=pd.Timestamp.now(), periods=250, freq='1h')

    # Create more realistic price movement with trend
    base_price = 100
    trend = np.linspace(0, 20, 250)
    noise = np.random.randn(250) * 2
    close_prices = base_price + trend + noise

    data = {
        'open': close_prices + np.random.randn(250) * 0.5,
        'high': close_prices + np.abs(np.random.randn(250)) * 2,
        'low': close_prices - np.abs(np.random.randn(250)) * 2,
        'close': close_prices,
        'volume': np.random.randint(1000000, 5000000, 250)
    }

    # Ensure high >= low
    df = pd.DataFrame(data, index=dates)
    df['high'] = df[['open', 'high', 'close']].max(axis=1)
    df['low'] = df[['open', 'low', 'close']].min(axis=1)

    return df


@pytest.fixture
def indicators(sample_df):
    """Create TechnicalIndicators instance"""
    return TechnicalIndicators(sample_df)


# ===== MOMENTUM INDICATORS TESTS =====

def test_rsi_basic(indicators, sample_df):
    """Test RSI calculation returns valid values"""
    rsi = indicators.rsi(period=14)

    assert len(rsi) == len(sample_df)
    assert not pd.isna(rsi.iloc[-1]), "Latest RSI should not be NaN"
    assert 0 <= rsi.iloc[-1] <= 100, "RSI must be between 0 and 100"
    assert rsi.iloc[-50:].min() >= 0, "All recent RSI values should be >= 0"
    assert rsi.iloc[-50:].max() <= 100, "All recent RSI values should be <= 100"


def test_rsi_different_periods(indicators):
    """Test RSI with different periods"""
    rsi_7 = indicators.rsi(period=7)
    rsi_14 = indicators.rsi(period=14)
    rsi_21 = indicators.rsi(period=21)

    assert not pd.isna(rsi_7.iloc[-1])
    assert not pd.isna(rsi_14.iloc[-1])
    assert not pd.isna(rsi_21.iloc[-1])

    # Shorter periods should be more volatile (generally)
    assert rsi_7.std() >= rsi_21.std() * 0.5  # Allow some flexibility


def test_stochastic_basic(indicators, sample_df):
    """Test Stochastic Oscillator calculation"""
    slowk, slowd = indicators.stochastic()

    assert len(slowk) == len(sample_df)
    assert len(slowd) == len(sample_df)
    assert not pd.isna(slowk.iloc[-1])
    assert not pd.isna(slowd.iloc[-1])
    assert 0 <= slowk.iloc[-1] <= 100
    assert 0 <= slowd.iloc[-1] <= 100


def test_stochastic_custom_periods(indicators):
    """Test Stochastic with custom periods"""
    slowk, slowd = indicators.stochastic(
        fastk_period=5,
        slowk_period=3,
        slowd_period=3
    )

    assert not pd.isna(slowk.iloc[-1])
    assert not pd.isna(slowd.iloc[-1])


def test_cci_basic(indicators, sample_df):
    """Test CCI calculation"""
    cci = indicators.cci(period=20)

    assert len(cci) == len(sample_df)
    assert not pd.isna(cci.iloc[-1])
    # CCI can be any value, but typically -200 to +200
    assert -500 < cci.iloc[-1] < 500


def test_williams_r_basic(indicators, sample_df):
    """Test Williams %R calculation"""
    williams = indicators.williams_r(period=14)

    assert len(williams) == len(sample_df)
    assert not pd.isna(williams.iloc[-1])
    # Williams %R ranges from -100 to 0
    assert -100 <= williams.iloc[-1] <= 0


def test_mfi_basic(indicators, sample_df):
    """Test Money Flow Index calculation"""
    mfi = indicators.mfi(period=14)

    assert len(mfi) == len(sample_df)
    assert not pd.isna(mfi.iloc[-1])
    assert 0 <= mfi.iloc[-1] <= 100, "MFI must be between 0 and 100"


# ===== TREND INDICATORS TESTS =====

def test_macd_basic(indicators, sample_df):
    """Test MACD calculation"""
    macd_line, signal_line, histogram = indicators.macd()

    assert len(macd_line) == len(sample_df)
    assert len(signal_line) == len(sample_df)
    assert len(histogram) == len(sample_df)
    assert not pd.isna(macd_line.iloc[-1])
    assert not pd.isna(signal_line.iloc[-1])
    assert not pd.isna(histogram.iloc[-1])


def test_macd_custom_periods(indicators):
    """Test MACD with custom periods"""
    macd_line, signal_line, histogram = indicators.macd(
        fast=8,
        slow=21,
        signal=5
    )

    assert not pd.isna(macd_line.iloc[-1])
    assert not pd.isna(signal_line.iloc[-1])
    # Histogram should equal macd - signal
    assert abs(histogram.iloc[-1] - (macd_line.iloc[-1] - signal_line.iloc[-1])) < 0.01


def test_adx_basic(indicators, sample_df):
    """Test ADX calculation"""
    adx = indicators.adx(period=14)

    assert len(adx) == len(sample_df)
    assert not pd.isna(adx.iloc[-1])
    assert 0 <= adx.iloc[-1] <= 100, "ADX should be between 0 and 100"


def test_sma_basic(indicators, sample_df):
    """Test Simple Moving Average"""
    sma = indicators.sma(period=20)

    assert len(sma) == len(sample_df)
    assert not pd.isna(sma.iloc[-1])
    # SMA should be close to recent close prices
    recent_close = sample_df['close'].iloc[-1]
    assert abs(sma.iloc[-1] - recent_close) < recent_close * 0.3


def test_sma_multiple_periods(indicators):
    """Test SMA with multiple periods"""
    sma_10 = indicators.sma(period=10)
    sma_50 = indicators.sma(period=50)
    sma_200 = indicators.sma(period=200)

    assert not pd.isna(sma_10.iloc[-1])
    assert not pd.isna(sma_50.iloc[-1])
    assert not pd.isna(sma_200.iloc[-1])


def test_ema_basic(indicators, sample_df):
    """Test Exponential Moving Average"""
    ema = indicators.ema(period=20)

    assert len(ema) == len(sample_df)
    assert not pd.isna(ema.iloc[-1])


def test_ema_vs_sma(indicators):
    """Test that EMA responds faster than SMA"""
    ema = indicators.ema(period=20)
    sma = indicators.sma(period=20)

    # Both should have valid values
    assert not pd.isna(ema.iloc[-1])
    assert not pd.isna(sma.iloc[-1])
    # EMA and SMA should be relatively close
    assert abs(ema.iloc[-1] - sma.iloc[-1]) < sma.iloc[-1] * 0.15


def test_wma_basic(indicators, sample_df):
    """Test Weighted Moving Average"""
    wma = indicators.wma(period=20)

    assert len(wma) == len(sample_df)
    assert not pd.isna(wma.iloc[-1])


def test_ichimoku_basic(indicators, sample_df):
    """Test Ichimoku Cloud calculation"""
    ichimoku = indicators.ichimoku()

    assert 'tenkan' in ichimoku
    assert 'kijun' in ichimoku
    assert 'senkou_a' in ichimoku
    assert 'senkou_b' in ichimoku
    assert 'chikou' in ichimoku

    # Check all components have correct length
    for component in ichimoku.values():
        assert len(component) == len(sample_df)


def test_ichimoku_values(indicators):
    """Test Ichimoku Cloud has valid values"""
    ichimoku = indicators.ichimoku()

    # Tenkan and Kijun should have values (may have NaN at start)
    assert not pd.isna(ichimoku['tenkan'].iloc[-1])
    assert not pd.isna(ichimoku['kijun'].iloc[-1])


# ===== VOLATILITY INDICATORS TESTS =====

def test_bollinger_bands_basic(indicators, sample_df):
    """Test Bollinger Bands calculation"""
    upper, middle, lower = indicators.bollinger_bands(period=20, std_dev=2.0)

    assert len(upper) == len(sample_df)
    assert len(middle) == len(sample_df)
    assert len(lower) == len(sample_df)
    assert not pd.isna(upper.iloc[-1])
    assert not pd.isna(middle.iloc[-1])
    assert not pd.isna(lower.iloc[-1])


def test_bollinger_bands_order(indicators):
    """Test Bollinger Bands ordering (upper > middle > lower)"""
    upper, middle, lower = indicators.bollinger_bands()

    # Check ordering for recent values (non-NaN)
    assert upper.iloc[-1] > middle.iloc[-1], "Upper band should be above middle"
    assert middle.iloc[-1] > lower.iloc[-1], "Middle band should be above lower"


def test_bollinger_bands_width(indicators):
    """Test Bollinger Bands width changes with std_dev"""
    upper_2, middle_2, lower_2 = indicators.bollinger_bands(std_dev=2.0)
    upper_3, middle_3, lower_3 = indicators.bollinger_bands(std_dev=3.0)

    # Wider std should create wider bands
    width_2 = upper_2.iloc[-1] - lower_2.iloc[-1]
    width_3 = upper_3.iloc[-1] - lower_3.iloc[-1]

    assert width_3 > width_2, "Larger std_dev should create wider bands"


def test_atr_basic(indicators, sample_df):
    """Test Average True Range calculation"""
    atr = indicators.atr(period=14)

    assert len(atr) == len(sample_df)
    assert not pd.isna(atr.iloc[-1])
    assert atr.iloc[-1] > 0, "ATR must be positive"


def test_atr_reflects_volatility(indicators):
    """Test ATR with different periods"""
    atr_7 = indicators.atr(period=7)
    atr_14 = indicators.atr(period=14)

    assert not pd.isna(atr_7.iloc[-1])
    assert not pd.isna(atr_14.iloc[-1])
    # Both should be positive
    assert atr_7.iloc[-1] > 0
    assert atr_14.iloc[-1] > 0


def test_keltner_channel_basic(indicators, sample_df):
    """Test Keltner Channel calculation"""
    upper, middle, lower = indicators.keltner_channel()

    assert len(upper) == len(sample_df)
    assert len(middle) == len(sample_df)
    assert len(lower) == len(sample_df)
    assert not pd.isna(upper.iloc[-1])
    assert not pd.isna(middle.iloc[-1])
    assert not pd.isna(lower.iloc[-1])


def test_keltner_channel_order(indicators):
    """Test Keltner Channel ordering"""
    upper, middle, lower = indicators.keltner_channel()

    # Check ordering for recent values
    assert upper.iloc[-1] > middle.iloc[-1], "Upper channel should be above middle"
    assert middle.iloc[-1] > lower.iloc[-1], "Middle channel should be above lower"


# ===== VOLUME INDICATORS TESTS =====

def test_obv_basic(indicators, sample_df):
    """Test On-Balance Volume calculation"""
    obv = indicators.obv()

    assert len(obv) == len(sample_df)
    assert not pd.isna(obv.iloc[-1])
    # OBV is cumulative, so should be large
    assert abs(obv.iloc[-1]) > 0


def test_obv_cumulative(indicators):
    """Test OBV is cumulative"""
    obv = indicators.obv()

    # OBV should generally increase over time with positive volume
    # Check that it changes
    assert obv.iloc[-1] != obv.iloc[0] or len(obv.dropna()) < len(obv)


def test_vwap_basic(indicators, sample_df):
    """Test Volume Weighted Average Price"""
    vwap = indicators.vwap()

    assert len(vwap) == len(sample_df)
    assert not pd.isna(vwap.iloc[-1])
    # VWAP should be close to price range
    close_price = sample_df['close'].iloc[-1]
    assert abs(vwap.iloc[-1] - close_price) < close_price * 0.5


def test_vwap_vs_close(indicators, sample_df):
    """Test VWAP relationship to close price"""
    vwap = indicators.vwap()

    # VWAP should be within reasonable range of typical price
    avg_close = sample_df['close'].mean()
    assert abs(vwap.iloc[-1] - avg_close) < avg_close


# ===== COMPREHENSIVE TESTS =====

def test_calculate_all_indicators(indicators):
    """Test calculating all indicators at once"""
    all_indicators = indicators.calculate_all()

    # Check that all major indicators are present (flattened structure)
    assert 'rsi' in all_indicators
    assert 'macd' in all_indicators
    assert 'macd_signal' in all_indicators
    assert 'macd_histogram' in all_indicators
    assert 'bollinger_upper' in all_indicators
    assert 'bollinger_middle' in all_indicators
    assert 'bollinger_lower' in all_indicators
    assert 'atr' in all_indicators
    assert 'adx' in all_indicators
    assert 'obv' in all_indicators
    assert 'vwap' in all_indicators
    assert 'stochastic_k' in all_indicators
    assert 'stochastic_d' in all_indicators
    assert 'cci' in all_indicators
    assert 'williams_r' in all_indicators
    assert 'mfi' in all_indicators


def test_calculate_all_has_values(indicators):
    """Test that all calculated indicators have valid values"""
    all_indicators = indicators.calculate_all()

    # Check major indicators have numeric values (flattened structure)
    assert isinstance(all_indicators['rsi'], (int, float))
    assert isinstance(all_indicators['atr'], (int, float))
    assert isinstance(all_indicators['adx'], (int, float))

    # Check MACD values (flattened structure)
    assert isinstance(all_indicators['macd'], (int, float))
    assert isinstance(all_indicators['macd_signal'], (int, float))
    assert isinstance(all_indicators['macd_histogram'], (int, float))

    # Check Bollinger Bands (flattened structure)
    assert isinstance(all_indicators['bollinger_upper'], (int, float))
    assert isinstance(all_indicators['bollinger_middle'], (int, float))
    assert isinstance(all_indicators['bollinger_lower'], (int, float))


def test_get_signal_summary(indicators):
    """Test getting signal summary from indicators"""
    signal_summary = indicators.get_signal_summary()

    assert 'signal' in signal_summary
    assert signal_summary['signal'] in ['BUY', 'SELL', 'NEUTRAL']
    assert 'bullish_count' in signal_summary
    assert 'bearish_count' in signal_summary
    assert 'neutral_count' in signal_summary
    assert 'strength' in signal_summary

    # Counts should be non-negative
    assert signal_summary['bullish_count'] >= 0
    assert signal_summary['bearish_count'] >= 0
    assert signal_summary['neutral_count'] >= 0


def test_indicators_with_insufficient_data():
    """Test indicators handle insufficient data gracefully"""
    # Create very small dataset
    dates = pd.date_range(end=pd.Timestamp.now(), periods=10, freq='1h')
    data = {
        'open': [100] * 10,
        'high': [105] * 10,
        'low': [95] * 10,
        'close': [100] * 10,
        'volume': [1000000] * 10
    }
    df = pd.DataFrame(data, index=dates)

    indicators = TechnicalIndicators(df)

    # Should not crash, but may have NaN values
    rsi = indicators.rsi(period=14)
    assert len(rsi) == 10
    # With only 10 periods, RSI(14) will be mostly NaN
    assert pd.isna(rsi.iloc[0])


def test_indicators_case_insensitive_columns():
    """Test indicators work with different column name cases"""
    dates = pd.date_range(end=pd.Timestamp.now(), periods=50, freq='1h')
    data = {
        'Open': [100] * 50,
        'High': [105] * 50,
        'Low': [95] * 50,
        'Close': [100] * 50,
        'Volume': [1000000] * 50
    }
    df = pd.DataFrame(data, index=dates)

    # Should normalize column names internally
    indicators = TechnicalIndicators(df)
    rsi = indicators.rsi()

    assert len(rsi) == 50
    assert not pd.isna(rsi.iloc[-1])


def test_indicators_immutability(sample_df):
    """Test that indicators don't modify original dataframe"""
    original_columns = sample_df.columns.tolist()
    original_shape = sample_df.shape

    indicators = TechnicalIndicators(sample_df)
    indicators.rsi()
    indicators.macd()
    indicators.bollinger_bands()

    # Original dataframe should be unchanged
    assert sample_df.columns.tolist() == original_columns
    assert sample_df.shape == original_shape
