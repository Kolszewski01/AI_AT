"""
Main window for desktop application
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QMenuBar, QMenu, QStatusBar, QMessageBox,
    QDockWidget
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction

from src.services.api_client import APIClient
from src.services.websocket_client import MarketDataStream, AlertsStream
from src.components.chart_widget import ChartWidget
from src.components.watchlist_panel import WatchlistPanel
from src.components.alerts_panel import AlertsPanel
from src.utils.logger import get_logger

logger = get_logger("main_window")


class MainWindow(QMainWindow):
    """Main application window"""

    def __init__(self, config):
        super().__init__()
        self.config = config
        logger.info("Initializing MainWindow")

        # Initialize API client
        self.api_client = APIClient(config.API_BASE_URL)

        # WebSocket clients
        self.market_stream = None
        self.alerts_stream = None

        self.init_ui()
        self.setup_connections()
        self.check_api_connection()
        logger.info("MainWindow initialization complete")

    def init_ui(self):
        """Initialize UI components"""
        self.setWindowTitle("AI Trading System")
        self.setGeometry(100, 100, self.config.WINDOW_WIDTH, self.config.WINDOW_HEIGHT)

        # Create menu bar
        self.create_menu_bar()

        # Create central widget with main layout
        central_widget = QWidget()
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)

        # Create main splitter (horizontal)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel - Watchlist
        self.watchlist = WatchlistPanel(
            self.api_client,
            self.config.DEFAULT_SYMBOLS
        )
        self.watchlist.setMaximumWidth(300)
        splitter.addWidget(self.watchlist)

        # Center - Chart
        self.chart_widget = ChartWidget(self.api_client, self.config)
        splitter.addWidget(self.chart_widget)

        # Right panel - Alerts
        self.alerts_panel = AlertsPanel(self.api_client)
        self.alerts_panel.setMaximumWidth(350)
        splitter.addWidget(self.alerts_panel)

        # Set splitter sizes (left, center, right)
        splitter.setSizes([250, 900, 300])

        main_layout.addWidget(splitter)
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        # Apply dark theme
        self.apply_dark_theme()

    def create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        refresh_action = QAction("&Refresh", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.refresh_all)
        file_menu.addAction(refresh_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        toggle_watchlist = QAction("Toggle &Watchlist", self)
        toggle_watchlist.triggered.connect(lambda: self.watchlist.setVisible(not self.watchlist.isVisible()))
        view_menu.addAction(toggle_watchlist)

        toggle_alerts = QAction("Toggle &Alerts", self)
        toggle_alerts.triggered.connect(lambda: self.alerts_panel.setVisible(not self.alerts_panel.isVisible()))
        view_menu.addAction(toggle_alerts)

        # Tools menu
        tools_menu = menubar.addMenu("&Tools")

        backtest_action = QAction("&Backtest...", self)
        backtest_action.triggered.connect(self.show_backtest_dialog)
        tools_menu.addAction(backtest_action)

        news_action = QAction("&News & Sentiment...", self)
        news_action.triggered.connect(self.show_news_dialog)
        tools_menu.addAction(news_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        api_docs_action = QAction("API &Documentation", self)
        api_docs_action.triggered.connect(self.show_api_docs)
        help_menu.addAction(api_docs_action)

    def setup_connections(self):
        """Setup signal/slot connections"""
        # Watchlist symbol selected -> load in chart
        self.watchlist.symbol_selected.connect(self.on_symbol_selected)

        # Load first symbol on startup
        QTimer.singleShot(500, self.load_initial_symbol)

    def load_initial_symbol(self):
        """Load first symbol from watchlist"""
        initial_symbol = self.watchlist.get_current_symbol()
        if initial_symbol:
            self.chart_widget.load_symbol(initial_symbol)
            self.start_websocket_stream(initial_symbol)

    def on_symbol_selected(self, symbol: str):
        """Handle symbol selection from watchlist"""
        logger.info(f"Symbol selected: {symbol}")
        self.status_bar.showMessage(f"Loading {symbol}...")
        self.chart_widget.load_symbol(symbol)

        # Restart WebSocket stream for new symbol
        self.start_websocket_stream(symbol)

        self.status_bar.showMessage(f"Loaded {symbol}", 3000)

    def start_websocket_stream(self, symbol: str):
        """Start WebSocket stream for market data"""
        # Stop existing stream
        if self.market_stream:
            self.market_stream.stop()

        # Start new stream
        self.market_stream = MarketDataStream(self.config.WS_BASE_URL, symbol)
        self.market_stream.message_received.connect(self.on_market_data_received)
        self.market_stream.connected.connect(lambda: self.status_bar.showMessage(f"🟢 WebSocket connected: {symbol}", 3000))
        self.market_stream.disconnected.connect(lambda: self.status_bar.showMessage("🔴 WebSocket disconnected", 3000))
        self.market_stream.error.connect(lambda err: self.status_bar.showMessage(f"❌ WebSocket error: {err}", 5000))
        self.market_stream.start()

    def start_alerts_stream(self):
        """Start WebSocket stream for alerts"""
        if self.alerts_stream:
            return  # Already running

        self.alerts_stream = AlertsStream(self.config.WS_BASE_URL)
        self.alerts_stream.message_received.connect(self.on_alert_received)
        self.alerts_stream.connected.connect(lambda: print("Alerts stream connected"))
        self.alerts_stream.start()

    def on_market_data_received(self, data: dict):
        """Handle market data from WebSocket"""
        # Update status bar with latest price
        if data.get('type') == 'market_data':
            symbol = data.get('symbol')
            price = data.get('price')
            if symbol and price:
                self.status_bar.showMessage(f"{symbol}: ${price:.2f}", 2000)

    def on_alert_received(self, data: dict):
        """Handle alert from WebSocket"""
        if data.get('type') == 'alert':
            self.alerts_panel.receive_websocket_alert(data)
            self.status_bar.showMessage(f"🔔 New alert: {data.get('message', '')}", 5000)

    def refresh_all(self):
        """Refresh all data"""
        self.status_bar.showMessage("Refreshing all data...")
        self.chart_widget.refresh_chart()
        self.watchlist.update_prices()
        self.alerts_panel.refresh_alerts()
        self.status_bar.showMessage("Refreshed", 2000)

    def check_api_connection(self):
        """Check if API is available"""
        logger.info("Checking API connection...")
        try:
            health = self.api_client.health_check()
            if health.get('status') == 'healthy':
                logger.info("API connection successful")
                self.status_bar.showMessage("✅ Connected to API", 3000)
                # Start alerts stream
                self.start_alerts_stream()
            else:
                logger.warning(f"API health check returned unexpected status: {health}")
                self.status_bar.showMessage("⚠️ API connection issue", 5000)
        except Exception as e:
            logger.error(f"API connection failed: {e}")
            self.status_bar.showMessage(f"❌ Cannot connect to API: {e}", 10000)
            QMessageBox.warning(
                self,
                "API Connection Error",
                f"Cannot connect to backend API at {self.config.API_BASE_URL}\n\n"
                f"Error: {e}\n\n"
                "Please make sure the backend is running."
            )

    def show_backtest_dialog(self):
        """Show backtest dialog"""
        QMessageBox.information(
            self,
            "Backtest",
            "Backtest dialog will be implemented in the next version.\n\n"
            "For now, use the API endpoint:\n"
            "POST /api/v1/backtest/run"
        )

    def show_news_dialog(self):
        """Show news & sentiment dialog"""
        current_symbol = self.watchlist.get_current_symbol()
        if not current_symbol:
            return

        try:
            sentiment = self.api_client.get_sentiment(current_symbol, days=7)

            news_count = sentiment.get('news_count', 0)
            sent = sentiment.get('sentiment', {})
            label = sent.get('label', 'neutral')
            score = sent.get('score', 0)

            QMessageBox.information(
                self,
                f"News & Sentiment - {current_symbol}",
                f"News Count (7 days): {news_count}\n\n"
                f"Sentiment: {label.upper()}\n"
                f"Score: {score:.2f} (-1 to +1)\n\n"
                f"Interpretation:\n"
                f"• Score > 0.3: Bullish sentiment\n"
                f"• Score < -0.3: Bearish sentiment\n"
                f"• Otherwise: Neutral\n\n"
                f"Full details available in API response."
            )
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to fetch sentiment: {e}")

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About AI Trading System",
            "<h2>AI Trading System</h2>"
            "<p><b>Version:</b> 0.1.0</p>"
            "<p><b>Author:</b> Sebastian2103</p>"
            "<p>Desktop application for AI-powered trading analysis.</p>"
            "<p>Features:</p>"
            "<ul>"
            "<li>Real-time market data</li>"
            "<li>Technical analysis (RSI, MACD, patterns)</li>"
            "<li>News sentiment analysis (FinBERT)</li>"
            "<li>Interactive charts with drawing tools</li>"
            "<li>Automated alerts</li>"
            "<li>Backtesting strategies</li>"
            "</ul>"
        )

    def show_api_docs(self):
        """Show API documentation info"""
        QMessageBox.information(
            self,
            "API Documentation",
            f"<h3>API Documentation</h3>"
            f"<p><b>Swagger UI:</b><br>"
            f"<a href='{self.config.API_BASE_URL.replace('/api/v1', '')}/api/docs'>"
            f"{self.config.API_BASE_URL.replace('/api/v1', '')}/api/docs</a></p>"
            f"<p><b>ReDoc:</b><br>"
            f"<a href='{self.config.API_BASE_URL.replace('/api/v1', '')}/api/redoc'>"
            f"{self.config.API_BASE_URL.replace('/api/v1', '')}/api/redoc</a></p>"
        )

    def apply_dark_theme(self):
        """Apply dark theme to application"""
        dark_stylesheet = """
        QMainWindow {
            background-color: #1e1e1e;
            color: #ffffff;
        }
        QWidget {
            background-color: #1e1e1e;
            color: #ffffff;
        }
        QListWidget {
            background-color: #2d2d2d;
            border: 1px solid #3d3d3d;
            border-radius: 4px;
            padding: 5px;
        }
        QListWidget::item {
            padding: 5px;
            border-radius: 3px;
        }
        QListWidget::item:selected {
            background-color: #4d4d4d;
        }
        QListWidget::item:hover {
            background-color: #3d3d3d;
        }
        QPushButton {
            background-color: #0d7377;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #14a085;
        }
        QPushButton:pressed {
            background-color: #0a5c5f;
        }
        QLineEdit {
            background-color: #2d2d2d;
            border: 1px solid #3d3d3d;
            border-radius: 4px;
            padding: 5px;
            color: white;
        }
        QComboBox {
            background-color: #2d2d2d;
            border: 1px solid #3d3d3d;
            border-radius: 4px;
            padding: 5px;
            color: white;
        }
        QComboBox::drop-down {
            border: none;
        }
        QComboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid #888;
        }
        QTextEdit {
            background-color: #2d2d2d;
            border: 1px solid #3d3d3d;
            border-radius: 4px;
            padding: 5px;
            color: white;
        }
        QLabel {
            color: #ffffff;
        }
        QMenuBar {
            background-color: #2d2d2d;
            color: white;
        }
        QMenuBar::item:selected {
            background-color: #3d3d3d;
        }
        QMenu {
            background-color: #2d2d2d;
            color: white;
            border: 1px solid #3d3d3d;
        }
        QMenu::item:selected {
            background-color: #3d3d3d;
        }
        QStatusBar {
            background-color: #2d2d2d;
            color: #aaa;
        }
        """
        self.setStyleSheet(dark_stylesheet)

    def closeEvent(self, event):
        """Handle window close event"""
        logger.info("Application closing...")
        # Stop WebSocket streams
        if self.market_stream:
            self.market_stream.stop()
        if self.alerts_stream:
            self.alerts_stream.stop()
        logger.info("Application closed")
        event.accept()
