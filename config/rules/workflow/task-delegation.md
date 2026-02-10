# Task Workflow

**Follow this workflow for coding tasks.**

---

## Overview

You have two workflow modes based on task size:

1. **Solo Workflow** — for small/medium tasks (1-3 files, simple changes)
   - Research (Explore agent) → Implement yourself → Verify

2. **Team Workflow** — for large tasks (4+ files, multiple features, tasks:run)
   - Create team → Spawn implementer agents (opus) → Validate results → Shutdown team

**Key principle:** Delegate heavy implementation to team agents to preserve main context window. Main chat handles orchestration and validation only.

**Available agent types:**
- `Explore` — read-only research agent
- `general-purpose` with `model: "opus"` — full implementation agent (same model as main chat)

---

## Task Size Assessment

### Decision Tree

```
Assess task complexity:
├─ Small (1-2 files, clear change, <30 min work)
│   → Solo Workflow (implement yourself)
│
├─ Medium (2-4 files, single feature, clear requirements)
│   → Solo Workflow (implement yourself)
│   → Consider single agent delegation if context is getting large
│
└─ Large (4+ files, multiple features, complex requirements)
    → Team Workflow (create team, delegate to agents)
    → ALWAYS for /tasks-run command
```

### Size Indicators

| Indicator | Small | Medium | Large |
|-----------|-------|--------|-------|
| Files to change | 1-2 | 2-4 | 4+ |
| Features involved | 1 | 1-2 | 2+ |
| Has design specs | No | Maybe | Yes |
| Has screenshots | No | Maybe | Yes |
| tasks:run command | No | No | Yes (always team) |
| Estimated effort | <30min | 30min-2h | 2h+ |

### Context Window Health

**Switch to Team Workflow when:**
- Context window is getting large (many files read/edited in session)
- Task is halfway done and remaining work is still substantial
- Multiple independent work streams can proceed in parallel
- User gives complex task with screenshots/design specs

---

## Solo Workflow (Small/Medium Tasks)

### Step 1: Research Phase (Explore agent)

1. Read and understand user's task
2. Check if memory exists: `.project-meta/memory/`
3. Delegate research to `Explore` agent with memory paths

**Explore agent invocation:**
```
Task tool:
  subagent_type: "Explore"
  description: "Research [what you're looking for]"
  prompt: |
    ## PROJECT MEMORY (READ FIRST)
    Memory files exist at: {CWD}/.project-meta/memory/
    Read these files FIRST to understand project context.

    ## RESEARCH TASK
    [What you need to find — be specific]

    ## THINK DEEPLY ABOUT:
    - What exact files and patterns are relevant?
    - What is the minimum set of information needed?
    - Are there edge cases or non-obvious dependencies?

    ## WHAT TO RETURN
    1. FULL CODE of similar components (not summaries - actual code)
    2. Exact import paths used in this project
    3. Type/interface definitions that will be needed
    4. Actual file paths (absolute paths)
    5. Code style patterns observed

    Return actual code snippets I can use as reference.
```

**Thoroughness:** Use `"very thorough"` for implementation research, `"medium"` for quick lookups.

### Step 2: Implementation (YOU do this)

**After research, implement the task directly using Write/Edit tools.**

Follow this checklist:
- Use patterns discovered during research
- Follow existing project conventions
- Handle edge cases and error states
- Use proper TypeScript types
- Follow accessibility requirements

### Step 3: Verification (YOU do this)

After implementation:
1. **Run format-and-check** (or format, lint, typecheck)
2. **Fix any issues** found by linters/formatters
3. **Re-read modified files** to verify correctness if needed

---

## Team Workflow (Large Tasks)

### When to Use

- `/tasks-run` command (ALWAYS use team)
- Large feature implementation (4+ files)
- Multiple independent work streams
- Context window getting full
- User explicitly asks for team/delegation
- Complex page from screenshot (multiple components to create)

### Step 1: Research Phase (Explore agent)

**Before creating team, research codebase patterns:**

```
Task tool:
  subagent_type: "Explore"
  description: "Research codebase patterns for [task]"
  prompt: |
    ## PROJECT MEMORY (READ FIRST)
    Memory files exist at: {CWD}/.project-meta/memory/
    Read these files FIRST to understand project context.

    ## RESEARCH TASK
    [What patterns, components, conventions to find]

    ## WHAT TO RETURN
    1. FULL CODE of similar implementations
    2. Import paths and project conventions
    3. Type definitions
    4. Code style patterns
    5. File structure patterns
```

### Step 2: Create Team

```
TeamCreate:
  team_name: "{descriptive-name}" (e.g., "tasks-execution", "feature-auth")
  description: "Working on [description]"
```

### Step 3: Spawn Implementer Agents

**CRITICAL: Use `model: "opus"` for implementation agents — same model as main chat.**

For each parallel task or group of tasks:

