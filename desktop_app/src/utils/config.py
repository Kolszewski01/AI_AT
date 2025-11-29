"""
Configuration manager for desktop application
"""
import os
from pathlib import Path
from dotenv import load_dotenv


class Config:
    """Application configuration"""

    def __init__(self):
        # Load .env file if exists
        env_path = Path(__file__).parent.parent.parent.parent / '.env'
        if env_path.exists():
            load_dotenv(env_path)

        # API settings
        self.API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000/api/v1')
        self.WS_BASE_URL = os.getenv('WS_BASE_URL', 'ws://localhost:8000')

        # Application settings
        self.WINDOW_WIDTH = int(os.getenv('WINDOW_WIDTH', '1400'))
        self.WINDOW_HEIGHT = int(os.getenv('WINDOW_HEIGHT', '900'))
        self.THEME = os.getenv('THEME', 'dark')

        # Chart settings
        self.DEFAULT_INTERVAL = os.getenv('DEFAULT_INTERVAL', '1h')
        self.DEFAULT_PERIOD = os.getenv('DEFAULT_PERIOD', '7d')
        self.CHART_THEME = os.getenv('CHART_THEME', 'plotly_dark')

        # Update intervals (milliseconds)
        self.PRICE_UPDATE_INTERVAL = int(os.getenv('PRICE_UPDATE_INTERVAL', '5000'))  # 5s
        self.CHART_UPDATE_INTERVAL = int(os.getenv('CHART_UPDATE_INTERVAL', '30000'))  # 30s

        # Default symbols
        self.DEFAULT_SYMBOLS = os.getenv(
            'DEFAULT_SYMBOLS',
            '^GDAXI,^GSPC,BTC-USD,ETH-USD,EURUSD=X'
        ).split(',')

    def __repr__(self):
        return f"Config(API={self.API_BASE_URL}, WS={self.WS_BASE_URL})"
