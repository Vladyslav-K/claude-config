---
name: tasks-run
description: Execute tasks from .project-meta/tasks/tasks.md using a team of agents. Parallelizes independent tasks (no shared files, no deps) for speed via separate agents. Validates each task after completion. Creates blocked-report.md at the end if any tasks are blocked. Use when user says /tasks-run or wants to execute initialized tasks.
---

# Task Execution (Team Workflow)

## Additional context from user before start task
$ARGUMENTS

## Purpose
Execute tasks from the initialized task system using a team of implementer agents. Independent tasks run in parallel via separate agents (inherits current chat model). After each task completion, the team lead (YOU) validates the result against requirements and screenshots before marking as done.

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
   - `Screenshots:` — paths to reference images (if present)
   - `Figma:` — paths to design specs (if present)
4. **Extract context** — everything after `### Context` until next `### Design Specs` or `---`
5. **Extract design specs** — everything after `### Design Specs` until `---` (optional)

## Execution Steps

### 1. Read and Parse (YOU do this)

```
1. Read tasks.md and status.md IN PARALLEL (two Read calls in one message)
2. Parse all tasks with their contexts
3. Get current statuses from table
4. Merge: create list of tasks with contexts and statuses
5. Count: total, done, pending, blocked
```

### 2. Research Codebase (DELEGATE to Explore agent)

**Before spawning implementers, research codebase patterns:**

```
Task tool:
  subagent_type: "Explore"
  description: "Research codebase patterns for tasks"
  prompt: |
    ## PROJECT MEMORY (READ FIRST)
    If exists: {CWD}/.project-meta/memory/ - read for project context.

    ## RESEARCH TASK
    Find code patterns, conventions, and examples for these tasks:
    [LIST ALL PENDING TASKS: titles + files]

    ## WHAT TO RETURN
    1. FULL CODE of similar components/features (actual code, not descriptions)
    2. Exact import paths used in this project
    3. Type/interface definitions
    4. Code style patterns (indentation, quotes, semicolons)
    5. Component patterns (function keyword, hooks usage, export style)
    6. File structure conventions

    Return ACTUAL code that can be used as reference.
```

### 3. Create Team (YOU do this)

```
TeamCreate:
  team_name: "tasks-execution"
  description: "Executing tasks from tasks.md"
```

### 4. Find Available Tasks and Group (YOU do this)

```
1. Find all tasks with status "pending"
2. Filter out tasks with unmet dependencies (deps not "done")
3. From available tasks, identify PARALLEL GROUPS
```

### CRITICAL: Parallel Task Grouping

```
Available tasks: [Task 3, Task 4, Task 5]

Can they run in parallel?
├─ Check 1: Do any share FILES? (compare Files: lists)
│   ├─ Task 3: src/components/btn.tsx
│   ├─ Task 4: src/components/input.tsx
│   └─ Task 5: src/components/btn.tsx  ← CONFLICTS with Task 3!
│
├─ Check 2: Do any depend on each other?
│   (all deps already "done")
│
└─ Result:
   ├─ Group 1 (parallel): Task 3 + Task 4
   └─ Group 2 (after Group 1): Task 5
```

**Parallel safety rules:**

| Check | Parallel OK? |
|-------|-------------|
| Tasks share NO files AND no dependency between them | ✅ Run in parallel |
| Tasks share ANY file | ❌ Run sequentially |
| Task B depends on Task A | ❌ Run sequentially |
| Tasks modify different files but import from same module | ✅ Usually safe |

**When in doubt → run sequentially.** Better slow than broken.

### 5. Spawn Implementer Agents (YOU do this)

**CRITICAL: NEVER specify `model` param. Omit it → agent inherits current chat model.**

For each task in a parallel group, spawn an agent:

