---
name: project-meta-init
description: Initialize project folder structure for task management, estimation, and swagger sync. Creates .project-meta/ with all required subfolders.
---

# Project Meta Initialization

Create the folder structure used by `/tasks-plan`, `/tasks-run`, `/estimate`, `/sync-swagger`, and `/sync-swagger-diff`.

## Structure

```
.project-meta/
├── tasks/
│   └── plan/
│       └── screenshots/     # Task descriptions + design documents + screenshots
├── estimation/
│   └── screenshots/         # Task files + screenshots for estimation
├── swagger/                 # swagger.json / swagger-old.json for /sync-swagger and /sync-swagger-diff
└── files/                   # Markdown reports
```

## Execute

```bash
mkdir -p .project-meta/tasks/plan/screenshots
mkdir -p .project-meta/estimation/screenshots
mkdir -p .project-meta/swagger
mkdir -p .project-meta/files
```

After creating, report what was created and remind usage:
- `/tasks-plan` — add .md files to `tasks/plan/`, screenshots to `tasks/plan/screenshots/`
- `/tasks-run` — execute planned tasks step by step
- `/estimate` — add task files to `estimation/`, screenshots to `estimation/screenshots/`
- `/sync-swagger`, `/sync-swagger-diff` — put `swagger.json` (and `swagger-old.json` for diff) into `swagger/`

## Notes
- Idempotent — safe to run multiple times
- Existing files will NOT be deleted or overwritten
- `.project-meta/` is typically gitignored
