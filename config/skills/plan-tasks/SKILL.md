---
name: plan-tasks
description: Deep task planning with full codebase research, API analysis, component inventory, and blocker detection. Plans the tasks from .project-meta/tasks/todo/ so thoroughly that /run-tasks can execute them without asking the user anything. Produces a detailed implementation plan, with the browser-test setup of every task, that always ends with a QA task compiling the testing instructions of all done tasks into one qa.md and running it as a browser regression pass.
---

# Task Planning

## Additional context from user before start task
$ARGUMENTS

**How to use arguments:**
- `/plan-tasks` — full deep analysis of all tasks in `todo/`
- `/plan-tasks focus only on tasks 1-3` — limit scope
- `/plan-tasks we use REST API at /api/v1, auth is JWT` — provide context
- `/plan-tasks skip API research, backend is not ready yet` — adjust behavior
- Called from `/sort-and-plan` — the arguments carry the list of tasks to plan and the user's answers already given during sorting; record those answers verbatim in `Decisions` and do not ask them again

## Purpose
Read the tasks from `.project-meta/tasks/todo/`, perform **deep codebase research**, and create a comprehensive implementation plan with detailed analysis of each task — existing components, API endpoints, dependencies, blockers, and step-by-step implementation guidance.

The plan is the context `/run-tasks` executes from, and `/run-tasks` does not stop for plan approval. **Every question `/run-tasks` would have to ask the user is a planning defect**: it interrupts the user on every task and slows development down. Resolve everything now — by research or by asking the user once, in this session.

## Task Board

```
.project-meta/tasks/
├── todo/            # Input: tasks ready to be executed
├── blocked/         # Tasks with a blocker (the reason is in the `## Blocked` block at the bottom)
├── waiting/         # The user's postponed tasks — never read or touch
├── done/            # Finished tasks: done/DD-MM-YYYY/
├── screenshots/     # Shared design docs and screenshots
├── tasks.md         # Output: detailed task plan
└── status.md        # Output: status tracking
```

## Input

**Tasks:** every entry in `.project-meta/tasks/todo/` (except `todo/screenshots/`, if present — it is a design folder). An entry is either:
- a `.md` file — the task description, or
- a task folder — read **every** file inside it (descriptions, notes, design docs, screenshots, any other material): the user put it there for a reason.

Only `todo/` is planned. Never read `waiting/` or `done/`; `blocked/` is not planned (sorting it is the job of `/sort-and-plan`).

**Design docs/screenshots:** the task folder itself, `todo/screenshots/` if present, and the shared `.project-meta/tasks/screenshots/`.

**Matching rules for shared screenshot folders (screenshots -> tasks):**
- Task "user-profile" matches:
  - `screenshots/user-profile/` folder (all files inside)
  - `screenshots/user-profile.png`, `screenshots/user-profile-*.png`
  - `screenshots/user-profile*__design.md`
- Folder contents override file name matching
- One file can relate to multiple tasks
- Files inside a task folder always belong to that task

## Output

```
.project-meta/tasks/
├── tasks.md          # Detailed task plan
└── status.md         # Status tracking
```

## Language

The content of tasks.md and status.md is written in **Ukrainian**: task titles, `What`, implementation steps, notes, blockers, decisions, summary. The structural labels from the templates below (`What`, `Source`, `Deps`, `Type`, section headings like `Existing Code to Reuse`, table headers) stay exactly as in the templates — `/run-tasks` parses them. Code identifiers, file paths, endpoints, package names and commit messages stay in English. The `## Blocked` block and the chat summary (step 11) are in Ukrainian as well.

---

## Execution Steps

### 0. Check for an Existing Plan

If `.project-meta/tasks/tasks.md` or `status.md` already exists, read both, then ask the user via AskUserQuestion before doing anything else:

- **Add new tasks only** — keep existing tasks, their statuses and decisions untouched; plan only the `todo/` entries that are not yet listed in `Sources`, append them with the next free IDs. The `QA` task stays the last entry: move its entry and its status.md row below the new tasks (add it if the plan has none, see step 8).
- **Re-plan from scratch** — overwrite both files; all statuses reset to `pending`.
- **Stop** — leave the files as they are.

Never overwrite an existing plan silently — status.md holds the user's progress. If `/sort-and-plan` already asked this question, its answer is in the arguments — apply it without asking again.

