# Codebase Conventions

This document outlines the architectural patterns, coding standards, and common practices used in the `CryptoAlarmBot` (Telegram Bot) project. Adhering to these conventions ensures maintainability and consistency across the codebase.

## 1. Architectural Patterns

### 1.1 Project Structure
The application follows a modular monolith architecture, separating concerns into logical directories:
- **`app.py`**: The entry point for the Flask web application. It handles routing, basic request validation, and application lifecycle.
- **`services/`**: Contains core domain logic. It encapsulates interactions with external systems and core application features (e.g., `telegram_service.py`, `helius_service.py`, `webhook_service.py`, `alarm_manager.py`).
- **`utils/`**: Reusable utility functions and infrastructure code (e.g., `logger.py`, `persistence.py`).
- **`data/`**: Directory for storing local JSON state files.
- **`tests/`**: Unit and integration test suite, mirroring the structure of the source modules.

### 1.2 Configuration & Environment Variables
- The project relies heavily on `python-dotenv` to load configurations from a `.env` file.
- `app.py` explicitly checks for `MANDATORY_VARS` at startup. If critical variables (e.g., `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `SECRET_TOKEN`) are missing, the application fails fast and exits immediately.
- Fallback values are explicitly configured for optional variables (e.g., `ALARM_INTERVAL`, `MAX_ALARM_DURATION`).

## 2. Coding Standards

### 2.1 Python Style & Naming
- **Naming**: `snake_case` is used consistently for variables, functions, and module names.
- **Imports**: standard libraries first, followed by third-party packages, and finally local application imports.
- **String Formatting**: `f-strings` are the standard for string formatting.
- **Comments**: Function-level docstrings are used to explain the purpose of non-obvious logic. Inline comments clarify complex manipulations (e.g., handling state migrations).

### 2.2 Error Handling & Returns
- Operations that can fail or produce context messages often return a tuple of `(success_boolean, message_string)`. This allows callers to gracefully inform the user of the outcome without resorting to excessive exception handling.
- Exceptions are caught when interacting with external APIs (like `requests` throwing exceptions), and errors are logged locally using the configured logger.

## 3. Persistent State Management

Data persistence is handled by `utils/persistence.py`, heavily leveraging local JSON files.
- **Flat Data Model**: Data is stored in simple lists and dictionaries (`wallets.json`, `signatures.json`, `alarm_state.json`, `user_states.json`) for ease of access and manual debugging.
- **Lazy Initialization**: File creation and directory checking (`ensure_data_files()`) happens dynamically upon read/write operations to prevent startup crashes in new environments.
- **Migration Logic**: There is built-in backward compatibility logic to handle structural changes in JSON storage (e.g., converting legacy multi-user dict structures to single-user flat lists).
- **Capping Size**: The system explicitly truncates logs/history to prevent storage bloat, such as keeping only the last 1000 webhook signatures.

## 4. Telegram Bot Communication

- **No Heavy Wrappers**: The project interacts with the Telegram Bot API directly using the standard `requests` library rather than large framework wrappers.
- **Parse Mode**: Messages are formatted using `HTML` parse mode to cleanly render bold tags (`<b>`), code blocks (`<code>`), and links.
- **State Machine for Conversations**: Interactive command flows (e.g., `/add`, `/remove`, `/edit_limit`) use a simple persistent state machine (`user_states.json`) mapped to `chat_id`. The application checks this state to understand the context of the user's free-text messages.
- **Inline Keyboards**: Interactive UI elements use inline keyboards (`callback_data`) to trigger specific actions (`toggle_x`, `delete_x`, `stop_alarm`), making the bot feel app-like.

## 5. Webhooks & Security

- **Obfuscated Paths**: The Webhook endpoints (Helius and Telegram) incorporate secret tokens directly into the URL path (`/webhook/<token>`) to prevent unauthorized scanning or triggering.
- **Request Validation**: Before processing, payloads are validated, and missing elements return straightforward `400 Bad Request` or `404 Not Found` JSON responses.
- **Idempotency**: Processed signatures from webhooks are saved. If a duplicate payload arrives, it is safely ignored to prevent spamming notifications.
