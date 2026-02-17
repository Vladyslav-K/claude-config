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

### tasks.md Context Quality Check

When writing Context sections in tasks.md:

- **DO include:** Clear requirements, acceptance criteria, existing code PATTERNS from codebase (actual examples)
- **DO NOT include:** Full implementation code written from scratch by the planner
- **Why:** If the planner writes the full code, errors in the plan become errors in implementation. Agents should implement based on requirements + researched patterns, not copy-paste from plan.

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

You have two workflow modes:

1. **Solo Workflow** — for tiny tasks (1 file, ≤150 lines change)
   - Implement yourself → Verify

2. **Delegate Workflow** — for everything else (2+ files, heavy research, skills, tasks:plan, tasks:run, estimate)
   - Research (agent) → Implement (agent) → You validate → Verify

**Key principle:** Delegate ALL heavy work to agents to preserve main context window. Main chat handles orchestration and validation ONLY. Reading files, writing code, debugging — all of this should happen in agent context, not main chat.

**Available agent types:**
- `Explore` — read-only, Haiku model. ONLY for file search, grep, simple lookups.
- `general-purpose` — inherits current chat model. For deep research, analysis, AND implementation.

**CRITICAL: NEVER specify `model` param when spawning `general-purpose` agents. Omit it → agent automatically inherits current chat model. This future-proofs against model changes.**

---

## ⚠️ MANDATORY Delegation Check

**Before EVERY task, ask yourself this question:**

> "Will this touch 2+ files OR require reading 5+ files for research?"

```
YES → Delegate Workflow (ALWAYS)
NO  → Solo Workflow (1 file, ≤150 lines)
```

**There is NO "medium" category. Either it's tiny enough to do yourself, or you delegate.**

### Decision Tree

```
Assess task:
├─ Solo (ALL conditions must be true):
│   ├─ Changes only 1 file
│   ├─ ≤150 lines of changes
│   └─ No deep research needed (you already know the patterns)
│   → Implement yourself → Verify
│
└─ Delegate (ANY condition is true):
    ├─ Changes 2+ files
    ├─ Requires reading 5+ files to understand patterns
    ├─ Generates a whole page/feature/component set
    ├─ Has design specs or screenshots
    ├─ Is a skill command (/estimate, /tasks:plan, /tasks:run, etc.)
    ├─ Requires deep codebase research/analysis
    └─ Context window already has substantial content
    → Spawn agent(s) → Validate result → Verify
```

### Why This Threshold Is So Low

Reading files eats context fast. Example:
- Read 5 components (Input, Select, Table, Button, Form) → ~30-40% context gone
- Make changes + re-read to verify → another ~20%
- After 1-2 tasks → context exhausted, session quality drops

**Agents have their own context windows.** Delegating saves YOUR context for orchestration and validation — which are cheap operations.

---

## Solo Workflow (Tiny Tasks Only)

**Use ONLY when: 1 file, ≤150 lines, no research needed.**

### Steps

1. **Implement** — Edit the file directly
2. **Verify** — Run format-and-check, fix issues

**That's it.** No research phase needed for tiny tasks — you should already know the patterns from context or memory.

---

## Delegate Workflow (Default for Most Tasks)

### When to Use

**ANY task that doesn't fit Solo criteria (1 file, ≤150 lines, no research).**

Common triggers:
- Task touches 2+ files
- Need to research codebase patterns (reading 5+ files)
- Creating a new page/feature/component set
- Task has design specs or screenshots
- Running a skill (/estimate, /tasks:plan, /tasks:run, etc.)
- Deep analysis or architectural research needed
- Context window already has substantial content

### Agent Mechanism: ALWAYS Use Teams (TeamCreate)

**All delegation MUST use the team mechanism (CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS):**

1. **TeamCreate** → creates team context
2. **Task with `team_name`** → spawns agents in the team
3. **SendMessage** → communicate with team agents
4. **TeamDelete** → cleanup when done

**NEVER spawn agents without `team_name`.** Even for a single agent — create a team first. This ensures proper communication via SendMessage and clean shutdown.

```
TeamCreate:
  team_name: "{descriptive-name}" (e.g., "page-implementation", "feature-auth")
  description: "Working on [description]"
```

