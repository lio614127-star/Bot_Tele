# Requirements

## Scope Boundaries

**In Scope:**
- Flask API with `/webhook` and `/telegram` endpoints.
- Basic deduplication of transactions.
- Sol transfer matching with tolerance.
- Infinite threading loop that spams Telegram.

**Out of Scope:**
- Twilio integration.
- Dynamic addition/removal of monitored wallets via UI (configured via environment variables initially).
- Multiple target amounts.

## Must Haves (Table Stakes)
- 1. Accept Webhook from Helius.
- 2. Filter transaction data to confirm TARGET amount (within 0.001 SOL tolerance) and matching wallet.
- 3. Spam Telegram with transaction details every 2 seconds.
- 4. Cease spamming when user sends `/stop` via Telegram.

## Differentiators
- Never stop notifying until user explicitly acknowledges.

## Context Needed for Planning
- Target Wallet Address and Target Amount.
- Telegram Bot Token and Chat ID for notifications.
