"""
Chart widget using Plotly for interactive candlestick charts
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QComboBox, QLabel, QToolBar, QSizePolicy
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import Qt, QUrl, QTimer
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional
from src.utils.logger import get_logger

logger = get_logger("chart_widget")


class ChartWidget(QWidget):
    """
    Interactive chart widget with Plotly

    Features:
    - Candlestick chart
    - Volume bars
    - Technical indicators overlay
    - Drawing tools (Fibonacci, trendlines)
    - Interactive zoom and pan
    """

    def __init__(self, api_client, config):
        super().__init__()
        self.api_client = api_client
        self.config = config

        self.current_symbol = None
        self.current_interval = config.DEFAULT_INTERVAL
        self.current_period = config.DEFAULT_PERIOD

        self.ohlcv_data = None
        self.indicators = None

        # Drawing tools data
        self.fibonacci_lines = []
        self.trend_lines = []
        self.horizontal_lines = []

        self.init_ui()

    def init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Toolbar
        toolbar = self.create_toolbar()
        layout.addWidget(toolbar)

        # Chart view (Plotly in WebEngine)
        self.chart_view = QWebEngineView()
        self.chart_view.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        layout.addWidget(self.chart_view)

        self.setLayout(layout)

        # Auto-update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.refresh_chart)
        self.update_timer.start(self.config.CHART_UPDATE_INTERVAL)

    def create_toolbar(self) -> QWidget:
        """Create chart toolbar with controls"""
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(5, 5, 5, 5)

        # Symbol label
        self.symbol_label = QLabel("Symbol: -")
        self.symbol_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        toolbar_layout.addWidget(self.symbol_label)

        toolbar_layout.addStretch()

        # Interval selector
        toolbar_layout.addWidget(QLabel("Interval:"))
        self.interval_combo = QComboBox()
        self.interval_combo.addItems(['1m', '5m', '15m', '1h', '4h', '1d'])
        self.interval_combo.setCurrentText(self.current_interval)
        self.interval_combo.currentTextChanged.connect(self.on_interval_changed)
        toolbar_layout.addWidget(self.interval_combo)

        # Period selector
        toolbar_layout.addWidget(QLabel("Period:"))
        self.period_combo = QComboBox()
        self.period_combo.addItems(['1d', '5d', '1mo', '3mo', '6mo', '1y'])
        self.period_combo.setCurrentText(self.current_period)
        self.period_combo.currentTextChanged.connect(self.on_period_changed)
        toolbar_layout.addWidget(self.period_combo)

        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_chart)
        toolbar_layout.addWidget(refresh_btn)

        # Drawing tools
        toolbar_layout.addWidget(QLabel("|"))

        fib_btn = QPushButton("📐 Fibonacci")
        fib_btn.clicked.connect(self.add_fibonacci)
        toolbar_layout.addWidget(fib_btn)

        line_btn = QPushButton("📏 Trendline")
        line_btn.clicked.connect(self.add_trendline)
        toolbar_layout.addWidget(line_btn)

        h_line_btn = QPushButton("━ H-Line")
        h_line_btn.clicked.connect(self.add_horizontal_line)
        toolbar_layout.addWidget(h_line_btn)

        clear_btn = QPushButton("🗑️ Clear")
        clear_btn.clicked.connect(self.clear_drawings)
        toolbar_layout.addWidget(clear_btn)

        toolbar.setLayout(toolbar_layout)
        return toolbar

    def load_symbol(self, symbol: str):
        """Load and display data for a symbol"""
        logger.info(f"Loading symbol: {symbol}")
        self.current_symbol = symbol
        self.symbol_label.setText(f"Symbol: {symbol}")
        self.load_data()

    def load_data(self):
        """Load OHLCV data and indicators"""
        if not self.current_symbol:
            return

        logger.debug(f"Loading data: symbol={self.current_symbol}, interval={self.current_interval}, period={self.current_period}")
        try:
            # Load OHLCV
            ohlcv_response = self.api_client.get_ohlcv(
                self.current_symbol,
                interval=self.current_interval,
                period=self.current_period
            )
            self.ohlcv_data = pd.DataFrame(ohlcv_response['data'])
            logger.debug(f"OHLCV data loaded: {len(self.ohlcv_data)} rows")

            # Load indicators
            indicators_response = self.api_client.get_indicators(
                self.current_symbol,
                interval=self.current_interval,
                period=self.current_period
            )
            self.indicators = indicators_response
            logger.debug("Indicators loaded")

            # Update chart
            self.update_chart()
            logger.info(f"Chart updated for {self.current_symbol}")

        except Exception as e:
            logger.error(f"Error loading data for {self.current_symbol}: {e}")
            self.symbol_label.setText(f"Symbol: {self.current_symbol} (Error)")

    def update_chart(self):
        """Update chart with current data"""
        if self.ohlcv_data is None or self.ohlcv_data.empty:
            return

        # Create figure with subplots (price + volume)
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.7, 0.3],
            subplot_titles=(f'{self.current_symbol} - {self.current_interval}', 'Volume')
        )

        # Candlestick chart
        candlestick = go.Candlestick(
            x=self.ohlcv_data['Date'],
            open=self.ohlcv_data['Open'],
            high=self.ohlcv_data['High'],
            low=self.ohlcv_data['Low'],
            close=self.ohlcv_data['Close'],
            name='Price',
            increasing_line_color='#26a69a',
            decreasing_line_color='#ef5350'
        )
        fig.add_trace(candlestick, row=1, col=1)

        # Volume bars
        colors = ['#26a69a' if c >= o else '#ef5350'
                  for c, o in zip(self.ohlcv_data['Close'], self.ohlcv_data['Open'])]

        volume = go.Bar(
            x=self.ohlcv_data['Date'],
            y=self.ohlcv_data['Volume'],
            name='Volume',
            marker_color=colors,
            showlegend=False
        )
        fig.add_trace(volume, row=2, col=1)

        # Add drawing tools
        self.add_drawings_to_chart(fig)

        # Update layout
        fig.update_layout(
            template=self.config.CHART_THEME,
            xaxis_rangeslider_visible=False,
            height=700,
            margin=dict(l=50, r=50, t=50, b=50),
            hovermode='x unified',
            dragmode='zoom'
        )

        fig.update_xaxes(title_text="Date", row=2, col=1)
        fig.update_yaxes(title_text="Price", row=1, col=1)
        fig.update_yaxes(title_text="Volume", row=2, col=1)

        # Convert to HTML and display
        html = fig.to_html(include_plotlyjs='cdn')
        self.chart_view.setHtml(html)

    def add_drawings_to_chart(self, fig):
        """Add drawing tools annotations to chart"""
        if not self.ohlcv_data.empty:
            # Add Fibonacci retracement levels
            for fib in self.fibonacci_lines:
                self.draw_fibonacci(fig, fib['start'], fib['end'])

            # Add trendlines
            for line in self.trend_lines:
                self.draw_trendline(fig, line['start'], line['end'])

            # Add horizontal lines
            for h_line in self.horizontal_lines:
                self.draw_horizontal_line(fig, h_line['price'], h_line['label'])

    def draw_fibonacci(self, fig, start_idx: int, end_idx: int):
        """Draw Fibonacci retracement levels"""
        if start_idx >= len(self.ohlcv_data) or end_idx >= len(self.ohlcv_data):
            return

        start_price = self.ohlcv_data.iloc[start_idx]['High']
        end_price = self.ohlcv_data.iloc[end_idx]['Low']

        diff = start_price - end_price
        fib_levels = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1]

        for level in fib_levels:
            price = end_price + diff * level
            fig.add_hline(
                y=price,
                line=dict(color='rgba(255, 215, 0, 0.5)', width=1, dash='dash'),
                annotation_text=f"{level:.1%}",
                row=1, col=1
            )

    def draw_trendline(self, fig, start_idx: int, end_idx: int):
        """Draw trendline between two points"""
        if start_idx >= len(self.ohlcv_data) or end_idx >= len(self.ohlcv_data):
            return

        fig.add_shape(
            type="line",
            x0=self.ohlcv_data.iloc[start_idx]['Date'],
            y0=self.ohlcv_data.iloc[start_idx]['Close'],
            x1=self.ohlcv_data.iloc[end_idx]['Date'],
            y1=self.ohlcv_data.iloc[end_idx]['Close'],
            line=dict(color='cyan', width=2),
            row=1, col=1
        )

    def draw_horizontal_line(self, fig, price: float, label: str = ""):
        """Draw horizontal support/resistance line"""
        fig.add_hline(
            y=price,
            line=dict(color='yellow', width=2),
            annotation_text=label,
            row=1, col=1
        )

    def add_fibonacci(self):
        """Add Fibonacci retracement (simplified - uses last 20% and 80% of data)"""
        if self.ohlcv_data is None or self.ohlcv_data.empty:
            return

        length = len(self.ohlcv_data)
        start_idx = int(length * 0.2)
        end_idx = int(length * 0.8)

        self.fibonacci_lines.append({
            'start': start_idx,
            'end': end_idx
        })

        self.update_chart()

    def add_trendline(self):
        """Add trendline (simplified - uses last 30% of data)"""
        if self.ohlcv_data is None or self.ohlcv_data.empty:
            return

        length = len(self.ohlcv_data)
        start_idx = int(length * 0.7)
        end_idx = length - 1

        self.trend_lines.append({
            'start': start_idx,
            'end': end_idx
        })

        self.update_chart()

    def add_horizontal_line(self):
        """Add horizontal line at current price"""
        if self.ohlcv_data is None or self.ohlcv_data.empty:
            return

        current_price = self.ohlcv_data.iloc[-1]['Close']

        self.horizontal_lines.append({
            'price': current_price,
            'label': f"Level {current_price:.2f}"
        })

        self.update_chart()

    def clear_drawings(self):
        """Clear all drawing tools"""
        self.fibonacci_lines.clear()
        self.trend_lines.clear()
        self.horizontal_lines.clear()
        self.update_chart()

    def on_interval_changed(self, interval: str):
        """Handle interval change"""
        self.current_interval = interval
        self.load_data()

    def on_period_changed(self, period: str):
        """Handle period change"""
        self.current_period = period
        self.load_data()

    def refresh_chart(self):
        """Refresh chart data"""
        if self.current_symbol:
            self.load_data()
