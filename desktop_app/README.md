# 🖥️ AI Trading System - Desktop Application

Professional desktop application for AI-powered trading analysis built with PyQt6.

## ✨ Features

### 📊 Interactive Charts
- **Plotly-powered candlestick charts** with zoom and pan
- **Real-time data updates** via WebSocket
- **Multi-timeframe support** (1m, 5m, 15m, 1h, 4h, 1d)
- **Volume bars** with price-color correlation

### 📐 Drawing Tools
- **Fibonacci Retracement** - automatic levels (0%, 23.6%, 38.2%, 50%, 61.8%, 78.6%, 100%)
- **Trendlines** - draw lines between key points
- **Horizontal Lines** - support/resistance levels
- **One-click clear** for all drawings

### 📋 Watchlist Panel
- **Add/remove symbols** dynamically
- **Real-time price updates** every 5 seconds
- **Color-coded** price changes (green/red)
- **Quick symbol switching**

### 🔔 Alerts Panel
- **Real-time alerts** from backend via WebSocket
- **Severity levels** (critical, high, medium, low)
- **Detailed alert view** with conditions
- **Auto-refresh** every 30 seconds

### 🌐 WebSocket Integration
- **Market data stream** - real-time prices
- **Alerts stream** - instant notifications
- **Auto-reconnect** on connection loss

### 🎨 Modern UI
- **Dark theme** optimized for long sessions
- **Resizable panels** with splitters
- **Status bar** with connection status
- **Keyboard shortcuts** (F5 to refresh, Ctrl+Q to quit)

## 🚀 Installation

### Prerequisites
- Python 3.11+
- Backend API running at `http://localhost:8000`

### Setup

```bash
cd desktop_app

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run application
python main.py
```

### Configuration

Create/edit `.env` file in project root:

```env
# API endpoints
API_BASE_URL=http://localhost:8000/api/v1
WS_BASE_URL=ws://localhost:8000

# Window settings
WINDOW_WIDTH=1400
WINDOW_HEIGHT=900
THEME=dark

# Chart settings
DEFAULT_INTERVAL=1h
DEFAULT_PERIOD=7d
CHART_THEME=plotly_dark

# Update intervals (milliseconds)
PRICE_UPDATE_INTERVAL=5000
CHART_UPDATE_INTERVAL=30000

# Default symbols (comma-separated)
DEFAULT_SYMBOLS=^GDAXI,^GSPC,BTC-USD,ETH-USD,EURUSD=X
```

## 📖 Usage

### Basic Workflow

1. **Start Backend API**
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

2. **Launch Desktop App**
   ```bash
   cd desktop_app
   python main.py
   ```

3. **Select Symbol**
   - Click on a symbol in the Watchlist panel
   - Chart automatically loads and updates

4. **Analyze**
   - Use timeframe selectors (toolbar)
   - Add drawing tools (Fibonacci, trendlines, etc.)
   - Monitor real-time price updates

5. **Monitor Alerts**
   - Alerts panel shows active alerts
   - Double-click for details
   - WebSocket delivers real-time alerts

### Drawing Tools

**Fibonacci Retracement:**
- Click "📐 Fibonacci" button
- Automatically draws levels on last major move
- Shows key retracement levels (23.6%, 38.2%, 50%, 61.8%, etc.)

**Trendline:**
- Click "📏 Trendline" button
- Draws trend based on recent price action
- Useful for identifying trend direction

**Horizontal Line:**
- Click "━ H-Line" button
- Places line at current price
- Great for marking key levels

**Clear All:**
- Click "🗑️ Clear" to remove all drawings

### Keyboard Shortcuts

- **F5** - Refresh all data
- **Ctrl+Q** - Quit application

### Menu Options

**File**
- Refresh - Update all data
- Exit - Close application

**View**
- Toggle Watchlist - Show/hide watchlist panel
- Toggle Alerts - Show/hide alerts panel

**Tools**
- Backtest - Run strategy backtests (coming soon)
- News & Sentiment - View sentiment for current symbol

