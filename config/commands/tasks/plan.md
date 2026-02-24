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

## Purpose
Read task descriptions from `.project-meta/tasks/plan/`, create a lightweight task index.

**KEY PRINCIPLE:** At this stage you create the INDEX only. Deep analysis of designs and codebase happens during `/tasks:run`.

## Input

**Task files:** `.project-meta/tasks/plan/*.md`
**Design docs/screenshots:** `.project-meta/tasks/plan/screenshots/`

**Matching rules (screenshots → tasks):**
- Task "user-profile" matches:
  - `screenshots/user-profile/` folder (all files inside)
  - `screenshots/user-profile.png`, `screenshots/user-profile-*.png`
  - `screenshots/user-profile*__design.md`
- Folder contents override file name matching
- One file can relate to multiple tasks

## Output

```
.project-meta/tasks/
├── tasks.md          # Task index
└── status.md         # Status tracking
```

---

## Pre-requisite: Plan Mode

**If you are NOT already in plan mode — enter plan mode (EnterPlanMode) BEFORE starting any execution steps.**
Plan mode ensures the user can review and approve the task index before any files are written.

---

## Execution Steps

### 1. Read Task Files
Read all .md files from `.project-meta/tasks/plan/` root.

### 2. List Screenshots (Glob ONLY, DON'T read images)
Glob `.project-meta/tasks/plan/screenshots/**/*` → group by task name.
If no screenshots/ folder — skip, all tasks are code-only.

### 3. API Verification (MANDATORY)
If user provided ONLY screenshots/designs WITHOUT API docs:
1. **ASK:** "Is there a backend API? What are the endpoints?"
2. If no API → note "mock data only" in tasks
3. **NEVER invent** endpoint URLs, field names, or response structures

### 4. Determine Tasks
Extract per task: ID (sequential), short title, description (1-2 sentences from source), dependencies, matched design/screenshot paths, type (visual/code).
Order: no-dep tasks first, then by dependency chain. One task per logical unit.

### 5. Write tasks.md + status.md
Write both files, then verify they exist with correct format.

### 6. Show Summary
Report: source files, design references matched, tasks created, output files.

---

## tasks.md Format

```markdown
# Tasks

Goal: Overall goal
Sources: file1.md, file2.md
Created: YYYY-MM-DD

---

## Task 1: Short title
- What: Brief description (from task description, don't elaborate)
- Deps: none
- Type: visual
- Design: screenshots/list__design.md
- Screenshots: screenshots/list.png

---

## Task 2: Another title
- What: Brief description
- Deps: 1
- Type: code
```

## status.md Format

```markdown
# Tasks Status
Updated: YYYY-MM-DD HH:mm

## Progress: 0/N (0%)

| # | Task | Type | Status | Blocker |
|---|------|------|--------|---------|
| 1 | Task title | visual | pending | |
```

**Status values:** `pending` → `research` → `running` → `done` / `blocked`

---

## Rules

1. **Create INDEX only** — no deep analysis at this stage
2. **DO NOT delete files from plan/** — user manages them
3. **What field = copy from task description** — don't elaborate
4. **One task per logical unit** — don't combine unrelated changes
5. **Verify API exists** before planning API tasks
