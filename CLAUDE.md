# AI TRADING SYSTEM - DEVELOPER RULES

> **CLAUDE: Wersjonowanie tego pliku**
>
> Ten plik zawiera "esencję" projektu - strukturę, reguły, komendy.
> **Aktualizuj TYLKO gdy zmienia się:**
> - Struktura katalogów projektu
> - Nowe/usunięte endpointy API
> - Nowe/usunięte komendy npm
> - Kluczowe zależności lub konfiguracja
> - Reguły deweloperskie (CORE DIRECTIVE)
>
> **NIE aktualizuj przy:** bugfixach, refaktoringu, zmianach w logice biznesowej.
>
> Wersja esencji: **1.1.0** (2025-11-29)

---

## CORE DIRECTIVE
1. **NO MANUAL API CLIENTS:** Never write HTTP requests manually.
2. **ALWAYS USE GENERATOR:** If Backend API changes -> Run `npm run sync`.
3. **WRAPPER PATTERN:** Only write a wrapper service around the generated code (for Auth/Retry).

## TOOLBOX (COMMANDS)
| Command | Description |
|---------|-------------|
| `npm run sync` | Regenerate API clients (desktop + mobile) after backend changes |
| `npm run sync:desktop` | Regenerate only Python API client |
| `npm run sync:mobile` | Regenerate only Dart API client |
| `npm run connect:phone` | ADB reverse port forwarding for physical phone |
| `npm run commit` | Commitizen - standardized commits |
| `npm run release` | Automated versioning & GitHub release |

---

## PROJECT ARCHITECTURE

```
AI_Agent_Trading_system/
├── backend/          # FastAPI (Python) - runs in WSL on 0.0.0.0:8000
├── desktop_app/      # PyQt6 (Python) - runs on Windows
├── mobile_app/       # Flutter (Dart) - Android/iOS
├── package.json      # Monorepo controller (npm scripts)
└── openapitools.json # OpenAPI Generator config (v7.17.0)
```

### Networking
- Backend (WSL): `0.0.0.0:8000` - source of truth
- Desktop (Win): connects to `localhost:8000`
- Mobile (USB): `npm run connect:phone` -> ADB reverse -> `localhost:8000`
- API Docs: `http://localhost:8000/api/docs`

---

## BACKEND (FastAPI)

**Location:** `backend/`
**Entry:** `uvicorn app.main:app --reload --host 0.0.0.0`
**Venv:** `backend/venv_wsl/`

### Structure
```
backend/app/
├── main.py                    # FastAPI app entry
├── api/endpoints/
│   ├── market_data.py         # OHLCV, quotes, symbols (yfinance)
│   ├── analysis.py            # Technical indicators, patterns, signals
│   ├── alerts.py              # Alert CRUD
│   ├── news.py                # News & sentiment (RSS, NLP)
│   ├── websocket.py           # Real-time streaming
│   ├── backtest.py            # Backtesting engine
│   └── risk_management.py     # Risk calculations
├── core/
│   ├── config.py              # Pydantic settings
│   ├── security.py            # JWT auth
│   ├── logger.py              # Centralized logging
│   ├── error_middleware.py    # HTTP error logging middleware
│   └── alert_notifier.py      # Telegram/Discord alerts (prepared)
├── database/
│   ├── connection.py          # PostgreSQL pool
│   ├── redis_cache.py         # Redis caching
│   └── influx_client.py       # InfluxDB time-series
├── services/
│   ├── data_fetchers/
│   │   ├── yfinance_client.py # Yahoo Finance (primary)
│   │   ├── ccxt_client.py     # Crypto exchanges
│   │   └── tradingview_scraper.py
│   ├── technical_analysis/
│   │   ├── indicators.py      # RSI, MACD, ADX, Bollinger, Stochastic
│   │   ├── patterns.py        # Candlestick patterns (TA-Lib)
│   │   └── support_resistance.py
│   ├── nlp/
│   │   ├── sentiment.py       # HuggingFace transformers
│   │   ├── news_fetcher.py    # RSS feeds
│   │   └── llm_integration.py # Ollama
│   ├── alerts/
│   │   ├── telegram_bot.py
│   │   ├── discord_bot.py
│   │   ├── sms_sender.py      # Twilio
│   │   └── tts_engine.py      # gTTS, pyttsx3
│   ├── backtesting/engine.py  # Backtrader
│   └── scheduler/             # Celery + APScheduler
└── schemas/                   # Pydantic models
```

### API Endpoints
| Prefix | Purpose |
|--------|---------|
| `/api/v1/market/*` | OHLCV, quotes, symbols, rate-limit status |
| `/api/v1/analysis/*` | Indicators, patterns, signals, S/R levels |
| `/api/v1/alerts/*` | Alert CRUD |
| `/api/v1/news/*` | News feed, sentiment |
| `/api/v1/backtest/*` | Run backtests |
| `/api/v1/risk/*` | Position sizing, risk metrics |
| `/api/v1/errors/*` | Client error reporting (desktop/mobile) |
| `/ws` | WebSocket real-time stream |

### Key Dependencies
- **Web:** FastAPI, Uvicorn, websockets
- **DB:** SQLAlchemy, psycopg2, Redis, InfluxDB
- **Data:** pandas, numpy, yfinance, CCXT
- **TA:** TA-Lib 0.6.8 (requires system lib)
- **NLP:** transformers, torch, LangChain
- **Alerts:** python-telegram-bot, discord-webhook, twilio, gTTS

