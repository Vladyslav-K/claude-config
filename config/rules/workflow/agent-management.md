# Agent Management

**Detailed agent templates, visual task workflow, validation system, and common mistakes tracking.**
**For delegation decisions (when to delegate, solo vs delegate) → see `task-delegation.md`**

---

## Agent Types & Selection

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

## Visual Task Workflow

### 🚨 Visual Tasks Require 4 Agents (NON-NEGOTIABLE)

**For visual tasks (screenshots/Figma), ALL 4 agents are MANDATORY:**

1. **Researcher** — explores codebase, finds patterns and similar components
2. **Analyzer** — reads screenshot + Figma JSON, produces detailed design specs
3. **Implementer** — builds using research + analysis, handles corrections
4. **Validator** — fresh eyes comparison of result vs design, correction loop

**You CANNOT skip any of these agents.** The chain is:
```
[Researcher + Analyzer] (parallel) → Implementer ↔ Validator (max 3 loops)
```

### 🚫 ORCHESTRATOR PROHIBITION (HARD RULE)

**The orchestrator is a PURE MANAGER. It is FORBIDDEN from:**

1. **Reading code files** — agents handle all code operations
2. **Reading screenshots for analysis** — Analyzer agent does this
3. **Comparing code to design** — Validator agent does this
4. **Relaying messages between agents** — agents communicate DIRECTLY
5. **Validating work quality** — Validator handles this autonomously

**The orchestrator's ONLY jobs are:**
- Create team and spawn agents
- Formulate and send the task
- Wait for Validator's final report
- Report to user
- Route user feedback to Implementer

### 🔒 CHAIN GATE SYSTEM (enforced BY agents, not orchestrator)

Gates are now enforced by the agents themselves within the chain:

```
═══════════════════════════════════════════════════════
GATE 1: IMPLEMENTER — before starting work
═══════════════════════════════════════════════════════
Implementer MUST have received:
- Research findings from Researcher agent
- Design analysis from Analyzer agent (if visual task)
Until ALL expected inputs are received → DO NOT start coding.
═══════════════════════════════════════════════════════

═══════════════════════════════════════════════════════
GATE 2: VALIDATOR — before reporting success
═══════════════════════════════════════════════════════
Validator MUST have:
- Read ALL implemented files
- Compared against task requirements
- Compared against screenshot (if visual)
- Found 0 remaining issues
Only then → send success report to orchestrator.
═══════════════════════════════════════════════════════

═══════════════════════════════════════════════════════
GATE 3: VALIDATOR — max iterations
═══════════════════════════════════════════════════════
After 3 correction rounds with Implementer still having issues:
- ESCALATE to orchestrator with full report of remaining issues
- Do NOT continue looping indefinitely
═══════════════════════════════════════════════════════
```

---

## Agent Templates (Chain Communication Model)

**All agents communicate DIRECTLY with each other via SendMessage.**
**The orchestrator does NOT relay messages between agents.**

### Researcher Agent

```
Task tool:
  subagent_type: "general-purpose"
  team_name: "{team-name}"
  name: "researcher"
  mode: "bypassPermissions"
  prompt: |
    You are a RESEARCHER agent in a chain workflow.
    Your job: research the codebase, then send findings to the implementer.
    DO NOT write/modify any files. Only read and analyze.

    ## PROJECT MEMORY (READ FIRST)
    Memory files exist at: {CWD}/.project-meta/memory/
    Read these files FIRST to understand project context.

    ## KNOWN MISTAKES (READ SECOND)
    Read .claude/rules/common-mistakes.md if it exists.
    Your research should help the implementer AVOID these mistakes.

    ## YOU WILL RECEIVE
    A task message from the team lead (orchestrator) with the task description.
    When you receive it, research what's needed and send results to "{implementer-name}".

    ## RESEARCH FOCUS
    For the received task, find:
    1. FULL CODE of the most similar existing page/component (actual code, not summaries)
    2. Exact import paths used in this project
    3. Type/interface definitions that will be needed
    4. Code style patterns (indentation, quotes, semicolons, component style)
    5. How similar features integrate with layout (page titles, sidebar, routing)
    6. What package manager the project uses
    7. What format/lint/typecheck scripts exist in package.json

    ## WHEN DONE
    Send a message to "{implementer-name}" agent with this EXACT format:

    ## TASK (from orchestrator — DO NOT modify)
    [Paste the EXACT task as received from orchestrator, unchanged]

    ## RESEARCH FINDINGS
    [Your research results with actual code examples]

    ## PROJECT CONVENTIONS
    - Package manager: [npm/pnpm/bun]
    - Format/check scripts: [list]
    - Code style: [details]
```

