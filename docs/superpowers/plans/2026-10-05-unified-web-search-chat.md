# Unified Web Search Chat Implementation Plan

> **For Codex:** Execute test-first and verify every stage before completion.

**Goal:** Remove the six-chapter answer-mode control, supply chapter artwork on chat pages, and synthesize no-key web search results with DeepSeek while keeping local evidence safeguards.

**Architecture:** Add a small `ddgs` search adapter that normalizes untrusted web results into the existing `RetrievedChunk` evidence contract. Run it before any DeepSeek call, merge it with locally reviewed evidence, and retain current guards and graceful fallbacks. Frontend chat becomes a single-mode experience and renders external citations as links.

**Tech Stack:** FastAPI, Pydantic Settings, httpx-compatible DeepSeek client, ddgs, Vue 3, Pinia, Playwright, pytest.

---

### Task 1: Lock frontend behavior with a failing Playwright check

- Add `frontend/tests/e2e_unified_chat_check.py`.
- Check all six chat routes have no mode controls or labels.
- Check the Yuan left image resolves to the approved Yuntai asset.
- Run the check and confirm it fails against the current UI.

### Task 2: Lock web-search behavior with failing unit tests

- Add `backend/tests/test_web_search.py`.
- Test result cleanup, URL de-duplication, metadata conversion, and graceful provider failure.
- Add a service-order test proving web search runs before the first LLM call.
- Run pytest and confirm the missing implementation fails.

### Task 3: Implement the no-key search adapter and synthesis flow

- Add `ddgs` dependency and web-search settings.
- Add `backend/app/ai/web_search.py` with a bounded async adapter.
- Search before query rewrite, merge web and local chunks, and explicitly treat web text as untrusted supplementary evidence.
- Preserve the existing fallback path when web search or DeepSeek is unavailable.
- Update DeepSeek defaults and `.env.example` without adding a real key.

### Task 4: Implement the unified frontend

- Remove the mode switch UI, store state, and request payload field.
- Add chapter-level default images and use the Yuntai stone-carving image for Yuan.
- Open web citations by URL while keeping local citations connected to the source drawer.

### Task 5: Verify the whole slice

- Run backend unit tests.
- Run frontend typecheck/build.
- Run unified chat Playwright checks against all six chapters.
- Restart backend and verify health plus a safe fallback response without a key.
