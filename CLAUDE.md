# AI TRADING SYSTEM - DEVELOPER RULES

## 🚨 CORE DIRECTIVE: TOKEN ECONOMY & SAFETY
1. **NO MANUAL API CLIENTS:** Never write HTTP requests manually.
2. **ALWAYS USE GENERATOR:** If Backend API changes -> Run 'npm run sync'.
3. **WRAPPER PATTERN:** Only write a wrapper service around the generated code (for Auth/Retry).

## 🏗️ ARCHITECTURE
- **Backend (WSL):** Source of Truth. Listens on 0.0.0.0.
- **Clients (Win):** Use generated api_client libraries.
- **Networking:** localhost:8000 (works on Emulator & USB Phone via 'npm run connect:phone').

## 🛠️ TOOLBOX (COMMANDS)
- Update Codebase after API change: npm run sync
- Connect Physical Phone: npm run connect:phone
- Smart Commit: npm run commit
- Deploy/Tag: npm run release
