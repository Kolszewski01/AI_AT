"""
Backtesting engine using backtrader
"""
import logging
from typing import Dict, Optional, List
from datetime import datetime
import backtrader as bt
import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


class RSIStrategy(bt.Strategy):
    """
    Simple RSI-based trading strategy

    Buy when RSI < 30 (oversold)
    Sell when RSI > 70 (overbought)
    """
    params = (
        ('rsi_period', 14),
        ('rsi_overbought', 70),
        ('rsi_oversold', 30),
        ('stop_loss', 0.02),  # 2% stop loss
        ('take_profit', 0.04),  # 4% take profit
    )

    def __init__(self):
        # RSI indicator
        self.rsi = bt.indicators.RSI(
            self.data.close,
            period=self.params.rsi_period
        )

        # Track orders
        self.order = None
        self.entry_price = None

    def log(self, txt, dt=None):
        """Logging function"""
        dt = dt or self.datas[0].datetime.date(0)
        logger.info(f'{dt.isoformat()} {txt}')

    def notify_order(self, order):
        """Notify when order is executed"""
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED, Price: {order.executed.price:.2f}')
                self.entry_price = order.executed.price
            elif order.issell():
                self.log(f'SELL EXECUTED, Price: {order.executed.price:.2f}')
                if self.entry_price:
                    pnl = order.executed.price - self.entry_price
                    pnl_pct = (pnl / self.entry_price) * 100
                    self.log(f'P&L: {pnl:.2f} ({pnl_pct:.2f}%)')

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

    def next(self):
        """Execute on each bar"""
        # Check if we have an order pending
        if self.order:
            return

        # Check if we are in the market
        if not self.position:
            # Buy signal: RSI < oversold
            if self.rsi[0] < self.params.rsi_oversold:
                self.log(f'BUY CREATE, RSI: {self.rsi[0]:.2f}')
                self.order = self.buy()

        else:
            # Sell signal: RSI > overbought
            if self.rsi[0] > self.params.rsi_overbought:
                self.log(f'SELL CREATE, RSI: {self.rsi[0]:.2f}')
                self.order = self.sell()

            # Stop loss / Take profit
            current_price = self.data.close[0]
            if self.entry_price:
                pnl_pct = (current_price - self.entry_price) / self.entry_price

                if pnl_pct <= -self.params.stop_loss:
                    self.log(f'STOP LOSS HIT: {pnl_pct*100:.2f}%')
                    self.order = self.sell()

                elif pnl_pct >= self.params.take_profit:
                    self.log(f'TAKE PROFIT HIT: {pnl_pct*100:.2f}%')
                    self.order = self.sell()


class MACDStrategy(bt.Strategy):
    """
    MACD-based trading strategy

    Buy when MACD crosses above signal line
    Sell when MACD crosses below signal line
    """
    params = (
        ('fast_period', 12),
        ('slow_period', 26),
        ('signal_period', 9),
        ('stop_loss', 0.02),
        ('take_profit', 0.04),
    )

    def __init__(self):
        # MACD indicator
        self.macd = bt.indicators.MACD(
            self.data.close,
            period_me1=self.params.fast_period,
            period_me2=self.params.slow_period,
            period_signal=self.params.signal_period
        )

        # Crossover indicator
        self.crossover = bt.indicators.CrossOver(self.macd.macd, self.macd.signal)

        self.order = None
        self.entry_price = None

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        logger.info(f'{dt.isoformat()} {txt}')

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED, Price: {order.executed.price:.2f}')
                self.entry_price = order.executed.price
            elif order.issell():
                self.log(f'SELL EXECUTED, Price: {order.executed.price:.2f}')

        self.order = None

    def next(self):
        if self.order:
            return

        if not self.position:
            # Buy signal: MACD crosses above signal
            if self.crossover > 0:
                self.log(f'BUY CREATE, MACD: {self.macd.macd[0]:.4f}')
                self.order = self.buy()

        else:
            # Sell signal: MACD crosses below signal
            if self.crossover < 0:
                self.log(f'SELL CREATE, MACD: {self.macd.macd[0]:.4f}')
                self.order = self.sell()

            # Stop loss / Take profit
            current_price = self.data.close[0]
            if self.entry_price:
                pnl_pct = (current_price - self.entry_price) / self.entry_price

                if pnl_pct <= -self.params.stop_loss:
                    self.log(f'STOP LOSS HIT: {pnl_pct*100:.2f}%')
                    self.order = self.sell()

                elif pnl_pct >= self.params.take_profit:
                    self.log(f'TAKE PROFIT HIT: {pnl_pct*100:.2f}%')
                    self.order = self.sell()


