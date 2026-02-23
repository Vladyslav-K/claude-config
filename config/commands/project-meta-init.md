---
name: project-meta-init
description: Initialize project folder structure for task management, estimation, and memory. Creates .project-meta/ with all required subfolders.
---

# Project Meta Initialization

## Purpose
Create the complete project folder structure used by `/tasks:plan`, `/tasks:run`, `/estimate`, and the memory system.

## Folders to Create

```
.project-meta/
├── tasks/
│   └── plan/
│       └── screenshots/     # Input for /tasks:plan (task descriptions + design documents + screenshots)
├── estimation/
│   └── screenshots/         # Input for /estimate (task files + screenshots for estimation)
└── memory/                  # Project memory files (session context, structure, changelog)
```

## Execution Steps

### Step 1: Create Folder Structure

Create all required folders:

```bash
mkdir -p .project-meta/tasks/plan/screenshots
mkdir -p .project-meta/estimation/screenshots
mkdir -p .project-meta/memory
touch .project-meta/memory/recent-session.md
```

### Step 2: Confirm Creation

After creating folders, list them to confirm:

```bash
find .project-meta -type d
```

### Step 3: Report to User

Report what was created with usage instructions:

```
## Project Structure Created

Created folders:
- .project-meta/tasks/plan/
- .project-meta/tasks/plan/screenshots/
- .project-meta/estimation/
- .project-meta/estimation/screenshots/
- .project-meta/memory/
- .project-meta/memory/recent-session.md

## How to Use

### /tasks:plan — Plan tasks for execution
1. Add task description files (.md) to `.project-meta/tasks/plan/`
2. (Optional) Add screenshots (.png, .jpg) to `.project-meta/tasks/plan/screenshots/`
3. (Optional) Add design documents (`*__design.md`) to `.project-meta/tasks/plan/screenshots/`
4. Run `/tasks:plan` to create tasks.md and status.md
5. Pass extra context: `/tasks:plan focus on mobile first`

### /tasks:run — Execute planned tasks
1. First run `/tasks:plan` to create task files
2. Run `/tasks:run` to execute tasks sequentially

### /estimate — Estimate task effort
1. Add task files (.md, .xlsx) to `.project-meta/estimation/`
2. Add screenshots to `.project-meta/estimation/screenshots/`
3. Run `/estimate` for time estimation
```

## Important Notes

- This command is idempotent — running it multiple times is safe
- Existing files will NOT be deleted
- `.project-meta/` is typically gitignored
