---
name: tasks-run
description: Execute tasks from .project-meta/tasks/tasks.md using agent chains. Each task runs through researcher → [analyzer] → implementer ↔ validator. Independent tasks parallelized. Creates blocked-report.md if any blocked.
---

# Task Execution (Chain Workflow)

## Additional context from user before start task
$ARGUMENTS

## Purpose
Execute tasks from the lightweight task index using autonomous agent chains. Each task gets its own chain that reads its own context file, researches the codebase, implements, and validates — all without orchestrator involvement.

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

### 2. Find Available Tasks, Classify, and Group (YOU do this)

```
1. Find all tasks with status "pending"
2. Filter out tasks with unmet deps (deps not "done")
3. From available tasks, identify PARALLEL GROUPS:
   - Check: do any share FILES?
   - Check: do any depend on each other?
   - No conflicts → parallel group
   - Has conflicts → sequential
```

#### Parallel Safety Rules

| Check | Parallel? |
|-------|-----------|
| No shared files AND no deps between them | ✅ Parallel |
| Any shared file | ❌ Sequential |
| Task B depends on Task A | ❌ Sequential |

**When in doubt → sequential.**

### 3. Create Team (YOU do this)

```
TeamCreate:
  team_name: "tasks-execution"
  description: "Executing tasks from tasks.md"
```

### 4. Spawn Agent Chains for Current Batch

**Spawn ALL agents for ALL tasks in the batch in a SINGLE message (parallel Task calls).**

**CRITICAL: NEVER specify `model` param. Omit it → agents inherit current chat model.**

#### Chain by Task Type

| Type | Agents | Chain |
|------|--------|-------|
| **code** | 3: researcher, implementer, validator | researcher → implementer ↔ validator |
| **visual** | 4: researcher, analyzer, implementer, validator | researcher + analyzer → implementer ↔ validator |

#### Agent Prompt Templates

All agents load their skills as FIRST ACTION. Prompts are MINIMAL — agents read their own files.

**Researcher-{N}:**
```
Task tool:
  subagent_type: "general-purpose"
  team_name: "tasks-execution"
  name: "researcher-{N}"
  mode: "bypassPermissions"
  prompt: |
    You are RESEARCHER agent "researcher-{N}" in team "tasks-execution".

    ## FIRST ACTION (MANDATORY — before anything else)
    Invoke skills: 1. "agent:common" 2. "agent:researcher"
    Then follow loaded instructions.

    ## YOUR CHAIN
    - Receive from: orchestrator (start signal)
    - Send to: implementer-{N}

    ## TASK
    Read your task brief: {CWD}/.project-meta/tasks/context/task-{N}.md
    Task: "{title}"
    Files: {files list}
```

**Analyzer-{N} (visual tasks only):**
```
Task tool:
  subagent_type: "general-purpose"
  team_name: "tasks-execution"
  name: "analyzer-{N}"
  mode: "bypassPermissions"
  prompt: |
    You are ANALYZER agent "analyzer-{N}" in team "tasks-execution".

    ## FIRST ACTION (MANDATORY — before anything else)
    Invoke skills: 1. "agent:common" 2. "agent:analyzer"
    Then follow loaded instructions.

    ## YOUR CHAIN
    - Receive from: orchestrator (start signal)
    - Send to: implementer-{N}

    ## TASK
    Read your task brief: {CWD}/.project-meta/tasks/context/task-{N}.md
    Screenshots: {absolute paths — READ these}
    Figma JSON: {absolute paths or "none" — READ these}
```

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
    - Receive from: researcher-{N} {+ analyzer-{N} if visual}
    - Send to: validator-{N}
    - Expected inputs: {1 for code, 2 for visual}

    ## TASK
    Read your task brief: {CWD}/.project-meta/tasks/context/task-{N}.md
    Task: "{title}"
    Screenshots: {paths or "none"}
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
    - Receive from: implementer-{N}
    - Send corrections to: implementer-{N} (max 3 rounds)
    - Send final report to: orchestrator (team lead)

    ## TASK
    Read your task brief: {CWD}/.project-meta/tasks/context/task-{N}.md
    Screenshots: {paths or "none"}
```

### 5. Send Task Triggers

After spawning ALL agents for the batch, send start signals:

**Code tasks:** Send trigger to researcher-{N}
**Visual tasks:** Send trigger to researcher-{N} AND analyzer-{N} **in parallel**

```
SendMessage:
  type: "message"
  recipient: "researcher-{N}"
  content: |
    Start research for Task {N}: {title}.
    Read your task brief at: {CWD}/.project-meta/tasks/context/task-{N}.md
    Send findings to implementer-{N} when done.
  summary: "Start Task {N} research"
```

For visual tasks, also:
```
SendMessage:
  type: "message"
  recipient: "analyzer-{N}"
  content: |
    Start analysis for Task {N}: {title}.
    Read your task brief at: {CWD}/.project-meta/tasks/context/task-{N}.md
    Screenshots: {paths}
    Figma: {paths}
    Send analysis to implementer-{N} when done.
  summary: "Start Task {N} analysis"
