---
name: tasks-run
description: Execute tasks from .project-meta/tasks/tasks.md, update status.md after each task. Executes tasks sequentially. Creates blocked-report.md at the end if any tasks are blocked. Use when user says /tasks-run or wants to execute initialized tasks.
---

# Task Execution

## Additional context from user before start task
$ARGUMENTS

## Purpose
Execute tasks from the initialized task system (Markdown format), track progress in status.md, and generate a report of blocked tasks at the end.

## Input
- `.project-meta/tasks/tasks.md` — task definitions with full context in Markdown (READ ONLY)
- `.project-meta/tasks/status.md` — current status of each task

## Output
- Updated `.project-meta/tasks/status.md` — after each task completion
- `.project-meta/tasks/blocked-report.md` — generated at the end if any tasks are blocked

## Parsing tasks.md

The tasks.md file uses this structure:

```markdown
# Tasks Plan

Goal: ...
Sources: ...
Created: ...

---

## Task 1: Title here
- Files: file1.tsx, file2.tsx
- Deps: none

### Context

[Full context for execution here]

---

## Task 2: Another title
- Files: file3.tsx
- Deps: 1

### Context

[Full context]

---
```

### How to Parse

1. **Split by `---`** separators to get individual blocks
2. **Find task headers** matching pattern `## Task N: Title`
3. **Extract metadata**:
   - `Files:` — split by comma, trim whitespace
   - `Deps:` — "none" means empty array, otherwise split by comma and parse as numbers
4. **Extract context** — everything after `### Context` until the next `---` or end of block

### Example Parsing Result

From this block:
```markdown
## Task 3: Create UserCard component
- Files: src/components/user-card.tsx
- Deps: 1, 2

### Context

CREATE NEW FILE: src/components/user-card.tsx
...full context here...
```

Extract:
- ID: 3
- Title: "Create UserCard component"
- Files: ["src/components/user-card.tsx"]
- Deps: [1, 2]
- Context: "CREATE NEW FILE: src/components/user-card.tsx\n...full context here..."

## Execution Steps

### 1. Read Current State
```
1. Read tasks.md — parse all tasks with their contexts
2. Read status.md — get current statuses from table
3. Merge: create list of tasks with contexts and statuses
```

### 2. Find Next Task to Execute
```
1. Find all tasks with status "pending"
2. Filter out tasks with unmet dependencies (deps not "done")
3. Select the first available task
```

### 3. Execute Task

**For each task (sequential execution):**
1. Update status.md: set status to `running`
2. **Execute the task yourself** using the FULL context from Context section
3. Use Edit/Write tools to create or modify files as specified
4. On success: update status.md to `done`
5. On failure/blocker: update status.md to `blocked` with reason

**IMPORTANT:** Execute tasks yourself, do NOT delegate to agents. This prevents memory issues with parallel agent execution.

### 4. Continue Until Done
Repeat steps 2-3 until:
- All tasks are `done`, OR
- All remaining tasks are `blocked` or waiting for blocked tasks

### 5. Run Verification
After completing all tasks, run `format-and-check` (or equivalent) and fix any issues.

### 6. Generate Blocked Report (if needed)
If any tasks have status `blocked`, create `.project-meta/tasks/blocked-report.md`

## status.md Update Format

When updating status.md:
1. Find the row for the task by ID
2. Replace status cell value
3. Add blocker text if blocked
4. Update "Updated:" timestamp
5. Recalculate progress percentage

**Status values:**
- `pending` — not started
- `running` — in progress
- `done` — completed
- `blocked` — cannot proceed

## How to Execute Tasks

**CRITICAL:** You execute tasks directly. The Context section from tasks.md contains everything needed.

When executing a task:

1. **Read the Context section** — it contains all information needed
2. **Create/modify files** using Edit or Write tools
3. **Follow the patterns** shown in Context section
4. **Apply code style rules**:
   - Use functional components with TypeScript
   - Use 'function' keyword for components
   - Use spaces for indentation, semicolons, single quotes
   - Use Tailwind CSS
   - Use Shadcn UI components
   - Wrap callbacks in useCallback
5. **What NOT to do**:
   - Do NOT add comments unrelated to code
   - Do NOT create test files
   - Do NOT over-engineer

Note: The Context section should already include code patterns, examples, and specific instructions from tasks-init.

## blocked-report.md Format

```markdown
# Blocked Tasks Report
Generated: YYYY-MM-DD HH:mm

## Summary
- Total: N tasks
- Completed: X
- Blocked: Y
- Remaining: Z

## Blocked Tasks

### Task [ID]: Title
**Status:** blocked
**Reason:** Why it's blocked
**Files:** list of files
**What was done:** What progress was made before blocking
**Next steps:** What needs to happen to unblock

### Task [ID]: Another Blocked Task
...

## Tasks Waiting on Blocked
These tasks cannot proceed because they depend on blocked tasks:

| # | Task | Waiting for |
|---|------|-------------|
| 5 | Some task | Task 3 (blocked) |
```

## Important Rules

1. **NEVER modify tasks.md** — it's read-only after initialization
2. **Update status.md after EVERY task** — not in batches
3. **Execute tasks yourself** — do NOT delegate to other agents
4. **Continue past blocked tasks** — don't stop, do what you can
5. **Generate blocked-report.md ONLY at the end** — not during execution
6. **Run format-and-check after all tasks** — fix any issues found

## Example Execution Flow

```
Reading task state...
Parsing tasks.md...
Found 8 tasks: 0 done, 0 running, 8 pending

Finding next task...
Task with no blocking deps: #1

Executing Task 1: AuthContext
├─ Status: running
├─ Creating src/contexts/auth-context.tsx
├─ [writing code...]
└─ Status: done

Finding next task...
Tasks with all deps done: #2 (deps: 1 ✓), #3 (deps: 1 ✓), #4 (deps: none ✓)

Executing Task 2: LoginForm
├─ Status: running
├─ Creating src/components/login-form.tsx
├─ [writing code...]
└─ Status: done

[continues sequentially until all done or blocked]

Running format-and-check...
Fixing 2 lint errors...

Generating blocked report...
Created: .project-meta/tasks/blocked-report.md

Summary:
- Completed: 6/8
- Blocked: 2/8

See blocked-report.md for details on what couldn't be completed.
```

## Quick Reference: Task Metadata

| Field | Format | Example |
|-------|--------|---------|
| Header | `## Task N: Title` | `## Task 3: Create button` |
| Files | `- Files: path1, path2` | `- Files: src/btn.tsx, src/types.ts` |
| Deps | `- Deps: N, M` or `none` | `- Deps: 1, 2` |
| Context | After `### Context` | Free-form until `---` |
