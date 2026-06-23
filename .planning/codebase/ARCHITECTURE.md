# High-Level Architecture

The CryptoAlarmBot is a Python-based application built with the Flask framework. It acts as an integration layer between the Solana blockchain (via Helius) and end users (via Telegram and Ntfy.sh). Its primary purpose is to monitor specific Solana wallets for transactions within defined size limits and aggressively alert users when matching transactions occur.

## Core Components

### 1. Web Framework (Flask)
- **Role:** Exposes HTTP webhook endpoints to receive incoming data from Helius and Telegram.
- **Endpoints:**
  - `GET /`: Health check endpoint.
  - `POST /webhook/<token>`: Receives transaction payloads from Helius webhooks. Secured via a secret token.
  - `POST /telegram/<secret>`: Receives user commands and interactions from Telegram webhooks. Secured via a secret path.

### 2. External Integrations
- **Helius (Solana RPC/Webhooks):**
  - **Inbound:** Helius pushes JSON payloads to the bot's `/webhook/<token>` endpoint whenever monitored addresses transact.
  - **Outbound:** The bot calls Helius APIs to sync the list of tracked addresses whenever the user adds, removes, or toggles a wallet.
- **Telegram (User Interface):**
  - Acts as the control panel for the user. Users send commands (e.g., `/add`, `/wallets`, `/stop`) to configure which wallets to track.
  - The bot sends alerts, lists, and inline keyboards back to the configured user.
- **Ntfy.sh (Alerting):**
  - An optional but prioritized alerting mechanism. If an `NTFY_TOPIC` is configured, the bot pushes high-priority notifications to a user's Ntfy app, which can bypass silent modes on mobile devices.

### 3. State & Persistence
- **Storage Mechanism:** Local file-system (JSON files). No external database is required.
- **Data Stores:**
  - `wallets.json`: Flat list of monitored wallets, including address, name, active status, and min/max SOL thresholds.
  - `alarm_state.json`: Maintains the global alarm state (active/inactive) and details of the transaction that triggered the alarm. Allows the alarm to resume across bot restarts.
  - `signatures.json`: Stores recently processed transaction signatures to prevent duplicate processing of the same webhook payload.
  - `user_states.json`: Stores Telegram conversation states (e.g., `WAITING_ADD`, `WAITING_REMOVE`) to handle multi-step commands.

### 4. Background Alarm Manager
- **Concurrency Model:** Uses Python's `threading` module to run a background daemon thread.
- **Role:** When a matching transaction is detected, the alarm state is set to `True`. The background thread continuously checks this state and repeatedly sends notifications (via Telegram or Ntfy) at a defined interval until the user explicitly stops it (via Telegram) or a maximum duration expires.

## Data Flow
1. **Wallet Configuration:** User sends an `/add` command via Telegram -> `telegram_service` processes it -> `persistence` saves it to JSON -> `helius_service` calls Helius API to update the webhook configuration.
2. **Transaction Detection:** Wallet transacts on Solana -> Helius sends payload to `/webhook/<token>` -> `webhook_service` validates the payload against configured thresholds.
3. **Alarm Trigger:** If a match is found, `webhook_service` sets the global alarm state to active and wakes the `alarm_manager` thread -> `alarm_manager` repeatedly pushes notifications to Ntfy/Telegram.
4. **Alarm Resolution:** User clicks "Stop" in Telegram -> `telegram_service` sets the global alarm state to inactive -> `alarm_manager` goes back to sleep.