**Help**
- About - Application information
- API Documentation - Link to API docs

## 🏗️ Architecture

```
desktop_app/
├── main.py                    # Entry point
├── requirements.txt           # Dependencies
├── src/
│   ├── components/
│   │   ├── main_window.py     # Main application window
│   │   ├── chart_widget.py    # Plotly chart component
│   │   ├── watchlist_panel.py # Watchlist sidebar
│   │   └── alerts_panel.py    # Alerts w
│   ├── services/
│   │   ├── api_client.py      # REST API client
│   │   └── websocket_client.py # WebSocket client
│   └── utils/
│       └── config.py          # Configuration management
└── assets/                    # Icons, images (future)
```

### Component Communication

```
MainWindow
├── WatchlistPanel → symbol_selected → ChartWidget.load_symbol()
├── ChartWidget ← API Client → Backend API
├── AlertsPanel ← WebSocket → Backend Alerts Stream
└── MarketDataStream ← WebSocket → Backend Market Stream
```

## 🎨 Customization

### Themes

The app uses a dark theme by default. To customize:

1. Edit `main_window.py`
2. Modify `apply_dark_theme()` method
3. Change colors in stylesheet

### Chart Theme

Available Plotly themes:
- `plotly_dark` (default)
- `plotly`
- `ggplot2`
- `seaborn`
- `simple_white`

Change in `.env`:
```env
CHART_THEME=plotly
```

### Default Symbols

Edit in `.env`:
```env
DEFAULT_SYMBOLS=AAPL,GOOGL,MSFT,TSLA
```

## 🔧 Development

### Running in Development Mode

```bash
# With auto-reload (not available for PyQt6, restart manually)
python main.py
```

### Code Style

```bash
# Format code
black src/

# Type checking (if using mypy)
mypy src/
```

## 📝 API Integration

The desktop app integrates with all backend endpoints:

**Market Data:**
- `GET /api/v1/market/symbols`
- `GET /api/v1/market/ohlcv/{symbol}`
- `GET /api/v1/market/quote/{symbol}`

**Analysis:**
- `GET /api/v1/analysis/indicators/{symbol}`
- `GET /api/v1/analysis/patterns/{symbol}`
- `GET /api/v1/analysis/signal/{symbol}`

**Alerts:**
- `GET /api/v1/alerts`
- `POST /api/v1/alerts/create`
- `DELETE /api/v1/alerts/{id}`

**News:**
- `GET /api/v1/news/{symbol}`
- `GET /api/v1/news/sentiment/{symbol}`

**WebSocket:**
- `WS /ws/market/{symbol}` - Real-time market data
- `WS /ws/alerts` - Real-time alerts

## ⚠️ Troubleshooting

### Cannot connect to API

**Error:** `❌ Cannot connect to API`

**Solution:**
1. Ensure backend is running: `uvicorn app.main:app --reload`
2. Check API_BASE_URL in `.env`
3. Test backend: `curl http://localhost:8000/health`

### WebSocket connection failed

**Error:** `🔴 WebSocket disconnected`

**Solution:**
1. Backend must be running
2. Check WS_BASE_URL in `.env`
3. Ensure WebSocket endpoints are available

### Chart not loading

**Possible causes:**
- Symbol not found
- No data for selected timeframe
- API error

**Solution:**
- Check console/logs for errors
- Try different symbol
- Verify backend data availability

### Drawing tools not appearing

**Solution:**
- Ensure chart has data loaded
- Try clearing and re-adding
- Check that OHLCV data is not empty

## 🚀 Future Enhancements

- [ ] Save/load drawing templates
- [ ] Custom indicator overlays
- [ ] Multi-chart layout
- [ ] Trade journal integration
- [ ] Strategy backtester UI
- [ ] Portfolio tracker
- [ ] Export charts as images
- [ ] Alerts configuration UI
- [ ] Theme customization panel

## 📄 License

Proprietary - All rights reserved

---

**Version:** 0.1.0
**Author:** Sebastian2103
**Last Updated:** 2025-11-18
