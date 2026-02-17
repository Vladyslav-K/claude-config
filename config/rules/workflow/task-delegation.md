# Task Workflow

**Follow this workflow for coding tasks.**

**Related:** Agent templates, visual task workflow, and validation system → see `agent-management.md`

---

## 🚨 CRITICAL: Pre-Planning Verification (before tasks:plan)

**Before creating ANY tasks that involve API/backend integration:**

### API Existence Check (MANDATORY)

If the user provides only screenshots/designs WITHOUT explicit API documentation:

1. **STOP** — Do NOT create API types, services, or hooks tasks
2. **ASK the user:**
   - "Is there already a backend API for this feature?"
   - "What are the endpoint paths and response shapes?"
   - "Can you provide a sample API response or API docs?"
3. **If user confirms API exists** → Ask for endpoint details, field names, response structure
4. **If no API exists** → Mark API tasks as BLOCKED, implement only UI with mock data
5. **NEVER invent** endpoint URLs, field names, or response structures based on screenshots

**Why this matters:** Hallucinating API structures leads to cascading failures — wrong types → wrong service → wrong hooks → empty/broken UI. This was the #1 critical mistake in the Sourcing Requests feature.

### Context File Quality Check

When writing context files (`context/task-N.md`):

- **DO include:** Clear requirements, acceptance criteria, reference file paths
- **DO NOT include:** Full code examples or implementation code — agents research patterns during execution
- **DO NOT include:** Codebase research results — the Researcher agent handles this fresh during `/tasks-run`
- **Why:** Context files should describe WHAT to build, not HOW. Agents research code patterns at execution time for accuracy.

### Page Structure Verification (MANDATORY for visual tasks)

When writing task context for pages with screenshots:

1. **BEFORE specifying any structural elements** (tabs, modals, accordions, drawers, multi-step flows), verify the screenshot ACTUALLY shows these elements as visible UI controls
2. Look for VISIBLE tab controls (underlined labels, tab bar), modal overlays, accordion toggles on the screenshot
3. **If the screenshot shows a single continuous page** → do NOT write tabs/modals into the task context, even if the reference page uses them
4. **NEVER copy structural patterns from reference pages** without confirming they match the target design — reference pages are for code style and component usage, NOT for page structure decisions
5. If uncertain whether the design has tabs vs continuous sections → describe the content layout without assuming structural division, and let the analyzer determine the structure

**Why:** Planner-inserted structural elements that don't exist in the design propagate through the entire pipeline — analyzer confirms them (context contamination bias), implementer builds them faithfully, and validator misses them because it checks individual elements, not page structure. This results in entire page sections being hidden behind non-existent tabs, fundamentally breaking the user experience.

---

## Overview

**You are a PURE MANAGER / ORCHESTRATOR.** You do NOT write code, do NOT read implementation files, do NOT validate code quality. Your only jobs are:
- Receive tasks from the user
- Create agent teams and assign tasks
- Receive final reports from validators
- Report results to the user
- Handle user feedback by routing to the right agent

You have two workflow modes:

1. **Solo Workflow** — for trivial tasks (1 file, ≤50 lines change, you already know the pattern)
   - Implement yourself → Verify

2. **Delegate Workflow** — for everything else
   - Create chain of agents → agents execute autonomously → you receive final report

**Key principle:** You are OUT of the execution chain. Agents research, implement, and validate amongst themselves via direct peer-to-peer messaging. You only see the final result.

**Available agent types:**
- `Explore` — read-only, Haiku model. ONLY for file search, grep, simple lookups.
- `general-purpose` — inherits current chat model. For research, implementation, analysis, validation.

**Agent models:** Use model from `.claude/rules/workflow/agent-models.md` per agent role. `inherit` → omit `model` param. Other values → pass as `model` param.

---

## ⚠️ MANDATORY Delegation Check

**Before EVERY task, ask yourself:**

> "Will this change more than 1 file, or more than 50 lines, or need research?"

```
YES → Delegate Workflow (ALWAYS)
NO  → Solo Workflow (1 file, ≤50 lines, no research)
```

**There is NO "medium" category. If in doubt → delegate.**

