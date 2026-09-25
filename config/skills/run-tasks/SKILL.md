---
name: run-tasks
description: Execute the next available task from .project-meta/tasks/tasks.md without re-asking what the plan already answers, save its testing instructions into the task file, run them in the browser with /browser-test, move the finished task to .project-meta/tasks/done/DD-MM-YYYY/, then enter testing/fixing mode. The last task of the plan (QA) compiles the testing instructions of all done tasks into one qa.md for QA and runs it as a browser regression pass. Does NOT continue to the next task.
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
├── done/            # Finished tasks: done/DD-MM-YYYY/ (plus the archived plan and its qa.md)
├── screenshots/     # Shared design docs and screenshots
├── tasks.md         # Current plan
└── status.md        # Current plan statuses
```

The last task of every plan is the `QA` task (ID `QA`, Type `qa`). It compiles `qa.md`, runs it as a browser regression pass and follows its own flow — see **QA Task** below.

---

## Step 1: Read and Parse

Read tasks.md and status.md:

```
From tasks.md: ID, Title, What, Source, Deps, Type, Design/Screenshot paths, Test Setup, Decisions
From status.md: current status, Blocker column and commit message per task
Merge → task list with statuses
Count: total, done, pending, blocked
```

If there is no tasks.md — report that there is no active plan (finished plans are archived in `done/DD-MM-YYYY/`) and suggest `/sort-and-plan`; stop.

## Step 2: Find Next Available Task

1. Find all tasks with status `pending` **and an empty Blocker column** (`blocked` tasks and tasks with blocker text are skipped, even if their status says `pending`)
2. Filter out tasks with unmet deps (deps not `done`)
3. Order by ID (lowest first)
4. **Pick the FIRST available task** — this is the only task you will execute
5. The `QA` task is never picked while any other task is `pending`, `research` or `running`. It becomes available when every other task is `done` or `blocked` — blocked tasks do not hold it back.

If no tasks are available → report to user and stop. If the only remaining tasks are `blocked`, list each one with its blocker text so the user knows what to provide.

## Step 3: Execute the Task

Follow the **Task Execution Cycle** (section below). Update status.md as you move through states:

1. Update status.md → `research`
2. **Research** (cycle step 1) → **Check the plan** (cycle step 2)
3. Update status.md → `running`
4. **Implement** (cycle step 3) → **Verify** (cycle step 4)
5. **Write the testing instructions** into the task file (section **Testing Instructions in the Task File** below)
6. **Browser test** — run those instructions with the `browser-test` skill (section **Browser Test** below)
7. Update status.md → `done`, update progress %
8. **Move finished tasks** (section below)

The `QA` task skips this list and follows **QA Task** instead.

For `visual` and `mixed` tasks invoke the `design-work` skill before implementing — it holds the design-to-code rules (measuring, tokens, missing states, breakpoints). Do not restate them here.

If the task turns out to be blocked at any point (missing API, missing design asset, contradiction the user must resolve) → see **Blocked During Execution** below.

## Step 4: Report and Enter Testing Mode (MANDATORY)

**After completing the task, you MUST STOP and provide:**

### Completion Report
1. **Task ID and title** that was completed
2. **What was done** — brief summary of changes (files created/modified, key decisions)
3. **Files changed** — list all created/modified files with short descriptions
4. **Task board** — where the task source moved (`done/DD-MM-YYYY/...`), and whether the plan was archived

### Browser Test
5. **Result** — the output block of `browser-test` as is (step 3.6). If the test did not run or left ❌ — this goes to the very top of the report, before the task summary.

### Testing Instructions
6. **How to test** — the same instructions that were written to the task file's `## Testing` block (step 3.5), with the path of that file:
   - What to run (dev server, specific URL, etc.)
   - What to check visually or functionally
   - Expected behavior
   - Edge cases worth testing

### Status
7. **Progress** — how many tasks are done out of total (done/total)

### Testing Mode Message
> 🧪 Задача виконана і прогнана в браузері — звіт у `report.md` вище. Перевір результат, особливо кроки ⚠️ — якщо є зауваження чи баги, пиши, виправлю. Коли буде все ок — запусти `/run-tasks` для наступної задачі.

