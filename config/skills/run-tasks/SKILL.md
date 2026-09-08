---
name: run-tasks
description: Execute the next available task from .project-meta/tasks/tasks.md, then enter testing/fixing mode. Does NOT continue to the next task.
---

# Task Execution (Single Task Mode)

## Additional context from user before start task
$ARGUMENTS

## Purpose
Execute **exactly ONE task** from `.project-meta/tasks/tasks.md` — the next available one.
After completing the task — STOP, report, and enter **testing & fixing mode**. Do NOT proceed to the next task.

---

## Step 1: Read and Parse

Read tasks.md and status.md **IN PARALLEL** (two Read calls, one message):

```
From tasks.md: ID, Title, What, Deps, Type, Design/Screenshot paths, Decisions
From status.md: current status, Blocker column and commit message per task
Merge → task list with statuses
Count: total, done, pending, blocked
```

## Step 2: Find Next Available Task

1. Find all tasks with status `pending` **and an empty Blocker column** (`blocked` tasks and tasks with blocker text are skipped, even if their status says `pending`)
2. Filter out tasks with unmet deps (deps not `done`)
3. Order by ID (lowest first)
4. **Pick the FIRST available task** — this is the only task you will execute

If no tasks are available → report to user and stop. If the only remaining tasks are `blocked`, list each one with its blocker text so the user knows what to provide.

## Step 3: Execute the Task

Follow the **Task Execution Cycle** (section below). Update status.md as you move through states:

1. Update status.md → `research`
2. **Research** (cycle step 1)
3. **Plan** (cycle step 2) — for visual/complex tasks present a plan and wait for approval; simple code tasks → skip
4. Update status.md → `running`
5. **Implement** (cycle step 3) → **Self-review** (cycle step 4) → **Verify** (cycle step 5)
6. Update status.md → `done`, update progress %

For `visual` and `mixed` tasks invoke the `design-work` skill before implementing — it holds the design-to-code rules (measuring, tokens, missing states, breakpoints). Do not restate them here.

If the task turns out to be blocked at any point (missing API, missing design asset, contradiction the user must resolve) → see **Blocked During Execution** below.

## Step 4: Report and Enter Testing Mode (MANDATORY)

**After completing the task, you MUST STOP and provide:**

### Completion Report
1. **Task ID and title** that was completed
2. **What was done** — brief summary of changes (files created/modified, key decisions)
3. **Files changed** — list all created/modified files with short descriptions

### Testing Instructions
4. **How to test** — step-by-step instructions for the user to verify the task:
   - What to run (dev server, specific URL, etc.)
   - What to check visually or functionally
   - Expected behavior
   - Edge cases worth testing

### Status
5. **Progress** — how many tasks are done out of total (done/total)

### Testing Mode Message
> 🧪 Задача виконана. Тестуй результат — якщо є зауваження чи баги, пиши, виправлю. Коли буде все ок — запусти `/run-tasks` для наступної задачі.

### Commit Line (last thing in the message)
The very last element of the report is the task's commit message taken from status.md (the text after the title in the Task cell), alone in a fenced code block so the user can copy it with one click:

```
feat: add items list page with search and delete
```

The report is written in Ukrainian; the commit message stays in English exactly as in status.md. The report is the final text of the turn — no tool calls after it, otherwise the CLI collapses it.

---

## Task Execution Cycle

The research → plan → implement → review → verify cycle for a single task:

### 1. Research
- Read the task's full entry in tasks.md (What, Deps, Design, Existing Code to Reuse, Reference Implementation, API, New Code, Implementation Steps, Notes, Decisions). `Decisions` are the user's verbatim answers from planning and testing — treat them as requirements, do not re-ask what is already answered there
- Read matched design docs (`*__design.md`) **fully**; read screenshots for visual tasks
- Read the existing components/services/hooks the plan references — verify they exist and learn their API (props, signatures)
- Read 1-2 reference implementations to match the project's patterns
- Confirm API endpoints exist (swagger / existing code) — **never invent** endpoints, field names, or response shapes

### 2. Plan
- **Visual / complex tasks:** present a short implementation plan as the final text of the turn (one or two lines per point, no code) and end with «затверджуєш / що змінити?»; wait for approval before coding. Choices between alternatives go through AskUserQuestion **before** the plan text, never after it in the same turn
- **Simple code tasks:** skip the plan and implement directly