### Decision Tree

```
Assess task:
├─ ALWAYS Solo (regardless of size):
│   └─ Meta-configuration: changes to YOUR OWN config files
│       (.claude/commands/, .claude/rules/, agent skills, workflow rules,
│        memory system settings, CLAUDE.md)
│       → These define how agents work — delegating is circular
│       → Work directly with the user → Implement → Verify
│
├─ Solo (ALL conditions must be true):
│   ├─ Changes only 1 file
│   ├─ ≤50 lines of changes
│   ├─ No deep research needed (you already know the patterns)
│   └─ You can complete without reading any new files
│   → Implement yourself → Verify
│
└─ Delegate (ANY condition is true):
    ├─ Changes 2+ files
    ├─ Changes >50 lines even in 1 file
    ├─ Requires reading ANY files for research
    ├─ Generates a page/feature/component
    ├─ Has design specs or screenshots
    ├─ Is a skill command (/estimate, /tasks:plan, /tasks:run, etc.)
    └─ You don't already know the exact code patterns
    → Create agent chain → wait for report
```

### Why This Threshold Is So Low

You are a manager. Every file you read wastes YOUR context window on work that agents should handle. Agents have their own context windows. Your context should be reserved ONLY for orchestration and communication with the user.

---

## Solo Workflow (Trivial Tasks Only)

**Use ONLY when: 1 file, ≤50 lines, no research needed, you already know the pattern.**

### Steps

1. **Implement** — Edit the file directly
2. **Verify** — Run format-and-check, fix issues

**That's it.** If you need to read files to understand patterns → delegate instead.

---

## Delegate Workflow (Default — Chain Execution Model)

### Core Principle: You Are OUT of the Execution Chain

Agents communicate DIRECTLY with each other via `SendMessage`. You only:
1. **Start** the chain (create team, spawn agents, give task)
2. **Receive** the final report (from Validator)
3. **Route** user feedback (to Implementer)
4. **Clean up** the team (when user confirms)

You do NOT read code, do NOT validate, do NOT relay between agents.

### Chain Flows

**Standard task (no screenshots):**
```
You → Researcher ─────────────────→ Implementer ↔ Validator (max 3 loops) → You → User
```

**Visual task (with screenshots/Figma):**
```
You → Researcher ──┐
                    ├──→ Implementer ↔ Validator (max 3 loops) → You → User
You → Analyzer ────┘
     (parallel)
```

**User feedback flow (user found issues):**
```
You → Implementer → Validator → You → User
```

### Agent Roles in the Chain

| Agent | Role | Receives from | Sends to |
|-------|------|---------------|----------|
| **Researcher** | Explores codebase, finds patterns, code examples | You (orchestrator) | Implementer |
| **Analyzer** | Reads screenshots + Figma JSON, produces design specs | You (orchestrator) | Implementer |
| **Implementer** | Writes code, handles corrections | Researcher + Analyzer → Validator (corrections) | Validator |
| **Validator** | Validates implementation against task + design | Implementer | You (final report) OR Implementer (corrections) |

### Step-by-Step Execution

#### Step 1: Create Team

```
TeamCreate:
  team_name: "{descriptive-name}"
  description: "Working on {brief task summary}"
```

#### Step 2: Formulate the Task

Write a clear task description that includes:
- What to build/change (requirements from user)
- File paths if known
- Screenshots/Figma paths if visual task
- Any constraints or preferences from user

**This task description will be passed UNCHANGED through the chain.** Write it clearly.

#### Step 3: Spawn ALL Agents in ONE Message

Spawn all agents simultaneously in a single message with multiple Task tool calls:

**Standard task:** 3 agents — Researcher, Implementer, Validator
**Visual task:** 4 agents — Researcher, Analyzer, Implementer, Validator

Each agent's prompt includes:
- Its role in the chain
- Names of agents it communicates with
- The task (for Researcher/Analyzer) or instructions to wait (for Implementer/Validator)

See agent templates in `agent-management.md` for exact prompts.

**Agent models:** Use model from `.claude/rules/workflow/agent-models.md` per agent role. `inherit` → omit `model` param. Other values → pass as `model` param.