class BacktestEngine:
    """Backtesting engine wrapper for backtrader"""

    STRATEGIES = {
        'rsi': RSIStrategy,
        'macd': MACDStrategy,
    }

    def __init__(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        initial_capital: float = 10000.0,
        commission: float = 0.001
    ):
        """
        Initialize backtest engine

        Args:
            symbol: Ticker symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            initial_capital: Starting capital
            commission: Commission percentage (0.001 = 0.1%)
        """
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.commission = commission
        self.cerebro = None
        self.results = None

    def load_data(self) -> pd.DataFrame:
        """Load historical data for backtesting"""
        logger.info(f"Loading data for {self.symbol} from {self.start_date} to {self.end_date}")

        ticker = yf.Ticker(self.symbol)
        df = ticker.history(start=self.start_date, end=self.end_date, interval="1d")

        if df.empty:
            raise ValueError(f"No data available for {self.symbol}")

        logger.info(f"Loaded {len(df)} bars")
        return df

    def run_backtest(
        self,
        strategy_name: str = 'rsi',
        strategy_params: Optional[Dict] = None
    ) -> Dict:
        """
        Run backtest with specified strategy

        Args:
            strategy_name: Name of strategy ('rsi', 'macd')
            strategy_params: Optional strategy parameters

        Returns:
            Backtest results dictionary
        """
        if strategy_name not in self.STRATEGIES:
            raise ValueError(f"Unknown strategy: {strategy_name}")

        # Initialize Cerebro
        self.cerebro = bt.Cerebro()

        # Load data
        df = self.load_data()

        # Convert to backtrader format
        data = bt.feeds.PandasData(dataname=df)
        self.cerebro.adddata(data)

        # Add strategy
        strategy_class = self.STRATEGIES[strategy_name]
        if strategy_params:
            self.cerebro.addstrategy(strategy_class, **strategy_params)
        else:
            self.cerebro.addstrategy(strategy_class)

        # Set initial capital
        self.cerebro.broker.setcash(self.initial_capital)

        # Set commission
        self.cerebro.broker.setcommission(commission=self.commission)

        # Add analyzers
        self.cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        self.cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        self.cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        self.cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')

        # Run backtest
        logger.info(f"Starting backtest with {strategy_name} strategy")
        logger.info(f"Initial Capital: ${self.initial_capital:.2f}")

        start_value = self.cerebro.broker.getvalue()
        self.results = self.cerebro.run()
        end_value = self.cerebro.broker.getvalue()

        # Extract results
        strat = self.results[0]

        # Get analyzer results
        sharpe = strat.analyzers.sharpe.get_analysis()
        drawdown = strat.analyzers.drawdown.get_analysis()
        returns = strat.analyzers.returns.get_analysis()
        trades = strat.analyzers.trades.get_analysis()

        total_return = ((end_value - start_value) / start_value) * 100
        total_pnl = end_value - start_value

        results = {
            "symbol": self.symbol,
            "strategy": strategy_name,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "initial_capital": self.initial_capital,
            "final_capital": end_value,
            "total_return": total_return,
            "total_pnl": total_pnl,
            "sharpe_ratio": sharpe.get('sharperatio', None),
            "max_drawdown": drawdown.get('max', {}).get('drawdown', 0),
            "total_trades": trades.get('total', {}).get('total', 0),
            "won_trades": trades.get('won', {}).get('total', 0),
            "lost_trades": trades.get('lost', {}).get('total', 0),
            "win_rate": (trades.get('won', {}).get('total', 0) / trades.get('total', {}).get('total', 1)) * 100 if trades.get('total', {}).get('total', 0) > 0 else 0,
        }

        logger.info(f"Backtest completed!")
        logger.info(f"Final Capital: ${end_value:.2f}")
        logger.info(f"Total Return: {total_return:.2f}%")
        logger.info(f"Sharpe Ratio: {results['sharpe_ratio']}")
        logger.info(f"Max Drawdown: {results['max_drawdown']:.2f}%")
        logger.info(f"Win Rate: {results['win_rate']:.2f}%")

        return results

    def plot_results(self, filename: Optional[str] = None):
        """
        Plot backtest results

        Args:
            filename: Optional filename to save plot
        """
        if not self.cerebro:
            raise ValueError("Run backtest first")

        # Note: This requires matplotlib with GUI backend
        # For server environments, you might want to save to file instead
        self.cerebro.plot(style='candlestick')


# Example usage
if __name__ == "__main__":
    # Test backtest engine
    engine = BacktestEngine(
        symbol="AAPL",
        start_date="2023-01-01",
        end_date="2024-01-01",
        initial_capital=10000.0
    )

    # Run RSI strategy
    print("\n" + "=" * 50)
    print("RSI Strategy Backtest")
    print("=" * 50)
    results_rsi = engine.run_backtest(strategy_name='rsi')

    # Run MACD strategy
    print("\n" + "=" * 50)
    print("MACD Strategy Backtest")
    print("=" * 50)
    engine2 = BacktestEngine(
        symbol="AAPL",
        start_date="2023-01-01",
        end_date="2024-01-01",
        initial_capital=10000.0
    )
    results_macd = engine2.run_backtest(strategy_name='macd')

    # Compare
    print("\n" + "=" * 50)
    print("Comparison")
    print("=" * 50)
    print(f"RSI Return: {results_rsi['total_return']:.2f}%")
    print(f"MACD Return: {results_macd['total_return']:.2f}%")
