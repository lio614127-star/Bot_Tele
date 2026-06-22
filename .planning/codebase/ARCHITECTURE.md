---
last_mapped_commit: unknown
---
# Architecture

**Date:** 2026-06-22

## Architecture Pattern
- Modular Flask application using a service-oriented approach.

## Data Flow
- Incoming HTTP requests (webhooks) are received by `app.py`.
- Requests are routed to `services/webhook_service.py` to be parsed.
- Depending on the payload, alarms might be triggered via `services/alarm_manager.py`.
- Notifications are formatted and dispatched to users using `services/telegram_service.py`.

## Entry Points
- `app.py` is the main entry point for the Flask web server.
