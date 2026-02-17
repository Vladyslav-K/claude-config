---
name: tasks-run
description: Execute tasks from .project-meta/tasks/tasks.md using 2-agent chains. Each task runs through implementer ↔ validator. Independent tasks parallelized. Creates blocked-report.md if any blocked.
---

# Task Execution (2-Agent Chain)

## Additional context from user before start task
$ARGUMENTS

## Purpose
Execute tasks from the lightweight task index using autonomous 2-agent chains. Each task gets an Implementer + Validator pair. Both agents independently research the project and read all task materials.

**KEY PRINCIPLE:** You are a PURE MANAGER. You read ONLY the task index and status. Agents read their own context files, screenshots, Figma JSON, and codebase. You NEVER read code, screenshots, or context files.

## Input
- `.project-meta/tasks/tasks.md` — lightweight task INDEX (metadata only, READ ONLY)
- `.project-meta/tasks/status.md` — current status
- `.project-meta/tasks/context/` — individual context files (**agents read these, NOT you**)

## Output
- Updated `.project-meta/tasks/status.md`
- `.project-meta/tasks/blocked-report.md` — if any tasks blocked (generated at end)

---

## Execution Steps

### 1. Read and Parse (YOU do this)

Read tasks.md and status.md **IN PARALLEL** (two Read calls, one message):

```
From tasks.md extract ONLY metadata per task:
  - ID, Title
  - Files list
  - Deps
  - Type (code/visual)
  - Screenshots paths (if visual)
  - Figma paths (if visual)
  - Context file path

From status.md:
  - Current status per task

Merge → list of tasks with statuses
Count: total, done, pending, blocked
```

**DO NOT read context/ files.** Agents read their own.

### 2. Find Available Tasks and Group (YOU do this)

```
1. Find all tasks with status "pending"
2. Filter out tasks with unmet deps (deps not "done")
3. Group for parallel execution:
   - No shared files AND no deps between them → parallel
   - Any shared files or dependency → sequential
```

**When in doubt → sequential.**

### 3. Create Team (YOU do this)

```
TeamCreate:
  team_name: "tasks-execution"
  description: "Executing tasks from tasks.md"
```

### 4. Spawn Agent Pairs for Current Batch

**Spawn ALL agents for ALL tasks in the batch in a SINGLE message (parallel Task calls).**

Each task gets exactly 2 agents: `implementer-{N}` + `validator-{N}`.

**Implementer-{N}:**
```
Task tool:
  subagent_type: "general-purpose"
  team_name: "tasks-execution"
  name: "implementer-{N}"
  mode: "bypassPermissions"
  prompt: |
    You are IMPLEMENTER agent "implementer-{N}" in team "tasks-execution".

    ## FIRST ACTION (MANDATORY — before anything else)
    Invoke skills: 1. "agent:common" 2. "agent:implementer"
    Then follow loaded instructions.

    ## YOUR CHAIN
    - Receive task from: orchestrator (team lead)
    - After completion, send file paths to: orchestrator (team lead)
    - Corrections come from: validator-{N}
    - Send correction updates to: validator-{N}

    ## TASK
    Read your task brief: {CWD}/.project-meta/tasks/context/task-{N}.md
    Task: "{title}"
    Files: {files list}
    Screenshots: {paths or "none" — READ ALL}
    Figma JSON: {paths or "none" — READ ENTIRE FILE}
```

**Validator-{N}:**
```
Task tool:
  subagent_type: "general-purpose"
  team_name: "tasks-execution"
  name: "validator-{N}"
  mode: "bypassPermissions"
  prompt: |
    You are VALIDATOR agent "validator-{N}" in team "tasks-execution".

    ## FIRST ACTION (MANDATORY — before anything else)
    Invoke skills: 1. "agent:common" 2. "agent:validator"
    Then follow loaded instructions.

    ## YOUR CHAIN
    - Receive task + file paths from: orchestrator (team lead)
    - Send corrections to: implementer-{N} (max 3 rounds)
    - Send final report to: orchestrator (team lead)

    ## WAIT
    Wait for orchestrator to send you the task and file paths.
    Do NOT start until you receive a message.
```

### 5. Send Task to Implementers

Send start signals to each implementer-{N}:

```
SendMessage:
  type: "message"
  recipient: "implementer-{N}"
  content: |
    Start Task {N}: {title}.
    Read your task brief at: {CWD}/.project-meta/tasks/context/task-{N}.md
    Screenshots: {paths}
    Figma JSON: {paths}
    Research the project independently, implement, self-review.
    When done, send me the list of created/modified files.
  summary: "Start Task {N}"
```

Update status.md: batch tasks → `running`

### 6. Wait for Implementers

Each implementer will:
- Research the project independently
- Read ALL task materials (context file, screenshots, Figma JSON)
- Implement the task
- Self-review
- Send file paths to YOU

**You do NOT intervene. You WAIT.**

### 7. Forward to Validators (Blind Validation)

When implementer-{N} reports file paths:

```
SendMessage:
  type: "message"
  recipient: "validator-{N}"
  content: |
    Validate Task {N}: {title}.
    Read the task brief at: {CWD}/.project-meta/tasks/context/task-{N}.md
    Screenshots: {paths}
    Figma JSON: {paths}

    Files to validate:
    {file paths from implementer}

    Research the project independently, read ALL task materials,
    then read the code and validate.
  summary: "Validate Task {N}"
```

