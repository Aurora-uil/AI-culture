# Remove Yuan Fixed Dialogue Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the obsolete Yuan fixed-dialogue popup from the shared scene page so Vite can transform and build the frontend while preserving the Yuan story and rubbing comparison.

**Architecture:** Make one focused edit in `C02Scene.vue`: remove the missing component import and every UI/state path that exists only for that popup. Keep the independent `YuanRubbingCompare` lazy component, its state, events, button, and overlay unchanged.

**Tech Stack:** Vue 3 Single-File Components, TypeScript, Vite 6, vue-tsc

## Global Constraints

- Preserve the complete Yuan story at `/chapter/yuan/story`.
- Preserve the Yuan rubbing comparison flow.
- Do not refactor the dormant Yuan task state machine in this fix.
- Add no dependencies and no replacement placeholder component.
- The workspace is not a Git repository, so commit steps are not applicable.

---

### Task 1: Remove the obsolete fixed-dialogue path

**Files:**
- Modify: `frontend/src/pages/chapter/C02Scene.vue:262-290`
- Modify: `frontend/src/pages/chapter/C02Scene.vue:344-347`
- Modify: `frontend/src/pages/chapter/C02Scene.vue:415-423`
- Verify: `frontend/src/pages/chapter/C02Scene.vue`

**Interfaces:**
- Consumes: the existing Yuan route `/chapter/yuan/story` and the independent `YuanRubbingCompare` component.
- Produces: a `C02Scene.vue` module with no reference to `YuanFixedDialogue`, while retaining `showRubbing`, `yuanSeenScripts`, and `onRubbingSubmit(payload: { choice: string }): void`.

- [x] **Step 1: Re-run the red Vite transformation check**

Run from `frontend`:

```powershell
node --input-type=module -e "import { createServer } from 'vite'; const server = await createServer({ server: { middlewareMode: true }, appType: 'custom' }); try { await server.transformRequest('/src/pages/chapter/C02Scene.vue'); console.log('PASS'); } catch (error) { console.error(error.message); process.exitCode = 1; } finally { await server.close(); }"
```

Expected before the edit: exit code 1 with `Failed to resolve import "@/components/dialogue/YuanFixedDialogue.vue"`.

- [x] **Step 2: Apply the minimal source change**

In `frontend/src/pages/chapter/C02Scene.vue`:

1. Change the section comment from fixed dialogue/rubbing wording to rubbing-only wording.
2. Remove `dialogueOpen`.
3. Remove the entire `YuanFixedDialogue` `defineAsyncComponent` declaration and its `.catch()` placeholder.
4. Remove `startFixedDialogue()` and `onDialogueDone()`.
5. Remove the toolbar button whose visible label is `固定剧情对话`.
6. Remove the overlay whose `aria-label` is `固定剧情对话`.
7. Keep `showRubbing`, `YuanRubbingCompare`, `yuanSeenScripts`, `onRubbingSubmit`, the `拓片比对` button, and the `拓片校勘` overlay unchanged.

- [x] **Step 3: Verify the Vite transformation is green**

Re-run the Step 1 command.

Expected after the edit: exit code 0 and output `PASS`.

- [x] **Step 4: Verify TypeScript and Vue templates**

Run from `frontend`:

```powershell
npm run typecheck
```

Expected: exit code 0 with no vue-tsc errors.

- [x] **Step 5: Verify the production build**

Run from `frontend`:

```powershell
npm run build
```

Expected: exit code 0 and a completed Vite production build.

- [x] **Step 6: Confirm retained behavior and absence of stale imports**

Run from the workspace root:

```powershell
rg -n "YuanFixedDialogue|dialogueOpen|startFixedDialogue|onDialogueDone" frontend/src/pages/chapter/C02Scene.vue
rg -n "YuanRubbingCompare|showRubbing|onRubbingSubmit|拓片比对|拓片校勘" frontend/src/pages/chapter/C02Scene.vue
```

Expected: the first search returns no matches; the second search returns the retained import, state, handler, button, and overlay.
