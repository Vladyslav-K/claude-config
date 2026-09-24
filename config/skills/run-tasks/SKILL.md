---
name: run-tasks
description: Execute the next available task from .project-meta/tasks/tasks.md without re-asking what the plan already answers, move the finished task to .project-meta/tasks/done/YYYY-MM-DD/, then enter testing/fixing mode. Does NOT continue to the next task.
---

# Task Execution (Single Task Mode)

## Additional context from user before start task
$ARGUMENTS

## Purpose
Execute **exactly ONE task** from `.project-meta/tasks/tasks.md` — the next available one.
After completing the task — move it to `done/`, STOP, report, and enter **testing & fixing mode**. Do NOT proceed to the next task.

The plan was researched and agreed with the user during `/plan-tasks` (or `/sort-and-plan`), including a dry run of every task. Execute from it directly: no plan approval, no re-asking what `tasks.md` already answers. Every unnecessary question costs the user a context switch on every task.

## Task Board

```
.project-meta/tasks/
├── todo/            # Sources of planned tasks
├── blocked/         # Tasks with a blocker (the reason is in the `## Blocked` block at the bottom)
├── waiting/         # The user's postponed tasks — never read or touch
├── done/            # Finished tasks: done/YYYY-MM-DD/
├── screenshots/     # Shared design docs and screenshots
├── tasks.md         # Current plan
└── status.md        # Current plan statuses
```

---

## Step 1: Read and Parse

Read tasks.md and status.md:

```
From tasks.md: ID, Title, What, Source, Deps, Type, Design/Screenshot paths, Decisions
From status.md: current status, Blocker column and commit message per task
Merge → task list with statuses
Count: total, done, pending, blocked
```

If there is no tasks.md — report that there is no active plan (finished plans are archived in `done/YYYY-MM-DD/`) and suggest `/sort-and-plan`; stop.

## Step 2: Find Next Available Task

1. Find all tasks with status `pending` **and an empty Blocker column** (`blocked` tasks and tasks with blocker text are skipped, even if their status says `pending`)
2. Filter out tasks with unmet deps (deps not `done`)
3. Order by ID (lowest first)
4. **Pick the FIRST available task** — this is the only task you will execute

If no tasks are available → report to user and stop. If the only remaining tasks are `blocked`, list each one with its blocker text so the user knows what to provide.

## Step 3: Execute the Task

Follow the **Task Execution Cycle** (section below). Update status.md as you move through states:

1. Update status.md → `research`
2. **Research** (cycle step 1) → **Check the plan** (cycle step 2)
3. Update status.md → `running`
4. **Implement** (cycle step 3) → **Verify** (cycle step 4)
5. Update status.md → `done`, update progress %
6. **Move finished tasks** (section below)

For `visual` and `mixed` tasks invoke the `design-work` skill before implementing — it holds the design-to-code rules (measuring, tokens, missing states, breakpoints). Do not restate them here.

If the task turns out to be blocked at any point (missing API, missing design asset, contradiction the user must resolve) → see **Blocked During Execution** below.

## Step 4: Report and Enter Testing Mode (MANDATORY)

**After completing the task, you MUST STOP and provide:**

### Completion Report
1. **Task ID and title** that was completed
2. **What was done** — brief summary of changes (files created/modified, key decisions)
3. **Files changed** — list all created/modified files with short descriptions
4. **Task board** — where the task source moved (`done/YYYY-MM-DD/...`), and whether the plan was archived

### Testing Instructions
5. **How to test** — step-by-step instructions for the user to verify the task:
   - What to run (dev server, specific URL, etc.)
   - What to check visually or functionally
   - Expected behavior
   - Edge cases worth testing

### Status
6. **Progress** — how many tasks are done out of total (done/total)

### Testing Mode Message
> 🧪 Задача виконана. Тестуй результат — якщо є зауваження чи баги, пиши, виправлю. Коли буде все ок — запусти `/run-tasks` для наступної задачі.

### Commit Line (last thing in the message)
The very last element of the report is the task's commit message taken from status.md (the text after the `. \|` separator in the Task cell, without the separator itself), alone in a fenced code block so the user can copy it with one click:

```
feat: add items list page with search and delete
```

The report is written in Ukrainian; the commit message stays in English exactly as in status.md. The report is the final text of the turn — no tool calls after it, otherwise the CLI collapses it.

---

## Task Execution Cycle

The research → check → implement → verify cycle for a single task:

### 1. Research
- Read the task's full entry in tasks.md (What, Source, Deps, Design, Existing Code to Reuse, Reference Implementation, API, New Code, Implementation Steps, States and Texts, Notes, Decisions). `Decisions` are the user's verbatim answers from sorting, planning and testing — treat them as requirements
- Read the task's `Source` in full — the `.md` file, or every file in the task folder
- Read matched design docs (`*__design.md`) **fully**; read screenshots for visual tasks (task folder, `tasks/screenshots/`)
- Read the existing components/services/hooks the plan references — verify they exist and learn their API (props, signatures)
- Read 1-2 reference implementations to match the project's patterns
- Confirm API endpoints exist (swagger / existing code) — **never invent** endpoints, field names, or response shapes

### 2. Check the Plan
Do not present a plan and do not wait for approval — the plan in tasks.md is already approved. Compare it with what research found:
- **Plan matches reality** → go straight to implementation.
- **Discrepancy or gap** (a referenced component/endpoint changed or disappeared, the design shows something the plan does not cover, two requirements contradict each other) → first try to resolve it from the sources listed in "Before Asking the User"; only if they do not answer it — ask via AskUserQuestion and record the answer in `Decisions`.

### 3. Implement
- Follow THIS project's conventions exactly — file/folder structure, naming, styling approach
- Build per the Implementation Steps and States and Texts from tasks.md and respect every entry in `Decisions`
- **Reuse existing components** — don't duplicate; if a variant is missing, extend the existing component, don't create a one-off
- Code cleanliness rules (no raw components/icons, no raw styles, split into components, basic a11y) come from the global CLAUDE.md, section «Чистота коду»
- **Visual / mixed tasks:** follow the `design-work` skill — pixel-perfect transfer, verbatim static text, no substituted icons/assets, token mapping, missing states
- If a question comes up → go through "Before Asking the User" first; ask via AskUserQuestion only what remains, then append the answer verbatim to the task's `Decisions` in tasks.md (see "tasks.md Updates")

### 4. Verify
- Run the task completion gate from the global CLAUDE.md («Гейт завершення задачі»): `format`, then `check-errors` with the **full, unmodified output** (no `tail`/`head`, no output-limiting flags), then the security checklist on your own changes
- If `format` / `check-errors` don't exist but can be created → add them; if the project is too specific → use available equivalents (`prettier --write`, `eslint`, `tsc --noEmit`)
- Fix every error caused by this task's changes — the task is not done while they remain
- **Pre-existing errors outside the task's files are not yours to fix:** do not touch them, list them in the report (count + files) and let the user decide

---

## Before Asking the User

A question is justified only when none of these sources answers it. Check them in order:
1. The task's `Decisions`, States and Texts, Implementation Steps and Notes in tasks.md
2. The task's `Source` (file or folder) and its design material
3. `Decisions` of other tasks in the same plan — the user may have answered the same question for a sibling task
4. The project itself — an existing precedent for the same pattern, the API/swagger

If the answer is found — follow it and do not ask. If the question is really new — ask it, record the answer in `Decisions`, and mention it in the report so the user sees what the plan missed.

---

## Single Task Mode

1. Execute one task per invocation; the user reviews each result before the next one starts
2. **After the task is done — you are in TESTING & FIXING MODE:**
   - If the user reports issues → fix them immediately
   - If the user asks for changes → implement them
   - Run `format` then `check-errors` after every fix
   - Stay on this task until the user is satisfied
3. The next task starts only when the user runs `/run-tasks` again

---

## Move Finished Tasks

Right after setting the status to `done`:

1. **Task source → `done/YYYY-MM-DD/`** (today's date from `currentDate`, YYYY-MM-DD). Move every path from the task's `Source` (file or whole task folder) from `todo/` to `done/YYYY-MM-DD/`, creating the folder with `mkdir -p`. If other tasks in the plan share the same `Source` and are not `done` yet — leave it in `todo/`; it moves together with the last of them. Shared `tasks/screenshots/` never moves.
2. **Plan archive.** When no task in status.md is left as `pending`, `research` or `running` (every task is `done` or `blocked`), move `tasks.md` and `status.md` to the same `done/YYYY-MM-DD/`. Blocked tasks lose nothing: their sources already live in `blocked/` with the reason, and `/sort-and-plan` picks them up later.
3. **Never overwrite.** Move with `mv -n` and check the result. If the target name is already taken — add a numeric suffix (`tasks-2.md`, `status-2.md`, `items-list-2.md`). If a `Source` path does not exist (the user moved it) — skip it and say so in the report.

In testing mode after the archive, `tasks.md Updates` go to the archived copy in `done/YYYY-MM-DD/`.

---

## status.md Updates

1. Find row by task ID → replace status
2. Update "Updated:" date (YYYY-MM-DD only, no time — use `currentDate` from session context)
3. Recalculate progress: `done_count/total (percentage%)`

**Status values:** `pending` → `research` → `running` → `done` / `blocked`

---

## tasks.md Updates

tasks.md is read-only after planning with **one exception**: the `### Decisions` section of the task you are executing. Every answer the user gives during this task — while implementing or in testing mode — is appended there verbatim, one bullet per answer:

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
2. If the user cannot resolve it now:
   - set the task's status in status.md to `blocked` and write a short reason into the `Blocker` column;
   - move the task's `Source` from `todo/` to `blocked/` with `mv -n` (if other not-done tasks share the same `Source`, leave it in `todo/` and say so in the report);
   - append the `## Blocked` block to the bottom of the task's `.md` file (for a task folder — its main description file), replacing an existing `## Blocked` block if there is one. Nothing above the block changes:

