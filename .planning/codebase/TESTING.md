# Testing Strategy

This document details the testing framework, structure, and general approach for validating the logic of the `CryptoAlarmBot` project.

## 1. Testing Framework

The project uses **`pytest`** as its primary testing framework. 
- It leverages standard `pytest` conventions such as fixtures and `assert` statements.
- `unittest.mock.patch` is heavily utilized for mocking external interactions, environment variables, and filesystem dependencies.

## 2. Test Organization

Tests are located in the `tests/` directory at the root of the project. 
The test file structure mirrors the application structure:
- `test_webhook.py`: Validates the `app.py` Flask routing, webhook endpoints, and Helius payload parsing.
- `test_alarm_manager.py`: Tests the background worker loops, duration limits, and concurrency behaviors in `services/alarm_manager.py`.
- `test_telegram.py`: (Assumed) validates formatting, Telegram command processing, and conversational state transitions.

## 3. Mocking Strategy

Since the bot heavily relies on external services (Telegram API, Helius) and local file storage, tests are written to execute rapidly and deterministically without requiring a real network connection or touching the disk.

- **Environment Variables**: Sensitive or mandatory environment variables are patched at the module level *before* importing the main app to bypass the fast-fail mechanism on missing environment variables.
- **Persistence Layer**: Data fetching and saving functions from `utils.persistence` (e.g., `load_signatures`, `save_signatures`, `get_alarm_state`, `set_alarm_state`) are mocked using `@patch`. Side effects are applied to simulate data states (e.g., `mock_load.return_value = set()`).
- **External Network Calls**: Calls via the `requests` library or wrapped utility functions (e.g., `send_message`, `send_alarm_message`) are mocked. Assertions are made on `call_count` and `call_args` to verify the application formed the correct messages.

## 4. Flask Application Testing

For testing HTTP endpoints:
- A `pytest.fixture` named `client` is created utilizing Flask's `app.test_client()`.
- The application configuration is explicitly set to testing mode (`app.config['TESTING'] = True`).
- Tests simulate incoming webhook JSON payloads using `client.post(..., json=payload)` and assert on the `status_code` and JSON response payloads to ensure idempotency, authentication blocks, and successful processing.

## 5. Simulating Asynchronous Loops

When testing infinite or long-running worker loops (like the one in `alarm_manager.py`), tests must avoid blocking indefinitely.
- Mocked dependencies use `side_effect` lists to simulate a changing environment over time (e.g., the first check returns `is_active=True`, the second check returns `is_active=False` to break the loop).
- `time.sleep` is mocked to execute instantaneously (`return_value=None`) to keep test execution rapid while validating sequential logic.
