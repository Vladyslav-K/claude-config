---
name: tasks-plan
description: Plan tasks for execution by team agents from files in .project-meta/tasks/plan/. Reads task files (md/xlsx/docx), delegates screenshot/Figma analysis to planner agents, creates lightweight tasks.md index + individual context files + status.md.
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
Read task descriptions from `.project-meta/tasks/plan/`, create a structured task system:
- **Lightweight index** (`tasks.md`) — metadata only, NO full context
- **Individual context files** (`context/task-N.md`) — one per task
- **Status tracking** (`status.md`)

**KEY PRINCIPLE:** The orchestrator NEVER reads screenshots or Figma JSON. Visual analysis is delegated to a Planner Agent with its own context window. NO codebase research during planning — agents research during execution.

## Input

### Task files (root of plan/)
Files in `.project-meta/tasks/plan/` directory (.md files with task descriptions)

### Screenshots and Figma JSON (screenshots/ subfolder)
`.project-meta/tasks/plan/screenshots/` containing:
- **Image files** (.png, .jpg, .jpeg, .webp)
- **Figma JSON** (.json) — exported Figma node snapshots

**Matching rules (screenshots → tasks):**
- Task "user-profile" matches:
  - `screenshots/user-profile/` folder (all files inside)
  - `screenshots/user-profile.png`
  - `screenshots/user-profile-*.png` (e.g., `-mobile.png`)
  - `screenshots/user-profile.json`
  - `screenshots/user-profile-*.json`
- Folder contents override file name matching
- One file can relate to multiple tasks

## Output

```
.project-meta/tasks/
├── tasks.md          # INDEX: metadata only (NO context!)
├── status.md         # Status tracking table
└── context/          # Individual task briefs
    ├── task-1.md     # Context for task 1
    ├── task-2.md     # Context for task 2
    └── ...
```

---

## Execution Steps

### Step 1: Read Task Files (YOU do this)
Read all files from `.project-meta/tasks/plan/` root using Read tool.
These are text descriptions — small enough for your context.

### Step 2: List Screenshots (YOU do this — Glob ONLY, DON'T read images!)

```
1. Glob: .project-meta/tasks/plan/screenshots/**/*
2. Note file names and paths — DO NOT open/read image files!
3. Group by task name (folder name or file prefix)
```

**If no screenshots/ folder — skip, all tasks are code-only.**

### Step 3: API Verification Check (MANDATORY)

If user provided ONLY screenshots/designs WITHOUT API documentation:
1. **ASK:** "Is there a backend API for this feature? What are the endpoints?"
2. If API exists → ask for endpoint details, field names, response shapes
3. If no API → mark API tasks as BLOCKED, create UI-only tasks with mock data
4. **NEVER invent** endpoint URLs, field names, or response structures

### Step 4: Determine Tasks (YOU do this)

Extract from descriptions:
- Unique ID (sequential number)
- Short title
- Files to create/modify
- Dependencies on other tasks
- Matched screenshot/Figma paths
- Classification: **visual** (has screenshots/figma) or **code** (no visual refs)

**Task ordering:** no-dep tasks first, then by dependency chain.

### Step 5: Create Directory Structure

```bash
mkdir -p .project-meta/tasks/context
```

### Step 6: Write Context Files

#### For CODE tasks — write yourself:
Context for code tasks is lightweight text — write directly with Write tool.

#### For VISUAL tasks — delegate to Planner Agent(s):

Spawn planner agent(s) to read screenshots + Figma JSON and write context files.

**Distribution strategy:**

| Visual tasks | Planners | Notes |
|-------------|----------|-------|
| 1-3 | 1 planner | Handles all visual tasks |
| 4-6 | 2 planners | Split evenly |
| 7+ | 3 planners | ~2-3 tasks per planner |

**Each planner writes its own context files directly — no assembler needed.**

**Model selection:** Use model from `.claude/rules/workflow/agent-models.md` per agent role. `inherit` → omit `model` param. Other values → pass as `model` param.

**Planner-{N}:**
```
Task tool:
  subagent_type: "general-purpose"
  description: "Create visual task context files"
  mode: "bypassPermissions"
  prompt: |
    You are PLANNER agent "planner-{N}".

    ## FIRST ACTION (MANDATORY — before anything else)
    Invoke skills: 1. "agent:common" 2. "agent:planner"
    Then follow loaded instructions.

    ## TASKS TO PROCESS

    [For EACH visual task assigned to this planner:]
    ---
    Task {ID}: {title}
    Output: {CWD}/.project-meta/tasks/context/task-{ID}.md
    Screenshots: {absolute paths — READ these}
    Figma JSON: {absolute paths or "none" — READ these}
    Description: {from plan files}
    Files to create/modify: {list}
    ---
```

