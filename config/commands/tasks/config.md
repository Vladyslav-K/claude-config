---
name: tasks-config
description: Create required folder structure for task management system (.project-meta/tasks/ with subfolders for init, estimation, estimation-small).
---

# Task Management Configuration

## Purpose
Create the required folder structure for the task management system used by other `/tasks-*` commands.

## Folders to Create

```
.project-meta/
└── tasks/
    ├── init/                    # For /tasks-init: place task description files here
    │   └── screenshots/         # Screenshots, designs, and Figma JSON for task reference
    ├── estimation/              # For /tasks-estimate: place xlsx/md task files here
    │   └── screenshots/         # Screenshots/designs for estimation reference
    └── estimation-small/        # For /tasks-estimate-small: place md task files here
```

## Execution Steps

### Step 1: Create Folder Structure

Create all required folders:

```bash
mkdir -p .project-meta/tasks/init/screenshots
mkdir -p .project-meta/tasks/estimation/screenshots
mkdir -p .project-meta/tasks/estimation-small
```

### Step 2: Confirm Creation

After creating folders, list them to confirm:

```bash
find .project-meta/tasks -type d
```

### Step 3: Report to User

Report what was created with usage instructions:

```
## Task Management Structure Created ✓

Created folders:
- .project-meta/tasks/init/
- .project-meta/tasks/init/screenshots/
- .project-meta/tasks/estimation/
- .project-meta/tasks/estimation/screenshots/
- .project-meta/tasks/estimation-small/

## How to Use

### /tasks-init
1. Add task description files (.md) to `.project-meta/tasks/init/`
2. (Optional) Add screenshots (.png, .jpg) to `.project-meta/tasks/init/screenshots/`
3. (Optional) Add Figma JSON exports (.json) to `.project-meta/tasks/init/screenshots/`
4. Run `/tasks-init` to create tasks.md and status.md
5. Pass extra context: `/tasks-init focus on mobile first`

### /tasks-run
1. First run `/tasks-init` to create task files
2. Run `/tasks-run` to execute tasks sequentially

### /tasks-estimate
1. Add task list files (.xlsx or .md) to `.project-meta/tasks/estimation/`
2. Add screenshots to `.project-meta/tasks/estimation/screenshots/`
3. Run `/tasks-estimate` for detailed estimation

### /tasks-estimate-small
1. Add task description files (.md) to `.project-meta/tasks/estimation-small/`
2. Run `/tasks-estimate-small` for quick estimation
```

## Important Notes

- This command is idempotent — running it multiple times is safe
- Existing files in these folders will NOT be deleted
- The `.project-meta/` folder is typically gitignored for project-specific files