```
Task tool:
  subagent_type: "general-purpose"
  model: "opus"
  team_name: "{team-name}"
  name: "impl-{N}"
  mode: "bypassPermissions"
  run_in_background: true
  prompt: |
    You are an implementer agent.

    ## YOUR TASK
    [Full context: what to create/modify, requirements, code patterns]

    ## SCREENSHOTS / DESIGN SPECS
    [Screenshot paths to READ — include absolute paths]
    [Dimension tables, colors, typography if available]

    ## PROJECT CONTEXT
    Working directory: {CWD}
    Memory: {CWD}/.project-meta/memory/ (read these first!)

    ## CODEBASE PATTERNS (from research)
    [Paste relevant code examples, import paths, conventions found during research]

    ## RULES
    - Read project memory files FIRST for project patterns
    - Follow existing code patterns exactly
    - Don't create tests unless specified
    - Don't add unnecessary comments
    - Use English for all code and comments
    - Follow the project's code style (spaces, semicolons, single quotes)
    - If project uses Tailwind — follow Tailwind patterns
    - If project uses Shadcn UI — use existing components

    ## WHEN DONE
    1. Re-read your created/modified files to verify
    2. Run format-and-check (or format, lint, typecheck), fix issues
    3. Send message to team lead summarizing what was done and files changed
```

**For parallel tasks:** Spawn multiple agents in a SINGLE message (parallel Task tool calls).

### Step 4: Monitor and Validate (CRITICAL)

**As each agent completes, YOU validate:**

1. **Read output files** — the files agent created/modified
2. **Compare with requirements** — see Validation System section below
3. **Run format-and-check** if not run by agent
4. **Decision:**
   - ✅ Good → Accept, proceed
   - ⚠️ Minor issues → Fix yourself (faster than re-delegating)
   - ❌ Major issues → Send correction to agent via SendMessage with specific instructions

### Step 5: Iterate

After current batch completes:
1. Find newly available tasks (dependencies now met)
2. Spawn new agents for next batch
3. Repeat until all done or blocked

### Step 6: Final Verification

1. Run `format-and-check` for entire project
2. Fix any remaining issues

### Step 7: Shutdown Team

```
SendMessage type: "shutdown_request" to each agent
Then: TeamDelete
```

---

## Validation System

### CRITICAL: Always Validate Delegated Work

**After ANY work delegated to an agent, YOU MUST validate the result.**

This is the most important step — it ensures quality despite delegation.

### Validation Steps

1. **Read created/modified files** — understand what agent produced

2. **Compare with requirements:**

   | Source | What to check |
   |--------|--------------|
   | Screenshot | Layout, components, colors, spacing match design |
   | Figma specs | Exact dimensions, colors, typography match specs |
   | Task description | ALL listed requirements are implemented |
   | Code patterns | Agent used correct project conventions |

3. **Run format-and-check** — catch lint/type errors

4. **Check common issues:**
   - Missing imports or wrong import paths
   - Wrong component library usage (e.g., custom instead of Shadcn)
   - Hardcoded values that should be dynamic
   - Missing responsive styles
   - Missing accessibility attributes
   - Incomplete implementation (missing parts of the task)

### Validation Decision Tree

```
Read agent's output files:
├─ Matches requirements + no issues
│   → ✅ Accept, mark done
│
├─ Minor issues (typos, small styling, missing import)
│   → ⚠️ Fix yourself (faster than round-trip to agent)
│
├─ Moderate issues (wrong pattern, missing section)
│   → 🔄 Send correction to agent via SendMessage
│   → OR fix yourself if simpler
│
└─ Major issues (wrong approach, fundamentally broken)
    → 🔄 Send detailed correction with FULL correct pattern example
```

### Screenshot Comparison Checklist

When task has screenshots, after reading agent's code AND the screenshot:

```
- [ ] All visible components are present in code
- [ ] Layout structure matches (flex direction, alignment, order)
- [ ] Spacing looks correct (padding, margins, gaps)
- [ ] Colors match the design
- [ ] Typography is correct (font size, weight, line-height)
- [ ] Interactive elements are present (buttons, inputs, links)
- [ ] Responsive behavior considered
- [ ] Nothing extra added that's not in the design
```

### After Validation

- **Solo task:** Report result to user
- **tasks:run:** Update status.md (task → `done` or `blocked`)
- **If fixes were needed:** Note what was fixed for learning

---

## Context Window Optimization

### Why Team Workflow Saves Context

| Activity | Solo (main context) | Team (agent context) |
|----------|--------------------|--------------------|
| Reading codebase files | ✅ Heavy | Agent handles |
| Writing/editing code | ✅ Heavy | Agent handles |
| Debug/fix cycles | ✅ Very heavy | Agent handles |
| Validation (read output) | ✅ Light | — |
| Orchestration | ✅ Light | — |

**Result:** Main context only handles orchestration + validation = light operations.

### Strategies

1. **Don't read implementation code in main context** when agents handle it
2. **Provide FULL context in agent prompt** — patterns, specs, conventions
3. **Validate by reading ONLY output files** — not entire codebase
4. **Fix minor issues yourself** — avoids expensive round-trip to agent
5. **Use `run_in_background: true`** for agent tasks — don't block main context
6. **Research once, share results** — do Explore research, paste findings into agent prompts

### When to Compact Despite Teams

