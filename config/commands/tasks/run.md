---
name: tasks-run
description: Execute tasks from .project-meta/tasks/tasks.md, update status.md after each task. Parallelizes independent tasks (no shared files, no deps between them) for speed, runs dependent tasks sequentially. Creates blocked-report.md at the end if any tasks are blocked. Use when user says /tasks-run or wants to execute initialized tasks.
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

### 1. Read Current State (YOU do this)
```
1. Read tasks.md and status.md IN PARALLEL (two Read calls in one message)
2. Parse all tasks with their contexts
3. Get current statuses from table
4. Merge: create list of tasks with contexts and statuses
```

### 2. Find Available Tasks (YOU do this)
```
1. Find all tasks with status "pending"
2. Filter out tasks with unmet dependencies (deps not "done")
3. From available tasks, identify PARALLEL GROUPS (see below)
```

### CRITICAL: Parallel Task Execution

**Check if multiple available tasks can run in parallel:**

```
Available tasks: [Task 3, Task 4, Task 5]

Can they run in parallel?
├─ Check 1: Do any share FILES? (compare Files: lists)
│   ├─ Task 3: src/components/btn.tsx
│   ├─ Task 4: src/components/input.tsx
│   └─ Task 5: src/components/btn.tsx  ← CONFLICTS with Task 3!
│
├─ Check 2: Do any depend on each other?
│   ├─ Task 3: Deps: 1 (done ✓)
│   ├─ Task 4: Deps: 2 (done ✓)
│   └─ Task 5: Deps: 1 (done ✓)
│
└─ Result:
   ├─ Group 1 (parallel): Task 3 + Task 4 (no shared files, no shared deps)
   └─ Group 2 (after Group 1): Task 5 (shares files with Task 3)
```

**Parallel safety rules:**

| Check | Parallel OK? |
|-------|-------------|
| Tasks share NO files AND have no dependency between them | ✅ Run in parallel |
| Tasks share ANY file | ❌ Run sequentially |
| Task B depends on Task A | ❌ Run sequentially |
| Tasks modify different files but import from same module | ✅ Usually safe |

**When in doubt → run sequentially.** Better slow than broken.

### 3. Execute Task(s) (YOU do this)

**For a single task or each task in a parallel group:**

1. Update status.md: Set task status(es) to `running`
2. Read the task's Context section carefully
3. If Context references screenshots or Figma JSON, read those files
4. Implement the task using Write/Edit tools following the Context instructions
5. Follow code patterns specified in Context
6. Follow CODE STYLE rules from Context

**For parallel tasks:** Use multiple Write/Edit tool calls in a single message when creating/editing DIFFERENT files. Read multiple Context sections and screenshots in parallel too.

### 4. Verify Task(s) (YOU do this)

After implementing each task (or parallel group):

1. **Run format-and-check** (or format, lint, typecheck)
2. **Fix any issues** found
3. **Re-read created/modified files** to verify they match Context requirements
4. **If issues found:** Fix them directly, re-run format-and-check

### 5. Update Status

After task(s) pass verification:
- Update status.md: Set task status(es) to `done`
- Update progress percentage
- Update timestamp

If task is blocked:
- Update status.md: Set status to `blocked` with reason in Blocker column
- Move to next available task(s)

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
2. **Update status.md after EVERY task or parallel group** — not in large batches
3. **Parallelize independent tasks** — when tasks share NO files and have NO dependency between them, execute in parallel for speed
4. **When in doubt → sequential** — better slow than broken
5. **Implement code YOURSELF** — use Write/Edit tools directly
6. **Verify YOURSELF** — run format-and-check, read files, check requirements
7. **Continue past blocked tasks** — don't stop, do what you can
8. **Generate blocked-report.md ONLY at the end** — not during execution
9. **Run format-and-check after all tasks** — for final lint/format cleanup

## Example Execution Flow

```
Reading task state... (read tasks.md + status.md in parallel)
Parsing tasks.md...
Found 8 tasks: 0 done, 0 running, 8 pending

Finding available tasks...
Task #1: AuthContext (no deps, files: src/contexts/auth.tsx) → available
Task #4: API types (no deps, files: src/types/api.ts) → available
Task #5: Utils (no deps, files: src/lib/utils.ts) → available

Parallel check:
├─ #1, #4, #5 share NO files ✓
├─ #1, #4, #5 have NO deps between them ✓
└─ → Run #1 + #4 + #5 in PARALLEL

Updating status.md: #1, #4, #5 → running

Implementing Tasks 1, 4, 5 in parallel:
├─ Reading 3 Context sections in parallel...
├─ Writing 3 files in parallel (different files)...
├─ Running format-and-check...
├─ All checks pass ✓
└─ Updating status.md: #1, #4, #5 → done

Finding available tasks...
Task #2: LoginForm (deps: 1 ✓, files: src/components/login-form.tsx)
Task #3: RegisterForm (deps: 1 ✓, files: src/components/register-form.tsx)

Parallel check:
├─ #2, #3 share NO files ✓
├─ #2, #3 have NO deps between them ✓
└─ → Run #2 + #3 in PARALLEL

Implementing Tasks 2, 3 in parallel:
├─ Reading Context sections + screenshots in parallel...
├─ Writing different component files in parallel...
├─ Running format-and-check...
├─ Found 1 lint error in #2 → fixing...
├─ Re-running format-and-check...
├─ All checks pass ✓
└─ Updating status.md: #2, #3 → done

[continues with remaining tasks...]

All tasks complete!

Final verification:
├─ Running format-and-check...
└─ All checks pass ✓

Summary:
- Completed: 8/8
- Blocked: 0/8
- Parallel groups used: 3 (saved ~40% time)
```

## Quick Reference: Task Metadata

| Field | Format | Example |
|-------|--------|---------|
| Header | `## Task N: Title` | `## Task 3: Create button` |
| Files | `- Files: path1, path2` | `- Files: src/btn.tsx, src/types.ts` |
| Deps | `- Deps: N, M` or `none` | `- Deps: 1, 2` |
| Context | After `### Context` | Free-form until `---` |
