# AI Trading Desktop App - Claude Code Guidelines

## Project Overview
Desktop trading application built with PyQt6, Plotly charts, and real-time WebSocket data.

## Development Rules

### 1. Version Control & Documentation
- **ALWAYS** update `CHANGES.txt` before committing changes
- Use semantic versioning: MAJOR.MINOR.PATCH
- Document all changes with date, category (Added/Changed/Fixed/Removed), and description
- Include known issues if any bugs are discovered

### 2. Logging
- Use the logging system in `src/utils/logger.py`
- Get module logger with: `from src.utils.logger import get_logger; logger = get_logger("module_name")`
- Log levels:
  - `DEBUG` - Detailed information for debugging
  - `INFO` - General operational messages
  - `WARNING` - Something unexpected but not critical
  - `ERROR` - Errors that need attention
- Never use `print()` for debugging - always use logger

### 3. Code Style
- Follow PEP 8 guidelines
- Use type hints for function parameters and returns
- Keep functions focused and small
- Document public methods with docstrings

### 4. Project Structure
```
AI_AT_DESKTOP-master/
├── main.py                 # Entry point
├── requirements.txt        # Dependencies
├── .env                    # Configuration (not in git)
├── CHANGES.txt            # Version history (ALWAYS UPDATE!)
├── CLAUDE.md              # This file - project guidelines
├── logs/                  # Log files (not in git)
├── src/
│   ├── components/        # UI components (PyQt6 widgets)
│   ├── services/          # API and WebSocket clients
│   └── utils/             # Utilities (config, logger)
└── venv/                  # Virtual environment (not in git)
```

### 5. Git Workflow
- Commit messages should be descriptive
- Always update CHANGES.txt before committing
- Push to `master` branch
- Remote: `git@github.com:Kolszewski01/AI_AT_DESKTOP.git`

### 6. Configuration
- All config in `.env` file
- Access via `src/utils/config.py`
- Never hardcode API URLs or credentials

### 7. Error Handling
- Always wrap API calls in try/except
- Log errors with full context
- Show user-friendly messages in UI

### 8. Backend Integration
- Backend API runs on WSL at `http://localhost:8000`
- WebSocket at `ws://localhost:8000`
- API docs: `http://localhost:8000/api/docs`

## Quick Commands
```bash
# Activate venv (Windows)
venv\Scripts\activate

# Run application
python main.py

# Check logs
type logs\app_YYYYMMDD.log
```

## Current Known Issues
- None currently - all backend endpoints working (backend v0.2.0)