If the browser test was skipped (nothing observable in the browser) or did not run, replace the first sentence with «Задача виконана, у браузері не тестувалась: <причина>.»

### Commit Line (last thing in the message)
The very last element of the report is the task's commit message taken from status.md (the text after the `. \|` separator in the Task cell, without the separator itself), alone in a fenced code block so the user can copy it with one click:

```
feat: add items list page with search and delete
```

The report is written in Ukrainian; the commit message stays in English exactly as in status.md. The report is the final text of the turn — no tool calls after it, otherwise the CLI collapses it.

The `QA` task has its own report — see **QA Task**.

---

## Task Execution Cycle

The research → check → implement → verify cycle for a single task:

### 1. Research
- Read the task's full entry in tasks.md (What, Source, Deps, Design, Existing Code to Reuse, Reference Implementation, API, New Code, Implementation Steps, States and Texts, Test Setup, Notes, Decisions). `Decisions` are the user's verbatim answers from sorting, planning and testing — treat them as requirements
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
   - If a fix or a change changes what or how to test — update this task's subsection in the `## Testing` block (the file may already be in `done/`), so it describes the final behaviour
   - Re-run the affected scenarios with `browser-test` in the task's existing run folder, and put its output block into the reply
   - Stay on this task until the user is satisfied
3. The next task starts only when the user runs `/run-tasks` again

---

## Testing Instructions in the Task File

Before the task is set to `done`, the testing instructions from the report are written into the task's own file. They move to `done/` together with the task, and the `QA` task compiles them into one file for QA later.

- **Where:** the task's `Source` `.md` file; for a task folder — its main description file; for a task with several `Source` entries — the first one.
- **Block:** `## Testing` at the bottom of the file. If the file has a `## Blocked` block, `## Testing` goes right above it — `## Blocked` always stays last. Nothing else in the file changes.
- **One subsection per task:** `### Task N: <title exactly as in tasks.md>` — the `QA` task finds the instructions by this heading. Tasks that share one `Source` each get their own subsection inside the same `## Testing` block. An existing subsection of this task is replaced; subsections of other tasks stay untouched.
- **Content:** the same instructions as in the report, in Ukrainian. Write them for someone who does not read the code: every step is an action and the expected result. Cover every role, state and edge case of the task (empty state on the first visit, errors, validation, direct URL), not only the happy path. Every step relies on behaviour you saw in the code — no steps added "because it is logical".

```markdown
## Testing

### Task 3: Список items з пошуком і видаленням
_Оновлено: DD-MM-YYYY_

Передумови: `pnpm dev`, сторінка `/items`, юзер з роллю admin, у базі є хоча б 2 items.

1. **Список**: відкрий `/items`. Очікується: таблиця з 6 колонками, 10 рядків на сторінці.
2. **Пошук**: введи "abc" у поле Search. Очікується: лишаються тільки items, у назві яких є "abc".
3. **Видалення**: натисни Delete у рядку, підтверди в модалці "Delete this item?". Очікується: тост "Item deleted", рядок зник.

Крайні випадки:
- Порожній список (items ще немає) — текст "No items yet", кнопки немає.
- Юзер з роллю viewer — кнопки Delete немає.
```

---

## Browser Test

Right after the `## Testing` subsection is written, invoke the `browser-test` skill via the Skill tool. Pass in the arguments:
- the scenario: the path of the task file and the `### Task N: <title>` subsection just written;
- the run slug: `task-<N>-<short-summary>` (English kebab-case, e.g. from the commit message without its type);
- the task's `Test Setup` from tasks.md (accounts, data, allowed destructive actions) and its Type (`visual` / `mixed` tasks get the design comparison).

The skill runs the scenario, fixes clear failures in this task's code (with `format` / `check-errors` after every fix) and asks the user about the rest. The task becomes `done` after that:
- every ❌ is fixed, or the user decided what to do with it (the answer goes to `Decisions`);
- a task with nothing observable in the browser (Type `code` without UI effect) skips the test — the skill returns the reason;
- the test did not run (no Playwright MCP, the dev server did not start) — the task still becomes `done`, and the report says prominently that it was not tested.

Fixes made during the test belong to this task: they are covered by its commit message and, if they change the behaviour, by an update of its `## Testing` subsection.

---

## QA Task

