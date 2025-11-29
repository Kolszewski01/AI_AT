"""
Alerts panel - display and manage trading alerts
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QTextEdit
)
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QColor
from datetime import datetime
from typing import List, Dict
from src.utils.logger import get_logger

logger = get_logger("alerts")


class AlertsPanel(QWidget):
    """
    Alerts panel widget

    Signals:
        alert_dismissed: Emitted when an alert is dismissed
    """

    alert_dismissed = pyqtSignal(str)

    def __init__(self, api_client):
        super().__init__()
        self.api_client = api_client
        self.alerts = []

        self.init_ui()
        self.setup_timer()

    def init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)

        # Header
        header_layout = QHBoxLayout()
        header = QLabel("🔔 Alerts & Signals")
        header.setStyleSheet("font-size: 14px; font-weight: bold; padding: 5px;")
        header_layout.addWidget(header)

        # Refresh button
        refresh_btn = QPushButton("🔄")
        refresh_btn.setMaximumWidth(40)
        refresh_btn.clicked.connect(self.refresh_alerts)
        header_layout.addWidget(refresh_btn)

        layout.addLayout(header_layout)

        # Alerts list
        self.alerts_list = QListWidget()
        self.alerts_list.itemDoubleClicked.connect(self.show_alert_details)
        layout.addWidget(self.alerts_list)

        # Details view (hidden by default)
        self.details_label = QLabel("Alert Details:")
        self.details_label.setVisible(False)
        layout.addWidget(self.details_label)

        self.details_view = QTextEdit()
        self.details_view.setReadOnly(True)
        self.details_view.setMaximumHeight(150)
        self.details_view.setVisible(False)
        layout.addWidget(self.details_view)

        # Clear button
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self.clear_alerts)
        layout.addWidget(clear_btn)

        self.setLayout(layout)

        # Load initial alerts
        self.refresh_alerts()

    def setup_timer(self):
        """Setup timer for alerts refresh"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.refresh_alerts)
        self.update_timer.start(30000)  # Update every 30 seconds

    def refresh_alerts(self):
        """Refresh alerts from API"""
        try:
            response = self.api_client.get_alerts(status='active')
            self.alerts = response.get('alerts', [])
            logger.debug(f"Alerts refreshed: {len(self.alerts)} active alerts")
            self.update_list()
        except Exception as e:
            logger.error(f"Error refreshing alerts: {e}")

    def update_list(self):
        """Update alerts list widget"""
        self.alerts_list.clear()

        for alert in self.alerts:
            symbol = alert.get('symbol', 'UNKNOWN')
            severity = alert.get('severity', 'medium')
            message = alert.get('message', 'No message')
            timestamp = alert.get('created_at', '')

            # Emoji based on severity
            if severity == 'critical':
                emoji = "🚨"
            elif severity == 'high':
                emoji = "⚠️"
            elif severity == 'medium':
                emoji = "ℹ️"
            else:
                emoji = "💡"

            # Format time
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    time_str = dt.strftime('%H:%M')
                except:
                    time_str = ''
            else:
                time_str = ''

            text = f"{emoji} [{time_str}] {symbol}: {message[:50]}"

            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, alert)

            # Color based on severity
            if severity == 'critical':
                item.setForeground(QColor(255, 100, 100))
            elif severity == 'high':
                item.setForeground(QColor(255, 200, 100))

            self.alerts_list.addItem(item)

    def show_alert_details(self, item: QListWidgetItem):
        """Show detailed alert information"""
        alert = item.data(Qt.ItemDataRole.UserRole)

        details = f"""
Symbol: {alert.get('symbol', 'N/A')}
Type: {alert.get('alert_type', 'N/A')}
Severity: {alert.get('severity', 'N/A')}
Message: {alert.get('message', 'N/A')}

Conditions: {alert.get('conditions', {})}

Channels: {', '.join(alert.get('channels', []))}
Created: {alert.get('created_at', 'N/A')}
Status: {alert.get('status', 'N/A')}
        """

        self.details_view.setText(details.strip())
        self.details_label.setVisible(True)
        self.details_view.setVisible(True)

    def add_alert(self, alert: Dict):
        """Add a new alert to the list"""
        self.alerts.insert(0, alert)  # Add to beginning
        self.update_list()

    def clear_alerts(self):
        """Clear all alerts"""
        self.alerts.clear()
        self.alerts_list.clear()
        self.details_label.setVisible(False)
        self.details_view.setVisible(False)

    def receive_websocket_alert(self, alert_data: Dict):
        """Handle alert received from WebSocket"""
        logger.info(f"WebSocket alert received: {alert_data.get('message', 'No message')}")
        # Add to list
        self.add_alert(alert_data)
