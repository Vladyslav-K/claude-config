---
name: tasks-plan
description: Create task index from files in .project-meta/tasks/plan/. Links tasks to design documents and screenshots.
---

# Task Planning

## Additional context from user before start task
$ARGUMENTS

**How to use arguments:**
- `/tasks-plan` — run with default behavior
- `/tasks-plan focus on mobile layout first` — additional context for task ordering
- `/tasks-plan skip auth tasks, only UI` — scope limitations
- `/tasks-plan use existing Button component from shadcn` — technical hints

## Purpose
Read task descriptions from `.project-meta/tasks/plan/`, create a lightweight task system:
- **Task index** (`tasks.md`) — task titles + links to design documents/screenshots
- **Status tracking** (`status.md`)

**KEY PRINCIPLE:** At this stage you create the INDEX only. You read task description text files, match them to design documents/screenshots by name, and write a minimal index. Deep analysis of designs and codebase happens during execution (`/tasks:run`).

## Input

### Task files (root of plan/)
Files in `.project-meta/tasks/plan/` directory (.md files with task descriptions)

### Design Documents and Screenshots (screenshots/ subfolder)
`.project-meta/tasks/plan/screenshots/` containing:
- **Design documents** (`*__design.md`) — structured design specs generated from Figma
- **Image files** (.png, .jpg, .jpeg, .webp)

**Matching rules (design docs/screenshots → tasks):**
- Task "user-profile" matches:
  - `screenshots/user-profile/` folder (all files inside)
  - `screenshots/user-profile.png`
  - `screenshots/user-profile-*.png` (e.g., `-mobile.png`)
  - `screenshots/user-profile*__design.md`
- Folder contents override file name matching
- One file can relate to multiple tasks

## Output

```
.project-meta/tasks/
├── tasks.md          # Task index: titles + design doc/screenshot links
└── status.md         # Status tracking table
```

---

## Execution Steps

### Step 1: Read Task Files
Read all .md files from `.project-meta/tasks/plan/` root using Read tool.
These are text descriptions — small enough for your context.

### Step 2: List Screenshots (Glob ONLY, DON'T read images at this stage)

```
1. Glob: .project-meta/tasks/plan/screenshots/**/*
2. Note file names and paths — DO NOT open/read image files
3. Group by task name (folder name or file prefix)
```

**If no screenshots/ folder — skip, all tasks are code-only.**

### Step 3: API Verification Check (MANDATORY)

If user provided ONLY screenshots/designs WITHOUT API documentation:
1. **ASK:** "Is there a backend API for this feature? What are the endpoints?"
2. If API exists → ask for endpoint details, field names, response shapes
3. If no API → note "mock data only" in tasks
4. **NEVER invent** endpoint URLs, field names, or response structures

### Step 4: Determine Tasks

Extract from task description files:
- Unique ID (sequential number)
- Short title
- What to build (1-2 sentences — copy from task description, don't elaborate)
- Dependencies on other tasks
- Matched design document/screenshot paths
- Type: **visual** (has design docs/screenshots) or **code** (no visual refs)

**Task ordering:** no-dep tasks first, then by dependency chain.
**One task per logical unit** — don't combine unrelated changes.

### Step 5: Write tasks.md
Write the task index with Write tool.

### Step 6: Write status.md
Write the status tracking table with Write tool.

### Step 7: Verify
Check that both files exist with correct format (read them).

### Step 8: Show Summary
Report what was created.

---

## tasks.md Format

```markdown
# Tasks

Goal: Overall goal
Sources: file1.md, file2.md
Created: YYYY-MM-DD

---

## Task 1: Short title
- What: Brief description of what to build (from task description)
- Deps: none
- Type: visual
- Design: screenshots/list__design.md
- Screenshots: screenshots/list.png

---

## Task 2: Another title
- What: Brief description
- Deps: 1
- Type: code

---
```

## Field Descriptions

| Field | Description |
|-------|-------------|
| **Task N: Title** | Unique ID and short title |
| **What** | 1-2 sentences from task description (copy, don't elaborate) |
| **Deps** | Task IDs that must complete first, or "none" |
| **Type** | `code` or `visual` |
| **Design** | Paths to design documents `*__design.md` (visual tasks only) |
| **Screenshots** | Paths relative to plan/ (visual tasks only) |

## Parsing Rules (for tasks:run)

1. Split file by `---` separators
2. Find task blocks: `## Task N: Title`
3. Extract metadata: `- What:`, `- Deps:`, `- Type:`, `- Design:`, `- Screenshots:`
4. Tasks are executed sequentially during `/tasks:run`

## status.md Format

```markdown
# Tasks Status
Updated: YYYY-MM-DD HH:mm

## Progress: 0/N (0%)

| # | Task | Type | Status | Blocker |
|---|------|------|--------|---------|
| 1 | Task title | visual | pending | |
| 2 | Task title | code | pending | |
```

**Status values:** `pending` → `research` → `running` → `done` / `blocked`

---

## Important Rules

1. **At planning stage, focus on creating the INDEX** — deep analysis happens during execution
2. **DO NOT delete files from plan/** — user manages them
3. **tasks.md is INDEX ONLY** — titles + links to design docs/screenshots
4. **One task per logical unit** — don't combine unrelated changes
5. **Order tasks by dependencies** — no-dep first
6. **Verify API exists** before planning API tasks (Step 3)
7. **What field = copy from task description** — don't elaborate, don't analyze

---

## Example Output Summary

```
Planned 2 tasks from 1 source file:

Source files:
- sourcing-requests.md

Design references:
- screenshots/list__design.md + list.png → Task 1
- screenshots/details__design.md + details.png → Task 2

Tasks created:
1. Sourcing Requests List Page (visual, no deps)
2. Sourcing Request Details Page (visual, deps: 1)

Files created:
- .project-meta/tasks/tasks.md
- .project-meta/tasks/status.md
```