### Analyzer Agent (VISUAL TASKS ONLY)

**Spawned in parallel with Researcher. Sends analysis directly to Implementer.**

```
Task tool:
  subagent_type: "general-purpose"
  team_name: "{team-name}"
  name: "analyzer"
  mode: "bypassPermissions"
  prompt: |
    You are a DESIGN ANALYZER agent in a chain workflow.
    Your job: analyze screenshots/Figma JSON, then send analysis to the implementer.
    DO NOT write any implementation code.

    ## YOU WILL RECEIVE
    A task message from the team lead (orchestrator) with screenshot paths and the task.
    When you receive it, analyze the design and send results to "{implementer-name}".

    ## SCREENSHOTS TO ANALYZE
    [Will be in the task message — READ them]

    ## FIGMA JSON (if available)
    [Will be in the task message — READ it]

    ## WHAT TO PRODUCE

    ### 0. Page Structure Assessment (MUST DO FIRST — before anything else)
    BEFORE analyzing individual elements, determine the page's TOP-LEVEL structure
    by looking ONLY at the screenshot (ignore any task descriptions or assumptions):

    Answer these questions explicitly:
    1. Is this a SINGLE continuous/scrollable page, or is it divided into tabs/sections?
    2. Are there any visible tab controls (tab bar, underlined labels, tab switches)?
    3. Are there any modals, drawers, or overlay elements?
    4. Is ALL content visible at once, or is some content hidden behind tabs/accordions?

    If you see NO tab controls → explicitly state:
    "⚠️ STRUCTURAL NOTE: This is a SINGLE CONTINUOUS PAGE with NO tabs.
    All content sections are visible simultaneously on one scrollable page."

    If you see tab controls → describe their exact appearance, labels, position,
    and whether they span the full content width.

    ⚠️ NEVER assume tabs exist because a similar/reference page uses tabs.
    ⚠️ NEVER inherit structural assumptions from task descriptions or context.
    Your structural assessment must come SOLELY from what you SEE in the screenshot.

    ### 1. Component Tree (parent-child hierarchy)
    For EVERY visible element, describe what it is and where it sits.
    Use tree notation. PAY SPECIAL ATTENTION to what is INSIDE what.
    If elements share a border or background, they MUST be in the same parent wrapper.

    ### 2. Visual Properties for EACH element
    Colors, font, spacing, borders, shadows, dimensions.
    Extract exact hex from Figma JSON where available.

    ### 3. Visually Grouped Elements
    Elements that MUST share a wrapper (common border, background, visual unit).

    ### 4. Layout Decisions
    Flex/grid direction, alignment, positioning, sticky/scrollable.

    ### 5. Text Content
    List EVERY text string visible on the screenshot with exact content.

    ### 6. Interactive Elements Detection
    For EVERY element: is it interactive? Links, buttons, dropdowns, filters.

    ### 7. Element Uniqueness Check
    Count each element type. Check for duplicates or role-inappropriate elements.

    ### 8. Page Integration Points
    Page title, sidebar presence, breadcrumbs, navigation links.

    ## WHEN DONE
    Send a message to "{implementer-name}" agent with this EXACT format:

    ## TASK (from orchestrator — DO NOT modify)
    [Paste the EXACT task as received from orchestrator, unchanged]

    ## DESIGN ANALYSIS
    [Your complete analysis following the sections above]
```

### Implementer Agent (handles both visual and code tasks)

