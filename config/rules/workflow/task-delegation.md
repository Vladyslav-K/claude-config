# Task Workflow

**Follow this workflow for coding tasks.**

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

---

### Step 1: Research Phase

**Choose the right agent for research based on complexity:**

| Research type | Agent | When |
|--------------|-------|------|
| Find files, grep patterns, simple lookups | `Explore` (Haiku) | "Where is Button component?" |
| Deep analysis, understanding flows, expert opinion | `general-purpose` (inherits model) | "How does auth flow work? What are edge cases?" |

**For simple lookups (Explore):**
```
Task tool:
  subagent_type: "Explore"
  description: "Find [what you're looking for]"
  prompt: |
    ## PROJECT MEMORY (READ FIRST)
    Memory files exist at: {CWD}/.project-meta/memory/
    Read these files FIRST to understand project context.

    ## SEARCH TASK
    [What to find — be specific]

    ## WHAT TO RETURN
    1. FULL CODE of found components (not summaries)
    2. Exact import paths
    3. Actual file paths (absolute)
```

**For deep research (general-purpose, NO model param):**
```
Task tool:
  subagent_type: "general-purpose"
  team_name: "{team-name}"
  name: "researcher"
  description: "Deep research [topic]"
  mode: "bypassPermissions"
  prompt: |
    You are a research agent. DO NOT write/modify any files. Only read and analyze.

    ## PROJECT MEMORY (READ FIRST)
    Memory files exist at: {CWD}/.project-meta/memory/
    Read these files FIRST to understand project context.

    ## RESEARCH TASK
    [What to analyze, understand, or decide — be specific]

    ## THINK DEEPLY ABOUT:
    - What exact patterns does this project use?
    - What are the edge cases and non-obvious dependencies?
    - What architectural decisions are relevant?

    ## WHAT TO RETURN
    1. FULL CODE of similar implementations (actual code, not descriptions)
    2. Exact import paths used in this project
    3. Type/interface definitions that will be needed
    4. Code style patterns observed
    5. Your expert analysis and recommendations

    Send findings to the team lead when done.
```

### Step 2: Screenshot Analysis (VISUAL TASKS ONLY)

**When task has screenshots or Figma specs, spawn a dedicated analyzer agent BEFORE implementation.**

This agent's ONLY job is to deeply understand the design and produce a structured analysis. This gives the implementer TWO sources of truth: the screenshot + a textual analysis.

```
Task tool:
  subagent_type: "general-purpose"
  team_name: "{team-name}"
  name: "analyzer"
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
    Use tree notation to show NESTING explicitly:
    ```
    Page
    ├── Header (flex, justify-between, sticky top)
    │   ├── Logo (left side)
    │   ├── Navigation (center)
    │   │   ├── Link "Dashboard"
    │   │   └── Link "Settings"
    │   └── Button "Sign Up" (right side, INSIDE header)
    ├── Main Content
    │   └── TableWrapper (single unified container)
    │       ├── Table (inside wrapper)
    │       └── Pagination (inside wrapper, at bottom)
    └── Footer
    ```
    PAY SPECIAL ATTENTION to what is INSIDE what. If elements share
    a border or background, they MUST be in the same parent wrapper.

    ### 2. Visual Properties for EACH element
    For every element list:
    - Colors: background, text, border (exact hex from Figma JSON, or best visual estimate)
    - Font: size, weight (bold/semibold/medium/normal), style
    - Spacing: padding, margin, gap between elements
    - Borders: color, width, radius
    - Shadows if any
    - Dimensions: width, height if determinable

    ### 3. Visually Grouped Elements
    List elements that MUST share a wrapper because they:
    - Share a common border or background
    - Form a visual unit (e.g., table + pagination = one card)
    - Have connected styling (e.g., first/last border radius)

    ### 4. Layout Decisions
    - Flex/grid direction and alignment for each container
    - How elements are positioned relative to each other
    - What's fixed/sticky vs scrollable
    - Responsive considerations if visible

    ### 5. Text Content
    List EVERY text string visible on the screenshot with its exact content.

    Send your complete analysis to the team lead when done.
```

### Step 3: Spawn Implementer Agents

**For code tasks:** use the code implementer template.
**For visual tasks:** use the visual implementer template (includes analysis from analyzer agent).

#### Visual Implementer (screenshots/Figma)