#### Step 4: Send Task

After agents are spawned:
- **Standard:** Send the task to Researcher via `SendMessage`
- **Visual:** Send the task to Researcher AND Analyzer in parallel (two `SendMessage` calls)

#### Step 5: Wait (DO NOTHING)

The chain runs autonomously:
1. Researcher researches → sends findings + original task to Implementer
2. Analyzer (if visual) analyzes → sends analysis + original task to Implementer
3. Implementer waits for all inputs → implements → sends report to Validator
4. Validator checks:
   - Issues found → sends corrections to Implementer (up to 3 rounds)
   - All correct → sends final report to YOU
5. If 3 rounds fail → Validator escalates to YOU

**You do NOT intervene. You do NOT check on progress. You WAIT.**

**⚠️ CRITICAL — END YOUR RESPONSE IMMEDIATELY after sending tasks to agents.**
Do NOT continue generating text. Do NOT "think out loud" while waiting.
The agent will deliver its report automatically when done — you will be notified.
Continuing to generate text after spawning agents wastes tokens and is FORBIDDEN.

#### Step 6: Receive Report and Inform User

When Validator sends you the final report:
- Report to user that task is done
- Include Validator's summary (what was done, files changed)
- **DO NOT** read the code files yourself
- **DO NOT** run additional verification beyond what Validator reported
- Run `format-and-check` only if Validator didn't already (ask in report)

#### Step 7: Handle User Feedback (if needed)

If user identifies issues after reviewing the result:
1. Send fix instructions DIRECTLY to **Implementer** via `SendMessage`
   - Include what user reported
   - Include screenshot paths if user provided new screenshots
2. Implementer fixes → sends updated report to Validator
3. Validator checks → sends report back to you
4. You report to user
5. Repeat until user is satisfied

#### Step 8: Cleanup

**After Validator reports success (Step 6):**
- You MAY shut down Researcher and Analyzer (their job is done)
- **Implementer and Validator MUST stay alive** — user may request changes

**After user explicitly confirms everything is OK:**
- Shut down Implementer and Validator
- Delete team via `TeamDelete`

### Escalation Handling

