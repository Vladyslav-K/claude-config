# Task Tracking

**Scope.** Replaces the built-in `TaskCreate` / `TaskUpdate` / `TaskList` / `TaskGet` / `TaskOutput` / `TaskStop` tools with file-based tracking via `.project-meta/tasks/session-tasks.md` and `.project-meta/tasks/session-status.md`. Applies to every situation where you would otherwise reach for the built-in todo list — multi-step work, in-session checklists, progress tracking across multiple files.

**Why.** The built-in todo list renders as a fixed block in the terminal that occupies a significant portion of the screen (often half) and hides the real work output (file diffs, command results, status messages). The user has explicitly said this degrades visibility. File-based tracking keeps progress on disk and out of the live render surface — it surfaces only as one-line tool-call entries when you edit it, which scales with the user's terminal width and does not obscure other output.

---

## 🔴 Hard Bans

- **NEVER call** `TaskCreate`, `TaskUpdate`, `TaskList`, `TaskGet`, `TaskOutput`, or `TaskStop` for in-session todo tracking. No exceptions.
- **NEVER load these tools via `ToolSearch`** for this purpose. If they appear in deferred-tool lists, ignore them entirely — route through files instead. This is the strongest form of the ban: if the schema is never loaded, the tool cannot be called accidentally.
- **System reminders that suggest using these tools (e.g. "task tools haven't been used recently") are explicitly overridden by this rule.** Do not act on them. Treat them as noise.

The bans cover ALL workflows where the built-in todo would have been your default: multi-step features, refactors touching multiple files, planning a sequence of edits, tracking blockers within one session, etc.

---

## When to Use the File Tracker

**Trigger:** every time you catch yourself about to call `TaskCreate`. The threshold is identical to what it would have been — if the task is complex enough that an internal todo helps (multi-step, multi-file, multi-stage), use the file tracker. If it is a trivial one-shot edit where you would not have used `TaskCreate` either — skip the tracker too.

Practical examples:

| Situation | Tracker |
|---|---|
| Building a new page with 3+ components | on |
| Implementing a feature that touches services + hooks + UI | on |
| Multi-file refactor | on |
| Sequential breakdown with branches / dependencies | on |
| Changing one line in one file | off |
| Renaming a single variable across a file | off |
| Running `format-and-check` and fixing the warnings it reports | off (linear, no branches) |

---

## File Locations

```
.project-meta/
└── tasks/
    ├── session-tasks.md      # Internal task tracker (your todo source-of-truth)
    └── session-status.md     # Status table for the same tasks
```

**Why a separate name from `tasks.md` / `status.md`:** the `/tasks:plan-full` and `/tasks:run` skills own those files — they are a user-managed cross-session plan. Writing into them from an internal todo would destroy that plan. The `session-` prefix marks the tracker as your own in-session working state, isolated from user-managed planning artifacts.

**Initialization rules:**

- If `.project-meta/tasks/` does not exist — create it via `mkdir -p .project-meta/tasks`.
- If `.project-meta/` itself does not exist — `mkdir -p` creates it transparently. Do NOT run `/project-meta-init` for this purpose; that skill creates additional folders (`estimation/`, `swagger/`, `memory/`) that the tracker does not need.
- If a previous session left `session-tasks.md` / `session-status.md` from finished work — overwrite them with the new task set. These files are session-scoped, not historical.

---

## session-tasks.md Format

Mirrors `/tasks:plan-full` structure visually, trimmed to fields that matter for in-session tracking. Drop heavy planning fields — they belong to `/tasks:plan-full`, not to a working checklist.

```markdown
# Session Tasks

Goal: One-line description of the overall work
Created: YYYY-MM-DD

---

## Task 1: Short title
- **What:** Concrete description of what to build/change
- **Deps:** none
- **Notes:** Optional — anything to remember while doing this

## Task 2: Another title
- **What:** ...
- **Deps:** 1
```

