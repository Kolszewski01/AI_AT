# INSTRUKCJA SZYBKIEGO STARTU

## ETAP 1: WINDOWS (Przygotowanie)
1. Otwórz PowerShell w tym folderze.
2. Wpisz: npm install
3. Wpisz: npx husky init
4. Sprawdź Javę: java -version (musi być min. 17).

## ETAP 2: BACKEND (WSL)
1. Otwórz nowy terminal WSL.
2. cd backend
3. python3 -m venv venv_wsl
4. source venv_wsl/bin/activate
5. pip install -r requirements.txt
6. START: uvicorn app.main:app --reload --host 0.0.0.0

## ETAP 3: SYNCHRONIZACJA
1. Wróć do PowerShell.
2. Wpisz: npm run sync
3. Jeśli zobaczysz sukces -> Jesteś gotowy do pracy!