If main context is still getting large:
- Many tasks validated in one session
- Solo work done before switching to team
- Consider: "Can remaining work be a fresh agent delegation?"

---

## Research Criteria

### When to DELEGATE research to Explore agent

Delegate to `Explore` agent when:
- **Unknown patterns:** Need to find how project does something
- **Large codebase:** Need to search across many files
- **Multiple examples:** Need 2-3 similar implementations for reference
- **Type definitions:** Need to find interfaces/types across the project

### When to SEARCH yourself

Handle directly when:
- **Known location:** You already know which file to read
- **Simple lookup:** One file, one grep, one glob
- **Already researched:** You have context from earlier in session

### Thoroughness Guide

| Level | When to use | Example |
|-------|------------|---------|
| `"quick"` | Find one specific file/pattern | "Find Button component" |
| `"medium"` | Understand a feature area, find 2-3 patterns | "How are forms built?" |
| `"very thorough"` | Deep analysis across multiple areas | "Full auth system analysis" |

**Default to `"very thorough"` for implementation research.**

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

## Quality Checklist

Use this checklist when verifying work (yours or agent's):

```
## Code Quality
- [ ] All requirements from user's request are implemented
- [ ] Code compiles without errors (TypeScript)
- [ ] No console.log, debugger, or commented-out code
- [ ] Types are properly defined (no `any` unless justified)
- [ ] Follows existing project patterns

## UI/Styling (if applicable)
- [ ] Matches design specs (±2px tolerance)
- [ ] Responsive behavior works
- [ ] Dark mode supported (if project uses it)
- [ ] Accessibility basics (semantic HTML, ARIA where needed)

## Integration
- [ ] Imports are correct and from right locations
- [ ] No circular dependencies introduced
- [ ] Works with existing state/data flow

## Final
- [ ] format-and-check passes
- [ ] No new warnings introduced
- [ ] Validated against original requirements/screenshots
```

---

## Debugging Workflow

### Small Bugs
Typos, missing imports, wrong props, CSS tweaks → Fix directly, no research needed.

### Larger Bugs
Architecture issues, wrong data flow, multiple bugs → Research with Explore first, then fix.

### Team Agent Bugs
If an agent produced buggy code:
- Minor → Fix yourself
- Major → Send correction via SendMessage with specific instructions and correct code examples

---

## Common Mistakes to Avoid

### Research Phase
- ❌ "Find card components and tell me how they work"
- ✅ "Find card components - return FULL CODE of 2 best examples"

### Team Workflow
- ❌ Spawning agents without full task context in prompt
- ✅ Including ALL requirements, patterns, and design specs in agent prompt
- ❌ Not validating agent's work after completion
- ✅ Always reading output files and comparing with requirements
- ❌ Using default model for implementation agents
- ✅ Always using `model: "opus"` for code-writing agents
- ❌ Reading all implementation code in main context
- ✅ Only reading output files during validation

### Verification Phase
- ❌ Skipping validation after delegation
- ✅ Reading output files and comparing with requirements/screenshots
- ❌ Only running lint/typecheck without reviewing
- ✅ Running format-and-check AND reading the output

---

## Example: Solo Workflow

```
User: "Add a new button variant"

1. RESEARCH (Explore agent, "medium"):
   "Find existing button component, return FULL CODE."

2. COMMUNICATE: "Досліджую button → додаю новий варіант"

3. IMPLEMENT (yourself):
   - Edit button component
   - Add new variant

4. VERIFY:
   - Run format-and-check
   - Fix any issues
   - Confirm to user
```

## Example: Team Workflow (Single Large Task)

```
User: "Create this page" + screenshot

1. ASSESS: Large task (new page, multiple components)
2. RESEARCH (Explore, "very thorough"):
   Find similar pages, component patterns, imports
3. CREATE TEAM "page-implementation"
4. SPAWN agent (opus) with full context:
   - Screenshot path
   - Codebase patterns from research
   - Code style rules
   - Design specs (if Figma available)
5. WAIT for completion
6. VALIDATE:
   - Read created files
   - Read screenshot
   - Compare: layout, components, colors, spacing
   - ❌ Missing "forgot password" link → fix myself
7. RUN format-and-check
8. SHUTDOWN TEAM
9. Report to user
```

## Example: Team Workflow (tasks:run)

```
User: "/tasks-run" (8 tasks)

1. READ tasks.md + status.md
2. CREATE TEAM "tasks-execution"
3. FIND available: Tasks #1, #4, #5 (no deps)
4. PARALLEL CHECK: no shared files ✓
5. SPAWN 3 agents (opus) in ONE message
6. WAIT for completions

   impl-1 done Task #1 → validate → ✅ done
   impl-2 done Task #4 → validate → ⚠️ minor fix → done
   impl-3 done Task #5 → validate → ✅ done

7. UPDATE status.md: #1, #4, #5 → done
8. FIND available: Tasks #2, #3 (deps: 1 ✓)
9. SPAWN 2 agents for #2, #3
10. VALIDATE each → fix issues → done
11. CONTINUE until all complete

12. FINAL format-and-check
13. SHUTDOWN team
14. Summary: 8/8 completed, 0 blocked
```