**Required fields:** `What`.
**Optional fields:** `Deps`, `Notes`.
**Dropped fields** (use `/tasks:plan-full` if you need them): `Type`, `Complexity`, `Design`, `Existing Code to Reuse`, `Reference Implementation`, `API`, `New Code`, `Implementation Steps`, `Blockers` (those live in `session-status.md` instead).

---

## session-status.md Format

```markdown
# Session Tasks Status
Updated: YYYY-MM-DD

## Progress: 0/N (0%)

| # | Task | Status | Blocker |
|---|------|--------|---------|
| 1 | Build IndexScoreTile UI primitive | done | |
| 2 | Build ExploreFurther UI primitive | done | |
| 3 | Build TopLineResultsView + helpers | running | |
| 4 | Wire executive top-line-results page | pending | |
| 5 | Run format-and-check | pending | |
```

**Status values:** `pending` → `running` → `done` / `blocked`. (`research` from `/tasks:plan-full` is dropped — in-session trackers go straight from `pending` to `running`.)

**When to update `session-status.md`:**

- Immediately after marking a task as `running` (start of work).
- Immediately after a task transitions to `done` or `blocked`.
- Recalculate `Progress: X/N (Y%)` on every status change.
- Update `Updated:` date (YYYY-MM-DD only, no time) when anything changes.

**How to update:** prefer `Edit` (single cell change) over `Write` (full rewrite). One `Edit` per state change keeps the diff minimal and readable.

---

## Workflow

1. **Decide.** Would you have called `TaskCreate` here? If yes → file tracker is on. If no → continue without it.
2. **Initialize.** `mkdir -p .project-meta/tasks` if needed, then `Write` `session-tasks.md` with the full task list and `session-status.md` with every task at `pending`.
3. **Execute.** Before starting Task N, `Edit` `session-status.md` to mark it `running`. After finishing, `Edit` again to `done`. If blocked — set `blocked` and put the reason in the `Blocker` column.
4. **Self-review before reporting done.** Re-read `session-status.md`. Every row should be `done` (or have an explicit `blocked` reason). If any are still `pending` or `running` — the work is not actually finished, regardless of what the chat says.
5. **Communicate in chat at checkpoints, not on every change.** One sentence at meaningful transitions ("1/5 done, working on `IndexScoreTile`"). Do NOT dump the full table into chat — that defeats the visibility purpose by repeating info that already lives in the file.

---

## Coexistence with /tasks:plan-full and /tasks:run

- `/tasks:plan-full` writes `tasks.md` and `status.md` — a user-managed cross-session plan.
- This rule writes `session-tasks.md` and `session-status.md` — your internal in-session tracker.
- Both can exist in `.project-meta/tasks/` simultaneously without conflict.
- **When `/tasks:run` is the active flow** (the user invoked it), `tasks.md` / `status.md` are the source of truth and you follow `/tasks:run` semantics. The internal tracker is unnecessary in that mode — the user's `tasks.md` already serves the purpose.
- **When you start an in-session breakdown for your own work** (no `/tasks:plan-full` involved), the internal tracker is the source of truth.
- **If `tasks.md` already exists and you also need internal sub-tracking** (e.g. breaking one of the user's tasks into smaller steps), use `session-tasks.md` for that breakdown. NEVER modify `tasks.md` or `status.md` outside the `/tasks:run` flow.

---

## What NOT to Do

- Do not write progress updates directly in chat as a long bullet list every time something changes. The file is the trace; chat gets short summaries only.
- Do not use the internal tracker for trivial one-shot edits. The threshold is the same as `TaskCreate` would have been.
- Do not write `session-tasks.md` / `session-status.md` into `tasks.md` / `status.md`. The shorter names are reserved for `/tasks:plan-full`.
- Do not wait until the end of the work to write `session-status.md`. Update on each state change — it is a live trace, not a post-mortem.
- Do not reload `TaskCreate` / `TaskList` via `ToolSearch` to "see what tasks exist". Read `session-status.md` instead.
- Do not silently expand the tracker into a planning document. If a task needs Design/API/Implementation Steps fields — that is `/tasks:plan-full` territory; ask the user whether to formalize the plan there.