The last task of every plan has ID `QA` and Type `qa` (added by `/plan-tasks`). It compiles the `## Testing` subsections of all `done` tasks of this plan into one `qa.md`, which the user hands to QA, and then runs every scenario of `qa.md` in the browser as a regression pass — later tasks may have broken what earlier ones delivered. It is picked only under the rule from Step 2.5.

### Steps
1. Update status.md → `running`.
2. **Collect the tasks** from status.md: every `done` task except `QA`, and every `blocked` task with its Blocker text.
3. **Find the instructions.** For each `done` task, find its `### Task N: <title>` subsection inside a `## Testing` block: search `done/` subfolders dated from the plan's `Created` date onward (folder names are DD-MM-YYYY, so compare them as dates, not as strings), then `todo/` and `blocked/` (a `Source` shared with a blocked task moves to `blocked/` together with the instructions). Also read the task's entry in tasks.md (What, States and Texts, Decisions) for context.
   - No subsection found (the task was done before this flow existed, or the user moved the file) → compose the steps from the tasks.md entry and the code, and name these tasks in the report.
4. **Collect the prerequisites.** Environment, URLs, roles, accounts and test data come only from the instructions, the project `CLAUDE.md`, README and `.env.example`. Never invent them: if something is missing, write it more generally and name the gap in the report.
5. **Compose the file** by the rules and the template below.
6. **Write** `done/DD-MM-YYYY/qa.md` (today, from `currentDate` converted to DD-MM-YYYY), creating the folder with `mkdir -p`. Never overwrite: if `qa.md` already exists — use `qa-2.md`, `qa-3.md`.
7. **Regression pass.** Invoke the `browser-test` skill with the whole `qa.md` as the scenario and the run slug `qa-<goal-summary>`. For every ❌ name the task whose behaviour broke (the scenario lists its tasks). A clear regression in the code of this plan is fixed by the skill's rules — with `format` / `check-errors` after the fix; the fix gets its own commit line in the report (`fix: ...`), because the task it belongs to is already committed. Anything else — the skill asks the user.
8. Update status.md → `done`. The `QA` task has no `Source`, so there is nothing to move; the plan is archived to the same `done/DD-MM-YYYY/` (Move Finished Tasks, step 2).
9. **Report** (below) and enter testing mode: the user may ask to change the file — edit it and keep the rules below; after a regression fix, re-run the affected scenarios with `browser-test`.

No `design-work` and no `## Testing` block for this task. It changes code only when the regression pass fixes something.

### Composition Rules
The file is a single testing pass through everything the plan delivered, not a concatenation of the task subsections:
- **Scenarios by feature or user flow**, not by task order. When several tasks touch the same page or flow, they form one end-to-end scenario, and the shared setup is written once.
- **Duplicates are merged.** If instructions contradict each other (a later task changed the behaviour an earlier one describes), the later task wins — it is the final behaviour; check the code if unclear.
- **Each scenario names the tasks it covers** by their titles, so QA can map a bug to a task.
- **Written for QA, who does not read the code:** no file paths, component names or code identifiers in the steps. UI texts, URL paths and role names stay exactly as in the app. Dev-only commands (`pnpm dev`, local ports) go into `Передумови` once, not into the steps.
- **Nothing invented:** every step traces back to a `## Testing` subsection, a tasks.md entry or the code.
- **Out of scope is explicit:** blocked tasks with their reason, and parts deliberately dropped in `Decisions` (e.g. "кнопку Export прибрали"), go to `Не входить у тестування`, so QA does not report them as bugs.
- Ukrainian; omit empty sections.

### qa.md Template

```markdown
# QA: <Goal з tasks.md>
_Дата: DD-MM-YYYY_

## Що увійшло
- <назва задачі>
- <назва задачі>

## Передумови
- Середовище: ...
- Ролі й акаунти: ...
- Дані: ...

## Сценарії

### 1. <Назва фічі або флоу>
Задачі: <назва задачі>, <назва задачі>

1. **Крок**: що зробити. Очікується: що має побачити тестувальник.
2. **Крок**: ...

Крайні випадки:
- ...

### 2. <Назва фічі або флоу>
...

## Не входить у тестування
- <назва задачі> — заблокована: <причина з колонки Blocker>
- <що свідомо не зроблено> — рішення: "<цитата з Decisions>"
```

