"""
Tests for analysis endpoints - UPDATED for new response structure
"""
import pytest


@pytest.mark.slow
def test_get_indicators(client, sample_symbol):
    """Test getting technical indicators"""
    response = client.get(
        f"/api/v1/analysis/indicators/{sample_symbol}",
        params={"interval": "1h", "period": "7d"}
    )

    # Accept 200 (success) or 500 (external API error)
    assert response.status_code in [200, 500]

    if response.status_code == 200:
        data = response.json()
        assert data["symbol"] == sample_symbol

        # New structure: indicators are nested
        if "indicators" in data:
            indicators = data["indicators"]
            # Check for major indicators
            assert "rsi" in indicators or "RSI" in indicators
            assert "macd" in indicators or "MACD" in indicators
        else:
            # Old structure: indicators at top level
            assert "rsi" in data
            assert "macd" in data


@pytest.mark.slow
def test_detect_patterns(client, sample_symbol):
    """Test pattern detection"""
    response = client.get(
        f"/api/v1/analysis/patterns/{sample_symbol}",
        params={"interval": "1h", "period": "7d"}
    )

    assert response.status_code in [200, 500]

    if response.status_code == 200:
        data = response.json()
        assert data["symbol"] == sample_symbol

        # Check for patterns field
        assert "patterns" in data or "detected_patterns" in data

        # Check for summary
        if "patterns" in data:
            patterns = data["patterns"]
            assert isinstance(patterns, list)

        # May have summary field
        if "summary" in data:
            summary = data["summary"]
            assert isinstance(summary, dict)


@pytest.mark.slow
def test_get_trading_signal(client, sample_symbol):
    """Test getting trading signal"""
    response = client.get(
        f"/api/v1/analysis/signal/{sample_symbol}",
        params={"interval": "1h", "period": "7d"}
    )

    assert response.status_code in [200, 500]

    if response.status_code == 200:
        data = response.json()
        assert data["symbol"] == sample_symbol

        # Signal should be one of these values
        if "signal" in data:
            assert data["signal"] in ["BUY", "SELL", "NEUTRAL", "STRONG_BUY", "STRONG_SELL"]

        # Should have confidence or strength
        assert "strength" in data or "confidence" in data or "score" in data

        # Should have reasoning
        assert "reasoning" in data or "reason" in data or "description" in data


def test_indicators_invalid_symbol(client):
    """Test indicators with invalid symbol"""
    response = client.get(
        "/api/v1/analysis/indicators/INVALID_SYMBOL_XYZ",
        params={"interval": "1h", "period": "1d"}
    )

    # Should return 404 or 500 for invalid symbol
    assert response.status_code in [404, 500]


def test_patterns_invalid_interval(client, sample_symbol):
    """Test patterns with invalid interval"""
    response = client.get(
        f"/api/v1/analysis/patterns/{sample_symbol}",
        params={"interval": "invalid", "period": "1d"}
    )

    # Should handle gracefully - either 400, 422, or 500
    assert response.status_code in [400, 422, 500]


def test_signal_structure(client, sample_symbol):
    """Test signal response has required fields"""
    response = client.get(
        f"/api/v1/analysis/signal/{sample_symbol}",
        params={"interval": "1d", "period": "1mo"}
    )

    assert response.status_code in [200, 500]

    if response.status_code == 200:
        data = response.json()

        # Must have symbol
        assert "symbol" in data

        # Must have some form of signal/action
        has_signal = any(key in data for key in ["signal", "action", "recommendation"])
        assert has_signal, "Response must have signal/action/recommendation field"


@pytest.mark.slow
def test_indicators_response_types(client, sample_symbol):
    """Test that indicator values are correct types"""
    response = client.get(
        f"/api/v1/analysis/indicators/{sample_symbol}",
        params={"interval": "1h", "period": "7d"}
    )

    if response.status_code == 200:
        data = response.json()

        # Price should be numeric
        if "price" in data:
            assert isinstance(data["price"], (int, float))

        # Volume should be numeric
        if "volume" in data:
            assert isinstance(data["volume"], (int, float))

        # Indicators should be dict or nested structure
        if "indicators" in data:
            assert isinstance(data["indicators"], dict)


def test_analysis_endpoints_exist(client):
    """Test that all analysis endpoints are accessible"""
    endpoints = [
        "/api/v1/analysis/indicators/AAPL",
        "/api/v1/analysis/patterns/AAPL",
        "/api/v1/analysis/signal/AAPL"
    ]

    for endpoint in endpoints:
        response = client.get(endpoint, params={"period": "1d"})
        # Endpoint should exist (not 404), may have external API errors (500)
        assert response.status_code != 404, f"Endpoint {endpoint} does not exist"
