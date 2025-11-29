# PLAN WDROŻENIA I ARCHITEKTURY: AI TRADING SYSTEM

**Wersja:** 1.0.0 (Hybrid Monorepo)
**Status:** PRODUCTION READY
**Główna zasada:** "Windows Host, Linux Guest"

---

## 1. ARCHITEKTURA FIZYCZNA I SIECIOWA

System działa w modelu hybrydowym.

| Komponent | Lokalizacja (Host) | Adres Sieciowy | Uwagi |
| :--- | :--- | :--- | :--- |
| **Root (CLI)** | **Windows (NTFS)** | - | Tu leży package.json. Stąd robisz commity. |
| **Backend** | Windows (zamontowany w **WSL**) | 0.0.0.0:8000 | Musi nasłuchiwać na 0.0.0.0. |
| **Mobile App** | **Windows** | localhost:8000 | Działa dzięki ADB Reverse. |
| **Desktop App** | **Windows** | localhost:8000 | Działa natywnie. |

---

## 2. STANDARD OPERACYJNY (SOP) - CODZIENNY WORKFLOW

### A. Zmiana w Backendzie (Nowe API)
Gdy dodasz nowy endpoint w Pythonie:
1. Zapisz plik w backend/.
2. W terminalu Windows (Root) wykonaj: npm run sync
   *To automatycznie przepisze kod w Mobile i Desktop.*

### B. Praca z Asystentem (Claude Code CLI)
Gdy chcesz wprowadzić zmiany w UI:
"Claude, backend się zmienił. Uruchom npm run sync. Teraz zaktualizuj widget X w Flutterze, używając nowego pola z wygenerowanego api_client."

### C. Testowanie na Fizycznym Telefonie (USB)
1. Podłącz telefon (Debugowanie USB włączone).
2. W terminalu Windows wpisz: npm run connect:phone
3. W aplikacji mobilnej używaj adresu http://localhost:8000.

### D. Commitowanie i Release
1. Commit: npm run commit
2. Release: npm run release

---

## 3. INSTRUKCJA INSTALACJI (SETUP)

Wykonaj te kroki tylko raz przy konfiguracji nowego stanowiska.

1. **Wymagania:** Node.js, Java (JRE 17+), Git.
2. **Setup Root:** npm install && npx husky init
3. **Setup Backend (WSL):** cd backend && python3 -m venv venv_wsl && source venv_wsl/bin/activate && pip install -r requirements.txt

---

## 4. WDROŻENIE NA PRODUKCJĘ (VPS)
Na serwer trafia TYLKO backend.
1. git clone <repo>
2. cd backend
3. docker compose up -d