```
Task tool:
  subagent_type: "general-purpose"
  team_name: "{team-name}"
  name: "impl-{N}"
  mode: "bypassPermissions"
  prompt: |
    You are an implementer agent.

    ## YOUR TASK
    [Full context: what to create/modify, requirements]

    ## SCREENSHOTS / DESIGN SPECS
    [Screenshot paths to READ — include absolute paths]
    [Figma JSON path if available]

    ## DESIGN ANALYSIS (from analyzer agent)
    [Paste the FULL analysis from the analyzer agent here]

    ## PROJECT CONTEXT
    Working directory: {CWD}
    Memory: {CWD}/.project-meta/memory/ (read these first!)

    ## CODEBASE PATTERNS (from research)
    [Paste relevant code examples, import paths, conventions found during research]

    ## KNOWN MISTAKES (read these files if they exist)
    - .claude/rules/common-mistakes.md (global known mistakes)
    - {CWD}/.project-meta/COMMON_MISTAKES.md (project-specific recent mistakes)
    Read them and avoid ALL listed mistakes.

    ## IMPLEMENTATION PROCESS (follow strictly)

    ### Phase 1: Preparation (before writing ANY code)
    1. Read project memory files for patterns and conventions
    2. Read common mistakes files (listed above) if they exist
    3. Find the MOST SIMILAR existing page/component in the project
       and use it as a TEMPLATE for structure, imports, and patterns
    4. List ALL existing project components you will reuse
       (buttons, inputs, tables, cards from the component library)
    5. Read the screenshot and describe IN YOUR OWN WORDS what you see:
       - Every element on the page
       - Where each element is located (inside which parent)
       - Colors, fonts, sizes you observe
    6. Compare your description with the analyzer's analysis — resolve
       any differences BEFORE coding

    ### Phase 2: Section-by-Section Implementation
    Build the page SECTION BY SECTION, not all at once:
    a. Build Header → re-read screenshot → verify header matches
    b. Build Main Content → re-read screenshot → verify
    c. Build remaining sections → re-read screenshot → verify each
    After EACH section, check: does my code match the screenshot for
    this specific area?

    ### Phase 3: Mandatory Self-Review (before reporting done)
    1. Re-read the screenshot FRESH
    2. Re-read ALL your implemented code
    3. Go element by element through the screenshot:
       - Is this element in my code? ✓/✗
       - Is it in the correct parent container? ✓/✗
       - Are styles correct (color, font-weight, size, spacing)? ✓/✗
    4. Fix EVERY discrepancy found
    5. Run format-and-check (or format, lint, typecheck), fix issues
    6. Only THEN proceed to reporting

    ## COMMON MISTAKES — VERIFY AGAINST EVERY SINGLE ONE:
    - NEVER place action buttons OUTSIDE their parent container
      (if a button appears inside a header on the screenshot,
       it MUST be a child of the header element in JSX)
    - NEVER separate visually grouped elements
      (if table and pagination share a border/background on the
       screenshot, they MUST be wrapped in ONE container)
    - NEVER guess colors — extract EXACT hex from Figma JSON or
      design analysis, or match precisely from screenshot
    - NEVER use wrong font-weight — check: is text bold/semibold/normal
      on the screenshot? Get it RIGHT
    - NEVER approximate spacing — use exact values from design analysis
      or Figma JSON
    - ALWAYS verify: does EVERY text visible on screenshot exist in your code
      with the EXACT same content?
    - ALWAYS verify: is EVERY element nested inside the CORRECT parent?
    - ALWAYS verify: are visually grouped elements in ONE shared wrapper?

    ## RULES
    - Follow existing code patterns exactly
    - Don't create tests unless specified
    - Don't add unnecessary comments
    - Use English for all code and comments
    - Follow the project's code style

    ## WHEN DONE
    Send message to team lead with:
    - What files were created/modified
    - What existing components were reused
    - Any uncertainties or areas you're not confident about
```

#### Code Implementer (no design)

