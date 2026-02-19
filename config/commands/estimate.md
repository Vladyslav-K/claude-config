---
name: estimate
description: Estimate frontend tasks from .project-meta/estimation/. Spawns estimator agents that read task files, screenshots, and codebase independently. Assembler merges results into estimation.md. Orchestrator reads ZERO task content.
---

# Task Estimation

## Additional context from user before start task
$ARGUMENTS

## Purpose
Estimate frontend tasks by delegating ALL reading (task files, screenshots, codebase research) to estimator agents. Orchestrator acts as pure manager — scans file names, spawns agents, receives summary.

**KEY PRINCIPLE:** You are a PURE MANAGER. You scan file NAMES only. Agents read file contents, screenshots, and research the codebase. You NEVER read task files or screenshots.

## IMPORTANT: Scope Limitation
**ONLY FRONTEND tasks are estimated.** Backend, DevOps, mobile native, database tasks are skipped by estimator agents automatically.

## Input
`.project-meta/estimation/` directory containing:
- **Root files:** Task lists (.md, .xlsx, .docx)
- **screenshots/ folder:** Images related to tasks

## Output
`.project-meta/estimation/estimation.md` — unified estimation report

---

## Execution Steps

### 1. Scan Input Folder (YOU do this — Glob ONLY, DON'T read files!)

```
1. Glob: .project-meta/estimation/*.{md,xlsx,docx} (root only)
2. Glob: .project-meta/estimation/screenshots/**/*
3. Group screenshots and design documents by task name:
   - Task "user-profile" matches:
     - screenshots/user-profile/ folder (all files inside)
     - screenshots/user-profile.png
     - screenshots/user-profile-*.png
     - screenshots/user-profile*__design.md
   - Folder contents override file name matching
   - `*__design.md` files are structured design specs from Figma for precise screenshot analysis
4. Build map: { taskFile → [matched screenshot paths] }
5. Count files, note file types
```

**If no task files found:** Inform user, ask to add files, stop.

### 2. Determine Distribution (YOU do this)

| Task files | Estimators | Assembler | Notes |
|------------|-----------|-----------|-------|
| 1 file | 1 | NO | Estimator writes estimation.md directly |
| 2-3 files | 1 per file | YES | Each writes partial, assembler merges |
| 4+ files | Group into 2-3 agents | YES | Balance load evenly |

**Single large xlsx:** 1 estimator (reads all sheets itself).
**Solo estimator:** writes `.project-meta/estimation/estimation.md` directly.
**Multiple estimators:** each writes `.project-meta/estimation/partial/estimator-N.md`, assembler merges.

### 3. Create Team (YOU do this)

```
TeamCreate:
  team_name: "estimation"
  description: "Estimating frontend tasks"
```

### 4. Spawn ALL Agents in ONE Message

**Model selection:** Use model from `.claude/rules/workflow/agent-models.md` per agent role. `inherit` → omit `model` param. Other values → pass as `model` param.

Spawn all estimators (and assembler if needed) in a SINGLE message with parallel Task calls.

**Estimator-{N}:**
```
Task tool:
  subagent_type: "general-purpose"
  team_name: "estimation"
  name: "estimator-{N}"
  mode: "bypassPermissions"
  prompt: |
    You are ESTIMATOR agent "estimator-{N}" in team "estimation".

    ## FIRST ACTION (MANDATORY — before anything else)
    Invoke skills: 1. "agent:common" 2. "agent:estimator"
    Then follow loaded instructions.

    ## YOUR CHAIN
    - Receive from: orchestrator (start signal with file assignments)
    - Send to: assembler (completion signal) / orchestrator (if solo)

    ## OUTPUT FILE
    Write results to: {output path — see distribution rules}
```

**Assembler (only if 2+ estimators):**
```
Task tool:
  subagent_type: "general-purpose"
  team_name: "estimation"
  name: "assembler"
  mode: "bypassPermissions"
  prompt: |
    You are ASSEMBLER agent "assembler" in team "estimation".

    ## YOUR ROLE
    Wait for ALL estimator agents to complete, then merge their
    partial results into a unified estimation report.

    ## YOUR CHAIN
    - Receive from: estimator-1, estimator-2, ... (completion signals)
    - Expected inputs: {N} estimators
    - Send to: orchestrator (final summary)

    ## WHEN ALL ESTIMATORS REPORT
    1. Read all partial files from: {CWD}/.project-meta/estimation/partial/
    2. Merge into unified estimation report
    3. Write to: {CWD}/.project-meta/estimation/estimation.md
    4. If original files were .xlsx — write estimates back using openpyxl
    5. Clean up: delete partial/ directory after successful merge

    ## ESTIMATION.MD FORMAT

    ```markdown
    # Task Estimation

    Generated: YYYY-MM-DD HH:MM
    Source files: [list]

    ## Summary

    | # | Task | Type | Opt | Avg | Pess | Notes |
    |---|------|------|-----|-----|------|-------|
    | 1 | [name] | [type] | Xh | Xh | Xh | |

    Frontend tasks: X
    Skipped (non-frontend): Y

    **Totals:**
    - Optimistic: XXh
    - Average: XXh
    - Pessimistic: XXh

    ---

    ## Detailed Estimates

    ### 1. [Task Name]
    **Source:** [file]
    **Description:** [brief]
    **Estimate:** Opt: Xh | Avg: Xh | Pess: Xh
    **Reasoning:**
    - [from estimator]
    **Codebase context:**
    - [from estimator]

    ---

    [...repeat for all tasks...]

    ## Assumptions
    [merged from all estimators]

    ## Risks
    [merged from all estimators]

    ## Clarifications Needed
    [merged from all estimators]
    ```

    ## XLSX WRITE-BACK (if applicable)
    If original files were .xlsx and have estimate columns:
    - Use openpyxl via Bash + Python
    - Find estimate columns (opt/min, avg/ave, pess/max)
    - Write values back

    ## FINAL REPORT TO ORCHESTRATOR
    Send via SendMessage to team lead:
    ```
    ## ✅ ESTIMATION COMPLETE

    ### Summary
    - Total tasks: X
    - Frontend: Y estimated, Z skipped
    - Totals: Opt XXh | Avg XXh | Pess XXh

    ### Files
    - estimation.md written
    - xlsx updated: [yes/no]

    ### Clarifications Needed
    - [list if any]
    ```
```

