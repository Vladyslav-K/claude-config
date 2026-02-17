---
name: project-meta-init
description: Initialize project folder structure for task management, estimation, and memory. Creates .project-meta/ with all required subfolders.
---

# Project Meta Initialization

## Purpose
Create the complete project folder structure used by `/tasks-plan`, `/tasks-run`, `/estimate`, and the memory system.

## Folders to Create

```
.project-meta/
├── tasks/
│   └── init/
│       └── screenshots/     # Input for /tasks:plan (task descriptions + screenshots/Figma JSON)
├── estimation/
│   └── screenshots/         # Input for /estimate (task files + screenshots for estimation)
└── memory/                  # Project memory files (session context, structure, changelog)
```

## Execution Steps

### Step 1: Create Folder Structure

Create all required folders:

```bash
mkdir -p .project-meta/tasks/init/screenshots
mkdir -p .project-meta/estimation/screenshots
mkdir -p .project-meta/memory
```

### Step 2: Create COMMON_MISTAKES.md (if not exists)

If `.project-meta/COMMON_MISTAKES.md` does not exist, create it with this template:

```markdown
# Common Implementation Mistakes (Project-Specific)

New entries from this project. Copy to `.claude/rules/common-mistakes.md` when curated.

```

### Step 3: Confirm Creation

After creating folders and files, list them to confirm:

```bash
find .project-meta -type d
```

### Step 4: Report to User

Report what was created with usage instructions:

```
## Project Structure Created

Created folders:
- .project-meta/tasks/init/
- .project-meta/tasks/init/screenshots/
- .project-meta/estimation/
- .project-meta/estimation/screenshots/
- .project-meta/memory/
- .project-meta/COMMON_MISTAKES.md

## How to Use

### /tasks-plan — Plan tasks for execution
1. Add task description files (.md) to `.project-meta/tasks/init/`
2. (Optional) Add screenshots (.png, .jpg) to `.project-meta/tasks/init/screenshots/`
3. (Optional) Add Figma JSON exports (.json) to `.project-meta/tasks/init/screenshots/`
4. Run `/tasks-plan` to create tasks.md and status.md
5. Pass extra context: `/tasks-plan focus on mobile first`

### /tasks-run — Execute planned tasks
1. First run `/tasks-plan` to create task files
2. Run `/tasks-run` to execute tasks with team agents

### /estimate — Estimate task effort
1. Add task files (.md, .xlsx) to `.project-meta/estimation/`
2. Add screenshots to `.project-meta/estimation/screenshots/`
3. Run `/estimate` for time estimation
```

## Important Notes

- This command is idempotent — running it multiple times is safe
- Existing files will NOT be deleted
- `.project-meta/` is typically gitignored