**CRITICAL: NEVER specify `model` param when spawning agents. Omit it → agent inherits current chat model.**

### Two Workflow Variants

| Task type | Agents needed | Flow |
|-----------|--------------|------|
| **Code tasks** (no design) | research + implementer | Research → Team → Implementer → Validate → Shutdown |
| **Visual tasks** (screenshots/Figma) | research + analyzer + implementer + validator | Research → Team → Analyzer → Implementer → Validator → Fix → Shutdown |

**For detailed agent templates, visual task rules, and validation system → see `agent-management.md`**

### Delegate Steps (High-Level)

**Code tasks:**
1. Research (Explore or general-purpose agent) — see agent templates in `agent-management.md`
2. Spawn implementer agent — see code implementer template in `agent-management.md`
3. Validate result (read output files, compare with requirements)
4. Fix issues (minor → yourself, major → send to agent)
5. Run format-and-check
6. Shutdown team

**Visual tasks:**
1. Research (Explore or general-purpose agent)
2. Spawn analyzer agent → get design analysis — **GATE 1 must pass** (see `agent-management.md`)
3. Spawn implementer agent (with analyzer output)
4. Spawn validator agent → get discrepancy report — **GATE 2 must pass** (see `agent-management.md`)
5. Fix issues based on validator report
6. Run format-and-check
7. Shutdown team

### Fix Issues (after agent completion)

Based on validator's report (visual) or code review (code), the orchestrator decides:
- ⚠️ Minor issues (1-3 simple style fixes) → Fix yourself in main context
- 🔄 Moderate issues (4+ fixes or layout changes) → Send corrections to implementer via SendMessage
- After fixes, optionally re-run validator for a second pass if many issues were found

### Monitor and Iterate (for multi-task workflows)

After current batch completes:
1. Find newly available tasks (dependencies now met)
2. Spawn new agents for next batch
3. Repeat until all done or blocked

### Final Verification

1. Run `format-and-check` for entire project
2. Fix any remaining issues

### Shutdown Team

```
SendMessage type: "shutdown_request" to each agent
Then: TeamDelete
```

---

## Context Window Optimization

### Why Delegation Saves Context

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
Architecture issues, wrong data flow, multiple bugs → Delegate research to general-purpose agent first, then fix.

### Team Agent Bugs
If an agent produced buggy code:
- Minor → Fix yourself
- Major → Send correction via SendMessage with specific instructions and correct code examples

---

## Common Mistakes to Avoid

### Research Phase
- ❌ "Find card components and tell me how they work"
- ✅ "Find card components - return FULL CODE of 2 best examples"

### Delegate Workflow
- ❌ Spawning agents WITHOUT `team_name` (not using TeamCreate)
- ✅ ALWAYS create team first, then spawn agents with `team_name`
- ❌ Spawning agents without full task context in prompt
- ✅ Including ALL requirements, patterns, and design specs in agent prompt
- ❌ Hardcoding `model: "opus"` or any model in agent spawn
- ✅ Omitting `model` param → agent inherits current chat model automatically
- ❌ Skipping analyzer agent for visual/screenshot tasks
- ✅ Always spawning analyzer → implementer → validator for visual tasks
- ❌ Orchestrator "comparing" screenshot to code (superficial, unreliable)
- ✅ Spawning a dedicated validator agent for visual comparison
- ❌ Doing tasks that touch 2+ files yourself in main context
- ✅ Delegating ANY task that touches 2+ files to agents
- ❌ Reading all implementation code in main context
- ✅ Only reading output files during validation

### Verification Phase
- ❌ Skipping validation after delegation
- ✅ Reading output files and comparing with requirements/screenshots
- ❌ Only running lint/typecheck without reviewing
- ✅ Running format-and-check AND reading the output

### Orchestrator Overreach
- ❌ Orchestrator reading screenshot and writing analysis instead of spawning analyzer
- ✅ ALWAYS spawn analyzer agent — orchestrator NEVER does visual analysis
- ❌ Orchestrator comparing code to screenshot and saying "looks correct"
- ✅ ALWAYS spawn validator agent — orchestrator NEVER does visual validation
- ❌ Orchestrator claiming "validated ✅" without having a validator agent_id
- ✅ Gate system: must reference actual agent name + report before marking done