**If multiple planners:** spawn ALL in a SINGLE message (parallel Task calls).

**If NO visual tasks exist → skip this step entirely. Write all context files yourself.**

Wait for ALL planner agents to complete before proceeding to Step 7.

### Step 7: Write tasks.md INDEX (YOU do this)

Write lightweight index with Write tool. **NO context sections — just metadata.**

### Step 8: Write status.md (YOU do this)

Write status tracking table with Write tool.

### Step 9: Verify (YOU do this)

Check that files were created:
1. `tasks.md` exists with correct format (read it)
2. `status.md` exists with all tasks (read it)
3. `context/task-N.md` exists for EACH task (Glob check)

**DO NOT re-read full context files.** Just verify existence.

### Step 10: Show Summary

Report what was created.

---

## tasks.md Format (LIGHTWEIGHT INDEX)

```markdown
# Tasks Plan

Goal: Overall goal
Sources: file1.md, file2.md
Created: YYYY-MM-DD

---

## Task 1: Short title
- Files: path/to/file.tsx, path/to/other.tsx
- Deps: none
- Type: code
- Context: context/task-1.md

---

## Task 2: Page title
- Files: path/to/page.tsx, path/to/components.tsx
- Deps: 1
- Type: visual
- Screenshots: screenshots/page.png
- Figma: screenshots/page.json
- Context: context/task-2.md

---
```

**NO `### Context` sections in tasks.md!** Context lives in `context/task-N.md` files.

## Field Descriptions

| Field | Description |
|-------|-------------|
| **Task N: Title** | Unique ID and short title |
| **Files** | Comma-separated files to create/modify |
| **Deps** | Task IDs that must complete first, or "none" |
| **Type** | `code` or `visual` |
| **Screenshots** | Paths relative to plan/ (visual tasks only) |
| **Figma** | Paths to Figma JSON (visual tasks only) |
| **Context** | Path to individual context file |

## Parsing Rules (for tasks-run)

1. Split file by `---` separators
2. Find task blocks: `## Task N: Title`
3. Extract metadata: `- Files:`, `- Deps:`, `- Type:`, `- Screenshots:`, `- Figma:`, `- Context:`
4. All tasks use 2-agent chain: implementer + validator (both research independently)

## context/task-N.md Format

### For CODE tasks (written by orchestrator):

```markdown
# Task N: Title

## Action
CREATE / MODIFY — which files

## Requirements
What to build, constraints, acceptance criteria.

## Acceptance Criteria
- [ ] criterion 1
- [ ] criterion 2

## References
- Similar existing file: [path]
- Types/interfaces: [paths]
- Components to use: [list]
```

### For VISUAL tasks (written by Planner Agent):

Lightweight format — describes WHAT to build, not HOW. No design specs, no component trees.
Full format defined in `agent:planner` skill. Implementers extract design specs themselves from screenshots/Figma JSON.

## status.md Format

```markdown
# Tasks Status
Updated: YYYY-MM-DD HH:mm

## Progress: 0/N (0%)

| # | Task | Type | Status | Blocker |
|---|------|------|--------|---------|
| 1 | Task title | code | pending | |
| 2 | Task title | visual | pending | |
```

**Status values:** `pending` → `running` → `done` / `blocked`

---

## Important Rules

1. **DO NOT read screenshots yourself** — delegate to Planner Agent
2. **DO NOT do codebase research** — agents research during execution (/tasks-run)
3. **DO NOT delete files from plan/** — user manages them
4. **tasks.md is INDEX ONLY** — no full context, just metadata + paths
5. **Each task gets its own context file** in `context/`
6. **Verify API exists** before planning API tasks (Step 3)
7. **Page structure comes from SCREENSHOT only** — never copy structure from reference pages
8. **Order tasks by dependencies** — no-dep first
9. **One task per logical unit** — don't combine unrelated changes

---

## Example Output Summary

```
Planned 6 tasks from 1 source file:

Source files:
- sourcing-requests.md

Design references:
- screenshots/list.png + list.json → Task 3 (visual)
- screenshots/details.png + details.json → Task 4 (visual)
- No visual reference: Tasks 1, 2, 5, 6

Tasks created:
1. API Types (code, no deps) → context/task-1.md
2. API Service + Hooks (code, deps: 1) → context/task-2.md
3. List Page (visual, deps: 1,2) → context/task-3.md [planner agent]
4. Detail Page (visual, deps: 1,2) → context/task-4.md [planner agent]
5. Sidebar Navigation (code, no deps) → context/task-5.md
6. Page Titles (code, deps: 3,4) → context/task-6.md

Files created:
- .project-meta/tasks/tasks.md (index, ~30 lines)
- .project-meta/tasks/status.md
- .project-meta/tasks/context/task-1.md through task-6.md
```
