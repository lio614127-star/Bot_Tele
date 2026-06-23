# External Integrations

This document details the external APIs, services, and integrations utilized by the CryptoAlarmBot project.

## 1. Telegram Bot API
* **Purpose**: User interaction, command processing, and alerting.
* **Mechanism**: 
  * Receives updates from users via a secure Webhook endpoint (`/telegram/<secret>`).
  * Sends messages, replies, and interactive inline keyboards to a specific admin chat (`TELEGRAM_CHAT_ID`) using the Telegram REST API (`https://api.telegram.org/bot<token>`).
* **Key Features**: Supports commands (`/add`, `/remove`, `/wallets`, `/stop`) and inline callback queries to manage monitored wallets and stop active alarms.

## 2. Helius API (Solana RPC & Webhooks)
* **Purpose**: Monitoring Solana blockchain transactions in real-time.
* **Mechanism**: 
  * The bot dynamically registers and updates webhook configurations on Helius (`https://api.helius.xyz/v0/webhooks/...`) with a list of user-specified wallet addresses.
  * Receives transaction payloads via the `/webhook/<token>` Flask endpoint when monitored wallets send or receive funds.
* **Key Features**: Filters transactions (like `TRANSFER`) and triggers internal parsing logic to identify large or specific transactions based on minimum/maximum SOL limits.

## 3. ntfy.sh (Push Notifications)
* **Purpose**: High-priority push notifications for mobile devices and desktops.
* **Mechanism**: When an alarm triggers and an `NTFY_TOPIC` is defined in the environment, the bot sends HTTP POST requests to `https://ntfy.sh/<topic>`.
* **Key Features**: Leverages tags (`rotating_light`, `warning`) and high priority (`5`) to ensure the user's phone or desktop receives a loud, prominent alert immediately, circumventing standard notification silences.

## 4. Solscan
* **Purpose**: Block explorer integration for transaction tracking.
* **Mechanism**: Generates direct links (`https://solscan.io/tx/<signature>`) within the Telegram alert messages. It doesn't use the Solscan API programmatically, but deeply integrates with its URL scheme to provide users a 1-click experience to verify transactions on the chain.
