# Project Research: Stack

## Recommended Stack
- **Web Framework**: Flask
- **HTTP Client**: requests
- **Concurrency**: threading (built-in)
- **Deployment**: Railway
- **Solana Webhook**: Helius
- **Notification Provider**: Telegram Bot API

## Rationale
The user requested a simple Python Flask backend to receive Helius webhooks. Since the alarm loop must run indefinitely without blocking the main webhook receiver, `threading` is optimal. `requests` handles sending Telegram messages. Railway provides free 24/7 hosting.

## What NOT to use
- Async frameworks (e.g., FastAPI) unless complexity grows; the user specifically requested Flask and `threading`.
- Heavy database ORMs (e.g., SQLAlchemy) since v1 only requires in-memory state for alarms and tx deduplication logic.
