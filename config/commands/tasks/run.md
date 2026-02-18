---
name: tasks-run
description: Execute tasks from .project-meta/tasks/tasks.md using phased model. Phase 1: parallel research. Phase 2: sequential user plan review. Phase 3: parallel implementation. Phase 4: user result review.
---

# Task Execution

## Additional context from user before start task
$ARGUMENTS

## Purpose
Execute tasks using a phased model. Each task gets 1 implementer that researches independently, presents a research plan for user approval, then implements after approval.

**KEY PRINCIPLE:** You are a PURE MANAGER. You read ONLY the task index and status. Agents read screenshots, Figma JSON, and codebase. You NEVER read code, screenshots, or Figma. The USER approves plans and validates results.

## Execution Phases

```
PHASE 1: Research (parallel)
  All implementers research project + read designs → send plans to you

PHASE 2: Plan Review (sequential — one at a time)
  You present each plan to user → user approves or requests changes

PHASE 3: Implementation (parallel)
  All approved implementers code simultaneously

PHASE 4: Result Review
  User reviews results → feedback routed to correct implementer
```

## Input
- `.project-meta/tasks/tasks.md` — task INDEX (READ ONLY)
- `.project-meta/tasks/status.md` — current status

## Output
- Updated `.project-meta/tasks/status.md`
- `.project-meta/tasks/blocked-report.md` — if any tasks blocked (generated at end)

---

## Execution Steps

### 1. Read and Parse (YOU do this)

Read tasks.md and status.md **IN PARALLEL** (two Read calls, one message):

```
From tasks.md extract per task:
  - ID, Title
  - What (description)
  - Deps
  - Type (code/visual)
  - Screenshots paths (if visual)
  - Figma paths (if visual)

From status.md:
  - Current status per task

Merge → list of tasks with statuses
Count: total, done, pending, blocked
```

### 2. Find Available Tasks and Group (YOU do this)

```
1. Find all tasks with status "pending"
2. Filter out tasks with unmet deps (deps not "done")
3. Group for parallel execution:
   - No shared dependencies between them → parallel
   - Any dependency → sequential
```

**When in doubt → sequential.**

### 3. Create Team (YOU do this)

```
TeamCreate:
  team_name: "tasks-execution"
  description: "Executing tasks from tasks.md"
```

### 4. Spawn Implementers for Current Batch

**Spawn ALL implementers for the batch in a SINGLE message (parallel Task calls).**

Each task gets exactly 1 agent: `implementer-{N}`.

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
    - FIRST send research plan to: orchestrator → user reviews
    - ONLY implement after orchestrator says "approved"
    - After completion, send file paths to: orchestrator (team lead)
    - Corrections come from: orchestrator (team lead) — these are USER feedback

    ## TASK
    Task {N}: "{title}"
    What: {what description from tasks.md}
    Screenshots: {absolute paths or "none" — READ ALL}
    Figma JSON: {absolute paths or "none" — READ ENTIRE FILE}
```

### 5. Send Research Tasks (PHASE 1)

Send start signals to each implementer-{N}:

```
SendMessage:
  type: "message"
  recipient: "implementer-{N}"
  content: |
    PHASE 1: RESEARCH ONLY — do NOT write code yet.

    Task {N}: {title}
    What: {description}
    Screenshots: {paths}
    Figma JSON: {paths}

    1. Read ALL screenshots and Figma JSON carefully
    2. Research the project — find existing components, patterns, similar pages
    3. Send me your RESEARCH PLAN (format from your skill instructions)

    DO NOT write any code. Wait for my approval.
  summary: "Research Task {N}"
```

Update status.md: batch tasks → `research`

### 6. Collect All Plans (YOU wait)

Each implementer will:
- Read all task materials (screenshots, Figma JSON)
- Research the project independently
- Send a research plan to YOU

**Wait for ALL implementers in the batch to send their plans.**
Store each plan internally.

### 7. Present Plans to User (PHASE 2 — one by one)

Present plans **ONE AT A TIME** to the user:

```
"Task {N} ({title}) — план дослідження імплементера:

