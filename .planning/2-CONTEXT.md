# Phase 2 Context: Telegram Interactivity

This document captures the decisions made during the discussion phase for Phase 2. These decisions guide the research and planning for integrating the Telegram Bot API.

## Decisions

### 1. Webhook Security
- **Separate Endpoint**: Use a dedicated endpoint for Telegram webhooks at `/telegram/<TELEGRAM_SECRET>`.
- **Unique Secret**: Use a separate environment variable `TELEGRAM_SECRET` for this endpoint (different from the Helius secret).

### 2. User Authorization
- **Strict Whitelisting**: The bot will ONLY process commands or callbacks if they originate from the `TELEGRAM_CHAT_ID` specified in the environment variables.
- **Ignore Mode**: All other requests from different chat IDs will be ignored completely for security.

### 3. Alert Formatting & Interaction
- **Content**: Messages must include emoji warnings, SOL amount, direction (IN/OUT), the related wallet address, and a direct Solscan link.
- **Inline Keyboard**: Every alarm message must include an Inline Button labeled "🛑 Dừng báo động" (Stop Alarm).
- **Callback Handling**: This button should send a callback to the bot to trigger the stop logic immediately, bypassing the need to type commands.

### 4. Command Set
- **Required**:
    - `/stop`: Immediately terminates the active alarm loop.
- **Supportive**:
    - `/status`: Displays the current alarm state (active/inactive) and the target wallet being monitored.
    - `/start`: Minimalist connectivity test, confirms the bot is responding.
- **Excluded**: No help, config, or management commands are needed for V1 to keep the system simple and robust.

### 5. Startup Notification
- **Status Update**: The bot will send a single "Bot Online" message to the `TELEGRAM_CHAT_ID` upon successful server startup.
- **Meta-data**: Include a timestamp in this message to help identify server restarts.

## Code Context
- **Provider**: Telegram Bot API via standard webhook delivery.
- **Library**: `requests` for sending messages (keep it consistent with Phase 1).
- **Endpoint Protection**: Already planned via `SECRET_TOKEN` in URL.
- **State Integration**: Commands will interact with `alarm_state.json` created in Phase 1.