### 3. Implement
- Follow THIS project's conventions exactly — file/folder structure, naming, styling approach
- Build per the Implementation Steps from tasks.md and respect every entry in `Decisions`
- **Reuse existing components** — don't duplicate; if a variant is missing, extend the existing component, don't create a one-off
- Code cleanliness rules (no raw components/icons, no raw styles, split into components, basic a11y) come from the global CLAUDE.md, section «Чистота коду»
- **Visual / mixed tasks:** follow the `design-work` skill — pixel-perfect transfer, verbatim static text, no substituted icons/assets, token mapping, missing states
- If a question comes up that only the user can answer → ask via AskUserQuestion, then append the answer verbatim to the task's `Decisions` in tasks.md (see "tasks.md Updates")

### 4. Self-review
- Re-check the result against the task requirements, `Decisions` and design — every element present and correct
- No leftover TODOs, empty/placeholder handlers, disabled fields, or empty catch blocks (unless explicitly agreed with the user)
- Walk through the result as a real user: first visit with empty data, loading, error, and the final state — not only the happy path
- Confirm every requirement of the task is fully met

### 5. Verify
- Run the task completion gate from the global CLAUDE.md («Гейт завершення задачі»): `format`, then `check-errors` with the **full, unmodified output** (no `tail`/`head`, no output-limiting flags), then the security checklist on your own changes
- If `format` / `check-errors` don't exist but can be created → add them; if the project is too specific → use available equivalents (`prettier --write`, `eslint`, `tsc --noEmit`)
- Fix every error caused by this task's changes — the task is not done while they remain
- **Pre-existing errors outside the task's files are not yours to fix:** do not touch them, list them in the report (count + files) and let the user decide

---

## 🚨 CRITICAL: Single Task Mode Rules

1. **Execute EXACTLY ONE task** — do NOT continue to the next task after completion
2. **After the task is done — you are in TESTING & FIXING MODE:**
   - If the user reports issues → fix them immediately
   - If the user asks for changes → implement them
   - Run `format` then `check-errors` after every fix
   - Stay on this task until the user is satisfied
3. **NEVER auto-continue** to the next task — the user must explicitly run `/run-tasks` again
4. **This command = one task cycle.** Each invocation handles one task, period.

---

## status.md Updates

1. Find row by task ID → replace status
2. Update "Updated:" date (YYYY-MM-DD only, no time — use `currentDate` from session context)
3. Recalculate progress: `done_count/total (percentage%)`

**Status values:** `pending` → `research` → `running` → `done` / `blocked`

---

## tasks.md Updates

tasks.md is read-only after planning with **one exception**: the `### Decisions` section of the task you are executing. Every answer the user gives during this task — while planning, implementing or in testing mode — is appended there verbatim, one bullet per answer:

```markdown
### Decisions
- (planning, YYYY-MM-DD) Q: ... A: "..."
- (run, YYYY-MM-DD) Q: Порожній стан таблиці — текст? A: "Nothing here yet, як на сторінці users"
- (testing, YYYY-MM-DD) A: "кнопку Export прибрати, бекенд не готовий"
```

If the section does not exist for this task — add it as the last section of the task's entry. Nothing else in tasks.md is edited.

---

## Blocked During Execution

When the task cannot be finished without something only the user can provide (an endpoint, an asset, a decision that changes the scope):

1. Ask the user via AskUserQuestion first — most blockers are resolved in one answer, and the answer goes to `Decisions`.
2. If the user cannot resolve it now: set the task's status in status.md to `blocked`, write a short reason into the `Blocker` column, and stop the task.
3. Report: what was already implemented (files), what exactly is missing, and what the user must do to unblock. Do not pick another task — the user decides whether to run `/run-tasks` for the next one.
4. When the user provides the missing piece later, they (or you, on their instruction) clear the `Blocker` column and set the status back to `pending`; the next `/run-tasks` picks the task up again.

No separate blocked report file — status.md is the single source of blocker state.

---

## Rules

1. **ONE task per invocation** — complete it, report, enter testing mode, DONE
2. **Follow the Task Execution Cycle** (section above) for research/plan/implement/review/verify
3. **Update status.md after EACH state change**
4. **tasks.md is read-only** except for appending to the current task's `Decisions` (see "tasks.md Updates")
5. **NEVER proceed to the next task** — user must run the command again
6. **When in doubt about complexity → present a plan**
7. **NEVER skip the report step** — even for simple tasks; the report ends with the commit line
8. **Testing mode after completion** — user feedback → fix → re-verify; scope changes requested in testing mode go to `Decisions`
9. **Never pick a `blocked` task or a task with blocker text** — only the user unblocks tasks