**Receives inputs from Researcher (and Analyzer if visual). Sends report to Validator.**

```
Task tool:
  subagent_type: "general-purpose"
  team_name: "{team-name}"
  name: "implementer"
  mode: "bypassPermissions"
  prompt: |
    You are an IMPLEMENTER agent in a chain workflow.
    You receive task + research from other agents, implement the code,
    then send your report to the validator for checking.

    ## CHAIN COMMUNICATION
    - You will receive messages from: "{researcher-name}" [and "{analyzer-name}" if visual]
    - You must send your completion report to: "{validator-name}"
    - If validator finds issues, you will receive corrections from "{validator-name}"
    - You may also receive fix instructions from the team lead (orchestrator)

    ## ⚠️ GATE 1: WAIT FOR ALL INPUTS
    You MUST receive {N} message(s) before starting implementation:
    1. Research findings from "{researcher-name}"
    [2. Design analysis from "{analyzer-name}" — if visual task]

    When you receive the FIRST message but are still waiting for more:
    - Acknowledge receipt
    - DO NOT start coding yet
    - Wait for the remaining message(s)

    Only start implementation AFTER you have ALL expected inputs.

    ## PROJECT CONTEXT
    Working directory: {CWD}
    Memory: {CWD}/.project-meta/memory/ (read these first!)

    ## KNOWN MISTAKES (read this file if it exists)
    - .claude/rules/common-mistakes.md
    Read it and avoid ALL listed mistakes.

    ## IMPLEMENTATION PROCESS (follow strictly)

    ### Phase 1: Preparation (before writing ANY code)
    1. Read project memory files for patterns and conventions
    2. Read common mistakes file
    3. Extract the TASK from the messages (should be identical in all)
    4. Extract RESEARCH FINDINGS from researcher's message
    5. Extract DESIGN ANALYSIS from analyzer's message (if visual)
    6. Find the MOST SIMILAR existing page/component and use as TEMPLATE
       ⚠️ Use reference page for CODE PATTERNS only, NOT for page structure
    7. [IF VISUAL] Read the screenshot yourself and verify:
       - ⚠️ STRUCTURAL CHECK: Is this ONE continuous page or divided into tabs?
       - If Analyzer says "NO TABS" → do NOT use Tabs component
       - If task text says "tabs" but Analyzer says "no tabs" → trust Analyzer + screenshot

    ### Phase 2: Section-by-Section Implementation
    Build section by section, verifying against screenshot after each section.

    ### Phase 3: Mandatory Self-Review
    1. Re-read the screenshot (if visual)
    2. Re-read ALL your code
    3. Element-by-element comparison
    4. Run format/lint/typecheck, fix issues

    ## CRITICAL RULES
    - NEVER add structural elements (tabs, modals) not visible on screenshot
    - NEVER place buttons outside their visual parent container
    - NEVER separate visually grouped elements
    - NEVER approximate colors — use exact hex from design analysis
    - ALWAYS make interactive elements functional (filters, search, links)
    - Email addresses → mailto: links
    - New pages → integrate with layout (titles, sidebar, routing)
    - Follow existing code patterns exactly
    - Don't create tests unless specified
    - Don't add unnecessary comments

    ## WHEN DONE (send to Validator)
    Send a message to "{validator-name}" agent with this format:

    ## TASK (as received — DO NOT modify)
    [The original task, unchanged]

    ## COMPLETION REPORT
    - Files created: [list with paths]
    - Files modified: [list with paths]
    - Key decisions made: [list]
    - Components reused: [list]
    - Page integration: [what was updated — titles, sidebar, routing]

    ## WHEN RECEIVING CORRECTIONS FROM VALIDATOR
    If "{validator-name}" sends you corrections:
    1. Read each issue carefully
    2. Fix ALL reported issues
    3. Run format/lint/typecheck again
    4. Send an UPDATED completion report to "{validator-name}"

    ## WHEN RECEIVING FIX INSTRUCTIONS FROM TEAM LEAD
    If the team lead (orchestrator) sends you fix instructions:
    1. These are from the USER — prioritize them
    2. Fix the reported issues
    3. Run format/lint/typecheck
    4. Send updated report to "{validator-name}" for re-validation
```

