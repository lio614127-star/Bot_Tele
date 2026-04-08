# Phase 2: Telegram Interactivity Implementation Plan

## Goal
Integrate Telegram Bot API to send alerts with interactive buttons and handle command/callback interactions securely via webhooks.

## Steps

### Step 1: Configuration Updates
- Update `.env.example` with `TELEGRAM_SECRET`.
- Update `app.py` fail-fast check to include `TELEGRAM_SECRET`.

### Step 2: Telegram Service Implementation
- Create `services/telegram_service.py`:
    - `send_message(text, reply_markup=None)`: Helper to send POST requests to Telegram.
    - `send_startup_message()`: Sends "Bot Online" with timestamp.
    - `send_alarm_message(amount, wallet, signature)`: 
        - Formats text with emojis and Solscan link.
        - Includes InlineKeyboardButton "🛑 Dừng báo động" with callback_data="stop_alarm".
    - `handle_webhook(payload)`:
        - Validate `chat_id == TELEGRAM_CHAT_ID`.
        - Route `/start`, `/stop`, `/status` commands.
        - Handle `callback_query` for `stop_alarm`.

### Step 3: Webhook Integration in Flask
- Update `app.py`:
    - Add `@app.route('/telegram/<telegram_secret>', methods=['POST'])`.
    - Validate `<telegram_secret>` against environment.
    - Pass payload to `telegram_service.handle_webhook()`.
    - Trigger `send_startup_message()` in `if __name__ == '__main__':` or via a separate startup hook.

### Step 4: Logic Synchronization
- Ensure `/stop` command and "Stop Alarm" button both call `utils.persistence.set_alarm_state(False)`.
- Update `/status` to read `get_alarm_state()` and `TARGET_WALLET`.

### Step 5: Verification
- Create mock Telegram update payloads (Message and CallbackQuery).
- Test secured `/telegram` route with valid/invalid tokens.
- Verify `set_alarm_state` is triggered correctly by Telegram interactions.
- Test startup message delivery.

## Verification Plan
- **Security Check**: Verify that messages from unauthorized Chat IDs are ignored.
- **Interactive Check**: Verify that clicking the Inline Button triggers the alarm stop logic.
- **Formatting Check**: Verify the Solscan link and SOL amount display correctly in the message.
