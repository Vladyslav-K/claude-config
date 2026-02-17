---
name: tasks-run
description: Execute tasks from .project-meta/tasks/tasks.md using a team of agents. Parallelizes independent tasks (no shared files, no deps) for speed via separate agents. Validates each task after completion. Creates blocked-report.md at the end if any tasks are blocked. Use when user says /tasks-run or wants to execute initialized tasks.
---

# Task Execution (Team Workflow)

## Additional context from user before start task
$ARGUMENTS

## Purpose
Execute tasks from the initialized task system using a team of agents. Independent tasks run in parallel via separate agents (inherits current chat model). After each task completion, the team lead (YOU) validates the result against requirements and screenshots before marking as done.

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

### 4. Find Available Tasks, Classify, and Group (YOU do this)

```
1. Find all tasks with status "pending"
2. Filter out tasks with unmet dependencies (deps not "done")
3. CLASSIFY each available task:
   - HAS "Screenshots:" or "Figma:" field → VISUAL TASK (requires 3-agent flow)
   - NO screenshots/figma → CODE TASK (standard implementer flow)
4. From available tasks, identify PARALLEL GROUPS
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

---

## 🚨 CRITICAL: Visual Task Flow (3-Agent Mandatory)

**This section OVERRIDES any simplified validation approach below.**

**If a task has `Screenshots:` or `Figma:` metadata → it is a VISUAL TASK.**

**For EVERY visual task, you MUST spawn ALL 3 agents in sequence:**

1. **Analyzer agent** → reads screenshot + Figma JSON → produces element-by-element specs
2. **Implementer agent** → builds using analyzer's output + codebase patterns
3. **Validator agent** → fresh-eyes comparison of result vs design → reports every discrepancy

**You CANNOT skip any of these agents. The orchestrator (YOU) is FORBIDDEN from:**
- ❌ Reading screenshots and writing analysis yourself — this is the ANALYZER's job
- ❌ Comparing code to design and saying "looks correct" — this is the VALIDATOR's job
- ❌ Claiming validation without a validator agent_id — this is FAKE validation
- ❌ Rationalizing "the analysis is already in tasks.md so analyzer is unnecessary" — NO, spawn it anyway

**Even if tasks.md already contains design specs, the analyzer agent MUST still be spawned.**
Why: The analyzer reads the ACTUAL screenshot with fresh eyes and catches details that
the planning phase may have missed. Skipping it has caused critical errors 3 times.

### GATE System (HARD STOPS)

```
═══════════════════════════════════════════════════════
GATE 1: BEFORE spawning implementer for a visual task
═══════════════════════════════════════════════════════
REQUIRED PROOF: Analyzer agent was spawned AND returned analysis.
- Analyzer agent name: [must exist]
- Analyzer output received: [YES — paste first 3 lines as proof]

WITHOUT THIS PROOF → you CANNOT spawn the implementer.
If you find yourself writing "I'll analyze the screenshot..." → STOP.
That is the analyzer agent's job. Spawn it.
═══════════════════════════════════════════════════════