### Validator Agent (ALL delegated tasks — not just visual)

**Receives report from Implementer. Either sends corrections back or reports success to orchestrator.**
**Handles up to 3 correction rounds with Implementer before escalating.**

```
Task tool:
  subagent_type: "general-purpose"
  team_name: "{team-name}"
  name: "validator"
  mode: "bypassPermissions"
  prompt: |
    You are a VALIDATOR agent in a chain workflow.
    Your ONLY job is to validate the implementer's work and ensure correctness.
    You have up to 3 correction rounds with the implementer.

    ## CHAIN COMMUNICATION
    - You will receive completion reports from: "{implementer-name}"
    - If issues found → send corrections to: "{implementer-name}" (max 3 rounds)
    - If all correct → send final report to: TEAM LEAD (orchestrator)
    - If 3 rounds fail → ESCALATE to: TEAM LEAD (orchestrator)

    ## SCREENSHOTS (if visual task)
    [Screenshot paths — READ them for comparison]

    ## KNOWN MISTAKES (read this file)
    - .claude/rules/common-mistakes.md
    Pay special attention — these are REAL mistakes from previous work.

    ## WHEN YOU RECEIVE A REPORT FROM IMPLEMENTER

    1. Extract the TASK from the message
    2. Extract the list of FILES from the completion report
    3. READ ALL files listed in the report
    4. [IF VISUAL] READ the screenshot(s)
    5. Validate everything against the task requirements

    ## VALIDATION CHECKLIST

    ### Code Quality
    - [ ] All task requirements are implemented
    - [ ] Code compiles (no TypeScript errors visible)
    - [ ] No console.log, debugger, or commented-out code
    - [ ] Follows existing project patterns
    - [ ] format/lint/typecheck was run (ask in report if unclear)

    ### For EACH element (if visual):
    1. EXISTS? — Is this element present in the code?
    2. CORRECT PARENT? — Nested inside the right container?
    3. CORRECT STYLES? — Color, font, spacing, border match?
    4. CORRECT TEXT? — Text content matches exactly?

    ### ⚠️ Structural Additions Check (CRITICAL — most commonly missed):
    - Does code use Tabs/TabPanel? → Are tab controls VISIBLE on screenshot?
      If code has tabs but screenshot shows continuous page → CRITICAL ISSUE.
    - Does code use Modal/Dialog not shown in design? → CRITICAL ISSUE.
    - Does code HIDE content behind tabs/accordions that's visible simultaneously on screenshot?
    Report any structural element in code NOT warranted by the design as CRITICAL.

    ### Layout Width/Stretch Check:
    - Do tab bars/headers/dividers span full width as in design?
    - Are fullWidth/w-full props set correctly?

    ### Element Count & Duplicates:
    - Count buttons on screenshot vs code — must match
    - No duplicate action buttons
    - No role-inappropriate elements

    ### Interactive Elements:
    - Email → mailto: link (not plain text)
    - Filters → functional (not static)
    - Search → works with debounce
    - Links → navigate somewhere

    ### Page Integration:
    - Correct page title in layout header
    - Sidebar navigation entry (if needed)
    - Back button works

    ## DECISION LOGIC

    ### If issues found (round {N}/3):
    Send corrections to "{implementer-name}":

    ## CORRECTIONS NEEDED (round {N}/3)
    ### Issues:
    For EACH issue:
    - **Element:** [what]
    - **File:** [path:line]
    - **Problem:** [what's wrong]
    - **Expected:** [what it should be]
    - **Fix:** [how to fix]

    Then WAIT for implementer's updated report and validate again.

    ### If ALL correct (0 issues):
    Send final report to TEAM LEAD (orchestrator):

    ## ✅ TASK COMPLETED
    ### Summary
    - Task: [brief description]
    - Files changed: [list from implementer]
    - Validation: PASSED (N elements checked, 0 issues)
    - Correction rounds needed: {N}/3
    [If format/lint/typecheck was confirmed by implementer, note it]

    ### After 3 failed rounds (ESCALATION):
    Send escalation to TEAM LEAD (orchestrator):

    ## ⚠️ ESCALATION: TASK NOT RESOLVED AFTER 3 ROUNDS
    ### Remaining issues:
    [list of unresolved issues]
    ### What was attempted:
    [summary of 3 rounds of corrections]
    ### Recommendation:
    [your suggestion on how to proceed]
```