```
Task tool:
  subagent_type: "general-purpose"
  team_name: "{team-name}"
  name: "impl-{N}"
  mode: "bypassPermissions"
  prompt: |
    You are an implementer agent.

    ## YOUR TASK
    [Full context: what to create/modify, requirements, code patterns]

    ## PROJECT CONTEXT
    Working directory: {CWD}
    Memory: {CWD}/.project-meta/memory/ (read these first!)

    ## CODEBASE PATTERNS (from research)
    [Paste relevant code examples, import paths, conventions found during research]

    ## IMPLEMENTATION PROCESS
    1. Read project memory files for patterns and conventions
    2. Find SIMILAR existing code in the project and use as template
    3. Implement the task following existing patterns exactly
    4. Re-read your created/modified files to verify
    5. Run format-and-check (or format, lint, typecheck), fix issues

    ## RULES
    - Follow existing code patterns exactly
    - Don't create tests unless specified
    - Don't add unnecessary comments
    - Use English for all code and comments
    - Follow the project's code style

    ## WHEN DONE
    Send message to team lead with:
    - What files were created/modified
    - Any uncertainties or decisions made
```

**For parallel tasks:** Spawn multiple agents in a SINGLE message (parallel Task tool calls).

### Step 4: Spawn Validator Agent (VISUAL TASKS ONLY)

**After implementer finishes, spawn a SEPARATE validator agent with fresh eyes.**

This agent has NOT seen the implementation process — it only sees the screenshot and the resulting code. This eliminates the bias of "I wrote it so it looks right."

```
Task tool:
  subagent_type: "general-purpose"
  team_name: "{team-name}"
  name: "validator"
  mode: "bypassPermissions"
  prompt: |
    You are a validation agent. Your ONLY job is to find EVERY discrepancy
    between the design and the implementation. Be extremely thorough and critical.

    ## SCREENSHOT(S) TO COMPARE AGAINST
    [Absolute paths to screenshot files — READ them]

    ## DESIGN ANALYSIS (from analyzer agent, if available)
    [Paste the analysis]

    ## IMPLEMENTED CODE TO VALIDATE
    [List of file paths created/modified by the implementer — READ them all]

    ## KNOWN MISTAKES (read these files if they exist)
    - .claude/rules/common-mistakes.md (global known mistakes)
    - {CWD}/.project-meta/COMMON_MISTAKES.md (project-specific)
    Pay special attention to these — they are REAL mistakes from previous work.

    ## YOUR TASK
    Go through EVERY element visible on the screenshot and verify
    it exists correctly in the code.

    ### For EACH element check:
    1. EXISTS? — Is this element present in the code?
    2. CORRECT PARENT? — Is it nested inside the right container?
       (e.g., button inside header, NOT after header)
    3. CORRECT POSITION? — Left/center/right placement correct?
    4. CORRECT STYLES?
       - Color: does the hex match?
       - Font size: correct value?
       - Font weight: bold/semibold/normal matches screenshot?
       - Spacing/padding/margin: reasonable match?
       - Border/radius: present if shown in design?
    5. CORRECT TEXT? — Does text content match exactly?
    6. NO EXTRAS? — Is there anything in the code NOT on the screenshot?

    ### Layout structure check:
    - Are visually grouped elements in the same wrapper?
    - Are flex directions correct (row vs column)?
    - Are alignments correct (items-center, justify-between, etc.)?
    - Does nesting hierarchy match the visual hierarchy?

    ## OUTPUT FORMAT (follow exactly)

    ### ✅ Correct Elements
    - [Element]: [brief confirmation]

    ### ❌ Issues Found
    For EACH issue:
    - **Element:** [what element]
    - **File:** [file path:line number]
    - **Problem:** [specific description of what's wrong]
    - **Expected:** [what it should be based on screenshot]
    - **Actual:** [what it currently is in the code]
    - **Fix:** [how to fix it]

    ### 📊 Summary
    - Total elements checked: N
    - Correct: N
    - Issues found: N
    - Severity: [minor styling / moderate layout / critical structure]

    Send your complete report to the team lead.
```

### Step 5: Fix Issues (based on validator report)

Based on validator's report, the orchestrator decides:
- ⚠️ Minor issues (1-3 simple style fixes) → Fix yourself in main context
- 🔄 Moderate issues (4+ fixes or layout changes) → Send corrections to implementer via SendMessage
- After fixes, optionally re-run validator for a second pass if many issues were found

### Step 6: Monitor and Iterate (for multi-task workflows)

After current batch completes:
1. Find newly available tasks (dependencies now met)
2. Spawn new agents for next batch
3. Repeat until all done or blocked

### Step 7: Final Verification

