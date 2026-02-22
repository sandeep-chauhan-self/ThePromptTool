# Technical Deep Dive: ThePromptTool

This document provides a high-level technical specification of **ThePromptTool** for AI analysis.

## Core Objective
An automated system to bridge the gap between high-quality prompt libraries (specifically Anthropic’s) and end-users, delivering a gamified "Daily Prompt" experience with guaranteed uniqueness (one-time serve) and one-click execution in external LLM interfaces (Claude).

---

## 🏗️ System Architecture

### 1. Ingestion Layer (Scraper)
- **Engine**: Playwright (Synchronous).
- **Target**: Anthropic Prompt Library (HTML/JS documentation).
- **Extraction Strategy**:
    - Scans index page for slugs.
    - Deep-scrapes detail pages.
    - **Parsing**: Uses regex against API code blocks to extract:
        - `system_prompt`: Captured from the `system=` Python parameter.
        - `prompt_body`: Captured from the `messages` JSON `text` field.
- **Idempotency**: Implements `INSERT ... ON CONFLICT (source_slug) DO UPDATE`. This allows re-seeding the database with updated extraction logic (e.g., when system prompt support was added) without duplicating entries.

### 2. Backend Layer (API)
- **Framework**: Flask (Python 3.11).
- **ORM**: SQLAlchemy.
- **Concurrency & Atomicity**:
    - **PostgreSQL (Production)**: Uses Common Table Expressions (CTE) with `FOR UPDATE SKIP LOCKED`.
        ```sql
        WITH next_p AS (SELECT id FROM prompts WHERE is_served = FALSE LIMIT 1 FOR UPDATE SKIP LOCKED)
        UPDATE prompts SET is_served = TRUE ... FROM next_p WHERE prompts.id = next_p.id ...
        ```
        This guarantees zero collisions and zero "double serves" even under high concurrent load.
    - **SQLite (Local Fallback)**: Implements manual transaction/counter logic for development ease without requiring a full Postgres instance.
- **Service Pattern**: Business logic is abstracted into `services/prompt_service.py` to decouple API routes from database implementation details.

### 3. Frontend Layer (UI/UX)
- **Framework**: React 18 (Vite build system).
- **Design System**: "Neon Codex" (custom Vanilla CSS).
- **Core UX Flow (State Machine)**:
    - `idle`: Initial state, showing stats.
    - `loading`: Async fetch in progress.
    - `revealed`: Prompt data received, typewriter animation starts.
    - `exhausted`: No more unserved prompts in the DB.
- **Integrations**:
    - **Try it on Claude**: Encodes both system and user prompts into a `claude.ai/new?q=...` URL.
    - **Clipboard**: Smart formatting that combines system and user prompts into a single structured text block.

---

## 📊 Data Model (SQLAlchemy)

### `Prompt` Table
- `id`: Primary key.
- `title`/`description`: Metadata.
- `system_prompt`: (Text) Instructions extracted from API code block.
- `prompt_body`: (Text) The actual user message.
- `is_served`: (Boolean) Critical flag for the serving logic.
- `serve_order`: (Integer) Global sequence number.
- `source_slug`: (String, Unique) Used for idempotency check during scraping.

### `AppState` Table
- Key-Value store for global counters (e.g., `serve_counter`, `total_prompts`). Prevents expensive `COUNT(*)` operations on every request.

---

## 🛠️ Performance & Scalability
- **Static Frontend**: Optimized for Vercel/CDN deployment.
- **Stateful Backend**: Stateless API design (audit logs in `ServeLog` table).
- **Atomic Selection**: The `SKIP LOCKED` pattern ensures the database remains the single source of truth for the serve-order, avoiding race conditions in distributed environments.