### Logging System
- **Backend:** `app/core/logger.py` - centralized logging with rotating files
  - Logs: `backend/logs/app.log`, `backend/logs/errors.log`
  - Middleware: auto-logs HTTP errors and slow requests (>5s)
- **Desktop:** `src/utils/logger.py` - local + remote error reporting
  - Logs: `desktop_app/logs/app.log`, `desktop_app/logs/errors.log`
  - Errors sent to backend: `POST /api/v1/errors/report`
- **Mobile:** `lib/utils/app_logger.dart` - console + file + remote
  - Uses `logger` package, errors sent to backend

### Alert Notifications (prepared for future)
- `app/core/alert_notifier.py` - ready for Telegram/Discord
- To enable: set `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` or `DISCORD_WEBHOOK_URL` in `.env`

### Known Issues
- **Yahoo Finance rate limiting:** `market_data.py` has `AdaptiveRateLimitedCache`
  - Normal: 30s between requests
  - After 429: 5 min backoff, then gradual recovery
  - Check status: `GET /api/v1/market/status`

---

## DESKTOP APP (PyQt6)

**Location:** `desktop_app/`
**Entry:** `python main.py`
**Venv:** `desktop_app/venv/`

### Structure
```
desktop_app/
├── main.py                    # QApplication entry
├── src/
│   ├── components/
│   │   ├── main_window.py     # Main PyQt6 window
│   │   ├── chart_widget.py    # Plotly charts (QWebEngineView)
│   │   ├── watchlist_panel.py
│   │   └── alerts_panel.py
│   ├── services/
│   │   ├── api_client.py      # Wrapper around generated client
│   │   └── websocket_client.py
│   ├── utils/
│   │   ├── config.py          # Settings (.env)
│   │   └── logger.py
│   └── api_client/            # GENERATED - DO NOT EDIT
│       └── backend_api/
│           ├── api/           # AlertsApi, AnalysisApi, MarketApi...
│           └── models/
├── logs/                      # Runtime logs
└── requirements.txt
```

### Config (src/utils/config.py)
- API: `http://localhost:8000/api/v1`
- WebSocket: `ws://localhost:8000`
- Window: 1400x900, dark theme
- Default symbols: `^GDAXI`, `^GSPC`, `BTC-USD`, `ETH-USD`, `EURUSD=X`
- Intervals: 5s (prices), 30s (charts)

### Key Dependencies
- PyQt6 6.6.1 + PyQtWebEngine
- Plotly 5.18.0
- pandas, numpy
- requests, httpx, websockets

---

## MOBILE APP (Flutter)

**Location:** `mobile_app/`
**Entry:** `flutter run`

### Structure
```
mobile_app/lib/
├── main.dart
├── screens/
│   ├── home_screen.dart       # Dashboard
│   ├── chart_screen.dart      # Trading charts
│   ├── watchlist_screen.dart
│   ├── signals_screen.dart
│   ├── alerts_screen.dart
│   ├── risk_calculator_screen.dart
│   └── settings_screen.dart
├── services/
│   ├── api_service.dart       # Wrapper around generated client
│   └── websocket_service.dart
├── models/
│   ├── alert.dart
│   ├── market_data.dart
│   └── signal.dart
├── widgets/
│   └── drawing_tools_panel.dart
└── api_client/                # GENERATED - DO NOT EDIT
    └── lib/
        ├── api/
        └── model/
```

### Key Dependencies (pubspec.yaml)
- **Charts:** fl_chart, candlesticks, Syncfusion
- **State:** Provider, Riverpod
- **HTTP:** dio, web_socket_channel
- **Storage:** Hive, SQLite, SharedPreferences
- **Firebase:** firebase_core, firebase_messaging

---

## GENERATED CODE - DO NOT EDIT

These directories are auto-generated by OpenAPI Generator:

| Location | Language | Regenerate |
|----------|----------|------------|
| `desktop_app/src/api_client/` | Python | `npm run sync:desktop` |
| `mobile_app/lib/api_client/` | Dart | `npm run sync:mobile` |

**Wrapper pattern:** Create wrapper services that import generated code:
- Desktop: `desktop_app/src/services/api_client.py`
- Mobile: `mobile_app/lib/services/api_service.dart`

---

## DEVELOPMENT WORKFLOW

### Starting the system
```bash
# 1. Backend (in WSL terminal)
cd backend
source venv_wsl/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0

# 2. Desktop (in Windows terminal)
cd desktop_app
venv\Scripts\activate
python main.py

# 3. Mobile (in separate terminal)
cd mobile_app
flutter run
```

### After backend API changes
```bash
npm run sync  # Regenerates both desktop and mobile clients
```

### Testing
```bash
cd backend
pytest  # Run all tests
pytest tests/test_api/  # API tests only
```

---

## TECH STACK SUMMARY

| Layer | Technology | Version |
|-------|------------|---------|
| Backend | FastAPI + Uvicorn | 0.109.0 |
| Backend DB | PostgreSQL + Redis + InfluxDB | - |
| Backend TA | TA-Lib | 0.6.8 |
| Desktop | PyQt6 | 6.6.1 |
| Desktop Charts | Plotly | 5.18.0 |
| Mobile | Flutter/Dart | 3.0.0+ |
| Mobile Charts | fl_chart, Syncfusion | - |
| API Gen | OpenAPI Generator | 7.17.0 |
| VCS | Git + Husky | - |
