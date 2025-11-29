"""
Backtesting endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime

router = APIRouter()


class BacktestRequest(BaseModel):
    """Backtest request model"""
    symbol: str
    start_date: str  # YYYY-MM-DD
    end_date: str  # YYYY-MM-DD
    strategy: str = "rsi"  # rsi, macd
    initial_capital: float = 10000.0
    commission: float = 0.001
    strategy_params: Optional[Dict] = None


@router.post("/run")
async def run_backtest(request: BacktestRequest):
    """
    Run a backtest

    Args:
        request: Backtest configuration

    Returns:
        Backtest results with performance metrics
    """
    try:
        from app.services.backtesting.engine import BacktestEngine

        # Create engine
        engine = BacktestEngine(
            symbol=request.symbol,
            start_date=request.start_date,
            end_date=request.end_date,
            initial_capital=request.initial_capital,
            commission=request.commission
        )

        # Run backtest
        results = engine.run_backtest(
            strategy_name=request.strategy,
            strategy_params=request.strategy_params
        )

        return {
            "status": "success",
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Backtest failed: {str(e)}"
        )


@router.get("/strategies")
async def get_strategies():
    """
    Get list of available backtest strategies

    Returns:
        List of strategy names and descriptions
    """
    strategies = [
        {
            "name": "rsi",
            "description": "RSI-based strategy (buy when RSI < 30, sell when RSI > 70)",
            "parameters": {
                "rsi_period": "RSI calculation period (default: 14)",
                "rsi_oversold": "Oversold threshold (default: 30)",
                "rsi_overbought": "Overbought threshold (default: 70)",
                "stop_loss": "Stop loss percentage (default: 0.02)",
                "take_profit": "Take profit percentage (default: 0.04)"
            }
        },
        {
            "name": "macd",
            "description": "MACD crossover strategy",
            "parameters": {
                "fast_period": "Fast EMA period (default: 12)",
                "slow_period": "Slow EMA period (default: 26)",
                "signal_period": "Signal line period (default: 9)",
                "stop_loss": "Stop loss percentage (default: 0.02)",
                "take_profit": "Take profit percentage (default: 0.04)"
            }
        }
    ]

    return {"strategies": strategies}


@router.post("/compare")
async def compare_strategies(
    symbol: str,
    start_date: str,
    end_date: str,
    initial_capital: float = 10000.0
):
    """
    Compare all available strategies on the same data

    Args:
        symbol: Ticker symbol
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        initial_capital: Starting capital

    Returns:
        Comparison of all strategies
    """
    try:
        from app.services.backtesting.engine import BacktestEngine

        strategies = ['rsi', 'macd']
        results = {}

        for strategy_name in strategies:
            engine = BacktestEngine(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital
            )

            result = engine.run_backtest(strategy_name=strategy_name)
            results[strategy_name] = result

        # Find best strategy
        best_strategy = max(
            results.items(),
            key=lambda x: x[1]['total_return']
        )

        return {
            "symbol": symbol,
            "period": f"{start_date} to {end_date}",
            "results": results,
            "best_strategy": {
                "name": best_strategy[0],
                "return": best_strategy[1]['total_return']
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Strategy comparison failed: {str(e)}"
        )
