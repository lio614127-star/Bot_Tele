# Project Research: Pitfalls

## Common Mistakes
1. **Blocking the Flask thread**: If the alarm loop runs in the Flask request handler, the web server fails to respond to Helius and crashes.
   - **Prevention**: Use `threading.Thread(target=alarm_loop).start()`.
2. **Rate Limits & IP Bans**: Spamming Telegram every 1-2 seconds indefinitely might trigger Telegram API rate limits (HTTP 429).
   - **Prevention**: Be mindful of limits. Limit burst messaging or adapt spam speed dynamically. Standard limit is 30 msg/sec overall, but usually 1 msg/sec to specific chat is safer.
3. **Transaction Deduplication**: Helius webhooks can sometimes fire multiple times for the same transaction due to retries or overlapping webhook specs.
   - **Prevention**: Maintain a `set()` of processed transaction signatures.
4. **Deploying on Railway**: Railway stops idle services or requires proper environment variables.
   - **Prevention**: Ensure appropriate health checks.