**Do NOT include implementer's self-assessment. Only file paths.**

### 8. Wait for Validators

Validators work autonomously:
- Research project independently
- Read ALL task materials
- Read implemented code
- Compare and validate
- If issues → send corrections to implementer-{N} directly (up to 3 rounds)
- If all OK → send final report to YOU

### 9. Process Validator Reports

**Success report:**
1. Update status.md: task → `done`
2. Update progress percentage and timestamp

**Escalation report:**
1. Report remaining issues to user
2. Wait for user decision:
   - User provides guidance → send to implementer-{N}
   - User accepts as-is → mark `done`
   - User takes over → mark `done` with note

### 10. Continue with Next Batch

After current batch completes:
1. Update status.md
2. Find newly available tasks (deps now met)
3. Group for parallelism
4. Spawn new chains (step 4)
5. Repeat until all done or blocked

### 11. Final Verification (YOU do this)

After ALL tasks complete:
1. Run `format-and-check` (or format, lint, typecheck)
2. Fix any issues found

### 12. Shutdown

```
Send shutdown_request to ALL active agents
TeamDelete
```

### 13. Generate Reports

If any tasks are `blocked` → create `.project-meta/tasks/blocked-report.md`
Update status.md with final state.
Report summary to user.

---

## User Feedback Flow

If user identifies issues after reviewing completed work:

```
1. Send fix instructions to implementer-{N} via SendMessage
2. Implementer fixes → sends updated files to validator-{N}
3. Validator checks → sends report to you
4. Update status.md if needed
5. Report to user
```

**DO NOT fix code yourself. Route to the chain.**

---

## status.md Update Format

When updating:
1. Find row by task ID
2. Replace status value
3. Add blocker text if needed
4. Update "Updated:" timestamp
5. Recalculate progress: `done_count/total (percentage%)`

**Status values:** `pending` → `running` → `done` / `blocked`

---

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
**Reason:** Why blocked
**Files:** list
**Next steps:** What needs to happen to unblock

## Tasks Waiting on Blocked

| # | Task | Waiting for |
|---|------|-------------|
| 5 | Task title | Task 3 (blocked) |
```

---

## Important Rules

1. **NEVER read context/ files** — agents read their own
2. **NEVER read screenshots** — agents handle this independently
3. **NEVER validate code yourself** — validator agents handle this
4. **NEVER modify tasks.md** — read-only after planning
5. **2 agents per task** — implementer + validator, both research independently
6. **Blind validation** — validator gets original task, NOT implementer's report
7. **Spawn ALL batch agents in ONE message** — parallel Task calls
8. **Update status.md after EACH completed task** — not in large batches
9. **When in doubt → sequential** — better slow than broken
10. **Continue past blocked tasks** — do what you can
11. **Run format-and-check ONCE at the end** — not per task
12. **Generate blocked-report.md ONLY at the end**
13. **Route ALL user feedback to implementer** — never fix yourself

---

## Example Execution Flow

```
Reading task index... (tasks.md + status.md in parallel)
Found 4 tasks: 0 done, 4 pending

Grouping:
├─ Batch 1: Tasks #1, #2 (no deps, no shared files) — PARALLEL
├─ Batch 2: Task #3 (visual, deps: 1)
└─ Batch 3: Task #4 (deps: 2, 3)

Creating team "tasks-execution"...

═══ Batch 1: Tasks #1, #2 ═══

Spawning 4 agents in ONE message:
├─ implementer-1, validator-1
└─ implementer-2, validator-2

Send tasks to implementer-1, implementer-2...
status.md: #1, #2 → running

[implementers work autonomously — research, implement, self-review]

implementer-1 reports files → forward task + files to validator-1
implementer-2 reports files → forward task + files to validator-2

[validators work autonomously — research, read code, compare]

validator-1: ✅ done (0 issues)
validator-2: ✅ done (2 issues fixed in 1 correction round)
status.md: #1, #2 → done (2/4, 50%)

═══ Batch 2: Task #3 (visual) ═══

Spawning 2 agents: implementer-3, validator-3
Send task to implementer-3 (with screenshot + Figma paths)
status.md: #3 → running

implementer-3 reports files → forward task + files + screenshot paths to validator-3

validator-3: ✅ done (12 elements checked, 0 issues, 1 correction round)
status.md: #3 → done (3/4, 75%)

═══ Batch 3: Task #4 ═══
...
status.md: #4 → done (4/4, 100%)

═══ Final ═══
format-and-check → ✅
Shutdown all agents → ✓
TeamDelete → ✓

Summary: 4/4 completed, 0 blocked
```

---

## Quick Reference

| Field | Format | Example |
|-------|--------|---------|
| Header | `## Task N: Title` | `## Task 3: List page` |
| Files | `- Files: path1, path2` | `- Files: src/page.tsx` |
| Deps | `- Deps: N, M` or `none` | `- Deps: 1, 2` |
| Type | `- Type: code/visual` | `- Type: visual` |
| Screenshots | `- Screenshots: path` | `- Screenshots: screenshots/list.png` |
| Figma | `- Figma: path` | `- Figma: screenshots/list.json` |
| Context | `- Context: path` | `- Context: context/task-3.md` |

| Type | Agents | Flow |
|------|--------|------|
| code | 2 | implementer ↔ validator → you |
| visual | 2 | implementer ↔ validator → you (both read screenshots independently) |
