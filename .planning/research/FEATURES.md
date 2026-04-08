# Project Research: Features

## Table Stakes (Must Have)
- Receives HTTP POST webhooks from Helius.
- Parses `nativeTransfers` to identify SOL movements.
- Tolerant value comparison (`abs(sol - target) < 0.001`).
- Runs an infinite loop spamming the Telegram bot upon hitting criteria.
- Webhook endpoints to accept commands from Telegram ("`/stop`").
- Deduplication of events so the same transaction does not trigger multiple duplicate spam loops.

## Differentiators
- Continuous alarm spamming (as opposed to standard one-off notifications).
- Completely hands-off cloud monitoring (24/7 on Railway).

## Anti-Features (Deliberately Not Building in V1)
- Advanced UI/Dashboard.
- Twilio integration for automated phone calls.
- Multi-wallet configuration (keep it single target first for simplicity).
