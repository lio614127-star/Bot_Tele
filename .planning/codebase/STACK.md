# Technology Stack

This document details the core technologies and frameworks used in the CryptoAlarmBot project.

## Core Language & Runtime
* **Python**: The core programming language used to build the bot and its background services.

## Web Framework & Server
* **Flask**: A lightweight WSGI web application framework used to expose endpoints for health checks, Helius webhooks, and Telegram webhooks.
* **Gunicorn**: A Python WSGI HTTP Server for UNIX used as the application server in production (as specified in the `Procfile`).

## Background Processing & Concurrency
* **Python Threading (`threading` module)**: Used to spawn background tasks (`alarm_manager.py`) for maintaining persistent alarm loops and sending repeating notifications without blocking the web server or webhook endpoints.

## Utilities & Libraries
* **requests**: Used to interact with external APIs synchronously (Telegram API, Helius API, ntfy.sh).
* **python-dotenv**: Reads key-value pairs from a `.env` file and sets them as environment variables to keep secrets out of the codebase.
* **Pytest**: The testing framework configured for the project (found in `requirements.txt`).

## Data Persistence
* **File-based / Local State**: Uses a custom persistence layer (`utils.persistence`) to store alarm states, user state machines, and wallet configurations locally.

## Deployment Environment
* **Procfile-based PaaS**: The presence of a `Procfile` (`web: gunicorn app:app`) indicates that the application is built to be deployed on platforms like Heroku, Render, or Railway.
