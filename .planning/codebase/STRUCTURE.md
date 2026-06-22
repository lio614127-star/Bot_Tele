---
last_mapped_commit: unknown
---
# Structure

**Date:** 2026-06-22

## Directory Layout
- `app.py`: Flask application initialization and route definitions.
- `services/`: Core business logic modules.
  - `alarm_manager.py`: Logic for managing user alarms/alerts.
  - `telegram_service.py`: Wrapper for Telegram API interactions.
  - `webhook_service.py`: Logic for parsing and handling incoming webhooks.
- `data/`: Local data storage (likely JSON files or SQLite).
- `utils/`: Helper scripts and common functions.
- `tests/`: Pytest test suite.

## Naming Conventions
- Modules and files use `snake_case`.
- Classes generally use `PascalCase`.
