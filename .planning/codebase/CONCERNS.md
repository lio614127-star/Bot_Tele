---
last_mapped_commit: unknown
---
# Concerns

**Date:** 2026-06-22

## Technical Debt
- The `data/` directory suggests file-based or local storage might be used instead of a robust database like PostgreSQL, which could lead to concurrency issues if traffic scales up (especially since `gunicorn` implies multiple workers).

## Security
- Make sure that `.env` is properly ignored in `.gitignore`. It is ignored currently, but an environment variable check in `app.py` is needed to ensure the app doesn't crash on start without it.