```
Task tool:
  subagent_type: "general-purpose"
  # model is NOT specified — inherits current chat model
  team_name: "tasks-execution"
  name: "impl-{N}"
  mode: "bypassPermissions"
  run_in_background: true
  prompt: |
    You are implementer agent "impl-{N}".

    ## YOUR TASK
    Task {N}: {Title}
    Files: {files list}

    {FULL CONTEXT from tasks.md — copy entire Context section}

    ## DESIGN SPECS
    {Design Specs section from tasks.md if present}

    ## SCREENSHOTS
    {Screenshot paths if present — agent should READ these files}

    ## PROJECT CONTEXT
    Working directory: {CWD}
    Memory: {CWD}/.project-meta/memory/ (read these first!)

    ## CODEBASE PATTERNS (from research)
    {Paste relevant code patterns found by Explore agent}

    ## KNOWN MISTAKES (read these files if they exist)
    - .claude/rules/common-mistakes.md (global known mistakes)
    - {CWD}/.project-meta/COMMON_MISTAKES.md (project-specific mistakes)
    Read them and avoid ALL listed mistakes.

    ## RULES
    - Read project memory files FIRST for project architecture and patterns
    - Read common mistakes files (listed above) if they exist
    - Follow existing code patterns EXACTLY
    - Don't create tests unless specified
    - Don't add unnecessary comments (no task descriptions, no change notes)
    - Use English for all code and comments
    - Follow the project's code style
    - If screenshots exist, READ them to understand the visual design

    ## WHEN DONE
    1. Re-read your created/modified files to verify correctness
    2. Run format-and-check (or format, lint, typecheck), fix any issues
    3. Report: list all files created/modified and what was done
```

**For parallel groups:** Spawn ALL agents for the group in a SINGLE message (multiple Task tool calls in parallel).

### 6. Validate Each Task (YOU do this — CRITICAL)

**After each agent completes, YOU MUST validate:**

1. **Read output files** the agent created/modified
2. **If task has screenshots:**
   - Read the screenshot file(s) using Read tool
   - Compare with agent's implementation:
     - All visible components present?
     - Layout direction correct?
     - Spacing reasonable?
     - Colors match?
     - Typography correct?
     - Interactive elements present?
3. **If task has design specs:**
   - Verify dimensions match Figma specs
   - Verify colors match
   - Verify typography matches
4. **Check code quality:**
   - Follows project patterns (from research)
   - Proper TypeScript types
   - No console.log or commented code
   - Imports from correct locations
   - No extra features beyond requirements
5. **Decision:**
   - ✅ Good → Update status.md: task → `done`
   - ⚠️ Minor issues → Fix yourself with Edit tool, then mark `done`
   - ❌ Major issues → Send correction to agent OR fix yourself

### 7. Update Status and Continue

After validating current group:
1. Update status.md: completed tasks → `done`, blocked tasks → `blocked`
2. Update progress percentage and timestamp
3. Find newly available tasks (dependencies now met)
4. Analyze parallel groups again
5. Spawn new agents for next batch
6. Repeat steps 5-7 until all tasks done or blocked

### 8. Final Verification (YOU do this)

After all tasks complete:
1. Run `format-and-check` (or equivalent) — final lint/format cleanup
2. Fix any issues found

### 9. Shutdown Team

```
SendMessage type: "shutdown_request" to each active agent
Then: TeamDelete
```

### 10. Generate Reports

If any tasks have status `blocked`, create `.project-meta/tasks/blocked-report.md`

Update status.md with final state and report summary to user.

## status.md Update Format

When updating status.md:
1. Find the row for the task by ID
2. Replace status cell value
3. Add blocker text if blocked
4. Update "Updated:" timestamp
5. Recalculate progress percentage

**Status values:**
- `pending` — not started
- `running` — in progress (agent working on it)
- `done` — completed and validated
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
- [ ] Design specs match (if applicable)
- [ ] Screenshot comparison passes (if applicable)
```

## Screenshot Validation

When task has screenshots:
```
1. Read the screenshot file (Read tool handles images)
2. Read the created/modified code file(s)
3. Compare:
   - [ ] All visible components are present in code
   - [ ] Layout structure matches (row/column, alignment)
   - [ ] Spacing is reasonable (padding, gaps)
   - [ ] Colors match visible design
   - [ ] Typography looks correct (size, weight)
   - [ ] Interactive elements present (buttons, inputs, links)
   - [ ] Nothing extra added that's not in the design
