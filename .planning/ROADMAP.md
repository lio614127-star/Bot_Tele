# Project Roadmap

## Phase 1: Foundation and Webhooks
**Goal**: Set up basic Flask environment, Helius integration, and message verification.
- [ ] Initialize Python environment and dependencies (`Flask`, `requests`).
- [ ] Create simple `/webhook` receiver.
- [ ] Implement deduplication and validation logic against Target Sol Amount.
- [ ] Configure `Procfile` and deployment settings for Railway.

## Phase 2: Telegram Interactivity
**Goal**: Integrate Telegram Bot API for alerts and commands.
- [ ] Create `/telegram` webhook handler.
- [ ] Basic logic for responding to commands (e.g., `/stop`, `/start`).

## Phase 3: Infinite Alarm Manager
**Goal**: The core differentiator — spamming the user.
- [ ] Create `threading` loop for the persistent alarm.
- [ ] Connect webhook detection to trigger the alarm loop.
- [ ] Connect Telegram `/stop` command to terminate the loop safely.
