# Phase 3: Infinite Alarm Manager Implementation Plan

## Goal
Implement a robust background threading loop that spams Telegram alerts when an alarm is active, with integrated safety auto-stop and smart recovery after server restarts.

## Steps

### Step 1: Configuration & Persistence
- Update `.env.example`:
    - Add `MAX_ALARM_DURATION` (seconds, default 1200).
    - Add `ALARM_INTERVAL` (seconds, default 2).
- Update `utils/persistence.py`:
    - Refactor `set_alarm_state` to store `is_active`, `start_time` (string or epoch), and `current_tx` (dict).
    - Refactor `get_alarm_state` to return the full state dictionary.

### Step 2: Alarm Service Logic
- Create `services/alarm_manager.py`:
    - `get_manager_state()`: Global variable to track if the background thread is currently running in the process.
    - `start_alarm_thread()`: Starts `alarm_worker_loop` in a daemon thread if not already running.
    - `alarm_worker_loop()`:
        - The core loop that runs while `is_active` in JSON is true.
        - Check `start_time` vs `MAX_ALARM_DURATION`.
        - If exceeded: `set_alarm_state(False)`, send "Auto-stop" via `telegram_service`, break.
        - If valid: Send updated transaction alert via `telegram_service.send_alarm_message()`.
        - Sleep for `ALARM_INTERVAL`.

### Step 3: Flask Integration & Recovery
- Update `app.py`:
    - Import `start_alarm_thread` from `services.alarm_manager`.
    - At startup (`if __name__ == '__main__':`):
        - Load alarm state from JSON.
        - If `is_active == True`:
            - Check if within `MAX_ALARM_DURATION`.
            - If valid: 
                - `start_alarm_thread()`.
                - Send "⚠️ Alarm resumed after restart" via Telegram.
            - Else: `set_alarm_state(False)`.
    - In `webhook_receiver` route:
        - When a match is found:
            - `set_alarm_state(True, tx_data)`.
            - `start_alarm_thread()`.

### Step 4: Verification
- **Test Case 1: Infinite Spam**: Trigger a match, verify messages arrive every 2s.
- **Test Case 2: Manual Stop**: Call `/stop` or click button, verify loop terminates immediately.
- **Test Case 3: Auto-stop**: Set `MAX_ALARM_DURATION` to 30s, trigger alarm, verify it stops automatically.
- **Test Case 4: Smart Recovery**: Trigger alarm, restart server within 1 minute, verify "Resumed" message and continued spam.
- **Test Case 5: Update Content**: Trigger alarm with Tx1, then trigger with Tx2, verify alert content updates to Tx2.

## Verification Plan
- Create `tests/test_alarm_manager.py` with mocked time and sleep to verify duration logic.
- Perform manual verification on Railway/local for the restart and update-content scenarios.