1. Run `format-and-check` for entire project
2. Fix any remaining issues

### Step 8: Shutdown Team

```
SendMessage type: "shutdown_request" to each agent
Then: TeamDelete
```

---

## Validation System

### How Validation Works

**Visual tasks:** Validator AGENT does the detailed comparison (Step 4 above). Orchestrator reviews the validator's report and decides on fixes.

**Code tasks:** Orchestrator reads the output files and validates directly.

### Orchestrator Validation (code tasks)

1. **Read created/modified files** — understand what agent produced
2. **Compare with task requirements** — are ALL listed requirements implemented?
3. **Check code patterns** — does agent use correct project conventions?
4. **Run format-and-check** — catch lint/type errors

### Orchestrator Review of Validator Report (visual tasks)

1. **Read validator's report** — review each ❌ issue
2. **Prioritize fixes** — critical structure issues first, then styling
3. **Decide action:**
   - ⚠️ Minor (1-3 fixes) → Fix yourself
   - 🔄 Moderate (4+) → Send corrections to implementer
   - If many issues → re-run validator after fixes

### Decision Tree

```
Validator report / code review:
├─ 0 issues
│   → ✅ Accept, mark done
│
├─ 1-3 minor issues (styling, small fixes)
│   → ⚠️ Fix yourself (faster than round-trip)
│
├─ 4+ issues or layout problems
│   → 🔄 Send correction to implementer via SendMessage
│   → Include validator's specific findings
│
└─ Fundamental structure wrong
    → 🔄 Send full correction with correct structure example
    → Consider re-running analyzer + implementer
```

### After Validation

- **Solo task:** Report result to user
- **tasks:run:** Update status.md (task → `done` or `blocked`)
- **If fixes were needed:** Note common issues for future reference

---

## Common Mistakes System

### Two-File Architecture

| File | Path | Who edits | Contains |
|------|------|-----------|----------|
| **Global** | `.claude/rules/common-mistakes.md` | User (manually) | Curated rules from all projects |
| **Local** | `.project-meta/COMMON_MISTAKES.md` | Orchestrator (freely) | New entries not yet in global |

### When to Write

After user reports a mistake in agent's work:
1. Fix the issue
2. Read global file to check if this rule already exists
3. If rule exists → add "New example for [rule]:" in local file
4. If rule is NEW → write full rule entry in local file

### Entry Format (same in both files)

```markdown
## [Category]

### [General rule name]
[1-2 sentences: WHEN this rule applies and WHAT to do]
- Example: [specific incident that led to this rule]
- Example: [another incident of the same type]
```

Categories: Layout & Nesting, Colors, Typography, Spacing, Components, Text Content, Responsive

### Agent Integration

ALL implementer and validator agents MUST read both files:
```
Read these files if they exist (known mistakes to avoid):
- .claude/rules/common-mistakes.md (global)
- {CWD}/.project-meta/COMMON_MISTAKES.md (project-specific)
```

### Maintenance

- Local file: user periodically copies entries to global, then clears local
- Global file: grows over time with curated rules
- No hard limit on entries — rules are general (not incidents), so count stays manageable
- If a rule has 5+ examples, older examples can be removed (rule stays)

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

## Research Criteria

### Two Levels of Research

| Level | Agent | Model | Use when |
|-------|-------|-------|----------|
| **Simple lookup** | `Explore` | Haiku (fast, cheap) | Find files, grep patterns, check what exists |
| **Deep analysis** | `general-purpose` | Inherits chat model | Understand flows, analyze architecture, expert decisions |

### When to use Explore (Haiku)

- Find where a component/function is located
- Grep for a pattern across codebase
- List files in a directory structure
- Check what imports/exports exist
- Simple "does X exist?" questions

### When to use general-purpose (inherits model) for research

- Understanding how a complex flow works (auth, data pipeline, state management)
- Analyzing architecture decisions and trade-offs
- Expert opinion on how to implement something
- When research quality directly affects implementation quality
- When Haiku might miss important nuances

**Rule of thumb:** If the research answer will directly shape implementation decisions → use `general-purpose`. If you just need to find files/patterns → use `Explore`.

### When to SEARCH yourself (main context)

Handle directly ONLY when:
- **Known location:** You already know the exact file path
- **Single lookup:** One glob or one grep, takes 1 tool call
- **Already in context:** Information is already in current conversation

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
