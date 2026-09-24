---
name: sort-and-plan
description: Sort the text kanban board in .project-meta/tasks/ and plan the ready tasks. Goes through todo/ and blocked/, checks every task against the API and the project, moves each task to todo/ (ready), blocked/ (with a `## Blocked` reason block) or done/YYYY-MM-DD/ (already implemented), asks the user everything that affects the sorting, then runs /plan-tasks for the todo/ tasks only. Use whenever the user asks to sort tasks, check which tasks can be taken into work, re-check blocked tasks against a new backend, prepare a sprint or tasks for execution — e.g. «розсортуй задачі», «які задачі вже можна робити», «перевір blocked», «пройдись по todo і blocked», «підготуй задачі до виконання».
---

# Sort and Plan

## Additional context from user
$ARGUMENTS

## Purpose

`.project-meta/tasks/` is a text kanban board. This skill brings it up to date and prepares the ready tasks for `/run-tasks`:

1. **Sort** — every task from `todo/` and `blocked/` ends up where it belongs: ready → `todo/`, has a blocker → `blocked/`, already implemented → `done/YYYY-MM-DD/`.
2. **Plan** — `/plan-tasks` plans the tasks left in `todo/`, and only them.

The goal is that `/run-tasks` later executes every planned task without asking the user anything. So every question goes to the user here, in this session: sorting questions in step 4, implementation questions in `/plan-tasks`.

## Task Board

```
.project-meta/tasks/
├── todo/            # Tasks fully ready to be executed
├── blocked/         # Tasks with a blocker; the reason is in the `## Blocked` block at the bottom of the task
├── waiting/         # The user's postponed tasks — never read or touch
├── done/            # Finished tasks: done/YYYY-MM-DD/
├── screenshots/     # Shared design docs and screenshots
├── tasks.md         # Current plan (written by /plan-tasks)
└── status.md        # Current plan statuses
```

A task is either a `.md` file or a task folder. For a task folder, read **every** file inside it — the user put it there for a reason. Screenshots and design docs live in the task folder, in `todo/screenshots/` or `blocked/screenshots/` if present, and in the shared `tasks/screenshots/` (matched by task name, same rules as in `/plan-tasks`). Screenshot folders are not tasks.

## Language

Chat, questions, the `## Blocked` block and the final report — Ukrainian. Code identifiers, file paths and endpoints stay in English.

---

## Steps

### 0. Check the Board

