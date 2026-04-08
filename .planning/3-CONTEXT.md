# Phase 3 Context: Infinite Alarm Manager

This document captures the final architectural and logic decisions for Phase 3: the persistent spam loop and safety mechanisms.

## Decisions

### 1. Alarm Behavior
- **Update Logic**: If a new matching transaction occurs while an alarm is already active, the message content being spammed will be updated to reflect the newest transaction (SOL amount, signature).
- **Interval**: Fixed as defined in environment variables (default 2s). No dynamic control via Telegram.

### 2. Safety Mechanisms (Auto-stop)
- **Max Duration**: Implement a `MAX_ALARM_DURATION`. 
    - **Recommended**: 20 minutes.
- **Auto-Termination**: If the alarm has been running continuously for longer than the duration, it will automatically stop.
- **Final Message**: Send a specific notification: "Auto-stop activated" when the duration is exceeded.

### 3. Smart Persistence & Recovery
- **Enhanced State Tracking**: `alarm_state.json` will now track:
    - `is_active` (boolean)
    - `start_time` (timestamp of the initial match)
    - `current_transaction` (data of the transaction currently being spammed)
- **Restart Recovery Logic**:
    - On startup, check `is_active`.
    - If `True`, calculate `elapsed_time = current_time - start_time`.
    - **Resume** ONLY if `elapsed_time < MAX_ALARM_DURATION`.
    - Otherwise, mark as `False` and do nothing.
- **Recovery Notification**: If an alarm resumes after a restart, send: "⚠️ Alarm resumed after restart" to the user.

## Implementation Details
- **Background Task**: Use a `threading.Thread` in `app.py` for the loop.
- **State Atomicity**: Ensure `alarm_state.json` is updated before sending messages to prevent race conditions on restart.
- **Environment**: Add `MAX_ALARM_DURATION` (in seconds) to `.env.example`.

## Success Criteria
- Bot spams until `/stop` or callback button is clicked.
- Bot automatically stops after 20 minutes.
- Bot resumes correctly after a restart within the valid time window.
- Bot updates content if a second transaction hits.