### 1. Read ALL Tasks
Read every entry of `todo/` fully — every `.md` file and every file inside task folders. Understand the full scope.

### 2. Read Designs and Screenshots
Collect the design material per task (task folder + matched files from the shared screenshot folders).
- Design docs (`*__design.md`) — **read fully**, extract every UI element, field, action, state, text.
- Screenshots of `visual` / `mixed` tasks — **look at them now**: texts, states, elements and assets that the design shows but the task text does not mention are exactly what turns into questions during execution. Note every static text, every state, every icon/image/font.

### 3. Codebase Research

Use `helper` agents and direct reads to research the project:

#### 3a. Project Structure
- Identify framework, key directories, routing patterns
- Find package.json / config files — understand available libraries
- Identify state management, styling approach, API layer patterns

#### 3b. Existing Components Inventory
For each task that involves UI:
- Search for existing components that can be reused (forms, tables, modals, buttons, layouts)
- Read their API — props, variants, slots
- Note exact import paths
- Identify shared layouts, wrappers, providers that new pages must use
- Check that every icon/image/font from the design exists in the project

#### 3c. API Research
- Search for existing API services, hooks, types in the codebase
- Find API base URL configuration, auth headers setup
- If a swagger/openapi spec exists (`.project-meta/swagger/swagger.json` first) — check every endpoint and field the task needs with the `sync-swagger` scripts (`list-spec.py`, `show-endpoint.py`, `show-schema.py` in `~/.claude/skills/sync-swagger/scripts/`) instead of opening the large file directly
- Map which endpoints already exist vs which are needed; map every field the UI shows or sends to a concrete API field
- If NO API docs and tasks require API — add a question to the batch (step 6): "What are the API endpoints for these tasks? Or should I plan with mock data?"
- **NEVER invent** endpoint URLs, field names, or response structures

#### 3d. Patterns and Conventions
- Find 2-3 similar existing pages/features as reference
- Note the patterns: how pages are structured, how forms are built, how tables work
- Identify validation patterns, error handling, loading/empty states, toasts, confirmations
- Check i18n setup and existing translations structure

#### 3e. Test Accounts
Every task is run in the browser by `/run-tasks` through the `browser-test` skill. Read `.project-meta/qa/accounts.md` if it exists: which account IDs and roles are available, and the email template for new accounts. Use only IDs and roles in the plan — credentials never leave that file.

### 4. Blocker Analysis

For EACH task, check:
- **Missing API:** endpoints or fields not found and not documented -> BLOCKER
- **Missing components:** UI requires components that don't exist and aren't in the design system -> NOTE (the plan says which component to create or extend)
- **Missing designs:** task references screens that have no screenshot/design doc -> BLOCKER
- **Missing assets:** icons, images or fonts from the design are not in the project -> question for step 6
- **Unclear requirements:** ambiguous descriptions with multiple interpretations -> question for step 6
- **Technical blockers:** missing dependencies, incompatible library versions, unimplemented auth -> BLOCKER
- **Missing translations:** i18n keys needed but translation files not set up -> NOTE

### 5. Execution Dry Run

For EACH task, walk through the implementation as if you were coding it right now — file by file, step by step — and at every step ask: "what would I have to decide here, and do I know the answer?" Typical decision points:

- **Texts** — headings, labels, placeholders, button texts, empty-state texts, toasts, confirmation dialogs, error messages
- **States** — loading, empty (first visit, no data yet), error, disabled, partial data, long values and overflow
- **Data** — which endpoint feeds which element, field-to-UI mapping, formatting (dates, money, numbers), fields the design shows but the API lacks, server-side vs client-side pagination/sorting/filtering/search
- **Behavior** — what happens after submit / delete / cancel: where it redirects, which toast, whether the modal closes, which queries are invalidated; which actions need confirmation
- **Validation** — rules per field, where messages appear, how server errors map to fields
- **Access** — which roles see the feature and what the others see
- **Components** — which existing component and variant; which one to extend when a variant is missing
- **Assets** — every icon/image/font from the design, with its path in the project
- **Scope edges** — breakpoints, i18n keys, what is explicitly out of scope
- **Testing** — which accounts (IDs from `accounts.md`) the browser test logs in with and whether every needed role is covered; which data must exist and which the test creates itself (created accounts and entities are recorded in `accounts.md`); which destructive or outward-facing actions (delete, invites, emails) the test may perform on the real backend; what cannot be checked in the browser (emails, third-party services)

