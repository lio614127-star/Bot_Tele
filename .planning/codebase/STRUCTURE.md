# Directory and Module Structure

The project follows a standard modular Python architecture, separating the web layer, business logic, persistence, and external service integrations.

## Root Directory (`/`)
- `app.py`: The application entry point. Initializes the Flask application, defines the routing (`/`, `/webhook`, `/telegram`), enforces security via tokens, manages initial startup recovery, and launches the application server.
- `requirements.txt`: Defines Python package dependencies (e.g., Flask, requests, python-dotenv).
- `.env` / `.env.example`: Configuration files holding critical secrets and tuning parameters (Telegram tokens, Helius keys, alarm intervals).
- `Procfile`: Configuration for deployment (likely for Heroku or similar PaaS), indicating how to run the app.

## `services/`
Contains the core business logic, categorized by the domain it interacts with.

- `telegram_service.py`: 
  - Handles all interactions with the Telegram Bot API. 
  - Parses incoming webhooks (commands, messages, callback queries from inline buttons).
  - Contains presentation logic (formatting text strings and inline keyboards for Telegram).
  - Routes multi-step conversations (e.g., waiting for a user to input a wallet address).
- `helius_service.py`: 
  - Acts as a client for the Helius REST API. 
  - Provides the `sync_wallets_to_helius()` function, which reads the locally configured list of active wallets and pushes them to Helius to update the webhook tracking target addresses.
- `webhook_service.py`: 
  - Processes incoming Solana transaction payloads from Helius.
  - Contains the logic to iterate through transactions, evaluate them against tracked wallets and size thresholds (min/max SOL), prevent duplicate processing using signatures, and trigger the alarm system if a match is found.
- `alarm_manager.py`: 
  - Manages the active alarm cycle. 
  - Implements `alarm_worker_loop()`, a background daemon thread that continuously reads the alarm state and dispatches repeated, noisy alerts to Ntfy or Telegram until the state is deactivated or times out.

## `utils/`
Contains shared helper functions and cross-cutting concerns.

- `persistence.py`: 
  - Centralizes all data access logic. 
  - Provides CRUD (Create, Read, Update, Delete) operations for the JSON file-based database (`wallets.json`, `alarm_state.json`, `signatures.json`, `user_states.json`). 
  - Ensures data files are initialized correctly if they don't exist.
- `logger.py`: 
  - Configures the Python `logging` module to standard output, ensuring consistent log formatting across all application modules. 
  - Includes specific utility functions like `log_unauthorized()` for security events.

## `data/`
- The directory where local database files are stored.
- At runtime, it contains `wallets.json`, `alarm_state.json`, `signatures.json`, and `user_states.json`.
- These files are typically ignored by version control (except `.gitkeep`) to prevent committing user data and state.

## `tests/`
- Holds the automated test suite for the application (evident from `pytest` configurations in the root directory).
