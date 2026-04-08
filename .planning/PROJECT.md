# Crypto Alarm Bot

## Overview
A Python backend that monitors a Solana wallet via Helius webhook. When a targeted SOL transfer is detected, it triggers a continuous, aggressive notification loop via Telegram to awake/alert the user. It only stops when manually commanded.

## Problem Statement
The user needs an unignorable alert system for critical Solana transactions. Standard push notifications are easily dismissed or missed while sleeping. The system guarantees the user will be alerted by spamming the phone repeatedly (acting effectively as a high-priority alarm) until explicit acknowledgment (`/stop`).

## Requirements

### Validated
(None yet — ship to validate)

### Active
- [ ] Receive Solana transactions via Helius webhook (`/webhook`) using Flask
- [ ] Detect native SOL transfers to/from configured wallets 
- [ ] Compare transfer amount to TARGET_AMOUNT with a tolerance (e.g. `abs(sol - TARGET_AMOUNT) < 0.001`)
- [ ] Trigger an infinite alarm loop in a separate thread upon matching tx
- [ ] Send Telegram messages repeatedly (every 1-3 seconds) containing tx details and wallet info
- [ ] Listen for Telegram commands (`/telegram`)
- [ ] Stop the alarm loop when `/stop` command is received from Telegram
- [ ] Prevent duplicate alerts for the same transaction
- [ ] Run 24/7 without a local machine (deployable to Railway)

### Out of Scope
- Twilio integration for direct phone calls (Listed as level-up/optional, out of scope for v1)
- Multi-wallet / multi-amount configurations (Listed as optional, will stick to single configuration for v1 unless easy)

## Key Decisions
| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Python Flask Backend | Lightweight, standard for hook processing | Pending |
| Helius Webhook | Standard high-quality indexer for Solana | Pending |
| Telegram Bot Spam | Easiest way to send push notifications with sound/vibration persistently | Pending |
| Thread-based alarm loop | Does not block the main Flask thread handling webhooks | Pending |
| Railway deployment | Required by user, free-tier/cloud 24/7 friendly | Pending |

---
*Last updated: 2026-04-09 after initialization*
