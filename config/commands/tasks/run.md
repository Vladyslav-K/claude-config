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

**CRITICAL: Execute tasks SEQUENTIALLY. One task at a time.**

### 1. Read Current State (YOU do this)
```
1. Read tasks.md — parse all tasks with their contexts
2. Read status.md — get current statuses from table
3. Merge: create list of tasks with contexts and statuses
```

### 2. Find Next Task to Execute (YOU do this)
```
1. Find all tasks with status "pending"
2. Filter out tasks with unmet dependencies (deps not "done")
3. Pick the FIRST available task (lowest ID)
```

### 3. Execute Task (YOU do this)

**For each task, implement it directly:**

1. Update status.md: Set task status to `running`
2. Read the task's Context section carefully
3. If Context references screenshots or Figma JSON, read those files
4. Implement the task using Write/Edit tools following the Context instructions
5. Follow code patterns specified in Context
6. Follow CODE STYLE rules from Context

### 4. Verify Task (YOU do this)

After implementing each task:

1. **Run format-and-check** (or format, lint, typecheck)
2. **Fix any issues** found
3. **Re-read created/modified files** to verify they match Context requirements
4. **If issues found:** Fix them directly, re-run format-and-check

### 5. Update Status

After task passes verification:
- Update status.md: Set task status to `done`
- Update progress percentage
- Update timestamp

If task is blocked:
- Update status.md: Set status to `blocked` with reason in Blocker column
- Move to next available task

### 6. Continue Until Done
Repeat steps 2-5 until:
- All tasks are `done`, OR
- All remaining tasks are `blocked` or waiting for blocked tasks

### 7. Final Verification (YOU do this)
After all tasks complete:
1. Run `format-and-check` (or equivalent) — for final lint/format cleanup
2. Fix any issues found

### 8. Generate Blocked Report (if needed)
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

## Verification Checklist

After each task:
```
- [ ] All requirements from Context section are implemented
- [ ] Code compiles without errors (TypeScript)
- [ ] format-and-check passes
- [ ] No console.log, debugger, or commented-out code
- [ ] Types are properly defined
- [ ] Follows patterns specified in Context
- [ ] No extra features added beyond what Context specifies
```

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
3. **Execute tasks SEQUENTIALLY** — one at a time, in order
4. **Implement code YOURSELF** — use Write/Edit tools directly
5. **Verify YOURSELF** — run format-and-check, read files, check requirements
6. **Continue past blocked tasks** — don't stop, do what you can
7. **Generate blocked-report.md ONLY at the end** — not during execution
8. **Run format-and-check after all tasks** — for final lint/format cleanup

## Example Execution Flow

```
Reading task state...
Parsing tasks.md...
Found 8 tasks: 0 done, 0 running, 8 pending

Finding next available task...
Task #1: AuthContext (no deps) → available

Updating status.md: #1 → running

Implementing Task 1: AuthContext
├─ Reading Context section...
├─ Creating src/contexts/auth-context.tsx...
├─ Running format-and-check...
├─ All checks pass ✓
└─ Updating status.md: #1 → done

Finding next available task...
Task #2: LoginForm (deps: 1 ✓) → available

Updating status.md: #2 → running

Implementing Task 2: LoginForm
├─ Reading Context section...
├─ Reading screenshot: screenshots/login-form.png
├─ Creating src/components/login-form.tsx...
├─ Running format-and-check...
├─ Found 1 lint error → fixing...
├─ Re-running format-and-check...
├─ All checks pass ✓
└─ Updating status.md: #2 → done

[continues sequentially with remaining tasks...]

All tasks complete!

Final verification:
├─ Running format-and-check...
└─ All checks pass ✓

Summary:
- Completed: 8/8
- Blocked: 0/8
```

## Quick Reference: Task Metadata

| Field | Format | Example |
|-------|--------|---------|
| Header | `## Task N: Title` | `## Task 3: Create button` |
| Files | `- Files: path1, path2` | `- Files: src/btn.tsx, src/types.ts` |
| Deps | `- Deps: N, M` or `none` | `- Deps: 1, 2` |
| Context | After `### Context` | Free-form until `---` |