### QA Report
Ukrainian, the final text of the turn:
1. First, what needs attention: ❌ of the regression pass that wait for the user's decision, or the fact that the pass did not run; tasks without a `## Testing` subsection (their steps come from the plan and the code — check them first), gaps in the prerequisites, blocked tasks left out.
2. The output block of `browser-test` as is, plus the broken task for every ❌.
3. The path to `qa.md` and how many tasks and scenarios it covers.
4. Task board — where the plan was archived.
5. Progress (done/total).
6. The message:

> 🧪 QA-файл готовий і прогнаний у браузері. Якщо треба щось змінити в інструкції — пиши, виправлю. План завершено.

A commit line only if the regression pass fixed code — then the `fix: ...` message, alone in a fenced code block, is the last element of the report.

---

## Move Finished Tasks

Right after setting the status to `done`:

1. **Task source → `done/DD-MM-YYYY/`** (today's date from `currentDate`, converted to DD-MM-YYYY: `2026-09-25` → `25-09-2026`). Move every path from the task's `Source` (file or whole task folder) from `todo/` to `done/DD-MM-YYYY/`, creating the folder with `mkdir -p`. If other tasks in the plan share the same `Source` and are not `done` yet — leave it in `todo/`; it moves together with the last of them. Shared `tasks/screenshots/` never moves.
2. **Plan archive.** When no task in status.md is left as `pending`, `research` or `running` (every task is `done` or `blocked`), move `tasks.md` and `status.md` to the same `done/DD-MM-YYYY/`. Blocked tasks lose nothing: their sources already live in `blocked/` with the reason, and `/sort-and-plan` picks them up later.
3. **Never overwrite.** Move with `mv -n` and check the result. If the target name is already taken — add a numeric suffix (`tasks-2.md`, `status-2.md`, `items-list-2.md`). If a `Source` path does not exist (the user moved it) — skip it and say so in the report.

In testing mode after the archive, `tasks.md Updates` go to the archived copy in `done/DD-MM-YYYY/`.

---

## status.md Updates

1. Find row by task ID → replace status
2. Update "Updated:" date (DD-MM-YYYY only, no time — use `currentDate` from session context, converted: `2026-09-25` → `25-09-2026`)
3. Recalculate progress: `done_count/total (percentage%)`

**Status values:** `pending` → `research` → `running` → `done` / `blocked`

---

## tasks.md Updates

tasks.md is read-only after planning with **one exception**: the `### Decisions` section of the task you are executing. Every answer the user gives during this task — while implementing or in testing mode — is appended there verbatim, one bullet per answer:

```markdown
### Decisions
- (planning, DD-MM-YYYY) Q: ... A: "..."
- (run, DD-MM-YYYY) Q: Порожній стан таблиці — текст? A: "Nothing here yet, як на сторінці users"
- (testing, DD-MM-YYYY) A: "кнопку Export прибрати, бекенд не готовий"
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
_Оновлено: DD-MM-YYYY_
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
2. **Follow the Task Execution Cycle** (section above) for research/check/implement/verify; the `QA` task follows **QA Task** instead
3. **Testing instructions go into the task file** before the task is `done` — the report alone is not enough; the `QA` task relies on them
4. **Every task is run in the browser** with `browser-test` before it is `done`, and the `QA` task runs the whole `qa.md`; a skipped or failed-to-run test is named in the report, never hidden
5. **No plan approval** — the plan in tasks.md is already approved; stop only for a real discrepancy or gap (cycle step 2)
6. **Go through "Before Asking the User"** before every question
7. **Update status.md after EACH state change**
8. **tasks.md is read-only** except for appending to the current task's `Decisions` (see "tasks.md Updates")
9. **NEVER skip the report step** — even for simple tasks; the report ends with the commit line (the `QA` task has one only if its regression pass fixed code)
10. **Testing mode after completion** — user feedback → fix → re-verify; scope changes requested in testing mode go to `Decisions`
11. **Never pick a `blocked` task or a task with blocker text** — only the user (or `/sort-and-plan`) unblocks tasks
12. **Never read or touch `waiting/`**; never delete or overwrite task files — only move them with `mv -n`; the only edits inside a task file are its `## Testing` and `## Blocked` blocks