Resolve each decision point with the first source that answers it:
1. the task text or design — write the answer into the plan as a fact (texts verbatim);
2. an existing project precedent — write the fact with the file path;
3. the API/swagger — write the exact endpoint and field;
4. otherwise — it becomes a question for step 6.

The plan contains decisions, not investigations: "check whether the API supports bulk delete" is not a plan item — check it now and write the result. A task is ready for the plan only when its dry run leaves **zero open points**.

### 6. Ask the User Once

Collect everything that needs the user's input from steps 3-5 (missing API, unclear requirements, missing designs or assets, conflicts with existing code, missing test accounts or unclear limits for the browser test, open dry-run points) into one list. Do not ask anything mid-research.

Ask all collected questions via AskUserQuestion (up to 4 questions per call; if there are more, group them by task and use consecutive calls — more questions now is the intended trade-off for no questions during execution). Every question is self-contained: state the task, the problem and the consequences of each option, because the user does not see your research. Do not re-ask what the arguments or the task's existing `Decisions` already answer.

Record every answer **verbatim** in the task's `Decisions` section of tasks.md. If an answer opens a new decision point — resolve it or ask a follow-up before writing the plan.

If there is nothing to ask — skip this step.

### 7. Move Tasks That Stay Blocked

If a task still has a BLOCKER after step 6 (the user cannot provide the missing piece now), it does not go into the plan:
1. Move its `todo/` entry (file or whole task folder) to `blocked/` with `mv -n`; if the target name is taken — stop and ask the user instead of overwriting.
2. Append the `## Blocked` block to the bottom of the task's `.md` file (for a task folder — its main description file). Do not change anything above it:

```markdown
## Blocked
_Оновлено: DD-MM-YYYY_
- Причина: що саме відсутнє або незрозуміле, конкретно (ендпоінт, поле, дизайн, рішення)
- Перевірено: де шукав (swagger, файли коду, дизайн)
- Для розблокування: що має зʼявитись або що має вирішити юзер
```

If the file already has a `## Blocked` block — replace it with the new one instead of adding a second one.

### 8. Build Detailed Task Plan

For EACH ready task, compile:

