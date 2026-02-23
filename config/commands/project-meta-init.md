---
name: project-meta-init
description: Initialize project folder structure for task management, estimation, and memory. Creates .project-meta/ with all required subfolders.
---

# Project Meta Initialization

Create the folder structure used by `/tasks:plan`, `/tasks:run`, `/estimate`, and the memory system.

## Structure

```
.project-meta/
├── tasks/
│   └── plan/
│       └── screenshots/     # Task descriptions + design documents + screenshots
├── estimation/
│   └── screenshots/         # Task files + screenshots for estimation
└── memory/
    ├── recent-session.md    # Short-term: last session context (overwritten each time)
    └── persistent.md        # Long-term: project knowledge (append-only)
```

## Execute

```bash
mkdir -p .project-meta/tasks/plan/screenshots
mkdir -p .project-meta/estimation/screenshots
mkdir -p .project-meta/memory
touch .project-meta/memory/recent-session.md
touch .project-meta/memory/persistent.md
```

After creating, report what was created and remind usage:
- `/tasks:plan` — add .md files to `tasks/plan/`, screenshots to `tasks/plan/screenshots/`
- `/tasks:run` — execute planned tasks sequentially
- `/estimate` — add task files to `estimation/`, screenshots to `estimation/screenshots/`

## Notes
- Idempotent — safe to run multiple times
- Existing files will NOT be deleted
- `.project-meta/` is typically gitignored