### 5. Send Start Signals

After spawning ALL agents, send task assignments to each estimator:

```
SendMessage:
  type: "message"
  recipient: "estimator-{N}"
  content: |
    Start estimation.

    ## FILES TO READ
    [Absolute paths to task files for this estimator]

    ## SCREENSHOTS
    [Absolute paths to matched screenshots, grouped by task name]

    ## OUTPUT FILE
    Write results to: {path}

    ## WHEN DONE
    Signal assembler (or orchestrator if solo) with:
    task count + total hours (opt/avg/pess).
  summary: "Start estimation for {file names}"
```

If assembler exists, also notify:
```
SendMessage:
  type: "message"
  recipient: "assembler"
  content: |
    Waiting for {N} estimators: estimator-1, estimator-2, ...
    Partial files will be at: {CWD}/.project-meta/estimation/partial/
    Source files: [list of original task files]
  summary: "Assembler: wait for {N} estimators"
```

### 6. Wait (DO NOTHING)

Estimator agents work autonomously:
1. Invoke skills (agent:common, agent:estimator)
2. Read assigned task files (md/xlsx/docx)
3. Read matched screenshots
4. Research codebase for similar patterns
5. Read project memory
6. Apply estimation methodology
7. Write results to output file
8. Signal assembler (or orchestrator)

Assembler (if exists):
1. Waits for all estimator signals
2. Reads all partial files
3. Merges into estimation.md
4. Handles xlsx write-back
5. Cleans up partial/ directory
6. Sends summary to orchestrator

**You do NOT read task files. You do NOT read screenshots. You WAIT.**

### 7. Process Final Report

When assembler (or solo estimator) sends you the summary:
1. Report to user:
   - Total tasks estimated
   - Total hours (opt/avg/pess)
   - Clarifications needed
   - Reference: full details in estimation.md

### 8. Shutdown

```
Send shutdown_request to ALL agents
TeamDelete
```

---

## Important Rules

1. **NEVER read task file contents** — estimator agents read their own
2. **NEVER read screenshots** — estimator agents handle visual analysis
3. **NEVER do codebase research** — estimators research independently
4. **Use agent model config** (`.claude/rules/workflow/agent-models.md`) per role
5. **Glob ONLY for scanning** — just file names, not contents
6. **Spawn ALL agents in ONE message** — parallel Task calls
7. **For .xlsx use openpyxl** — as per project rules
8. **ALWAYS create estimation.md** — primary output
9. **Shutdown team after completion** — shutdown requests + TeamDelete
10. **Solo estimator writes estimation.md directly** — no assembler overhead

---

## Example Execution Flow

```
Scanning input folder...
├─ Task files: sourcing-requests.md, dashboard-redesign.xlsx
├─ Screenshots: 8 images in 3 folders
└─ Map: sourcing-requests.md → 3 screenshots, dashboard-redesign.xlsx → 5 screenshots

Distribution: 2 files → 2 estimators + 1 assembler

Creating team "estimation"...

Spawning 3 agents in ONE message:
├─ estimator-1 → sourcing-requests.md + 3 screenshots
├─ estimator-2 → dashboard-redesign.xlsx + 5 screenshots
└─ assembler → waits for 2 estimators

Sending start signals...
├─ estimator-1: files + screenshots assigned
├─ estimator-2: files + screenshots assigned
└─ assembler: waiting for 2 estimators

[agents work autonomously]

estimator-1: done (6 tasks, Opt 24h | Avg 48h | Pess 80h)
estimator-2: done (12 tasks, Opt 40h | Avg 72h | Pess 120h)

assembler: merging partials...
assembler: ✅ ESTIMATION COMPLETE
├─ 18 frontend tasks estimated
├─ Totals: Opt 64h | Avg 120h | Pess 200h
└─ 2 tasks need clarification

Shutting down team...
├─ shutdown_request → all agents
└─ TeamDelete ✓

Summary: 18 tasks estimated, details in estimation.md
```
