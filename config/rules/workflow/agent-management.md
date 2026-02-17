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

### 🚨 Visual Task Workflow is NON-NEGOTIABLE

**For visual tasks (screenshots/Figma), ALL 3 agents are MANDATORY:**

1. **Analyzer** — reads screenshot + Figma JSON, produces detailed specs
2. **Implementer** — builds using analyzer's output + code patterns
3. **Validator** — fresh eyes comparison of result vs design

**You CANNOT skip any of these agents.** If you skip:
- Analyzer → implementer will miss borders, shadows, gradients, exact colors
- Validator → critical mismatches will ship (buttons, tabs, spacing, borders)

**This has been violated multiple times.** Analyzer and validator agents were
not spawned, orchestrator did analysis and validation itself. Result: duplicate
buttons, missing links, broken filters, wrong page titles. NEVER repeat this.

### 🚫 ORCHESTRATOR PROHIBITION (HARD RULE)

**The orchestrator (main chat) is FORBIDDEN from:**

1. **Reading screenshots and writing analysis** — this is analyzer agent's job
2. **Comparing code to design and saying "looks correct"** — this is validator agent's job
3. **Claiming validation without a validator agent_id** — this is FAKE validation

**Why:** When the orchestrator does these roles itself, it has CONFIRMATION BIAS.
It subconsciously looks for "it's fine" instead of finding actual problems.
This is why 2 Quote buttons, non-functional filters, and missing mailto links
all "passed validation" — because no independent agent actually checked.

**The orchestrator's ONLY jobs are:**
- Orchestrate: decide what agents to spawn, in what order
- Relay: pass analyzer output to implementer, implementer output to validator
- Decide: based on validator report, what to fix and how
- Verify: run format-and-check

### 🔒 MANDATORY GATE SYSTEM

**Gates are HARD STOPS that prevent skipping steps. You MUST pass each gate before proceeding.**

```
═══════════════════════════════════════════════════════
GATE 1: BEFORE spawning implementer
═══════════════════════════════════════════════════════
REQUIRED PROOF: Analyzer agent was spawned and returned analysis.
- Analyzer agent name: [must exist, e.g., "analyzer"]
- Analyzer output received: [YES — paste first 3 lines as proof]

WITHOUT THIS PROOF → you CANNOT spawn the implementer.
If you find yourself writing "I'll analyze the screenshot..." → STOP.
That is the analyzer agent's job. Spawn it.
═══════════════════════════════════════════════════════

═══════════════════════════════════════════════════════
GATE 2: BEFORE saying task is done
═══════════════════════════════════════════════════════
REQUIRED PROOF: Validator agent was spawned and returned a report.
- Validator agent name: [must exist, e.g., "validator"]
- Validator issues found: [number from validator's report]
- All issues fixed: [YES/NO — if NO, list remaining]

WITHOUT THIS PROOF → task is NOT done.
If you find yourself writing "I compared the code to the screenshot..." → STOP.
That is the validator agent's job. Spawn it.
═══════════════════════════════════════════════════════
```

**What counts as "passing" a gate:**
- ✅ You have an actual agent name and received a message from it
- ❌ You "analyzed it yourself" — this is NOT passing the gate
- ❌ You "checked the code" — this is NOT passing the gate
- ❌ You have no agent name to reference — gate FAILED

---

## Agent Templates

### Research: Simple Lookup (Explore)

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

### Research: Deep Analysis (general-purpose)

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

### Analyzer Agent (VISUAL TASKS ONLY)

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

    ### 6. Interactive Elements Detection
    For EVERY element, determine if it should be interactive:
    - Text styled differently (color, underline) → likely a LINK (mailto:, href, etc.)
    - Buttons with labels → what should they DO? (navigate, open modal, submit?)
    - Dropdown-looking elements → should they OPEN a dropdown?
    - Filter/search elements → should they FILTER data?
    - List what action each interactive element should perform.

    ### 7. Element Uniqueness Check
    Count how many times each type of element appears:
    - How many action buttons? List each with exact label and location.
    - Are there duplicates that shouldn't exist?
    - Are there elements that DON'T belong on this page/role?
      (e.g., notification bell for admin, settings for guest user)

    ### 8. Page Integration Points
    Identify how this page connects to the rest of the app:
    - What should the page TITLE be in the layout header?
    - Should this page appear in the sidebar navigation?
    - What breadcrumbs or back-navigation should exist?
    - Are there links TO other pages or FROM other pages?

    Send your complete analysis to the team lead when done.
```

### Visual Implementer (screenshots/Figma)

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

    ## KNOWN MISTAKES (read this file if it exists)
    - .claude/rules/common-mistakes.md (known mistakes from past implementations)
    Read it and avoid ALL listed mistakes.

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
    - NEVER duplicate action buttons — count buttons on screenshot,
      count in your code, numbers MUST match
    - NEVER add role-inappropriate elements — if building admin page,
      do NOT add notification bells, user-specific elements, etc.
      unless explicitly shown in the design
    - ALWAYS make interactive-looking elements functional:
      * Email text styled as link → MUST be <a href="mailto:...">
      * Filter dropdowns → MUST open and filter data
      * Search inputs → MUST search with debounce
      * Tab switches → MUST switch content
      If you can't make it functional, add TODO comment explaining why

    ## NEW PAGE INTEGRATION (MANDATORY for new pages/routes)
    When creating a NEW page, you MUST integrate it with the existing app:
    1. Find how page titles work (header mapping, metadata, etc.)
       → Add this page's title to the mapping
    2. Find how sidebar navigation works
       → Add this page's link if it should be in sidebar
    3. Find how routing/breadcrumbs work
       → Configure properly for this page
    4. Check what layout wraps this page
       → Ensure it uses the correct layout group
    DO NOT just create the page content — the page must WORK within the app.

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
    - Page integration: what systems were updated (titles, sidebar, routing)
```

