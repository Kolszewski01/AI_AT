"""
Technical analysis endpoints - ALL indicators, patterns, signals
UPDATED to use complete indicator and pattern services
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import yfinance as yf
import pandas as pd

router = APIRouter()


@router.get("/indicators/{symbol}")
async def get_indicators(
    symbol: str,
    interval: str = Query(default="1h", description="Interval: 1m, 5m, 15m, 1h, 4h, 1d"),
    period: str = Query(default="7d", description="Period: 1d, 5d, 1mo, 3mo, 1y")
):
    """
    Calculate ALL technical indicators for a symbol

    Returns: RSI, MACD, Stochastic, ADX, Bollinger Bands, ATR, OBV, VWAP, Ichimoku, etc.
    """
    try:
        from app.services.technical_analysis.indicators import TechnicalIndicators

        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)

        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")

        # Use comprehensive indicator service
        indicators_service = TechnicalIndicators(df)
        all_indicators = indicators_service.calculate_all()
        signal_summary = indicators_service.get_signal_summary()

        return {
            "symbol": symbol,
            "timestamp": str(df.index[-1]),
            "price": float(df['Close'].iloc[-1]),
            "volume": int(df['Volume'].iloc[-1]),
            "indicators": all_indicators,
            "signal": signal_summary,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating indicators: {str(e)}")


@router.get("/patterns/{symbol}")
async def detect_patterns(
    symbol: str,
    interval: str = Query(default="1h", description="Interval"),
    period: str = Query(default="7d", description="Period"),
    lookback: int = Query(default=20, description="Number of recent candles to check")
):
    """
    Detect ALL candlestick patterns

    Returns: Engulfing, Hammer, Shooting Star, Morning/Evening Star, Doji, Harami, etc.
    """
    try:
        from app.services.technical_analysis.patterns import CandlestickPatterns

        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)

        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")

        # Use comprehensive pattern detection service
        pattern_service = CandlestickPatterns(df)
        all_patterns = pattern_service.detect_all(lookback=lookback)
        summary = pattern_service.get_pattern_summary()

        return {
            "symbol": symbol,
            "total_found": len(all_patterns),
            "patterns": all_patterns,
            "summary": summary
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detecting patterns: {str(e)}")


@router.get("/signal/{symbol}")
async def get_trading_signal(
    symbol: str,
    interval: str = Query(default="1h", description="Interval"),
    period: str = Query(default="7d", description="Period")
):
    """
    Generate comprehensive trading signal

    Combines indicators + patterns + sentiment for complete analysis
    """
    try:
        from app.services.technical_analysis.indicators import TechnicalIndicators
        from app.services.technical_analysis.patterns import CandlestickPatterns

        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)

        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")

        # Technical indicators analysis
        indicators_service = TechnicalIndicators(df)
        indicator_signal = indicators_service.get_signal_summary()
        all_indicators = indicators_service.calculate_all()

        # Pattern analysis
        pattern_service = CandlestickPatterns(df)
        pattern_summary = pattern_service.get_pattern_summary()

        # Combine signals
        total_bullish = indicator_signal['bullish_count'] + pattern_summary['bullish_count']
        total_bearish = indicator_signal['bearish_count'] + pattern_summary['bearish_count']

        total = total_bullish + total_bearish
        if total == 0:
            overall_signal = "NEUTRAL"
            strength = 50
        elif total_bullish > total_bearish * 1.3:
            overall_signal = "BUY"
            strength = int((total_bullish / total) * 100)
        elif total_bearish > total_bullish * 1.3:
            overall_signal = "SELL"
            strength = int((total_bearish / total) * 100)
        else:
            overall_signal = "NEUTRAL"
            strength = 50

        # Generate reasoning
        reasoning = []

        # RSI reasoning
        if all_indicators.get('rsi'):
            if all_indicators['rsi'] < 30:
                reasoning.append({"indicator": "RSI oversold", "signal": "bullish", "weight": 2})
            elif all_indicators['rsi'] > 70:
                reasoning.append({"indicator": "RSI overbought", "signal": "bearish", "weight": 2})

        # MACD reasoning
        if all_indicators.get('macd') and all_indicators.get('macd_signal'):
            if all_indicators['macd'] > all_indicators['macd_signal']:
                reasoning.append({"indicator": "MACD bullish cross", "signal": "bullish", "weight": 2})
            else:
                reasoning.append({"indicator": "MACD bearish", "signal": "bearish", "weight": 2})

        # ADX reasoning
        if all_indicators.get('adx'):
            if all_indicators['adx'] > 25:
                reasoning.append({"indicator": f"ADX strong trend ({all_indicators['adx']:.1f})", "signal": "neutral", "weight": 1})

        # Stochastic reasoning
        if all_indicators.get('stochastic_k'):
            if all_indicators['stochastic_k'] < 20:
                reasoning.append({"indicator": "Stochastic oversold", "signal": "bullish", "weight": 1})
            elif all_indicators['stochastic_k'] > 80:
                reasoning.append({"indicator": "Stochastic overbought", "signal": "bearish", "weight": 1})

        # Bollinger Bands reasoning
        if all_indicators.get('bollinger_lower') and all_indicators.get('bollinger_upper'):
            current_price = df['Close'].iloc[-1]
            if current_price < all_indicators['bollinger_lower']:
                reasoning.append({"indicator": "Price below Bollinger lower band", "signal": "bullish", "weight": 1})
            elif current_price > all_indicators['bollinger_upper']:
                reasoning.append({"indicator": "Price above Bollinger upper band", "signal": "bearish", "weight": 1})

        # Pattern reasoning
        for pattern in pattern_summary['patterns'][:3]:
            reasoning.append({
                "indicator": f"{pattern['pattern']} pattern",
                "signal": pattern['signal'],
                "weight": 2
            })

        return {
            "symbol": symbol,
            "timestamp": str(df.index[-1]),
            "signal": overall_signal,
            "strength": strength,
            "price": float(df['Close'].iloc[-1]),
            "indicators": all_indicators,
            "patterns": pattern_summary,
            "reasoning": reasoning,
            "analysis": {
                "total_bullish_signals": total_bullish,
                "total_bearish_signals": total_bearish,
                "confidence": "high" if strength > 70 else "medium" if strength > 55 else "low"
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating signal: {str(e)}")


@router.get("/support-resistance/{symbol}")
async def get_support_resistance(
    symbol: str,
    interval: str = Query(default="1h", description="Interval"),
    period: str = Query(default="3mo", description="Period"),
    method: str = Query(default="all", description="Method: all, fractals, pivots, volume")
):
    """
    Detect support and resistance zones

    Returns: Support and resistance levels with strength
    """
    try:
        from app.services.technical_analysis.support_resistance import SupportResistanceDetector

        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)

        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")

        # Normalize column names
        df.columns = [col.lower() for col in df.columns]

        detector = SupportResistanceDetector(sensitivity=0.02)
        current_price = float(df['close'].iloc[-1])

        zones = detector.detect_zones(df, current_price, lookback=200)

        return {
            "symbol": symbol,
            "current_price": current_price,
            "support": zones['support'],
            "resistance": zones['resistance'],
            "pivots": zones['pivots'],
            "volume_profile": {
                "poc": zones['volume_profile'].get('poc'),
                "value_area_count": len(zones['volume_profile'].get('value_area', []))
            },
            "timestamp": str(df.index[-1])
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detecting S/R: {str(e)}")


@router.get("/order-blocks/{symbol}")
async def get_order_blocks(
    symbol: str,
    interval: str = Query(default="1h", description="Interval"),
    period: str = Query(default="1mo", description="Period")
):
    """
    Detect institutional order blocks

    Returns: Bullish and bearish order blocks
    """
    try:
        from app.services.technical_analysis.support_resistance import SupportResistanceDetector

        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)

        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")

        # Normalize column names
        df.columns = [col.lower() for col in df.columns]

        detector = SupportResistanceDetector()
        order_blocks = detector.detect_order_blocks(df, lookback=100)

        bullish_blocks = [b for b in order_blocks if b['type'] == 'bullish']
        bearish_blocks = [b for b in order_blocks if b['type'] == 'bearish']

        return {
            "symbol": symbol,
            "order_blocks": order_blocks,
            "bullish_count": len(bullish_blocks),
            "bearish_count": len(bearish_blocks),
            "timestamp": str(df.index[-1])
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detecting order blocks: {str(e)}")