```markdown
## Blocked
_Оновлено: YYYY-MM-DD_
- Причина: що саме відсутнє або незрозуміле, конкретно
- Перевірено: де шукав (swagger, файли коду, дизайн)
- Вже зроблено: які файли реалізовані до блокера
- Для розблокування: що має зʼявитись або що має вирішити юзер
```

3. Stop the task. Report: what was already implemented (files), what exactly is missing, what the user must do to unblock. Do not pick another task — the user decides whether to run `/run-tasks` for the next one.
4. When the missing piece appears, `/sort-and-plan` moves the task back to `todo/` and plans it again.

---

## Rules

1. **ONE task per invocation** — complete it, move it to `done/`, report, enter testing mode, DONE
2. **Follow the Task Execution Cycle** (section above) for research/check/implement/verify
3. **No plan approval** — the plan in tasks.md is already approved; stop only for a real discrepancy or gap (cycle step 2)
4. **Go through "Before Asking the User"** before every question
5. **Update status.md after EACH state change**
6. **tasks.md is read-only** except for appending to the current task's `Decisions` (see "tasks.md Updates")
7. **NEVER skip the report step** — even for simple tasks; the report ends with the commit line
8. **Testing mode after completion** — user feedback → fix → re-verify; scope changes requested in testing mode go to `Decisions`
9. **Never pick a `blocked` task or a task with blocker text** — only the user (or `/sort-and-plan`) unblocks tasks
10. **Never read or touch `waiting/`**; never delete or overwrite task files — only move them with `mv -n`
