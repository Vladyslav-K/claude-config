---
name: project-meta-init
description: Initialize project folder structure for task management, estimation, and swagger sync. Creates .project-meta/ with all required subfolders.
---

# Project Meta Initialization

Create the folder structure used by `/plan-tasks`, `/run-tasks`, `/estimate` and `/sync-swagger`.

## Structure

```
.project-meta/
├── tasks/
│   └── plan/
│       └── screenshots/     # Task descriptions + design documents + screenshots
├── estimation/
│   └── screenshots/         # Task files + screenshots for estimation
├── swagger/                 # swagger.json (+ swagger-old.json baseline for diff mode) for /sync-swagger
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
- `/plan-tasks` — add .md files to `tasks/plan/`, screenshots to `tasks/plan/screenshots/`
- `/run-tasks` — execute planned tasks step by step
- `/estimate` — add task files to `estimation/`, screenshots to `estimation/screenshots/`
- `/sync-swagger` — put `swagger.json` into `swagger/`; add `swagger-old.json` (the previous, already synced snapshot) to switch the skill into diff mode

## Notes
- Idempotent — safe to run multiple times
- Existing files will NOT be deleted or overwritten
- `.project-meta/` is typically gitignored
