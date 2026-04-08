# Phase 1 Context: Foundation and Webhooks

This document captures the decisions made during the discussion phase for Phase 1. These decisions guide the research and planning for this phase.

## Decisions

### 1. Webhook Security
- **Secret URL Path**: Webhooks will be received at `/webhook/<SECRET_TOKEN>`. The `SECRET_TOKEN` will be an environment variable.
- **IP Whitelisting**: Not implemented in Phase 1 to maintain flexibility with Helius IP changes.
- **Logging**: Unauthorized access attempts (wrong token or endpoint) will be logged with IP, timestamp, and requested endpoint.
- **SSL/HTTPS**: Handled automatically by Railway; no additional configuration needed in the Flask app.

### 2. Transaction Matching Logic
- **Direction**: Alert on **OUTGOING** native SOL transfers from the target wallet.
- **Amount Matching**: Use a range check with `MIN_SOL` and `MAX_SOL` environment variables (or a base amount with 0.001 tolerance if preferred, but range is more flexible as requested).
- **Granularity**: Alert exactly **ONCE** per transaction signature, even if multiple transfers within that transaction match the criteria.
- **Scope**: Strictly Native SOL transfers for Phase 1.

### 3. Deduplication & Persistence
- **Storage**: Use a local `data/signatures.json` file for persistence across Railway restarts.
- **Retention**: Maintain a history of the last **1000 transaction signatures**.
- **Alarm State Persistence**: The "Alarm Active" state **MUST** be persisted. If the server restarts while an alarm is active, it must resume spamming immediately upon startup.
- **Real-time Focus**: On restart, don't re-process very old transactions; focus on maintaining state for recent/active events.

### 4. Environment Configuration
- **Fail-Fast Policy**: The application will crash/exit immediately if `TELEGRAM_BOT_TOKEN` or `TELEGRAM_CHAT_ID` are missing.
- **Alarm Configuration**:
    - `ALARM_INTERVAL`: Default to 2 seconds (configurable).
    - `SECRET_TOKEN`: Required for webhook security.
    - `TARGET_WALLET`, `MIN_SOL`, `MAX_SOL`: Required for matching.
- **Development**: Use `.env` for local development and Railway environment variables for production.
- **Debug Mode**: Implement a `DEBUG_MODE` flag for verbose logging.

## Code Context
- **Framework**: Flask (Python).
- **Concurrency**: `threading` for the infinite alarm loop.
- **Persistence**: Simple JSON file handling for signatures and alarm state.
