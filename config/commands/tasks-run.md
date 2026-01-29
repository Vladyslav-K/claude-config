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

**CRITICAL: Follow the delegation workflow to save tokens and extend session length.**

### 1. Read Current State (YOU do this)
```
1. Read tasks.md — parse all tasks with their contexts
2. Read status.md — get current statuses from table
3. Merge: create list of tasks with contexts and statuses
```

### 2. Find Next Task(s) to Execute (YOU do this)
```
1. Find all tasks with status "pending"
2. Filter out tasks with unmet dependencies (deps not "done")
3. Identify tasks that CAN run in parallel (no deps on each other)
```

### 3. Execute Task (DELEGATE to frontend-worker)

**For each task, delegate to `frontend-worker`:**

```
Task tool:
  subagent_type: "frontend-worker"
  prompt: |
    ## PROJECT MEMORY (READ FIRST)
    If exists: .project-meta/memory/ - read for project context.

    ## TASK
    [COPY EXACT TASK TITLE FROM tasks.md]

    ## CONTEXT (FROM tasks.md)
    [PASTE FULL CONTEXT SECTION HERE]

    ## FILES TO CREATE/MODIFY
    [LIST FROM TASK]

    ## POST-TASK
    After completing:
    1. Run format-and-check (or format, lint, typecheck)
    2. Fix any issues found
```

**PARALLEL EXECUTION:** If multiple tasks have no dependencies on each other, launch multiple frontend-worker agents in parallel using a single message with multiple Task tool calls.

**Update status.md BEFORE delegating:** Set status to `running`

### 4. Verify Each Task (YOU do this - CRITICAL)

**⚠️ VERIFICATION IS NOT JUST LINT CHECK! You MUST read the actual code!**

**After frontend-worker completes EACH task:**

#### A. READ THE CODE (mandatory!)
1. Use Read tool to open EVERY file created/modified
2. Actually read and understand what the agent wrote
3. This is NOT optional - agents make mistakes!

#### B. COMPARE TO REQUIREMENTS
1. Open the Context section from tasks.md for this task
2. Go through EACH requirement listed there
3. Check: Is this requirement implemented in the code?
4. Check: Is it implemented CORRECTLY?
5. Check: Did agent add anything NOT in requirements?

#### C. VERIFY PATTERNS
1. Does the code follow patterns specified in Context?
2. Are imports correct (from right paths)?
3. Are types/interfaces used correctly?

#### D. DECISION
- **If issues found:**
  - Document SPECIFICALLY what's wrong
  - Re-delegate to frontend-worker with exact fixes needed
  - Do NOT mark as done until YOU verify the fix
- **If ALL requirements met correctly:** Update status.md to `done`
- **If blocked:** Update status.md to `blocked` with reason

**Common agent mistakes to watch for:**
- Missing requirements (forgot to implement something)
- Wrong imports (used different library/path)
- Added extra features not requested
- Wrong types or missing type safety
- Didn't follow specified patterns

### 5. Continue Until Done
Repeat steps 2-4 until:
- All tasks are `done`, OR
- All remaining tasks are `blocked` or waiting for blocked tasks

### 6. Final Verification (YOU do this)
After all tasks complete:
1. **Quick review of all created files** — ensure nothing was missed
2. Run `format-and-check` (or equivalent) — for lint/format issues
3. If issues found → delegate fixes to frontend-worker

### 7. Generate Blocked Report (if needed)
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

## How to Delegate Tasks to frontend-worker

**CRITICAL:** Delegate ALL code writing to frontend-worker. You only coordinate, verify, and update status.

### Frontend-worker Prompt Template

```markdown
## PROJECT MEMORY (READ FIRST)
If exists: .project-meta/memory/ - read for project context.

## TASK
[EXACT task title from tasks.md]

## CONTEXT (COPY FROM tasks.md)
[PASTE the FULL Context section - it contains everything needed]

## FILES
- [file1.tsx] - [create/modify]: [what to do]
- [file2.tsx] - [create/modify]: [what to do]

## CODE STYLE RULES
- Use functional components with TypeScript
- Use 'function' keyword for components
- Use spaces for indentation, semicolons, single quotes
- Use Tailwind CSS
- Use Shadcn UI components
- Wrap callbacks in useCallback

## WHAT NOT TO DO
- Do NOT add comments unrelated to code
- Do NOT create test files
- Do NOT over-engineer
- Do NOT add features not specified in Context

## POST-TASK
After completing:
1. Run format-and-check (or format, lint, typecheck)
2. Fix any issues found
```

### Verification Checklist (YOU do this after each task)

**⚠️ THIS IS NOT JUST RUNNING LINT! You must READ and UNDERSTAND the code!**

```
STEP 1: READ THE CODE (mandatory - don't skip!)
- [ ] Used Read tool to open EVERY created/modified file
- [ ] Actually read the code (not just checked if file exists)

STEP 2: COMPARE TO REQUIREMENTS (mandatory!)
- [ ] Opened Context section for this task
- [ ] Checked EACH requirement - is it implemented?
- [ ] Checked EACH requirement - is it implemented CORRECTLY?
- [ ] No extra features added that weren't requested

STEP 3: VERIFY PATTERNS
- [ ] Follows code patterns from Context
- [ ] Uses correct imports (paths, libraries)
- [ ] Types/interfaces are correct

STEP 4: QUALITY (only after steps 1-3!)
- [ ] No TypeScript errors
- [ ] No lint warnings
```

**If ANY step 1-3 fails:** Re-delegate to frontend-worker with SPECIFIC issues.
**Only mark as done when YOU verified all requirements are correctly implemented.**

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
3. **DELEGATE code writing to frontend-worker** — saves tokens, extends session
4. **⚠️ VERIFY = READ CODE, NOT JUST LINT** — open files, read code, compare to requirements!
5. **Agents make mistakes** — ALWAYS verify before marking done
6. **Run tasks in parallel when possible** — tasks with no deps on each other
7. **Continue past blocked tasks** — don't stop, do what you can
8. **Generate blocked-report.md ONLY at the end** — not during execution
9. **Run format-and-check after all tasks** — for final lint/format cleanup

## Example Execution Flow

```
Reading task state...
Parsing tasks.md...
Found 8 tasks: 0 done, 0 running, 8 pending

Finding tasks with no blocking deps...
Available: #1, #4, #5, #6 (can run in parallel!)

Updating status.md: #1, #4, #5, #6 → running

Delegating to frontend-worker agents (in parallel):
├─ Task 1: AuthContext → frontend-worker
├─ Task 4: API /auth/login → frontend-worker
├─ Task 5: API /auth/register → frontend-worker
└─ Task 6: Dashboard header → frontend-worker

[Waiting for agents to complete...]

Verifying Task 1: AuthContext
├─ Reading src/contexts/auth-context.tsx
├─ Checking: context provider exists ✓
├─ Checking: useAuth hook exists ✓
├─ Checking: types correct ✓
└─ Status: done ✓

Verifying Task 4: API /auth/login
├─ Reading src/app/api/auth/login/route.ts
├─ Checking: POST handler exists ✓
├─ Issue: Missing error handling for invalid credentials
└─ Re-delegating fix to frontend-worker...

[After fix verified]
└─ Status: done ✓

[continues with remaining tasks...]

Finding next available tasks...
Tasks with all deps done: #2 (deps: 1 ✓), #3 (deps: 1 ✓)

[Delegating #2 and #3 in parallel...]

All tasks complete!

Final verification:
├─ Running format-and-check...
├─ Found 2 lint errors
├─ Delegating fix to frontend-worker...
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