1. If `.project-meta/tasks/todo/` and `blocked/` do not exist, but the old `.project-meta/tasks/plan/` does — stop and tell the user that the project uses the old structure and the tasks have to be moved into `todo/` / `blocked/` / `waiting/` first. Do not migrate on your own.
2. If `tasks.md` / `status.md` exist in the root of `tasks/`, read both:
   - every task is `done` or `blocked` → the plan is finished but not archived: move both files to `done/YYYY-MM-DD/` (today, `mv -n`, numeric suffix if the name is taken) and continue;
   - some tasks are still `pending` / `research` / `running` → ask via AskUserQuestion: **Re-plan from scratch** (sort all of `todo/` and `blocked/`, the current plan is overwritten), **Add new tasks only** (tasks already listed in the plan's `Sources` are not re-sorted, the plan keeps its statuses), **Stop**. Pass the answer to `/plan-tasks` in step 6 so it does not ask again.

### 1. Read All Tasks

Read every task from `todo/` and `blocked/` fully (except tasks excluded in step 0). For tasks from `blocked/`, read their `## Blocked` block: the recorded reason is what you have to re-check first. Look at the design material of every task — a design can reveal a screen or an asset that makes the task blocked.

### 2. Research the API and the Project

- **API:** swagger at `.project-meta/swagger/swagger.json` first. Check endpoints and fields with the `sync-swagger` scripts (`list-spec.py`, `show-endpoint.py`, `show-schema.py` in `~/.claude/skills/sync-swagger/scripts/`) instead of opening the large file. Also check the project's API layer (types, services, hooks) — an endpoint can already be wired.
- **Project:** existing pages, components, routes and assets that a task needs or that may already implement it. Use Explore agents for broad searches, then open the cited code yourself — a hint from an agent is a hypothesis, not a fact.
- Match each requirement of each task to concrete evidence: an endpoint and field, a file and line, a design file — or the absence of it.

### 3. Classify Every Task

- **Done** — every requirement of the task is already implemented; you can point to `file:line` for each one. If even one requirement is missing, the task is not done — it is ready or blocked, and the plan gets a note about what already exists.
- **Blocked** — something outside the frontend's control is missing and the user cannot provide it now: an endpoint or a field, a design for a screen, an asset, a decision of the client or the backend. A dependency on a task that is itself blocked or in `waiting/` also blocks. Be specific: "no `DELETE /api/items/{id}` in swagger" — not "API is not ready".
- **Ready** — everything the task needs exists, or the missing piece is a question the user can answer now (step 4). A dependency on another ready task does not block — `/plan-tasks` orders them.

A task that is already in `blocked/` goes back to ready only if its recorded blocker is really gone (the endpoint now exists in swagger, the design appeared) and no new blocker showed up.

### 4. Ask the User

Collect every question that affects where a task goes, and ask them before moving anything, so the result of the sorting is final. Typical ones:
- the API covers the task only partly — is the missing part required, or can the task go without it;
- the evidence of "done" is unclear, or the task is done partly — is the rest still needed;
- the task text contradicts the design, the API or another task;
- a blocker that the user may be able to remove right now (provide an endpoint, an asset, a decision).

Ask via AskUserQuestion — up to 4 questions per call; if there are more, group them by task and use consecutive calls. Every question is self-contained: the task (file name), what you found, and what each option means for the task (stays in `todo/`, goes to `blocked/`, goes to `done/`). Record every answer verbatim — they are passed to `/plan-tasks` in step 6. Implementation details (texts, states, behavior) are not asked here — `/plan-tasks` handles them in its dry run; ask them here only when the answer decides the sorting.

If there is nothing to ask — skip this step.

### 5. Move the Tasks

Move with `mv -n` and check the result; never overwrite — if the target name is taken, stop and ask the user. Move a task folder as a whole. The shared `tasks/screenshots/` never moves. Files in `todo/screenshots/` or `blocked/screenshots/` that match only the moved task move with it into the target's `screenshots/`; files shared with other tasks stay.

- **Blocked** — move to `blocked/` (tasks already there stay). Append the block to the bottom of the task's `.md` file (for a task folder — its main description file). If the file already has a `## Blocked` block, replace it with the new one. Nothing above the block changes:

```markdown
## Blocked
_Оновлено: YYYY-MM-DD_
- Причина: що саме відсутнє або незрозуміле, конкретно (ендпоінт, поле, дизайн, рішення)
- Перевірено: де шукав (swagger, файли коду, дизайн)
- Для розблокування: що має зʼявитись або що має вирішити юзер
```

- **Ready** — stays in `todo/`; a task from `blocked/` moves back to `todo/`, and its `## Blocked` block (from the `## Blocked` heading to the end of the file) is removed. The user's text above it stays untouched.
- **Done** — move to `done/YYYY-MM-DD/` (today, from `currentDate`), creating the folder with `mkdir -p`. Do not add anything to the file.

### 6. Plan the Ready Tasks

If `todo/` has tasks to plan, invoke the `plan-tasks` skill via the Skill tool. Pass in the arguments:
- that it is called from `/sort-and-plan` and the sorting is finished;
- the list of `todo/` entries to plan (only the ready ones; with "Add new tasks only" — only the new ones);
- the answer from step 0, if the question was asked;
- the user's answers from step 4, verbatim, grouped by task — to be recorded as `(sorting, YYYY-MM-DD)` entries in `Decisions`;
- for partly implemented tasks — what already exists (`file:line`), so the plan covers only the rest.

`/plan-tasks` runs its research, dry run and questions, and writes `tasks.md` / `status.md`. Blocked tasks never go into the plan. If `/plan-tasks` moves a task to `blocked/` during its own analysis, include that in the report.

If `todo/` is empty after the sorting — skip planning and say so in the report.

### 7. Final Report

One final message of the turn (no tool calls after it), in Ukrainian. It replaces the separate summary of `/plan-tasks` — merge its content here. Start with what needs the user's attention:

```
## Сортування і план задач

### Заблоковані (blocked/):
- [назва задачі] — причина одним рядком; що потрібно для розблокування

### Вже зроблені (перенесені в done/YYYY-MM-DD/):
- [назва задачі] — докази: file:line

### Повернуті з blocked/ в todo/:
- [назва задачі] — що змінилось (наприклад, "у swagger зʼявився GET /api/items")

### Готові до виконання (todo/):
- [назва задачі]

### План (tasks.md):
- кількість задач і складність, порядок виконання з поясненням
- зафіксовані рішення юзера (коротко, щоб юзер помітив непорозуміння)
```

Omit empty sections.

---

## Rules

1. **Never read or touch `waiting/`** — it is the user's folder; tasks there do not exist for this skill
2. **Never delete task files and never edit their text** — the only allowed change is appending, replacing or removing the `## Blocked` block at the bottom
3. **Move only with `mv -n`**, never overwrite; a taken target name → ask the user
4. **Every classification needs evidence** — endpoint and field, `file:line`, design file; "done" requires evidence for every requirement
5. **All sorting questions before any move** (step 4), via AskUserQuestion, never as text in the chat
6. **Only `todo/` tasks go to `/plan-tasks`** — blocked and done tasks are never planned
7. **$ARGUMENTS from the user are mandatory instructions** — e.g. "only the auth tasks", "backend for payments is ready"
