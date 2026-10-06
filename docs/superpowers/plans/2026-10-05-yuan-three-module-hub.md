# Yuan Three-Module Hub Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the Yuan briefing into a hub with three independent entries for script exploration, AI questions, and the twelve-scene evidence story.

**Architecture:** Keep the existing routes and feature components intact. Add route cards and lightweight saved-state labels to `C01Guide.vue`, then make the Yuan scene, chat page, and scene quest completion return to `/chapter/yuan` while preserving other chapters' navigation.

**Tech Stack:** Vue 3, TypeScript, Pinia, Vue Router, Vite, Python Playwright

## Global Constraints

- The three Yuan modules are independent and never locked.
- Only the twelve-scene story routes to the Yuan summary.
- Other chapters retain their existing briefing and scene flow.
- No AI backend or story-content changes.
- No new runtime dependencies.
- The workspace is not a Git repository, so commit steps do not apply.

---

### Task 1: Add the Yuan hub regression test

**Files:**
- Create: `frontend/tests/e2e_yuan_module_hub_check.py`

**Interfaces:**
- Consumes: `TONGXIN_BASE_URL`, the existing Yuan routes, and accessible button/link names.
- Produces: one browser test that fails unless all three entries and their return paths work at desktop and mobile widths.

- [ ] Create a Playwright test that opens `/chapter/yuan`, asserts buttons named `六体文字探查`, `AI 助手问答`, and `12 幕证据剧情`, visits each route, and returns to the hub.
- [ ] Assert `/chapter/han` still contains `接受身份，进入场景` and does not show the Yuan module grid.
- [ ] Assert a 390×844 Yuan hub has no horizontal document overflow.
- [ ] Run the test against the current dev server and confirm it fails because the three entries do not exist.

### Task 2: Implement the three-card Yuan hub

**Files:**
- Modify: `frontend/src/pages/chapter/C01Guide.vue`

**Interfaces:**
- Consumes: `game.stateFor('yuan')`, `tongxin.yuan.story.v6`, and Vue Router.
- Produces: `yuanModules`, three accessible card buttons, and responsive module-grid styling.

- [ ] Add safe story-save parsing and computed status labels for exploration, chat, and story.
- [ ] Add three equal-weight module cards routing to `/scene`, `/chat`, and `/story` only for Yuan.
- [ ] Preserve the existing narration toggle below the Yuan cards.
- [ ] Preserve the original single start button for all non-Yuan chapters.

### Task 3: Return independent modules to the hub

**Files:**
- Modify: `frontend/src/pages/chapter/C02Scene.vue`
- Modify: `frontend/src/pages/chapter/C05Chat.vue`
- Modify: `frontend/src/components/game/GameQuestDock.vue`

**Interfaces:**
- Consumes: the current route slug.
- Produces: Yuan-specific navigation to `/chapter/yuan`; unchanged behavior for every other slug.

- [ ] Add a visible `返回任务大厅` control to the Yuan scene toolbar.
- [ ] Make the Yuan chat back control return to `/chapter/yuan` and label it `返回元代任务大厅`.
- [ ] Make the Yuan scene quest result button return to the hub and label it `返回任务大厅`; keep other chapters routing to their summaries.

### Task 4: Verify behavior and build integrity

**Files:**
- Verify: `frontend/tests/e2e_yuan_module_hub_check.py`
- Verify: `frontend/tests/e2e_yuan_story_check.py`

**Interfaces:**
- Consumes: the completed implementation.
- Produces: fresh evidence that routing, story completion, type safety, and production bundling all pass.

- [ ] Run the Yuan hub test and confirm it passes.
- [ ] Run `npm run typecheck`.
- [ ] Run `npm run build`.
- [ ] Run the existing twelve-scene Yuan story test against the built preview.
