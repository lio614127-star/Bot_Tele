# Project Research: Architecture

## Component Boundaries
1. **Webhook Receiver (Flask Route `/webhook`)**: Receives data from Helius, extracts `nativeTransfers`.
2. **Transaction Validator**: Checks if the amount matches TARGET_AMOUNT. Also deduplicates `signature` to prevent double-processing.
3. **Alarm Manager (Threading Thread)**: Spawns the infinite spam loop if valid. Maintains `alarm_active` state.
4. **Telegram Commander (Flask Route `/telegram`)**: Receives POST from Telegram Webhook. If `/stop`, toggles `alarm_active = False`.

## Build Order
1. Basic Flask setup & Railway configuration (`Procfile`, `requirements.txt`).
2. Webhook Receiver + Validator.
3. Telegram integration & Commander.
4. Alarm Manager (Threads).
