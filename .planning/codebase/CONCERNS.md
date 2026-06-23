# Codebase Concerns & Technical Debt

This document outlines technical debt, potential bugs, security issues, missing tests, and architectural concerns in the CryptoAlarmBot codebase.

## 1. Architecture & Concurrency
- **Threading in WSGI Environment**: The application spawns a background thread in `services/alarm_manager.py` using standard `threading`. Since `Procfile` indicates deployment via Gunicorn, using background threads inside the web worker can lead to unexpected behavior. If multiple workers are deployed, each will spawn its own alarm thread, causing duplicate notifications. Alternatively, workers might be killed by Gunicorn due to timeouts, abruptly terminating the background thread.
- **Race Conditions in JSON Persistence**: Data is saved and loaded via JSON files in `utils/persistence.py`. There are no file locks (e.g., via `filelock`) used. Concurrent requests (e.g., a user adding a wallet via Telegram at the exact same moment a Helius webhook fires) will result in a race condition, potentially leading to JSON corruption and complete data loss.

## 2. Data Persistence
- **Ephemeral File System Risk**: Storing state in `data/*.json` is problematic for typical cloud deployments (like Heroku, Render, or Docker). These environments use ephemeral filesystems. Every restart or deployment will wipe out the `data/` directory, resulting in the loss of all configured wallets, alarm states, and signatures. Consider migrating to a lightweight database like SQLite (with persistent volume) or Redis/PostgreSQL.
- **Data Migration Logic in Reads**: `load_wallets()` contains logic to migrate old data structures to a new flat list structure. This couples data migration with data access, adding overhead and increasing the risk of bugs during concurrent reads.

## 3. Security
- **Secrets in URLs**: The webhook endpoints use secrets in the URL path (`/webhook/<SECRET_TOKEN>` and `/telegram/<TELEGRAM_SECRET>`). While this obscures the endpoint, secrets in paths are typically logged by reverse proxies (Nginx, Heroku router) and server access logs. It is significantly more secure to use HTTP headers (e.g., `X-Telegram-Bot-Api-Secret-Token` for Telegram, and Authorization headers for Helius).

## 4. Error Handling & Edge Cases
- **Missing SPL Token Support**: `services/webhook_service.py` currently only parses `nativeTransfers` (SOL). It ignores SPL token transfers (like USDC, USDT, or meme coins), which is a massive limitation for a Solana tracking bot.
- **Silent Synchronization Failures**: In `services/helius_service.py`, if syncing wallets to the Helius API fails (e.g., due to network issues or API rate limits), the system logs an error but the local `wallets.json` is still updated. This creates an inconsistent state where the bot thinks a wallet is being tracked, but the Helius webhook has not been updated.
- **System Program Fallback**: When no active wallets exist, `helius_service.py` hardcodes the System Program (`11111111111111111111111111111111`) to prevent Helius API errors. This could result in the webhook receiving massive amounts of irrelevant transactions, burning through API credits unnecessarily.

## 5. Testing & Quality
- **Outdated Tests**: The tests in `tests/test_webhook.py` are out of sync with the current implementation. For instance, `mock_set_alarm.assert_called_with(True)` will fail because `set_alarm_state` expects two arguments in the actual code (`set_alarm_state(True, tx_data)`).
- **Missing Coverage**: There are no tests for critical components such as:
  - File locking/concurrency handling (or lack thereof).
  - Validation of Solana addresses in Telegram commands.
  - Recovery behavior if a JSON file gets corrupted.
  - Handling of Helius API failures during syncing.
