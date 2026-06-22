---
last_mapped_commit: unknown
---
# Conventions

**Date:** 2026-06-22

## Code Style
- Follows PEP 8 for Python styling.
- `requirements.txt` keeps dependency versions pinned.

## Patterns
- The app uses `dotenv` to manage secrets via `.env` files (a `.env.example` is provided).
- Uses `gunicorn` for production deployment, defined via `Procfile` (indicating potentially a Heroku or similar deployment setup).
