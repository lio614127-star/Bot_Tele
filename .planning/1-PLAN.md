# Phase 1: Foundation and Webhooks Implementation Plan

## Goal
Set up the core Flask environment, implement a secure webhook receiver for Helius, and develop the transaction matching and deduplication logic.

## Steps

### Step 1: Environment and Setup
- Create `requirements.txt` with Flask, requests, python-dotenv, gunicorn.
- Create `Procfile` for Railway.
- Create `.env.example` with fallback values.
- Initialize `data/` directory with `.gitkeep`.

### Step 2: Persistence Layer
- Implement `utils/persistence.py`:
    - `load_signatures()` / `save_signatures(signatures)` using `data/signatures.json`.
    - `get_alarm_state()` / `set_alarm_state(is_active)` using `data/alarm_state.json`.

### Step 3: Webhook Service Logic
- Implement `services/webhook_service.py`:
    - Function `process_helius_webhook(payload)`:
        - Extract `nativeTransfers`.
        - Filter transfers where `fromUser == TARGET_WALLET`.
        - Check if `amount` is within `[MIN_SOL, MAX_SOL]`.
        - Check if `signature` is already in `signatures.json`.
        - If match found, return True (alert) and signature.

### Step 4: Flask Application
- Implement `app.py`:
    - Secure route `@app.route('/webhook/<secret_token>', methods=['POST'])`.
    - Validate `<secret_token>` against `SECRET_TOKEN` env var.
    - Call `webhook_service`.
    - If alert triggered, update `alarm_state.json`.
    - Log unauthorized attempts and successful matches using `utils/logger.py`.

### Step 5: Verification
- Create mock Helius payload.
- Run local server and test with `curl`.
- Verify file persistence and logs.

## Verification
- Test valid/invalid token access.
- Test matching logic with various amounts and wallets.
- Test deduplication (sending same signature twice).
- Test persistence (restart server and check if signatures are still there).