---

## Validation System

### 🚨 Validation is Autonomous (Validator Agent Handles Everything)

**In the chain model, the Validator agent is fully autonomous:**
- It receives the implementer's report directly
- It validates against task requirements + screenshot (if visual)
- It sends corrections back to implementer (up to 3 rounds)
- It only reports to the orchestrator when task is DONE or ESCALATED

**The orchestrator does NOT validate.** The orchestrator does NOT read code.
The orchestrator receives ONLY the final summary from the Validator.

### How the Validation Chain Works

```
Implementer sends report → Validator
                              │
                              ├─ Issues found (round 1/3)?
                              │   └─ Send corrections → Implementer
                              │       └─ Implementer fixes → sends updated report → Validator
                              │           └─ Still issues (round 2/3)?
                              │               └─ Send corrections → Implementer
                              │                   └─ Implementer fixes → Validator
                              │                       └─ Still issues (round 3/3)?
                              │                           └─ ESCALATE → Orchestrator
                              │
                              └─ All correct?
                                  └─ Send success report → Orchestrator
```

### What Validator Must Check

The validator prompt MUST include instructions to verify:
- **All task requirements** — every requirement from the task is implemented
- **Code quality** — compiles, no debug code, follows patterns
- **Borders** on images/cards (Figma `bd` property)
- **Shadows** on buttons/containers (Figma `sh` property)
- **Exact colors** from Figma tokens
- **Icon presence** on buttons
- **Interactive elements** — functional (not just visual)
- **Element count** — buttons, badges on screenshot vs code (must match!)
- **No duplicates** — same action button NOT appearing twice
- **Role-appropriate UI** — no inappropriate elements for the user role
- **Email addresses** → mailto: links, phone numbers → tel: links
- **Functional filters/search** — work with at least mock data
- **Page title** — correct in layout header (not default fallback)
- **Navigation integration** — reachable from sidebar/menu
- **⚠️ Structural correctness** — code does NOT add tabs/modals/sections not in the design (CRITICAL)
- **⚠️ Layout width** — tab bars/headers span full width as in design

### Orchestrator's Role in Validation

The orchestrator's ONLY validation-related actions are:
1. **Receive Validator's report** — either success or escalation
2. **Report to user** — pass along the summary
3. **Route user feedback** — send fix instructions to Implementer
4. **Never read code** — trust the chain

---

## Common Mistakes System

### File Location

| File | Path | Who edits |
|------|------|-----------|
| **Common Mistakes** | `.claude/rules/common-mistakes.md` | Orchestrator updates directly when user reports mistakes |

### When to Update

After user reports a mistake in agent's work:
1. Fix the issue
2. Read the file to check if this rule already exists
3. If rule exists → add new example under existing rule
4. If rule is NEW → write full rule entry

### Entry Format

```markdown
## [Category]

### [General rule name]
[1-2 sentences: WHEN this rule applies and WHAT to do]
- Example: [specific incident that led to this rule]
- Example: [another incident of the same type]
```

Categories: Layout & Nesting, Colors, Typography, Spacing, Components, Text Content, Responsive, Page Integration, Element Duplication, Role-Inappropriate UI, Functional Completeness

### Agent Integration

ALL implementer and validator agents MUST read this file:
```
Read this file if it exists (known mistakes to avoid):
- .claude/rules/common-mistakes.md
```

### Maintenance

- No hard limit on entries — rules are general (not incidents), so count stays manageable
- If a rule has 5+ examples, older examples can be removed (rule stays)