### Code Implementer (no design)

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
    2. Read common mistakes file if it exists:
       - .claude/rules/common-mistakes.md
    3. Find SIMILAR existing code in the project and use as template
    4. If creating a NEW PAGE/ROUTE:
       a. Find how page titles work → add this page to the title system
       b. Find how sidebar navigation works → add link if needed
       c. Find how routing/breadcrumbs work → configure properly
    5. Implement the task following existing patterns exactly
    6. If creating interactive UI elements (filters, search, dropdowns):
       → They MUST work, at least with mock data
       → Static non-functional elements are NOT acceptable
    7. If displaying email addresses → use <a href="mailto:...">
    8. Re-read your created/modified files to verify
    9. Run format-and-check (or format, lint, typecheck), fix issues

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
    - Page integration: what systems were updated (titles, sidebar, routing)
```

**For parallel tasks:** Spawn multiple agents in a SINGLE message (parallel Task tool calls).

### Validator Agent (VISUAL TASKS ONLY)

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

    ## KNOWN MISTAKES (read this file if it exists)
    - .claude/rules/common-mistakes.md (known mistakes from past implementations)
    Pay special attention — these are REAL mistakes from previous work.

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

    ### Duplicate & Role Check (CRITICAL):
    - Count EVERY button on the screenshot. Count every button in the code.
      Do the numbers match? If code has MORE buttons → REPORT as critical issue.
    - Are there UI elements that don't belong to this user role?
      (e.g., notification bell on admin page, user avatar on guest page)
    - Are there elements duplicated across different sections that should
      appear only ONCE? (e.g., same action button in header AND in content)

    ### Interactive Elements Check (CRITICAL):
    - Is email text rendered as a clickable mailto: link? (not plain text)
    - Do filter dropdowns actually open and filter data?
    - Does search input actually search?
    - Do tabs actually switch content?
    - Do "View" links actually navigate somewhere?
    - For EACH interactive element: is it functional or just visual?
      If just visual with no onClick/href → REPORT as issue.

    ### Page Integration Check:
    - Does the page have a correct title in the layout header?
      (not "Page" or other default fallback)
    - Is the page accessible from sidebar navigation if it should be?
    - Do back buttons navigate to the correct parent page?

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

---

## Validation System

### 🚨 CRITICAL: Validation is NOT Optional

**The previous implementation of Sourcing Requests feature had ZERO real validation.
Orchestrator claimed "validated ✅" without spawning validator agent or reading output files.
Result: 9/10 visual elements were wrong. This section exists to PREVENT that.**

### How Validation Works

**Visual tasks:** Validator AGENT does the detailed comparison (see Validator Agent template above). Orchestrator reviews the validator's report and decides on fixes. **If no validator agent was spawned, the task is NOT validated.**

**Code tasks:** Orchestrator reads the output files and validates directly.

### Orchestrator Validation (code tasks)

1. **Read created/modified files** — understand what agent produced (ACTUALLY READ THEM, don't skip)
2. **Compare with task requirements** — are ALL listed requirements implemented?
3. **Check code patterns** — does agent use correct project conventions?
4. **Run format-and-check** — catch lint/type errors

### Orchestrator Validation (visual tasks) — GATE ENFORCEMENT

**The orchestrator CANNOT validate visual tasks itself. It MUST use the GATE system.**

```
═══════════════════════════════════════════════════════
GATE CHECK (visual task validation):
═══════════════════════════════════════════════════════

1. Analyzer agent name: _________ (MUST be filled)
   → If blank: SPAWN analyzer NOW. Do not proceed.

2. Implementer received analyzer output: YES/NO
   → If NO: Re-spawn implementer WITH analyzer output.

3. Validator agent name: _________ (MUST be filled)
   → If blank: SPAWN validator NOW. Do not proceed.

4. Validator issues count: _________ (number from report)
   → If you don't have a number: you don't have a report.
     SPAWN validator NOW.

ALL 4 fields MUST be filled before task is marked done.
The orchestrator saying "I checked and it looks fine" is
NOT acceptable and does NOT pass this gate.
═══════════════════════════════════════════════════════
```

**After gate passes, review the validator's report:**

1. **Read validator's report** — review each ❌ issue
2. **Prioritize fixes** — critical structure issues first, then styling
3. **Decide action:**
   - ⚠️ Minor (1-3 fixes) → Fix yourself
   - 🔄 Moderate (4+) → Send corrections to implementer
   - If many issues → re-run validator after fixes

### Validator Agent Must Check (in addition to visual comparison)

The validator prompt MUST include instructions to verify:
- **Borders** on all images and cards (check Figma `bd` property)
- **Shadows** on buttons and containers (check Figma `sh` property)
- **Exact colors** from Figma tokens (not approximations)
- **Icon presence** on buttons (+ icons, arrow icons, etc.)
- **Data binding** — are all visible data fields actually connected to real data?
- **Interactive elements** — do tabs/buttons/links actually function?
- **Element count** — count buttons, icons, badges on screenshot vs code (must match!)
- **No duplicates** — same action button should NOT appear twice on the page
- **Role-appropriate UI** — admin pages should NOT have user-specific elements (notifications, etc.)
- **Links for emails** — email addresses MUST be mailto: links, not plain text
- **Functional filters** — filter dropdowns MUST open and filter, not just be static buttons
- **Page title** — does the page show correct title in layout header? (not default "Page")
- **Navigation integration** — is the page reachable from sidebar/menu?

### Validation Decision Tree

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
