# Research Summary

## Key Findings

**Stack:** Python with Flask will be used to process webhooks. `requests` handles Telegram API calls, while `threading` provides non-blocking concurrency for the infinite spam loop. Deployment is targeted at Railway.

**Table Stakes:** 
- Receive/parse Helius webhooks for native SOL transfers.
- Continuous, thread-based Telegram message spam acting as a persistent alarm.
- Explicit `/stop` command via Telegram to interrupt the loop.
- Transaction deduplication to avoid redundant alarms.

**Watch Out For:** 
- **Blocking Webhook Responses:** Always spawn the alarm loop in a separate thread so Helius receives its `200 OK` promptly.
- **Rate Limiting:** Telegram limits messaging. Pace the alarm spam appropriately (e.g., once every 2-3 seconds).
- **Concurrency Bugs:** Use basic thread-safe toggles (`alarm_active = False`) to control the alarm state cleanly. 