### Structural Assumptions (Planning & Implementation)
- ❌ Copying tab/modal structure from reference page without checking the target design screenshot
- ✅ Reference pages are for code style and component usage — page structure comes from the SCREENSHOT only
- ❌ Writing "TABS" or "Modal" in task context when screenshot shows a continuous page
- ✅ Verify every structural element (tabs, modals, drawers, sections) is VISIBLE on the screenshot before including it in the plan
- ❌ Validator only checking "is every code element in the design?" (one-directional)
- ✅ Validator MUST also check: "does code ADD structural elements (tabs, modals) NOT present in the design?" (bidirectional)
- ❌ Assuming layout elements (tabs, headers) render full-width by default
- ✅ Verify component width props match the design (check fullWidth, w-full, grow, stretch)

### Page Integration
- ❌ Creating new page without adding it to page title mapping
- ✅ Research how page titles work, add new page to the mapping
- ❌ Creating filters as static buttons with no functionality
- ✅ Filters must work with mock data OR have explicit TODO comments
- ❌ Rendering email as plain text when design shows it as a link
- ✅ Emails must be mailto: links, phone numbers must be tel: links
- ❌ Adding duplicate action buttons (same button in header AND content)
- ✅ Count buttons on design, ensure code matches exactly
- ❌ Adding role-inappropriate UI elements (notifications for admin)
- ✅ Only add UI elements that are explicitly shown in the design for that role

---

## Example: Solo Workflow

```
User: "Fix the typo in Button label"

1. ASSESS: 1 file, ~5 lines → Solo ✓
2. IMPLEMENT: Edit the file
3. VERIFY: Run format-and-check
```

## Example: Delegate (Code Task)

```
User: "Add a new button variant and update all usages"

1. ASSESS: Multiple files → Delegate
2. TeamCreate "button-variant"
3. RESEARCH (Explore): Find button component, all usages
4. SPAWN implementer (NO model param, team_name: "button-variant"):
   - Research results in prompt
   - Task description
5. WAIT → implementer sends completion message
6. VALIDATE: Read output files, check patterns
7. RUN format-and-check
8. SHUTDOWN TEAM → TeamDelete
```

## Example: Delegate (Visual Task — Full Flow)

```
User: "Create this page" + screenshot

1. ASSESS: Screenshot → Delegate (visual task flow)
2. TeamCreate "page-implementation"
3. RESEARCH (Explore): Find similar pages, components, imports
4. SPAWN analyzer (team_name: "page-implementation"):
   - Screenshot path
   - Figma JSON path (if available)
   → Analyzer sends back detailed component tree + styles analysis
5. SPAWN implementer (team_name: "page-implementation"):
   - Screenshot path
   - Analyzer's FULL analysis pasted into prompt
   - Research results (code patterns, imports)
   → Implementer builds section-by-section, self-reviews, sends done
6. SPAWN validator (team_name: "page-implementation"):
   - Screenshot path
   - List of files implementer created
   - Analyzer's analysis
   → Validator sends back report: 12 elements checked, 2 issues found
7. FIX: 2 minor issues → fix myself (button color, font-weight)
8. RUN format-and-check
9. SHUTDOWN all agents → TeamDelete
10. Report to user
```

## Example: Delegate (tasks:run)

```
User: "/tasks-run" (8 tasks)

1. READ tasks.md + status.md
2. TeamCreate "tasks-execution"
3. FIND available: Tasks #1, #4, #5 (no deps)
4. PARALLEL CHECK: no shared files ✓
5. SPAWN 3 implementers (NO model param) in ONE message
6. WAIT for completions

   impl-1 done Task #1 → validate → ✅ done
   impl-2 done Task #4 → validate → ⚠️ minor fix → done
   impl-3 done Task #5 → validate → ✅ done

   For visual tasks: also spawn validator for each

7. UPDATE status.md: #1, #4, #5 → done
8. FIND available: Tasks #2, #3 (deps: 1 ✓)
9. SPAWN 2 agents for #2, #3
10. VALIDATE each → fix issues → done
11. CONTINUE until all complete

12. FINAL format-and-check
13. SHUTDOWN all agents → TeamDelete
14. Summary: 8/8 completed, 0 blocked
```