{implementer's research plan — copy as-is}

Затверджуєш?"
```

**If user approves:** Mark as approved. Move to next plan.
**If user requests changes:**
  1. Send user's feedback to implementer-{N}
  2. Wait for revised plan
  3. Present revised plan to user again
  4. Repeat until approved

Update status.md as plans are approved.

**Continue until ALL plans in the batch are approved.**

### 8. Start Implementation (PHASE 3)

After ALL plans approved, send GO signal to all implementers:

```
SendMessage:
  type: "message"
  recipient: "implementer-{N}"
  content: "Plan approved. Implement now. Follow your approved plan."
  summary: "GO Task {N}"
```

Update status.md: approved tasks → `running`

### 9. Wait for Implementation

Implementers code independently. Each will:
- Implement following their approved plan
- Self-review against the design
- Run format-and-check
- Send file paths to YOU

**You do NOT intervene. You WAIT.**

### 10. Report Results to User (PHASE 4)

When implementer-{N} reports file paths:
1. Update status.md: task → `done`
2. Update progress percentage and timestamp
3. Report to user: task title + created/modified files

After ALL tasks in batch complete:
- Report full summary
- **Ask user to review the results**

### 11. Handle User Feedback (if any)

If user identifies issues after reviewing:

```
1. Determine which implementer-{N} worked on the relevant task
2. Send fix instructions to implementer-{N} via SendMessage
3. Implementer fixes → sends updated files to you
4. Report back to user
5. Repeat until user satisfied
```

**DO NOT fix code yourself. Route to the implementer.**

### 12. Continue with Next Batch

After current batch completes (including user review):
1. Update status.md
2. Find newly available tasks (deps now met)
3. Group for parallelism
4. Spawn new implementers (step 4)
5. Repeat until all done or blocked

### 13. Final Summary

After ALL batches complete:
1. Run `format-and-check` (or format, lint, typecheck)
2. Fix any issues found (route to relevant implementer)
3. Report full summary to user

### 14. Cleanup

After user confirms ALL is OK:
```
Send shutdown_request to ALL active implementers
TeamDelete
```

### 15. Generate Reports

If any tasks are `blocked` → create `.project-meta/tasks/blocked-report.md`
Update status.md with final state.

---

## status.md Update Format

When updating:
1. Find row by task ID
2. Replace status value
3. Add blocker text if needed
4. Update "Updated:" timestamp
5. Recalculate progress: `done_count/total (percentage%)`

**Status values:** `pending` → `research` → `plan-review` → `running` → `done` / `blocked`

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
**Next steps:** What needs to happen to unblock

## Tasks Waiting on Blocked

| # | Task | Waiting for |
|---|------|-------------|
| 5 | Task title | Task 3 (blocked) |
```

---

## Important Rules

1. **NEVER read screenshots, Figma, or code** — agents handle this
2. **NEVER validate work yourself** — user validates
3. **NEVER modify tasks.md** — read-only after planning
4. **1 implementer per task**
5. **Spawn ALL batch implementers in ONE message** — parallel Task calls
6. **Collect ALL plans before presenting to user**
7. **Present plans ONE BY ONE** — user reviews sequentially
8. **Send GO only after ALL plans in batch are approved**
9. **Update status.md after EACH state change**
10. **Route ALL user feedback to correct implementer**
11. **Keep team alive until user confirms ALL is OK**
12. **When in doubt → sequential**

---

## Example Execution Flow

```
Reading task index... (tasks.md + status.md in parallel)
Found 4 tasks: 0 done, 4 pending

Grouping:
├─ Batch 1: Tasks #1, #2 (no deps) — PARALLEL
├─ Batch 2: Task #3 (deps: 1)
└─ Batch 3: Task #4 (deps: 2, 3)

Creating team "tasks-execution"...

═══ Batch 1: Tasks #1, #2 ═══

--- PHASE 1: Research ---
Spawning 2 implementers in ONE message
├─ implementer-1 (researches Task 1)
└─ implementer-2 (researches Task 2)

status.md: #1, #2 → research

implementer-1 sends research plan
implementer-2 sends research plan

--- PHASE 2: Plan Review ---
"Task 1 план: [plan]. Затверджуєш?"
User: "Ок"

"Task 2 план: [plan]. Затверджуєш?"
User: "Прибери аватар, його немає в дизайні"
→ Send feedback to implementer-2
← Revised plan from implementer-2
"Оновлений план Task 2: [revised]. Ок?"
User: "Ок"

--- PHASE 3: Implementation ---
All plans approved → GO to both implementers
status.md: #1, #2 → running

implementer-1 reports files → status.md: #1 → done
implementer-2 reports files → status.md: #2 → done
Progress: 2/4 (50%)

--- PHASE 4: Review ---
"Tasks 1, 2 complete. Files: ..."
"Перевір результати."

User: "Task 1 фільтри не ті"
→ Send fix instructions to implementer-1
← Implementer-1 fixes → reports back
"Виправлено. Перевір."

User: "Все ок"

═══ Batch 2: Task #3 ═══
...

═══ Final ═══
format-and-check → ✅

Summary: 4/4 completed, 0 blocked
"Команда жива для виправлень."

User: "All good"
→ Shutdown all implementers
→ TeamDelete ✓
```

---

## Quick Reference

| Field | Format | Example |
|-------|--------|---------|
| Header | `## Task N: Title` | `## Task 3: List page` |
| What | `- What: description` | `- What: Create list page with table and filters` |
| Deps | `- Deps: N, M` or `none` | `- Deps: 1, 2` |
| Type | `- Type: code/visual` | `- Type: visual` |
| Screenshots | `- Screenshots: path` | `- Screenshots: screenshots/list.png` |
| Figma | `- Figma: path` | `- Figma: screenshots/list.json` |
