---
name: project-meta-init
description: Initialize project folder structure for task management and swagger sync. Creates .project-meta/ with all required subfolders.
---

# Project Meta Initialization

Create the folder structure used by `/sort-and-plan`, `/plan-tasks`, `/run-tasks`, `/browser-test` and `/sync-swagger`.

## Structure

```
.project-meta/
├── tasks/                   # Text kanban board
│   ├── todo/                # Tasks fully ready to be executed
│   ├── blocked/             # Tasks with a blocker; the reason is in the `## Blocked` block at the bottom of the task
│   ├── waiting/             # Postponed by the user; no skill reads or touches this folder
│   ├── done/                # Finished tasks, grouped by completion date: done/YYYY-MM-DD/
│   ├── screenshots/         # Shared design docs and screenshots
│   ├── tasks.md             # Current plan (created by /plan-tasks)
│   └── status.md            # Current plan statuses (created by /plan-tasks)
├── swagger/                 # swagger.json (+ swagger-old.json baseline for diff mode) for /sync-swagger
├── qa/                      # Browser tests (/browser-test)
│   ├── accounts.md          # Test accounts: the user's base ones + everything the tests create
│   ├── .auth/               # Saved browser sessions per account
│   └── YYYY-MM-DD-<slug>/   # One test run: report.md, screens/, trace/
└── files/                   # Markdown reports
```

A task is either a single `.md` file or a folder with the task description and any related files (screenshots, design docs, notes).

## Execute

```bash
mkdir -p .project-meta/tasks/todo .project-meta/tasks/blocked .project-meta/tasks/waiting .project-meta/tasks/done .project-meta/tasks/screenshots
mkdir -p .project-meta/swagger
mkdir -p .project-meta/files
mkdir -p .project-meta/qa
```

`accounts.md` is not created here — `/browser-test` creates it from its template on the first run.

After creating, report what was created and remind usage:
- Put new tasks into `tasks/todo/` (a `.md` file or a task folder), shared screenshots into `tasks/screenshots/`, postponed tasks into `tasks/waiting/`
- `/sort-and-plan` — sort `todo/` and `blocked/` (ready / blocked / already done), then plan the ready tasks
- `/plan-tasks` — plan the tasks from `todo/` without sorting
- `/run-tasks` — execute planned tasks one by one, each one tested in the browser; finished tasks move to `done/YYYY-MM-DD/`
- `qa/accounts.md` — put the base test accounts there (for example, an admin who can create companies); tests append every account they create
- `/sync-swagger` — put `swagger.json` into `swagger/`; add `swagger-old.json` (the previous, already synced snapshot) to switch the skill into diff mode

## Notes
- Idempotent — safe to run multiple times
- Existing files will NOT be deleted or overwritten
- `.project-meta/` is typically gitignored