1. **What** — clear description of what needs to be built (from source + your research)
2. **Source** — the `todo/` entry the task comes from (file or folder path relative to `.project-meta/tasks/`); `/run-tasks` moves it to `done/` when the task is finished. One entry may produce several tasks, and several entries may form one task (list all of them)
3. **Dependencies** — which tasks must be completed first and why
4. **Type** — visual / code / mixed
5. **Design refs** — matched screenshots and design docs
6. **Existing code to reuse** — specific components with import paths, existing hooks/services, utility functions
7. **Reference implementations** — similar existing pages/features to follow as patterns (with file paths)
8. **API endpoints** — exact endpoints needed (from swagger/existing code/user input), request/response structure, field mapping
9. **New code to create** — list of new files with purpose:
   - New pages/routes
   - New components (if existing ones don't cover it)
   - New API services/hooks
   - New types/interfaces
10. **Implementation steps** — ordered list of concrete steps; each step states what to do, not what to find out
11. **States and texts** — every state from the dry run with how it looks, and every static text verbatim
12. **Test setup** — the answers to the dry run's «Testing» point: accounts by ID, required and created data, allowed destructive actions, what stays for manual checking. A task with nothing observable in the browser says so in one line
13. **Blockers** — always `None` for a planned task (blocked tasks were moved out in step 7)
14. **Notes** — edge cases and gotchas only; no open questions, no "need to check"
15. **Decisions** — the user's answers (from sorting and from step 6) that concern this task, verbatim; `/run-tasks` treats them as requirements
16. **Estimated complexity** — simple / standard / complex (based on research)
17. **Commit** — a ready-to-use commit message for this task, written to status.md only (see "Commit Message Rules" below)

**The QA task.** After the ready tasks, always add one more task with ID `QA` and Type `qa` — exactly as in the template below. `/run-tasks` executes it last, when every other task is `done` or `blocked`: it compiles the `## Testing` instructions that `/run-tasks` wrote into the files of the done tasks into one `done/DD-MM-YYYY/qa.md`, which the user hands to QA, and runs every scenario of it in the browser as a regression pass. It has no `Source`, no commit and no research — everything it needs is described in `/run-tasks`, section «QA Task». If no task is ready (all of them moved to `blocked/` in step 7), there is no plan and no `QA` task.

### 9. Determine Task Order
- Tasks with no deps first
- Then by dependency chain
- Within same priority — simpler tasks first (build foundations before complex features)
- Group related tasks when it makes sense
- The `QA` task is always the last entry

### 10. Write tasks.md + status.md
Write both files with the detailed format below. Every planned task starts as `pending`.

### 11. Show Comprehensive Summary

When called from `/sort-and-plan`, do not write a separate final message — `/sort-and-plan` merges this content into its own final report.

Otherwise report to user (Ukrainian, as the final text of the turn — no tool calls after it):
- Tasks analyzed (`todo/` entries)
- Codebase areas researched
- Design references matched
- Tasks created (with complexity breakdown)
- Tasks moved to `blocked/` — **highlight these prominently**, with the reason and what the user must provide to unblock each one
- Decisions recorded from the user's answers (short list, so the user can spot a misunderstanding)
- Browser testing: the accounts the plan uses, and the ones missing from `.project-meta/qa/accounts.md` that the user has to add before `/run-tasks` (or that the tests will create)
- Recommended execution order explanation

---

## tasks.md Format (Full)

Every date in tasks.md and status.md is DD-MM-YYYY, taken from `currentDate` and converted: `2026-09-25` → `25-09-2026`.

```markdown
# Tasks

Goal: Overall goal
Sources: todo/items-list.md, todo/item-details/
Created: DD-MM-YYYY

---

## Task 1: Short title
- **What:** Detailed description of what needs to be built
- **Source:** todo/items-list.md
- **Deps:** none
- **Type:** visual
- **Complexity:** standard
- **Design:** screenshots/list__design.md
- **Screenshots:** screenshots/list.png

### Existing Code to Reuse
- `src/components/ui/data-table.tsx` — base table component with sorting/pagination
- `src/hooks/use-pagination.ts` — pagination state management
- `src/services/api-client.ts` — configured axios instance

### Reference Implementation
- `src/app/(dashboard)/users/page.tsx` — similar list page, follow this pattern
- `src/app/(dashboard)/users/components/users-table.tsx` — table structure reference

### API
- `GET /api/v1/items` — list with pagination (params: page, limit, search)
- `DELETE /api/v1/items/:id` — delete single item
- Response: `{ data: Item[], meta: { total, page, limit } }`

### New Code
- `src/app/(dashboard)/items/page.tsx` — main list page (Server Component)
- `src/app/(dashboard)/items/components/items-table.tsx` — table with columns from design
- `src/types/item.ts` — Item interface
- `src/services/items.ts` — API service functions
- `src/hooks/use-items.ts` — React Query hook

### Implementation Steps
1. Create Item type from API response structure
2. Create API service with list/delete functions
3. Create React Query hook wrapping the service
4. Build table component following users-table pattern
5. Create page component with search + table
6. Add route to navigation (if needed)
7. Test all interactive states

### States and Texts
- Loading — skeleton rows as in `users-table.tsx`
- Empty — text "No items yet", no button
- Delete — confirmation modal "Delete this item?", after success toast "Item deleted" and list refetch

### Test Setup
- Акаунти: `admin` (список, видалення), `viewer-01` (немає кнопки Delete)
- Дані: тест сам створює 2 items і видаляє тільки їх
- Вручну: нічого

### Blockers
- None

### Notes
- Table has 6 columns — on narrow viewports the table scrolls horizontally, as in `users-table.tsx`

### Decisions
- (sorting, DD-MM-YYYY) Q: Bulk delete — is there an API? A: "поки що ні, кнопку не робимо, буде в наступному спринті"
- (planning, DD-MM-YYYY) Q: Search — server-side or client-side? A: "серверний, параметр search уже є"

---

## Task 2: Another title
- **What:** Detailed description
- **Source:** todo/item-details/
- **Deps:** 1 (needs Item type from Task 1)
- **Type:** mixed
- **Complexity:** complex

...

---

## Task QA: Інструкція для QA
- **What:** Зібрати інструкції `## Testing` усіх done-задач цього плану в один файл `done/DD-MM-YYYY/qa.md` для QA; заблоковані задачі — у розділ «Не входить у тестування». Прогнати всі сценарії qa.md у браузері як регресію. Флоу — `/run-tasks`, секція «QA Task».
- **Source:** none
- **Deps:** усі інші задачі плану (`done` або `blocked`)
- **Type:** qa
- **Complexity:** simple
```

## status.md Format

```markdown
# Tasks Status
Updated: DD-MM-YYYY

## Progress: 0/N (0%)

| # | Task | Type | Complexity | Status | Blocker |
|---|------|------|------------|--------|---------|
| 1 | Task title. \| feat: add items list page with search and delete | visual | standard | pending | |
| 2 | Another task. \| fix: map api errors to form fields | mixed | complex | pending | |
| QA | Інструкція для QA | qa | simple | pending | |
```

**Type values:** `visual` / `code` / `mixed` for regular tasks; `qa` only for the `QA` task.

**Status values:** `pending` -> `research` -> `running` -> `done` / `blocked`

Planning writes only `pending` rows. `blocked` is set by `/run-tasks` when a blocker appears during execution; a task with a non-empty `Blocker` column is always `blocked`, never `pending` — `/run-tasks` picks only `pending` tasks. When the user resolves a blocker, they (or you, on their instruction) clear the column and set the status back to `pending`.

The Task cell ends with the task's commit message, appended after the title as plain text — no parentheses, brackets, backticks or other wrapping — so the user can select and copy it straight from the status table. The title and the commit message are separated by a period and an escaped pipe: `<title>. \| <commit>` (the pipe must be written as `\|` so it does not break the markdown table column).

Example: `Project і Trade Type на детальній WO (SCRUM-357). \| fix: resolve project and trade type names on work orders`

The `QA` task changes no code, so its Task cell is the title only, without the separator and a commit message.

---

## Commit Message Rules

Every task except `QA` gets one commit message, generated at planning time and written to status.md only — appended to the Task cell after the title, separated by `. \|` (period, space, escaped pipe), without parentheses or any wrapping. It is not duplicated in tasks.md. It is a title line only, meant to be copied as is:

- Conventional Commits format: `<type>: <summary>`. Types: `feat` (new behaviour), `fix` (bug fix), `refactor` (no behaviour change), `chore` (tooling, config, generated code), `test`, `docs`. Pick by what the task changes for the user or the codebase, not by task label.
- English, imperative mood, lowercase, no trailing period, no task ID, no ticket link.
- Short: one line, aim for 50 characters, never more than 72. Name the outcome, not the list of files or steps.
- One message per task even if the task touches many areas — pick the main outcome; details belong to the PR description, not the commit title.

**Examples:**

Task: "T1.10 — login and second factor on the real API"
Commit: `feat: connect auth flow and two-factor verification`

Task: "T1.5a — generate contract types in packages/api-client"
Commit: `chore: generate api-client types from contract`

Task: "T1.19 — API error mapping, retry on forms, field validation"
Commit: `feat: map api errors to forms with retry`

Too long, do not write like this: `feat: implement login page, OTP verification step, session cookie refresh, useMe hook and error handling for the real API`

---

## Rules

1. **Never delete or rewrite task files** — the user manages them; the only allowed changes are moving a task to `blocked/` and appending/replacing its `## Blocked` block (step 7)
2. **Plan only `todo/`** — never read `waiting/` or `done/`, never plan `blocked/` tasks
3. **Every claim must be verified** — don't say "component exists" without finding it via Glob/Grep
4. **Include exact file paths** — every referenced component/service must have its real path
5. **One task per logical unit** — don't combine unrelated changes
6. **Verify API exists** before planning API tasks — if not found, ask in step 6; no answer -> the task moves to `blocked/`
7. **Zero open points per planned task** — the dry run (step 5) must leave nothing for `/run-tasks` to ask
8. **Highlight ALL blocked tasks prominently** — user must see them immediately
9. **Use `helper` agents for broad searches and flow tracing** — save context for analysis; never use the built-in Explore agent
10. **$ARGUMENTS from user are MANDATORY instructions** — apply them to the planning process
11. **Ask questions if ambiguous** — better to ask than to guess wrong; all questions in one batch (step 6), via AskUserQuestion, never as text in the chat
12. **Record every user answer verbatim** in the task's `Decisions` section — answers that live only in the chat are lost for `/run-tasks`
13. **Never overwrite an existing plan without asking** (step 0)
14. **Every plan ends with the `QA` task** (step 8) — including a plan extended with "Add new tasks only"
