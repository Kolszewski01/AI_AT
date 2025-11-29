"""
Watchlist panel - display and manage symbols
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QLineEdit, QMessageBox
)
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
from typing import List, Dict
from src.utils.logger import get_logger

logger = get_logger("watchlist")


class WatchlistPanel(QWidget):
    """
    Watchlist panel widget

    Signals:
        symbol_selected: Emitted when a symbol is selected
        symbol_added: Emitted when a symbol is added
        symbol_removed: Emitted when a symbol is removed
    """

    symbol_selected = pyqtSignal(str)
    symbol_added = pyqtSignal(str)
    symbol_removed = pyqtSignal(str)

    def __init__(self, api_client, default_symbols: List[str]):
        super().__init__()
        self.api_client = api_client
        self.symbols = default_symbols.copy()
        self.quotes_cache = {}

        self.init_ui()
        self.setup_timer()

    def init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)

        # Header
        header = QLabel("📋 Watchlist")
        header.setStyleSheet("font-size: 14px; font-weight: bold; padding: 5px;")
        layout.addWidget(header)

        # Symbol list
        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        layout.addWidget(self.list_widget)

        # Add symbol controls
        add_layout = QHBoxLayout()
        self.symbol_input = QLineEdit()
        self.symbol_input.setPlaceholderText("Add symbol (e.g., AAPL)")
        self.symbol_input.returnPressed.connect(self.add_symbol)
        add_layout.addWidget(self.symbol_input)

        add_btn = QPushButton("+")
        add_btn.setMaximumWidth(40)
        add_btn.clicked.connect(self.add_symbol)
        add_layout.addWidget(add_btn)

        layout.addLayout(add_layout)

        # Remove button
        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self.remove_symbol)
        layout.addWidget(remove_btn)

        self.setLayout(layout)

        # Load initial symbols
        self.load_symbols()

    def setup_timer(self):
        """Setup timer for price updates"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_prices)
        self.update_timer.start(5000)  # Update every 5 seconds

    def load_symbols(self):
        """Load symbols into list"""
        self.list_widget.clear()
        for symbol in self.symbols:
            self.add_symbol_to_list(symbol)

    def add_symbol_to_list(self, symbol: str, price: float = None, change: float = None):
        """Add symbol to list widget"""
        if price is not None and change is not None:
            direction = "🟢" if change >= 0 else "🔴"
            text = f"{direction} {symbol}  ${price:.2f}  ({change:+.2f}%)"
        else:
            text = f"⚪ {symbol}  Loading..."

        item = QListWidgetItem(text)
        item.setData(Qt.ItemDataRole.UserRole, symbol)
        self.list_widget.addItem(item)

    def add_symbol(self):
        """Add new symbol to watchlist"""
        symbol = self.symbol_input.text().strip().upper()
        if not symbol:
            return

        if symbol in self.symbols:
            QMessageBox.warning(self, "Duplicate", f"{symbol} already in watchlist")
            return

        self.symbols.append(symbol)
        self.add_symbol_to_list(symbol)
        self.symbol_input.clear()
        self.symbol_added.emit(symbol)

        # Fetch price immediately
        self.update_quote(symbol)

    def remove_symbol(self):
        """Remove selected symbol from watchlist"""
        current = self.list_widget.currentItem()
        if not current:
            return

        symbol = current.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(
            self,
            "Remove Symbol",
            f"Remove {symbol} from watchlist?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.symbols.remove(symbol)
            self.list_widget.takeItem(self.list_widget.row(current))
            self.symbol_removed.emit(symbol)

    def on_item_clicked(self, item: QListWidgetItem):
        """Handle symbol selection"""
        symbol = item.data(Qt.ItemDataRole.UserRole)
        self.symbol_selected.emit(symbol)

    def update_prices(self):
        """Update prices for all symbols"""
        for symbol in self.symbols:
            self.update_quote(symbol)

    def update_quote(self, symbol: str):
        """Update quote for a specific symbol"""
        try:
            quote = self.api_client.get_quote(symbol)
            price = quote.get('current_price', 0)
            change = quote.get('change_percent', 0)

            self.quotes_cache[symbol] = quote
            logger.debug(f"Quote updated: {symbol} = ${price:.2f} ({change:+.2f}%)")

            # Update list item
            for i in range(self.list_widget.count()):
                item = self.list_widget.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == symbol:
                    direction = "🟢" if change >= 0 else "🔴"
                    item.setText(f"{direction} {symbol}  ${price:.2f}  ({change:+.2f}%)")
                    break

        except Exception as e:
            logger.error(f"Error updating quote for {symbol}: {e}")

    def get_current_symbol(self) -> str:
        """Get currently selected symbol"""
        current = self.list_widget.currentItem()
        if current:
            return current.data(Qt.ItemDataRole.UserRole)
        return self.symbols[0] if self.symbols else None