═══════════════════════════════════════════════════════
GATE 2: BEFORE marking a visual task as done
═══════════════════════════════════════════════════════
REQUIRED PROOF: Validator agent was spawned AND returned a report.
- Validator agent name: [must exist]
- Validator issues found: [number from validator's report]
- All issues fixed: [YES/NO — if NO, list remaining]

WITHOUT THIS PROOF → task is NOT done.
If you find yourself writing "I compared the code to the screenshot..." → STOP.
That is the validator agent's job. Spawn it.
═══════════════════════════════════════════════════════
```

### Visual Task Step-by-Step

For each visual task in a parallel group:

**Step A: Spawn Analyzer**
```
Task tool:
  subagent_type: "general-purpose"
  team_name: "tasks-execution"
  name: "analyzer-{N}"
  mode: "bypassPermissions"
  prompt: |
    You are a design analyzer agent. DO NOT write any implementation code.

    ## YOUR TASK
    Analyze the screenshot(s) and/or Figma JSON and produce a DETAILED structural analysis.

    ## SCREENSHOTS TO ANALYZE
    [Absolute paths to screenshot files — READ them]

    ## FIGMA JSON (if available)
    [Path to Figma JSON file — READ it]

    ## WHAT TO PRODUCE

    ### 1. Component Tree (parent-child hierarchy)
    For EVERY visible element, describe what it is and where it sits.
    Use tree notation to show NESTING explicitly.
    PAY SPECIAL ATTENTION to what is INSIDE what.

    ### 2. Visual Properties for EACH element
    - Colors: background, text, border (exact hex from Figma JSON, or best visual estimate)
    - Font: size, weight, style
    - Spacing: padding, margin, gap
    - Borders: color, width, radius
    - Shadows if any
    - Dimensions: width, height if determinable

    ### 3. Interactive Elements Detection
    For EVERY element, determine if it should be interactive:
    - Links (mailto:, href, etc.)
    - Buttons (what should they DO?)
    - Dropdowns, filters, search inputs
    - List what action each interactive element should perform.

    ### 4. Element Count
    Count how many times each type of element appears.
    List each button with exact label and location.
    Are there elements that DON'T belong on this page/role?

    ### 5. Page Integration Points
    - What should the page TITLE be?
    - Should this page appear in sidebar navigation?
    - What breadcrumbs or back-navigation should exist?

    Send your complete analysis to the team lead when done.
```

**GATE 1 CHECK** — Verify analyzer output received before proceeding.

**Step B: Spawn Implementer (with analyzer output)**
```
Task tool:
  subagent_type: "general-purpose"
  team_name: "tasks-execution"
  name: "impl-{N}"
  mode: "bypassPermissions"
  prompt: |
    You are implementer agent "impl-{N}".

    ## YOUR TASK
    {FULL CONTEXT from tasks.md}

    ## DESIGN SPECS
    {Design Specs section from tasks.md if present}

    ## SCREENSHOTS
    {Screenshot paths — READ these files}

    ## DESIGN ANALYSIS (from analyzer agent)
    {Paste the FULL analysis from the analyzer agent here — THIS IS CRITICAL}

    ## PROJECT CONTEXT
    Working directory: {CWD}
    Memory: {CWD}/.project-meta/memory/ (read these first!)

    ## CODEBASE PATTERNS (from research)
    {Paste relevant code patterns found by Explore agent}

    ## KNOWN MISTAKES (read this file if it exists)
    - .claude/rules/common-mistakes.md
    Read it and avoid ALL listed mistakes.

    ## RULES
    - Read project memory files FIRST
    - Read common mistakes file if it exists
    - Follow existing code patterns EXACTLY
    - Don't create tests unless specified
    - Don't add unnecessary comments
    - Use English for all code and comments
    - If screenshots exist, READ them to understand the visual design

    ## WHEN DONE
    1. Re-read your created/modified files to verify correctness
    2. Run format-and-check (or format, lint, typecheck), fix any issues
    3. Report: list all files created/modified and what was done
```

**Step C: Spawn Validator (after implementer completes)**
```
Task tool:
  subagent_type: "general-purpose"
  team_name: "tasks-execution"
  name: "validator-{N}"
  mode: "bypassPermissions"
  prompt: |
    You are a validation agent. Your ONLY job is to find EVERY discrepancy
    between the design and the implementation. Be extremely thorough and critical.

    ## SCREENSHOT(S) TO COMPARE AGAINST
    [Absolute paths to screenshot files — READ them]

    ## DESIGN ANALYSIS (from analyzer agent)
    [Paste the analysis]

    ## IMPLEMENTED CODE TO VALIDATE
    [List of file paths created/modified by the implementer — READ them all]

    ## KNOWN MISTAKES (read this file if it exists)
    - .claude/rules/common-mistakes.md
    Pay special attention — these are REAL mistakes from previous work.

    ## YOUR TASK
    Go through EVERY element visible on the screenshot and verify
    it exists correctly in the code.

    ### For EACH element check:
    1. EXISTS? — Is this element present in the code?
    2. CORRECT PARENT? — Is it nested inside the right container?
    3. CORRECT STYLES? — Color, font, spacing, border match?
    4. CORRECT TEXT? — Does text content match exactly?
    5. NO EXTRAS? — Is there anything in the code NOT on the screenshot?

    ### Critical Checks:
    - Count EVERY button. Code count must match screenshot count.
    - Email text → must be mailto: link (not plain text)
    - Filter dropdowns → must actually open and filter data
    - Interactive elements → must be functional, not just visual
    - Page title → correct in layout header? (not default "Page")
    - Product images → have border if shown in design?

    ## OUTPUT FORMAT

    ### ✅ Correct Elements
    - [Element]: [brief confirmation]

    ### ❌ Issues Found
    For EACH issue:
    - **Element:** [what element]
    - **File:** [file path:line number]
    - **Problem:** [specific description]
    - **Expected:** [what it should be]
    - **Actual:** [what it currently is]
    - **Fix:** [how to fix it]

    ### 📊 Summary
    - Total elements checked: N
    - Correct: N
    - Issues found: N

    Send your complete report to the team lead.
```

**GATE 2 CHECK** — Verify validator report received. Fix all issues.
Then mark task as done.

### Parallelizing Visual Tasks

Multiple visual tasks CAN run in parallel IF they don't share files:

```
Visual Task 3 + Visual Task 4 (no shared files):

1. Spawn analyzer-3 AND analyzer-4 in PARALLEL (single message)
2. Wait for both analyzers
3. GATE 1 check for both
4. Spawn impl-3 AND impl-4 in PARALLEL (with respective analyzer outputs)
5. Wait for both implementers
6. Spawn validator-3 AND validator-4 in PARALLEL
7. Wait for both validators
8. GATE 2 check for both
9. Fix issues, mark done
```

**Analyzers for different tasks CAN run in parallel.**
**Validators for different tasks CAN run in parallel.**
**But analyzer → implementer → validator for the SAME task MUST be sequential.**

---

### 5. Spawn Agents for Code Tasks (non-visual)

**CRITICAL: NEVER specify `model` param. Omit it → agent inherits current chat model.**

For code-only tasks (NO screenshots/figma), spawn implementer directly:

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

    ## PROJECT CONTEXT
    Working directory: {CWD}
    Memory: {CWD}/.project-meta/memory/ (read these first!)

    ## CODEBASE PATTERNS (from research)
    {Paste relevant code patterns found by Explore agent}

    ## KNOWN MISTAKES (read this file if it exists)
    - .claude/rules/common-mistakes.md (known mistakes from past implementations)
    Read it and avoid ALL listed mistakes.

    ## RULES
    - Read project memory files FIRST for project architecture and patterns
    - Read common mistakes files (listed above) if they exist
    - Follow existing code patterns EXACTLY
    - Don't create tests unless specified
    - Don't add unnecessary comments (no task descriptions, no change notes)
    - Use English for all code and comments
    - Follow the project's code style

    ## WHEN DONE
    1. Re-read your created/modified files to verify correctness
    2. Run format-and-check (or format, lint, typecheck), fix any issues
    3. Report: list all files created/modified and what was done
```

**For parallel groups:** Spawn ALL agents for the group in a SINGLE message (multiple Task tool calls in parallel).

### 6. Validate Completed Tasks

**After each agent completes, validation depends on task type:**

#### Code Tasks (no screenshots) — YOU validate directly:

1. **Read output files** the agent created/modified
2. **Check code quality:**
   - Follows project patterns (from research)
   - Proper TypeScript types
   - No console.log or commented code
   - Imports from correct locations
   - No extra features beyond requirements
3. **Decision:**
   - ✅ Good → Update status.md: task → `done`
   - ⚠️ Minor issues → Fix yourself with Edit tool, then mark `done`
   - ❌ Major issues → Send correction to agent OR fix yourself

#### Visual Tasks (has screenshots) — VALIDATOR agent validates:

**YOU DO NOT validate visual tasks yourself. The validator agent does it.**

1. After implementer completes → spawn validator agent (Step C above)
2. Wait for validator report
3. **GATE 2 CHECK** — verify you have validator agent name + issues count
4. Review validator's report:
   - 0 issues → mark done
   - 1-3 minor issues → fix yourself, mark done
   - 4+ issues → send corrections to implementer, optionally re-validate
5. Update status.md

**YOU reading the screenshot and saying "looks good" is NOT validation.**
**Only a validator agent report counts.**

### 7. Update Status and Continue

After validating current group:
1. Update status.md: completed tasks → `done`, blocked tasks → `blocked`
2. Update progress percentage and timestamp
3. Find newly available tasks (dependencies now met)
4. Classify new tasks (visual vs code)
5. Analyze parallel groups again
6. Spawn new agents for next batch
7. Repeat until all tasks done or blocked

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

After each CODE task:
```
- [ ] All requirements from Context section are implemented
- [ ] Code compiles without errors (TypeScript)
- [ ] format-and-check passes
- [ ] No console.log, debugger, or commented-out code
- [ ] Types are properly defined
- [ ] Follows patterns specified in Context
- [ ] No extra features added beyond what Context specifies
```

After each VISUAL task:
```
- [ ] GATE 1 passed: analyzer agent name = _________, output received
- [ ] Implementer received analyzer output in prompt
- [ ] GATE 2 passed: validator agent name = _________, issues found = ___
- [ ] All validator issues fixed
- [ ] format-and-check passes
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
4. **VISUAL TASKS REQUIRE 3 AGENTS** — analyzer → implementer → validator (NO EXCEPTIONS)
5. **ORCHESTRATOR NEVER reads screenshots to analyze or validate** — agents do this
6. **GATE system is mandatory** — must have agent names and output before proceeding
7. **Update status.md after EACH validated task** — not in large batches
8. **Parallelize independent tasks** — spawn agents in parallel when safe
9. **When in doubt → sequential** — better slow than broken
10. **Fix minor issues yourself** — faster than round-tripping to agent
11. **Continue past blocked tasks** — do what you can
12. **Run format-and-check after ALL tasks** — final cleanup
13. **Generate blocked-report.md ONLY at the end** — not during execution
14. **Shutdown team and clean up** — after all work is complete

## Example Execution Flow

```
Reading task state... (read tasks.md + status.md in parallel)
Parsing tasks.md...
Found 8 tasks: 0 done, 0 running, 8 pending

Classifying tasks:
├─ Task #1: CODE (no screenshots) — types
├─ Task #2: CODE — navigation
├─ Task #3: VISUAL (has screenshots + figma) — list page
├─ Task #4: VISUAL (has screenshots + figma) — detail page
├─ Tasks #5-8: CODE — services, hooks, etc.

Researching codebase patterns (Explore agent)...
Found: component patterns, import paths, code style

Creating team "tasks-execution"...

═══ Batch 1: Tasks #1, #2 (CODE, no deps, no shared files) ═══

Spawning 2 implementers in ONE message:
├─ impl-1 → Task #1
└─ impl-2 → Task #2

impl-1 completed → Validating (code task: read output files)...
└─ ✅ Validated → status.md: #1 → done

impl-2 completed → Validating (code task: read output files)...
└─ ✅ Validated → status.md: #2 → done

═══ Batch 2: Tasks #3, #4 (VISUAL, deps met, no shared files) ═══

Step A: Spawning 2 analyzers in PARALLEL:
├─ analyzer-3 → reads screenshot list.png + list.json
└─ analyzer-4 → reads screenshot details.png + details.json

analyzer-3 done → component tree + colors + elements
analyzer-4 done → component tree + colors + elements

GATE 1 CHECK:
├─ analyzer-3: ✅ output received
└─ analyzer-4: ✅ output received

Step B: Spawning 2 implementers in PARALLEL (with analyzer outputs):
├─ impl-3 → Task #3 + analyzer-3 analysis
└─ impl-4 → Task #4 + analyzer-4 analysis

impl-3 completed.
impl-4 completed.

Step C: Spawning 2 validators in PARALLEL:
├─ validator-3 → reads screenshot + impl-3 output files
└─ validator-4 → reads screenshot + impl-4 output files

validator-3 report: 15 elements checked, 2 issues found
validator-4 report: 12 elements checked, 1 issue found

GATE 2 CHECK:
├─ validator-3: ✅ report received, 2 issues
└─ validator-4: ✅ report received, 1 issue

Fixing issues:
├─ Task #3: 2 minor (missing border, wrong font-weight) → fix myself
└─ Task #4: 1 minor (button color) → fix myself

status.md: #3, #4 → done

═══ Batch 3: remaining tasks ═══
[continues...]

All tasks complete!

Final verification:
├─ Running format-and-check...
└─ ✅ All clear

Shutting down team...
├─ shutdown_request → all agents
└─ TeamDelete ✓

Summary:
- Completed: 8/8
- Blocked: 0/8
- Visual tasks validated by: validator-3, validator-4
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

## Quick Reference: Task Classification

| Has Screenshots? | Has Figma? | Type | Flow |
|---|---|---|---|
| No | No | CODE | implementer → orchestrator validates |
| Yes | No | VISUAL | analyzer → implementer → validator |
| No | Yes | VISUAL | analyzer → implementer → validator |
| Yes | Yes | VISUAL | analyzer → implementer → validator |
