# Daily Prompt — Enhancement Walkthrough

## Changes Made

### 1. System Prompt Extraction (Scraper + Data Model)

**Problem**: The scraper only captured the user message `text` field. The `system=` parameter from the API code block was ignored.

**Solution**:
- Added `system_prompt` column to [models.py](file:///c:/Users/scst1/2025/theprompttool/backend/models.py)
- Rewrote `extract_prompts_from_code_block()` in [scrape_prompts.py](file:///c:/Users/scst1/2025/theprompttool/backend/scripts/scrape_prompts.py) to extract both `system=` and `"text"` fields
- Changed upsert logic to `ON CONFLICT DO UPDATE` so re-runs populate the new field
- Updated [prompt_service.py](file:///c:/Users/scst1/2025/theprompttool/backend/services/prompt_service.py) to include `system_prompt` in the API response

**Result**: Prompts like "Career coach" (883 chars), "Brand builder" (639 chars), and "Alien anthropologist" (257 chars) now have system prompts. Prompts without system prompts (e.g., "Adaptive editor") correctly show empty.

---

### 2. Next Prompt Button

**Problem**: After a prompt was revealed, the CTA button showed "Prompt Delivered" and was disabled — no way to get another prompt.

**Solution**: In [App.jsx](file:///c:/Users/scst1/2025/theprompttool/frontend/src/App.jsx), the CTA button transforms to "⚡ Next Prompt" after reveal — same gradient style, stays interactive, calls `reset()` + `requestPrompt()`.

---

### 3. Try it on Claude Button

**Solution**: Added a `🚀 Try on Claude` button in [App.jsx](file:///c:/Users/scst1/2025/theprompttool/frontend/src/App.jsx). Opens `https://claude.ai/new?q=<encoded_prompt>` with both system and user prompts combined.

Styled with the gradient accent in [App.css](file:///c:/Users/scst1/2025/theprompttool/frontend/src/App.css).

---

### 4. UI Improvements

- System and user prompts are displayed in separate labeled sections: 🧠 System Prompt / 💬 User Prompt
- System prompt section has a distinct purple-tinted background
- Copy button now copies **both** system and user prompts with clear labels
- Prompt card footer: `[🚀 Try on Claude] [🔗 Source] [📋 Copy]`

## Verification

- ✅ **Vite build**: 0 errors (1.17s), CSS 17.46KB, JS 189.50KB
- ✅ **API**: Returns `system_prompt` field correctly
- ✅ **Scraper**: Extracts both prompts, verified against database (4+ prompts with system content)
- ✅ **Backend**: Running on http://127.0.0.1:5000
- ✅ **Frontend**: Running on http://localhost:5174

## Files Modified

| File | Change |
|---|---|
| [models.py](file:///c:/Users/scst1/2025/theprompttool/backend/models.py) | Added `system_prompt` column + serialization |
| [scrape_prompts.py](file:///c:/Users/scst1/2025/theprompttool/backend/scripts/scrape_prompts.py) | Dual extraction + ON CONFLICT UPDATE |
| [prompt_service.py](file:///c:/Users/scst1/2025/theprompttool/backend/services/prompt_service.py) | `system_prompt` in response |
| [App.jsx](file:///c:/Users/scst1/2025/theprompttool/frontend/src/App.jsx) | Prompt sections, Try on Claude, Next Prompt |
| [App.css](file:///c:/Users/scst1/2025/theprompttool/frontend/src/App.css) | Styles for new sections & buttons |
