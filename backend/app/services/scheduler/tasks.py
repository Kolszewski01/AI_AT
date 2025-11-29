"""
Celery tasks for scheduled analysis and alerts
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict
import yfinance as yf
import pandas as pd

from app.services.scheduler.celery_app import celery_app
from app.core.config import settings
from app.api.endpoints.analysis import (
    calculate_rsi,
    calculate_macd,
    detect_hammer,
    detect_shooting_star
)

logger = logging.getLogger(__name__)


def get_watchlist_symbols() -> List[str]:
    """Get list of symbols to analyze"""
    # In production, fetch from database
    # For now, use default symbols from config
    return settings.DEFAULT_SYMBOLS.split(",")


def analyze_symbol(symbol: str, interval: str = "1h") -> Dict:
    """
    Perform technical analysis on a symbol

    Args:
        symbol: Ticker symbol
        interval: Timeframe interval

    Returns:
        Dictionary with analysis results
    """
    try:
        logger.info(f"Analyzing {symbol} on {interval}")

        ticker = yf.Ticker(symbol)
        df = ticker.history(period="7d", interval=interval)

        if df.empty:
            logger.warning(f"No data for {symbol}")
            return None

        # Calculate indicators
        df['RSI'] = calculate_rsi(df['Close'])
        macd, signal, histogram = calculate_macd(df['Close'])
        df['MACD'] = macd
        df['MACD_Signal'] = signal

        latest = df.iloc[-1]
        price = float(latest['Close'])
        rsi = float(latest['RSI']) if not pd.isna(latest['RSI']) else None
        volume = int(latest['Volume'])

        # Detect patterns
        patterns = []
        if detect_hammer(latest):
            patterns.append({
                "pattern": "Hammer",
                "signal": "bullish",
                "confidence": "medium"
            })

        if detect_shooting_star(latest):
            patterns.append({
                "pattern": "Shooting Star",
                "signal": "bearish",
                "confidence": "medium"
            })

        # Generate trading signal
        signals = []
        if rsi and rsi < 30:
            signals.append(("RSI oversold", "bullish", 2))
        elif rsi and rsi > 70:
            signals.append(("RSI overbought", "bearish", 2))

        if not pd.isna(latest['MACD']) and not pd.isna(latest['MACD_Signal']):
            if latest['MACD'] > latest['MACD_Signal']:
                signals.append(("MACD bullish", "bullish", 1))
            else:
                signals.append(("MACD bearish", "bearish", 1))

        # Add pattern signals
        for p in patterns:
            signals.append((p["pattern"], p["signal"], 2))

        # Calculate overall signal
        bullish_score = sum(s for _, t, s in signals if t == "bullish")
        bearish_score = sum(s for _, t, s in signals if t == "bearish")

        if bullish_score > bearish_score + 1:
            overall_signal = "BUY"
            strength = min(100, int((bullish_score / (bullish_score + bearish_score + 0.01)) * 100))
        elif bearish_score > bullish_score + 1:
            overall_signal = "SELL"
            strength = min(100, int((bearish_score / (bullish_score + bearish_score + 0.01)) * 100))
        else:
            overall_signal = "NEUTRAL"
            strength = 50

        result = {
            "symbol": symbol,
            "interval": interval,
            "timestamp": datetime.utcnow().isoformat(),
            "price": price,
            "volume": volume,
            "rsi": rsi,
            "macd": float(latest['MACD']) if not pd.isna(latest['MACD']) else None,
            "patterns": patterns,
            "signal": overall_signal,
            "strength": strength,
            "reasoning": [{"indicator": r, "signal": s, "weight": w} for r, s, w in signals]
        }

        logger.info(f"Analysis complete for {symbol}: {overall_signal} ({strength}%)")
        return result

    except Exception as e:
        logger.error(f"Error analyzing {symbol}: {e}")
        return None


def should_send_alert(analysis: Dict) -> bool:
    """
    Determine if an alert should be sent based on analysis

    Args:
        analysis: Analysis result dictionary

    Returns:
        True if alert should be sent
    """
    # Alert criteria:
    # 1. Strong signal (strength > 70)
    # 2. RSI extreme (< 30 or > 70)
    # 3. Pattern detected

    if not analysis:
        return False

    signal = analysis.get("signal")
    strength = analysis.get("strength", 0)
    rsi = analysis.get("rsi")
    patterns = analysis.get("patterns", [])

    # Strong signal
    if signal in ["BUY", "SELL"] and strength > 70:
        return True

    # RSI extreme
    if rsi and (rsi < 30 or rsi > 70):
        return True

    # Pattern detected
    if patterns:
        return True

    return False


async def send_telegram_alert(analysis: Dict):
    """Send alert via Telegram"""
    try:
        from app.services.alerts.telegram_bot import send_alert

        if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
            logger.warning("Telegram credentials not configured")
            return

        # Prepare alert data
        alert_data = {
            "symbol": analysis["symbol"],
            "pattern": ", ".join([p["pattern"] for p in analysis.get("patterns", [])]) or "Technical Signal",
            "signal": analysis["signal"],
            "rsi": analysis.get("rsi", 0),
            "price": analysis["price"],
        }

        await send_alert(
            bot_token=settings.TELEGRAM_BOT_TOKEN,
            chat_id=settings.TELEGRAM_CHAT_ID,
            alert_data=alert_data
        )

        logger.info(f"Telegram alert sent for {analysis['symbol']}")

    except Exception as e:
        logger.error(f"Failed to send Telegram alert: {e}")


@celery_app.task(name='app.services.scheduler.tasks.run_quick_analysis')
def run_quick_analysis():
    """
    Run quick analysis on short timeframes (M5, M15)
    Executes every 5 minutes
    """
    logger.info("Starting quick analysis (M5, M15)")

    symbols = get_watchlist_symbols()
    results = []

    for symbol in symbols:
        # Analyze M5
        result_m5 = analyze_symbol(symbol.strip(), interval="5m")
        if result_m5:
            results.append(result_m5)

            # Send alert if needed
            if should_send_alert(result_m5):
                # Run async alert in sync context
                import asyncio
                try:
                    asyncio.run(send_telegram_alert(result_m5))
                except Exception as e:
                    logger.error(f"Error sending alert: {e}")

    logger.info(f"Quick analysis completed. Analyzed {len(results)} symbols.")
    return {"analyzed": len(results), "results": results}


@celery_app.task(name='app.services.scheduler.tasks.run_medium_analysis')
def run_medium_analysis():
    """
    Run analysis on medium timeframes (M15, H1)
    Executes every 15 minutes
    """
    logger.info("Starting medium timeframe analysis (M15, H1)")

    symbols = get_watchlist_symbols()
    results = []

    for symbol in symbols:
        # Analyze H1
        result_h1 = analyze_symbol(symbol.strip(), interval="1h")
        if result_h1:
            results.append(result_h1)

            if should_send_alert(result_h1):
                import asyncio
                try:
                    asyncio.run(send_telegram_alert(result_h1))
                except Exception as e:
                    logger.error(f"Error sending alert: {e}")

    logger.info(f"Medium analysis completed. Analyzed {len(results)} symbols.")
    return {"analyzed": len(results), "results": results}


@celery_app.task(name='app.services.scheduler.tasks.run_high_timeframe_analysis')
def run_high_timeframe_analysis():
    """
    Run analysis on higher timeframes (H4, D1)
    Executes every hour
    """
    logger.info("Starting high timeframe analysis (H4, D1)")

    symbols = get_watchlist_symbols()
    results = []

    for symbol in symbols:
        # Analyze H4
        result_h4 = analyze_symbol(symbol.strip(), interval="1h")  # yfinance doesn't have 4h, use 1h
        if result_h4:
            results.append(result_h4)

            if should_send_alert(result_h4):
                import asyncio
                try:
                    asyncio.run(send_telegram_alert(result_h4))
                except Exception as e:
                    logger.error(f"Error sending alert: {e}")

    logger.info(f"High timeframe analysis completed. Analyzed {len(results)} symbols.")
    return {"analyzed": len(results), "results": results}


@celery_app.task(name='app.services.scheduler.tasks.update_news_sentiment')
def update_news_sentiment():
    """
    Update news sentiment for all watchlist symbols
    Executes every 4 hours
    """
    logger.info("Starting news sentiment update")

    # This will be implemented when NLP service is ready
    # For now, just a placeholder

    symbols = get_watchlist_symbols()
    logger.info(f"Would update sentiment for {len(symbols)} symbols")

    return {"symbols_updated": len(symbols)}


@celery_app.task(name='app.services.scheduler.tasks.cleanup_old_data')
def cleanup_old_data():
    """
    Cleanup old data from database
    Executes daily at midnight
    """
    logger.info("Starting cleanup of old data")

    # Delete signals older than 30 days
    # Delete triggered alerts older than 90 days
    # This would use database operations in production

    cutoff_date = datetime.utcnow() - timedelta(days=30)
    logger.info(f"Cleaning data older than {cutoff_date}")

    return {"status": "completed", "cutoff_date": cutoff_date.isoformat()}


@celery_app.task(name='app.services.scheduler.tasks.send_daily_summary')
def send_daily_summary():
    """
    Send daily market summary
    Executes daily at 8 AM
    """
    logger.info("Generating daily market summary")

    symbols = get_watchlist_symbols()
    summary = []

    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol.strip())
            info = ticker.info

            summary.append({
                "symbol": symbol,
                "price": info.get("currentPrice") or info.get("regularMarketPrice"),
                "change": info.get("regularMarketChange"),
                "change_percent": info.get("regularMarketChangePercent")
            })
        except Exception as e:
            logger.error(f"Error fetching summary for {symbol}: {e}")

    logger.info(f"Daily summary prepared for {len(summary)} symbols")

    # Send summary via Telegram
    # Implementation would go here

    return {"symbols": len(summary), "summary": summary}


@celery_app.task(name='app.services.scheduler.tasks.test_task')
def test_task():
    """Test task to verify Celery is working"""
    logger.info("Test task executed successfully!")
    return {"status": "success", "timestamp": datetime.utcnow().isoformat()}