4. If mismatches found:
   - Minor (missing class, wrong spacing) → fix yourself
   - Major (missing component, wrong layout) → send to agent or fix
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
2. **Use TEAM workflow** — always TeamCreate, then spawn agents with team_name
3. **NEVER specify model param** — omit it, agent inherits current chat model
4. **VALIDATE every completed task** — read files, compare with requirements/screenshots
5. **Update status.md after EACH validated task** — not in large batches
6. **Parallelize independent tasks** — spawn agents in parallel when safe
7. **When in doubt → sequential** — better slow than broken
8. **Fix minor issues yourself** — faster than round-tripping to agent
9. **Continue past blocked tasks** — do what you can
10. **Run format-and-check after ALL tasks** — final cleanup
11. **Generate blocked-report.md ONLY at the end** — not during execution
12. **Shutdown team and clean up** — after all work is complete

## Example Execution Flow

```
Reading task state... (read tasks.md + status.md in parallel)
Parsing tasks.md...
Found 8 tasks: 0 done, 0 running, 8 pending

Researching codebase patterns (Explore agent, very thorough)...
Found: component patterns, import paths, code style

Creating team "tasks-execution"...

Finding available tasks...
Task #1: AuthContext (no deps, files: src/contexts/auth.tsx)
Task #4: API types (no deps, files: src/types/api.ts)
Task #5: Utils (no deps, files: src/lib/utils.ts)

Parallel check: #1, #4, #5 share NO files ✓ → parallel

Spawning 3 agents (no model param, inherits chat model) in ONE message:
├─ impl-1 → Task #1 (full context + patterns)
├─ impl-2 → Task #4 (full context + patterns)
└─ impl-3 → Task #5 (full context + patterns)

Waiting for completions...

impl-1 completed → Validating Task #1...
├─ Reading src/contexts/auth.tsx ✓
├─ Checking patterns match ✓
├─ Checking TypeScript types ✓
└─ ✅ Validated → status.md: #1 → done

impl-2 completed → Validating Task #4...
├─ Reading src/types/api.ts ✓
└─ ✅ Validated → status.md: #4 → done

impl-3 completed → Validating Task #5...
├─ Reading src/lib/utils.ts
├─ ⚠️ Missing export for formatDate
├─ Fixing myself (Edit tool)...
└─ ✅ Fixed + validated → status.md: #5 → done

Finding available tasks...
Task #2: LoginForm (deps: 1 ✓, has screenshot)
Task #3: RegisterForm (deps: 1 ✓, has screenshot)

Parallel check: #2, #3 share NO files ✓ → parallel

Spawning 2 agents:
├─ impl-1 → Task #2 (context + screenshot path + patterns)
└─ impl-2 → Task #3 (context + screenshot path + patterns)

impl-1 completed → Validating Task #2...
├─ Reading src/components/login-form.tsx
├─ Reading screenshot: login-form.png
├─ Comparing layout... ✓
├─ Comparing components... ✓
├─ ❌ Missing "Forgot password" link (visible in screenshot)
├─ Fixing myself (adding link)...
└─ ✅ Fixed + validated → status.md: #2 → done

impl-2 completed → Validating Task #3...
├─ Reading src/components/register-form.tsx
├─ Reading screenshot: register-form.png
├─ All components match ✓
└─ ✅ Validated → status.md: #3 → done

[continues with remaining tasks...]

All tasks complete!

Final verification:
├─ Running format-and-check...
├─ Found 1 lint warning → fixing...
└─ Re-running → ✅ All clear

Shutting down team...
├─ shutdown_request → impl-1 ✓
├─ shutdown_request → impl-2 ✓
└─ TeamDelete ✓

Summary:
- Completed: 8/8
- Blocked: 0/8
- Validation fixes: 2 (minor, fixed in-place)
```

## Quick Reference: Task Metadata

| Field | Format | Example |
|-------|--------|---------|
| Header | `## Task N: Title` | `## Task 3: Create button` |
| Files | `- Files: path1, path2` | `- Files: src/btn.tsx, src/types.ts` |
| Deps | `- Deps: N, M` or `none` | `- Deps: 1, 2` |
| Screenshots | `- Screenshots: path` | `- Screenshots: screenshots/btn.png` |
| Figma | `- Figma: path` | `- Figma: screenshots/btn.json` |
| Context | After `### Context` | Free-form until `---` |
| Design Specs | After `### Design Specs` | Optional, until `---` |
