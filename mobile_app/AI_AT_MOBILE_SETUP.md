# AI Trading Mobile App - Setup Instructions

## Backend Connection Info
- **Backend URL:** `http://localhost:8000` (WSL)
- **API Base:** `http://localhost:8000/api/v1`
- **WebSocket:** `ws://localhost:8000/ws`
- **API Docs:** `http://localhost:8000/api/docs`
- **Backend Version:** 0.2.0

---

## Windows Setup (Recommended)

### 1. Install Flutter SDK
```powershell
# Download from: https://docs.flutter.dev/get-started/install/windows

# Or use Chocolatey:
choco install flutter

# Add to PATH (if manual install):
# C:\flutter\bin
```

### 2. Install Android Studio
- Download: https://developer.android.com/studio
- During install, select:
  - Android SDK
  - Android SDK Platform
  - Android Virtual Device (AVD)

### 3. Configure Flutter
```powershell
# Check installation
flutter doctor

# Accept Android licenses
flutter doctor --android-licenses

# Enable web support (optional)
flutter config --enable-web
```

### 4. Clone & Setup Project
```powershell
# Clone repository
git clone git@github.com:Kolszewski01/AI_AT_MOBILE.git
cd AI_AT_MOBILE

# Get dependencies
flutter pub get

# Generate Hive adapters (if needed)
flutter packages pub run build_runner build
```

### 5. Configure API Endpoint
Edit `lib/services/api_service.dart`:
```dart
// For WSL backend accessible from Windows:
static const String baseUrl = 'http://localhost:8000/api/v1';
static const String wsUrl = 'ws://localhost:8000';

// For physical device testing (use your PC's IP):
// static const String baseUrl = 'http://192.168.x.x:8000/api/v1';
```

### 6. Run Application
```powershell
# List available devices
flutter devices

# Run on Android emulator
flutter run

# Run on Chrome (web)
flutter run -d chrome

# Run on connected phone
flutter run -d <device_id>
```

---

## Available API Endpoints

### Market Data
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/market/symbols` | GET | List available symbols |
| `/market/ohlcv/{symbol}` | GET | OHLCV candle data |
| `/market/quote/{symbol}` | GET | Current price quote |

### Technical Analysis
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/analysis/indicators/{symbol}` | GET | RSI, MACD, Bollinger, etc. |
| `/analysis/patterns/{symbol}` | GET | Candlestick patterns |
| `/analysis/signal/{symbol}` | GET | Trading signals |
| `/analysis/support-resistance/{symbol}` | GET | S/R levels |

### Alerts
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/alerts` | GET | List alerts |
| `/alerts/create` | POST | Create alert |
| `/alerts/{id}` | DELETE | Delete alert |

### News
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/news/{symbol}` | GET | News articles |
| `/news/sentiment/{symbol}` | GET | Sentiment analysis |

### WebSocket Streams
| Endpoint | Description |
|----------|-------------|
| `/ws/market/{symbol}` | Real-time price updates |
| `/ws/alerts` | Real-time alerts |
| `/ws/analysis/{symbol}` | Real-time indicators |

---

## Project Structure
```
mobile_app/
├── lib/
│   ├── main.dart              # Entry point
│   ├── models/                # Data models
│   │   ├── market_data.dart
│   │   ├── signal.dart
│   │   └── alert.dart
│   ├── screens/               # UI screens
│   │   ├── home_screen.dart
│   │   ├── chart_screen.dart
│   │   ├── watchlist_screen.dart
│   │   ├── alerts_screen.dart
│   │   ├── signals_screen.dart
│   │   ├── settings_screen.dart
│   │   └── risk_calculator_screen.dart
│   ├── services/              # API & WebSocket
│   │   ├── api_service.dart
│   │   └── websocket_service.dart
│   ├── widgets/               # Reusable widgets
│   │   └── drawing_tools_panel.dart
│   └── utils/
│       └── theme.dart
├── pubspec.yaml               # Dependencies
└── AI_AT_MOBILE_SETUP.md      # This file
```

---

## Dependencies (pubspec.yaml)

### Charts
- `fl_chart` - Line/bar charts
- `candlesticks` - Candlestick charts
- `syncfusion_flutter_charts` - Professional charts

### State Management
- `provider` / `riverpod` - State management

### Networking
- `http` / `dio` - REST API
- `web_socket_channel` - WebSocket

### Storage
- `hive` / `hive_flutter` - Local NoSQL
- `sqflite` - SQLite
- `shared_preferences` - Key-value storage

### Notifications
- `firebase_messaging` - Push notifications
- `flutter_local_notifications` - Local notifications

---

## Testing Connection

### 1. Check Backend is Running (WSL)
```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy","version":"0.2.0","environment":"development"}
```

### 2. Test from Windows
```powershell
Invoke-WebRequest -Uri "http://localhost:8000/health"
# or open in browser: http://localhost:8000/api/docs
```

### 3. Test from Physical Device
- Backend must be accessible from your phone
- Use your PC's local IP (not localhost)
- Ensure firewall allows port 8000

```bash
# Find your IP (Windows)
ipconfig
# Look for IPv4 Address: 192.168.x.x

# Update api_service.dart:
# baseUrl = 'http://192.168.x.x:8000/api/v1'
```

---

## Troubleshooting

### "Connection refused" on emulator
```dart
// Android emulator uses 10.0.2.2 for host localhost
static const String baseUrl = 'http://10.0.2.2:8000/api/v1';
```

### Flutter doctor issues
```powershell
# Missing Android SDK
flutter doctor --android-licenses

# Missing cmdline-tools
# Open Android Studio > SDK Manager > SDK Tools > Android SDK Command-line Tools
```

### Slow build times
```powershell
# Enable Gradle daemon
# Add to android/gradle.properties:
org.gradle.daemon=true
org.gradle.parallel=true
```

---

## Quick Start Commands

```powershell
# Full setup from scratch
git clone git@github.com:Kolszewski01/AI_AT_MOBILE.git
cd AI_AT_MOBILE
flutter pub get
flutter run -d chrome   # Web
flutter run             # Android emulator
```

---

## Version History
- **1.0.0** - Initial release with charts, WebSocket, alerts
- Backend compatibility: v0.2.0+

---

**Last Updated:** 2025-11-27
**Backend Status:** Running on WSL (localhost:8000)