```

Update status.md: batch tasks → `running`

### 6. Wait (DO NOTHING)

Chains run autonomously:
1. Researcher researches → sends findings + task to Implementer
2. Analyzer (visual) analyzes → sends design specs + task to Implementer
3. Implementer waits for all inputs → implements → sends report to Validator
4. Validator checks:
   - Issues? → corrections to Implementer (max 3 rounds)
   - All correct? → ✅ final report to YOU
   - 3 rounds fail? → ⚠️ escalation to YOU

**You do NOT intervene. You do NOT check progress. You WAIT.**

### 7. Process Validator Reports

**Success report:**
1. Update status.md: task → `done`
2. Update progress percentage and timestamp

**Escalation report:**
1. Report remaining issues to user
2. Wait for user decision:
   - User provides guidance → send to implementer-{N}
   - User accepts as-is → mark `done`
   - User takes over → mark `done` with note

### 8. Continue with Next Batch

After current batch completes:
1. Update status.md
2. Find newly available tasks (deps now met)
3. Group for parallelism
4. Spawn new chains (step 4)
5. Repeat until all done or blocked

### 9. Final Verification (YOU do this)

After ALL tasks complete:
1. Run `format-and-check` (or format, lint, typecheck)
2. Fix any issues found

### 10. Shutdown

```
Send shutdown_request to ALL active agents
TeamDelete
```

### 11. Generate Reports

If any tasks are `blocked` → create `.project-meta/tasks/blocked-report.md`
Update status.md with final state.
Report summary to user.

---

## GATE System

Gates are enforced BY agents (via their skills), NOT by you:

| Gate | Enforced by | Rule |
|------|-------------|------|
| **GATE 1** | Implementer | Must receive ALL expected inputs before coding |
| **GATE 2** | Validator | Must find 0 issues before reporting success |
| **GATE 3** | Validator | Max 3 correction rounds, then escalate |

**Your only gate check:** when you receive a report, verify it's a proper success/escalation report from a validator agent. If the report format is wrong or doesn't come from a validator — investigate.

---

## User Feedback Flow

If user identifies issues after reviewing completed work:

```
1. Send fix instructions to implementer-{N} via SendMessage
   (include what user reported + screenshot paths if new ones provided)
2. Implementer fixes → sends report to validator-{N}
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
2. **NEVER read screenshots** — analyzer/validator agents handle this
3. **NEVER do codebase research** — researcher agents handle this
4. **NEVER validate code yourself** — validator agents handle this
5. **NEVER modify tasks.md** — read-only after planning
6. **NEVER specify model param** — agents inherit current chat model
7. **ALL tasks go through full chain** — researcher → [analyzer] → implementer ↔ validator
8. **Spawn ALL batch agents in ONE message** — parallel Task calls
9. **Update status.md after EACH completed task** — not in large batches
10. **When in doubt → sequential** — better slow than broken
11. **Continue past blocked tasks** — do what you can
12. **Run format-and-check ONCE at the end** — not per task
13. **Generate blocked-report.md ONLY at the end**
14. **Route ALL user feedback to implementer** — never fix yourself

---

## Example Execution Flow

```
Reading task index... (tasks.md + status.md in parallel)
Found 6 tasks: 0 done, 6 pending

Grouping:
├─ Batch 1: Tasks #1, #5 (code, no deps, no shared files) — PARALLEL
├─ Batch 2: Task #2 (code, deps: 1)
├─ Batch 3: Tasks #3, #4 (visual, deps: 1,2, no shared files) — PARALLEL
└─ Batch 4: Task #6 (code, deps: 3,4)

Creating team "tasks-execution"...

═══ Batch 1: Tasks #1, #5 (code) ═══

Spawning 6 agents in ONE message:
├─ researcher-1, implementer-1, validator-1
└─ researcher-5, implementer-5, validator-5

Sending triggers to researcher-1, researcher-5...
status.md: #1, #5 → running

[chains run autonomously]

validator-1: ✅ done (0 issues, 0 correction rounds)
validator-5: ✅ done (0 issues, 0 correction rounds)
status.md: #1, #5 → done (2/6, 33%)

═══ Batch 2: Task #2 (code) ═══

Spawning 3 agents: researcher-2, implementer-2, validator-2
Trigger → researcher-2
status.md: #2 → running

validator-2: ✅ done
status.md: #2 → done (3/6, 50%)

═══ Batch 3: Tasks #3, #4 (visual) ═══

Spawning 8 agents in ONE message:
├─ researcher-3, analyzer-3, implementer-3, validator-3
└─ researcher-4, analyzer-4, implementer-4, validator-4

Triggers: researcher-3, analyzer-3, researcher-4, analyzer-4 (parallel)
status.md: #3, #4 → running

[chains run: researcher+analyzer → implementer → validator (with corrections)]

validator-3: ✅ (15 elements, 0 issues, 1 correction round)
validator-4: ✅ (12 elements, 0 issues, 0 rounds)
status.md: #3, #4 → done (5/6, 83%)

═══ Batch 4: Task #6 (code) ═══

Spawning 3 agents: researcher-6, implementer-6, validator-6
...
validator-6: ✅ done
status.md: #6 → done (6/6, 100%)

═══ Final ═══
format-and-check → ✅
Shutdown all agents → ✓
TeamDelete → ✓

Summary: 6/6 completed, 0 blocked
```

---

## Quick Reference: Task Metadata

| Field | Format | Example |
|-------|--------|---------|
| Header | `## Task N: Title` | `## Task 3: List page` |
| Files | `- Files: path1, path2` | `- Files: src/page.tsx` |
| Deps | `- Deps: N, M` or `none` | `- Deps: 1, 2` |
| Type | `- Type: code/visual` | `- Type: visual` |
| Screenshots | `- Screenshots: path` | `- Screenshots: screenshots/list.png` |
| Figma | `- Figma: path` | `- Figma: screenshots/list.json` |
| Context | `- Context: path` | `- Context: context/task-3.md` |

## Quick Reference: Chain per Type

| Type | Agents | Flow |
|------|--------|------|
| code | 3 | researcher → implementer ↔ validator → you |
| visual | 4 | researcher + analyzer → implementer ↔ validator → you |