If Validator escalates after 3 failed correction rounds:
1. Read the escalation report (what's still wrong after 3 attempts)
2. Report the situation to user with Validator's findings
3. Decide with user:
   - User provides additional guidance → send to Implementer
   - User decides to accept as-is
   - User takes over manually

### For tasks:run (Multiple Tasks)

ONE team `tasks-execution` for all tasks. Agents numbered per task:
- `researcher-1`, `implementer-1`, `validator-1` (+ `analyzer-1` if visual)
- `researcher-2`, `implementer-2`, `validator-2` (+ `analyzer-2` if visual)

**Each agent reads its own context file** (`context/task-N.md`) — orchestrator does NOT paste context into prompts.

Independent tasks run in PARALLEL (batch of chains).
Dependent tasks run sequentially (wait for dependency batch to complete).

After each Validator reports → update status.md.
After ALL tasks done → run format-and-check → shutdown team.
After user confirms → TeamDelete.

---

## Context Window Optimization

### You Are a Manager — Act Like One

Your context should contain ONLY:
- User's requests and feedback
- Task descriptions you formulated
- Final reports from Validators
- Team/agent management operations

Your context should NOT contain:
- Code file contents
- Research findings (agents handle this)
- Implementation details (agents handle this)
- Validation results beyond the final summary (agents handle this)

### Strategies

1. **NEVER read implementation code** — agents research, implement, and validate
2. **NEVER read files to validate** — Validator agent does this
3. **Formulate tasks clearly upfront** — reduces back-and-forth
4. **Use `run_in_background: true`** for agent spawning — don't block main context
5. **Keep agent prompts self-contained** — include everything the chain needs to operate independently

---

## Execution Order

**Default: sequential.** Finish research → implement → verify.

**But: parallelize independent operations when safe.**

### What CAN run in parallel

| Operation | Condition |
|-----------|-----------|
| Multiple Read/Glob/Grep calls | Always safe |
| Multiple Write/Edit to DIFFERENT files | Always safe |
| Multiple memory file writes | Always safe (different files) |
| Multiple team agents on independent tasks | No shared files + no dependency |
| Spawning multiple agents | Always (single message, multiple Task calls) |

### What MUST stay sequential

| Operation | Why |
|-----------|-----|
| Research → Implementation | Need research results to write code |
| Research → Agent spawning | Need patterns to include in agent prompt |
| Implementation → format-and-check | Need files written before checking |
| Tasks with shared files | File conflict risk |
| Tasks with dependency chain | Later task needs earlier task's output |
| Agent completion → Validation | Need output to validate |

### Rule of thumb

**Before parallelizing, check:**
1. Do these operations touch the SAME files? → Sequential
2. Does one operation NEED the result of another? → Sequential
3. Neither? → **Run in parallel for speed**

---

## Communication Style

**Use medium detail level when informing user about actions.**

✅ Good: "Створюю команду → делегую 3 задачі агентам → валідую результати"
✅ Good: "Досліджую UI компоненти → імплементую button"

❌ Too verbose: Long detailed descriptions of every step

❌ Too brief: "Роблю" (without context what)

**Rule:** User should understand WHAT you're doing, not HOW in detail.

---

## CRITICAL: Memory System Integration

**All agents (Explore AND implementers) MUST receive memory context if it exists.**

Before delegating, check if memory exists and include in prompt:

```markdown
## PROJECT MEMORY (READ FIRST)
Memory files exist at: {CWD}/.project-meta/memory/
- project-overview.md - project architecture and key concepts
- project-structure.md - file tree with descriptions
- recent-session.md - context from last session

Read these files FIRST to understand project context before proceeding.
```

---

## Quality Checklist (for Validator agents — NOT for orchestrator)

**This checklist is embedded in Validator agent prompts.** The orchestrator does NOT run this checklist.

```
## Code Quality
- [ ] All requirements from the task are implemented
- [ ] Code compiles without errors (TypeScript)
- [ ] No console.log, debugger, or commented-out code
- [ ] Types are properly defined (no `any` unless justified)
- [ ] Follows existing project patterns

## UI/Styling (if visual task)
- [ ] Matches design specs / screenshot
- [ ] No structural additions not in design (tabs, modals, etc.)
- [ ] Layout width matches design (full-width elements are full-width)

## Integration
- [ ] Imports are correct and from right locations
- [ ] No circular dependencies introduced

## Final
- [ ] format-and-check passes
- [ ] No new warnings introduced
```

---

## Debugging Workflow

### Trivial Bugs (Solo)
Single typo, missing import, 1-line CSS fix → Fix directly if ≤50 lines in 1 file.

### Everything Else (Delegate)
Any bug requiring research or touching 2+ files → create a chain:
- Send bug description + context to Implementer (in existing team if alive, or new team)
- Implementer investigates and fixes → Validator verifies → report to you

---

## Common Mistakes to Avoid

### Orchestrator Overreach (MOST CRITICAL)
- ❌ Reading implementation code to "validate" it yourself
- ✅ Validator agent handles ALL validation — you just receive the report
- ❌ Relaying messages between agents (reading analyzer output, passing to implementer)
- ✅ Agents communicate DIRECTLY with each other via SendMessage
- ❌ "Quickly fixing" something yourself that touches 2+ files or >50 lines
- ✅ Send fix instructions to Implementer — let the chain handle it
- ❌ Reading screenshots to analyze or validate yourself
- ✅ Analyzer and Validator agents handle all visual work
- ❌ Continuing to generate text / "thinking out loud" after spawning agents
- ✅ END the response immediately after sending tasks — agents notify you when done

### Chain Communication
- ❌ Spawning agents WITHOUT `team_name`
- ✅ ALWAYS create team first, then spawn agents with `team_name`
- ❌ Not telling agents who they communicate with (agent names)
- ✅ Each agent prompt must include names of agents it sends to / receives from
- ❌ Spawning agents without checking agent model config
- ✅ Reading model from `.claude/rules/workflow/agent-models.md` per role
- ❌ Spawning agents one-by-one as chain progresses
- ✅ Spawn ALL agents in a SINGLE message — they wait for their inputs

### Structural Assumptions (Planning & Implementation)
- ❌ Copying tab/modal structure from reference page without checking the target design screenshot
- ✅ Reference pages are for code style and component usage — page structure comes from the SCREENSHOT only
- ❌ Writing "TABS" or "Modal" in task context when screenshot shows a continuous page
- ✅ Verify every structural element is VISIBLE on the screenshot before including it
- ❌ Assuming layout elements (tabs, headers) render full-width by default
- ✅ Verify component width props match the design

### Visual Tasks
- ❌ Skipping Analyzer agent for tasks with screenshots
- ✅ Visual tasks ALWAYS need 4 agents: Researcher + Analyzer + Implementer + Validator
- ❌ Validator only checking "is every code element in the design?" (one-directional)
- ✅ Validator MUST also check: "does code ADD structural elements NOT present in the design?" (bidirectional)

---

## Example: Solo Workflow

```
User: "Fix the typo in Button label"

1. ASSESS: 1 file, ~5 lines → Solo ✓
2. IMPLEMENT: Edit the file
3. VERIFY: Run format-and-check
```

## Example: Delegate (Code Task — Chain)

```
User: "Add a new button variant and update all usages"

1. ASSESS: Multiple files → Delegate
2. TeamCreate "button-variant"
3. SPAWN 3 agents in ONE message:
   - researcher (prompt: explore button component, find all usages)
   - implementer (prompt: wait for researcher, then implement)
   - validator (prompt: wait for implementer, then validate)
4. Send task to researcher via SendMessage
5. WAIT — chain runs autonomously:
   researcher → implementer → validator (with correction loops if needed)
6. Validator sends final report to me
7. Report to user: "Task done — new button variant added, N files updated"
8. User confirms → shutdown team
```

## Example: Delegate (Visual Task — Chain)

```
User: "Create this page" + screenshot

1. ASSESS: Screenshot → Delegate (visual task, 4 agents)
2. TeamCreate "page-implementation"
3. SPAWN 4 agents in ONE message:
   - researcher (prompt: find similar pages, component patterns)
   - analyzer (prompt: analyze screenshot + Figma JSON)
   - implementer (prompt: wait for BOTH researcher and analyzer)
   - validator (prompt: wait for implementer, validate against screenshot)
4. Send task to researcher AND analyzer in parallel (two SendMessages)
5. WAIT — chain runs autonomously:
   [researcher + analyzer] → implementer → validator (max 3 loops)
6. Validator sends final report to me
7. Report to user: "Page created — validator confirmed all elements match"
8. User reviews:
   ├─ "Looks good" → shutdown all, delete team
   └─ "Fix X and Y" → send fixes to implementer → chain runs again → report
```

## Example: Delegate (tasks:run — Multiple Tasks)

```
User: "/tasks-run" (6 tasks)

1. READ tasks.md + status.md
2. FIND available: Tasks #1, #2, #3 (no deps, no shared files)
3. For EACH task, create separate team:
   - TeamCreate "task-1" → spawn researcher-1, impl-1, validator-1
   - TeamCreate "task-2" → spawn researcher-2, impl-2, validator-2
   - TeamCreate "task-3" → spawn researcher-3, analyzer-3, impl-3, validator-3 (visual)
4. Send tasks to each team's researcher (+ analyzer for visual)
5. WAIT for all validators to report

   validator-1 reports → update status.md: #1 done
   validator-3 reports → update status.md: #3 done
   validator-2 reports → update status.md: #2 done

6. FIND newly available: Tasks #4, #5 (deps met)
7. Create new teams, repeat
8. CONTINUE until all complete or blocked
9. Report summary to user
10. User confirms → clean up all teams
```

## Example: User Feedback Flow

```
User reviews completed page: "The button should be red, not blue"

1. Send fix to Implementer (in existing team):
   SendMessage to "implementer": "User feedback: button should be red not blue.
   Find the button and change its color."
2. Implementer fixes → sends report to Validator
3. Validator checks → sends report to me
4. Report to user: "Fixed — button is now red"
5. User: "Perfect, all done"
6. Shutdown team → TeamDelete
```
