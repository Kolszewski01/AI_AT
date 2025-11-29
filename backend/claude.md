# AI Trading System - Backend Changelog

## Wersjonowanie
Format: `MAJOR.MINOR.PATCH`
- MAJOR: Duże zmiany, breaking changes
- MINOR: Nowe funkcjonalności, kompatybilne wstecznie
- PATCH: Bugfixy, drobne poprawki

---

## [0.2.0] - 2025-11-27

### Naprawione
- Zainstalowano brakującą bibliotekę **TA-Lib** (skompilowana ze źródeł)
- Zainstalowano brakujący pakiet **feedparser** dla endpointu news
- Naprawiono wszystkie endpointy analizy technicznej które zwracały błąd `No module named 'talib'`

### Działające endpointy (po naprawie)
- `GET /api/v1/analysis/indicators/{symbol}` - RSI, MACD, ADX, Bollinger Bands, Stochastic, etc.
- `GET /api/v1/analysis/patterns/{symbol}` - Wykrywanie formacji świecowych (Hammer, Engulfing, Doji, etc.)
- `GET /api/v1/analysis/signal/{symbol}` - Sygnały tradingowe z reasoning
- `GET /api/v1/news/{symbol}` - Pobieranie newsów z Yahoo Finance RSS

### Zależności
- `ta-lib==0.6.8` (wymaga biblioteki systemowej TA-Lib)
- `feedparser==6.0.12`

### Uwagi instalacyjne
TA-Lib wymaga instalacji biblioteki C przed instalacją wrappera Python:
```bash
# Ubuntu/Debian
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib && ./configure --prefix=/usr && make && sudo make install
sudo ldconfig
pip install ta-lib
```

---

## [0.1.1] - 2025-11-27

### Naprawione
- Fix: OHLCV endpoint KeyError dla kolumny Date (commit: e6e5260)

---

## [0.1.0] - 2025-11-27

### Dodane
- Inicjalna implementacja backendu FastAPI
- Endpointy market data (OHLCV, quotes, symbols)
- Endpointy analizy technicznej (indicators, patterns, signals, support/resistance)
- WebSocket dla real-time data streaming
- Endpointy alertów
- Endpointy news i sentiment
- Endpointy backtestingu
- Risk management endpoints

### Struktura projektu
```
backend/
├── app/
│   ├── main.py              # FastAPI application
│   ├── api/endpoints/       # REST API endpoints
│   ├── core/                # Config, security
│   ├── database/            # DB connections
│   ├── services/            # Business logic
│   │   ├── technical_analysis/
│   │   ├── nlp/
│   │   ├── alerts/
│   │   ├── backtesting/
│   │   └── data_fetchers/
│   └── schemas/             # Pydantic models
├── tests/
├── requirements.txt
└── claude.md                # Ten plik
```

---

## Template dla przyszłych wersji

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Dodane
- Nowe funkcjonalności

### Zmienione
- Zmiany w istniejących funkcjonalnościach

### Naprawione
- Bugfixy

### Usunięte
- Usunięte funkcjonalności

### Bezpieczeństwo
- Poprawki bezpieczeństwa
```
