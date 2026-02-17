---
name: estimate
description: Estimate frontend tasks from .project-meta/estimation/. Reads task files (md/xlsx/docx), analyzes screenshots, researches codebase via agents, and provides optimistic/average/pessimistic estimates. Delegates task reading to agents to save main context.
---

# Task Estimation

## Additional context from user before start task
$ARGUMENTS

## Purpose
Analyze frontend tasks from estimation folder, review associated screenshots and designs, research existing codebase, and provide time estimates in optimistic/average/pessimistic format. Task file reading is delegated to agents to preserve main context window.

## IMPORTANT: Scope Limitation
**You ONLY estimate FRONTEND tasks.** Skip any tasks related to:
- Backend API development
- Database migrations/schemas
- DevOps/infrastructure
- Mobile native development
- Any non-frontend work

If a task has both frontend and backend parts, estimate ONLY the frontend portion.

## Input Location
`.project-meta/estimation/` directory containing:
- **Root files:** Task lists in any format (`.md`, `.xlsx`, `.docx`)
- **screenshots/ folder:** Images or folders with images related to tasks

## Output
`.project-meta/estimation/estimation.md` — unified estimation report with:
- Summary table of all tasks with estimates
- Detailed reasoning for each estimate
- Totals, assumptions, and risks

## Execution Steps

### Step 1: Scan Input Folder (YOU do this — lightweight)

**Only scan file names and structure. DO NOT read file contents — agents will do this.**

```
1. Use Glob to find all files in .project-meta/estimation/ root (not recursive)
2. Use Glob to find all files in .project-meta/estimation/screenshots/
   (recursive — check for subfolders named by task)
3. Group screenshots by task:
   - If task is "user-profile", look for:
     - screenshots/user-profile/ folder (all files inside)
     - screenshots/user-profile.png file
     - screenshots/user-profile-*.png files
   - Folder contents override file name matching
4. Count files, note file types (.md, .xlsx, .docx)
5. Build a map: { taskFile → [matched screenshots] }
```

**If no task files found:** Inform user that no files found in `.project-meta/estimation/`, ask them to add task files, and stop.

### Step 2: Research Codebase (DELEGATE to Explore agent)

**Delegate lightweight codebase research:**

```
Task tool:
  subagent_type: "Explore"
  description: "Research codebase for estimation"
  prompt: |
    ## PROJECT MEMORY (READ FIRST)
    If exists: .project-meta/memory/ - read for project context.

    ## RESEARCH FOR ESTIMATION
    I need to estimate frontend tasks. Research the codebase to find:
    1. Existing components and their complexity
    2. Code patterns used in the project
    3. Technology stack details
    4. Reusable components that could reduce effort
    5. Similar existing features and their scope

    ## THINK DEEPLY ABOUT:
    - What exact files and patterns are relevant?
    - What is the real complexity based on existing codebase?
    - Are there reusable components that reduce effort?

    ## RETURN FORMAT
    - List of reusable components with paths
    - Technology patterns observed
    - Complexity indicators for different feature types
    - Any custom implementations vs library usage
```

### Step 3: Create Team and Spawn Estimator Agents (YOU do this)

**Create estimation team:**
```
TeamCreate:
  team_name: "estimation"
  description: "Estimating tasks from .project-meta/estimation/"
```

**Distribution strategy:**
- 1-2 task files → 1 estimator agent handles all
- 3-5 task files → 2 agents, split evenly
- 6+ task files → 3+ agents, split evenly
- If any single file is very large (xlsx with many sheets/rows) → give it its own agent

**CRITICAL: NEVER specify `model` param. Omit it — agent inherits current chat model.**

**Estimator agent prompt template:**
```
Task tool:
  subagent_type: "general-purpose"
  team_name: "estimation"
  name: "estimator-{N}"
  mode: "bypassPermissions"
  run_in_background: true
  prompt: |
    You are an estimation agent. Your job is to READ task files, analyze them,
    and provide time estimates for each frontend task.

    ## IMPORTANT: Scope Limitation
    You ONLY estimate FRONTEND tasks. Skip any tasks related to:
    - Backend API development
    - Database migrations/schemas
    - DevOps/infrastructure
    - Mobile native development
    If a task has both frontend and backend, estimate ONLY the frontend portion.

    ## FILES TO READ
    [List of absolute file paths for this agent to read]

    ## SCREENSHOTS TO ANALYZE
    [List of absolute screenshot paths matched to tasks]

    ## CODEBASE CONTEXT (from research)
    [Paste research results from Explore agent]

    ## PROJECT CONTEXT
    Working directory: {CWD}
    Memory: {CWD}/.project-meta/memory/ (read if exists)

    ## HOW TO READ FILES
    - .md files: Read directly with Read tool
    - .xlsx files: Use Bash with Python + openpyxl to read contents
    - .docx files: Use Bash with Python + python-docx to read contents
    - Screenshots: Read with Read tool (it handles images)

    ## ESTIMATION GUIDELINES

    ### Base Time Units
    | Task Type | Opt | Avg | Pess |
    |-----------|-----|-----|------|
    | Simple UI component (button, input) | 1h | 2h | 4h |
    | Medium component (card, form field) | 2h | 4h | 6h |
    | Complex component (data table, chart) | 4h | 8h | 16h |
    | Simple page (static, few components) | 2h | 4h | 8h |
    | Medium page (forms, interactions) | 4h | 8h | 16h |
    | Complex page (dashboard, many features) | 8h | 16h | 32h |
    | Simple feature (toggle, filter) | 1h | 2h | 4h |
    | Medium feature (search, pagination) | 2h | 4h | 8h |
    | Complex feature (real-time, complex state) | 4h | 8h | 16h |

    ### Multipliers
    | Factor | Multiplier |
    |--------|------------|
    | Existing similar code to reuse | 0.5x - 0.7x |
    | New design system components needed | 1.3x - 1.5x |
    | Complex animations/transitions | 1.2x - 1.5x |
    | Accessibility requirements (WCAG) | 1.2x - 1.3x |
    | Responsive design complexity | 1.1x - 1.3x |
    | Integration with complex API | 1.2x - 1.4x |
    | Real-time updates (WebSocket) | 1.3x - 1.5x |
    | Internationalization (i18n) | 1.1x - 1.2x |
    | Complex form validation | 1.2x - 1.3x |
    | State management complexity | 1.2x - 1.4x |
    | First-time patterns for project | 1.3x - 1.5x |

    ### Formula
    Base estimate x Multipliers = Final estimate
    Round to: 0.5h, 1h, 2h, 4h, 6h, 8h, 12h, 16h, 24h, 32h

    ## SCREENSHOT ANALYSIS
    When screenshots exist for a task, note:
    - Number of unique UI components visible
    - Form fields and validation indicators
    - Interactive elements (buttons, dropdowns, modals)
    - Data tables or lists
    - Charts or visualizations
    - Navigation complexity
    - State variations shown (loading, error, empty)

    ## OUTPUT FORMAT (follow exactly)
    Return a structured estimation for each task:

    ### [Task Name/ID]
    **Source:** [file name]
    **Type:** [frontend / skipped (reason)]
    **Description:** [brief description]
    **Estimate:** Opt: Xh | Avg: Xh | Pess: Xh
    **Reasoning:**
    - [base type and base hours]
    - [multipliers applied and why]
    - [reusable components that reduce effort]
    - [risks that increase pessimistic]
    **Codebase context:**
    - [relevant existing files/patterns]

    ## ERROR HANDLING
    - If task description is unclear: note "Needs clarification: [question]", use wider pessimistic
    - If no screenshots for a task: note "No visual reference", base on description only
    - If file format unreadable: report the error, skip that file

    ## WHEN DONE
    Send your complete estimation results to the team lead.
```

### Step 4: Collect Results and Create estimation.md (YOU do this)

After all agents complete, collect their results and create the unified output file at `.project-meta/estimation/estimation.md`:

```markdown
# Task Estimation

Generated: [YYYY-MM-DD HH:MM]
Source files: [list of input files]

## Summary

| # | Task | Type | Opt | Avg | Pess | Notes |
|---|------|------|-----|-----|------|-------|
| 1 | [name] | Component | Xh | Xh | Xh | |
| ... | ... | ... | ... | ... | ... | ... |

Frontend tasks: X
Skipped (non-frontend): Y

**Totals:**
- Optimistic: XX hours
- Average: XX hours
- Pessimistic: XX hours

---

## Detailed Estimates

### 1. [Task Name]
**Source:** [file]
**Description:** [brief]
**Estimate:** Opt: Xh | Avg: Xh | Pess: Xh
**Reasoning:**
- [from agent]
**Codebase context:**
- [from agent]

---

[...repeat for all tasks...]

## Assumptions
1. [collected from agents]

## Risks
1. [collected from agents]
```

### Step 5: Update Source Files (if xlsx)

If original files were `.xlsx` and had estimate columns to fill:
- Use openpyxl (via Bash + Python) to write estimates back to the xlsx file
- Identify estimate columns (may be: opt/avg/pess, min/ave/max, best/likely/worst)
- Keep `estimation.md` as the primary output regardless

### Step 6: Shutdown Team

```
SendMessage type: "shutdown_request" to each estimator agent
Then: TeamDelete
```

### Step 7: Report Summary to User

Provide brief summary:
```
## Estimation Complete

Created: .project-meta/estimation/estimation.md

### Summary

| # | Task | Opt | Avg | Pess |
|---|------|-----|-----|------|
| ... | ... | ... | ... | ... |

**Totals:** Opt: XXh | Avg: XXh | Pess: XXh

Full details with reasoning in estimation.md
```

## Estimation Guidelines

### Base Time Units

| Task Type | Opt | Avg | Pess |
|-----------|-----|-----|------|
| Simple UI component (button, input) | 1h | 2h | 4h |
| Medium component (card, form field) | 2h | 4h | 6h |
| Complex component (data table, chart) | 4h | 8h | 16h |
| Simple page (static, few components) | 2h | 4h | 8h |
| Medium page (forms, interactions) | 4h | 8h | 16h |
| Complex page (dashboard, many features) | 8h | 16h | 32h |
| Simple feature (toggle, filter) | 1h | 2h | 4h |
| Medium feature (search, pagination) | 2h | 4h | 8h |
| Complex feature (real-time, complex state) | 4h | 8h | 16h |

### Multipliers

| Factor | Multiplier |
|--------|------------|
| Existing similar code to reuse | 0.5x - 0.7x |
| New design system components needed | 1.3x - 1.5x |
| Complex animations/transitions | 1.2x - 1.5x |
| Accessibility requirements (WCAG) | 1.2x - 1.3x |
| Responsive design complexity | 1.1x - 1.3x |
| Integration with complex API | 1.2x - 1.4x |
| Real-time updates (WebSocket) | 1.3x - 1.5x |
| Internationalization (i18n) | 1.1x - 1.2x |
| Complex form validation | 1.2x - 1.3x |
| State management complexity | 1.2x - 1.4x |
| First-time patterns for project | 1.3x - 1.5x |

### Estimation Formula

```
Base estimate x Multipliers = Final estimate

Example:
- Complex component (8h avg)
- New design patterns needed (1.4x)
- Responsive complexity (1.2x)
- Final: 8h x 1.4 x 1.2 = 13.4h -> round to 14h average

Estimates:
- Optimistic: 4h (heavy reuse, no issues)
- Average: 14h (normal pace with multipliers)
- Pessimistic: 24h (edge cases, revisions)
```

## Screenshot Analysis Checklist

When reviewing screenshots (handled by estimator agents), note:

```
[ ] Number of unique UI components visible
[ ] Form fields and validation indicators
[ ] Interactive elements (buttons, dropdowns, modals)
[ ] Data tables or lists
[ ] Charts or visualizations
[ ] Navigation complexity
[ ] Responsive breakpoint hints
[ ] Animation/transition indicators
[ ] State variations shown (loading, error, empty)
[ ] Accessibility requirements visible
```

## Handling Different File Formats

### .xlsx Files
```python
# Agents use openpyxl to read
from openpyxl import load_workbook

wb = load_workbook('tasks.xlsx')
ws = wb.active

# Find estimate columns (may vary)
# Look for: opt/min, avg/ave, pess/max, etc.
```

### .md Files
Read directly with the Read tool.

### .docx Files
```python
# Agents use python-docx to read
from docx import Document

doc = Document('tasks.docx')
for para in doc.paragraphs:
    print(para.text)

# Also check tables
for table in doc.tables:
    for row in table.rows:
        for cell in row.cells:
            print(cell.text)
```

## Important Rules

1. **ONLY estimate frontend tasks** — skip backend, devops, mobile native
2. **NEVER read task file contents yourself** — delegate to estimator agents
3. **Use Explore agent for codebase research** — to understand what exists
4. **NEVER specify `model` param for agents** — omit it, inherits current chat model
5. **For .xlsx use openpyxl** — as specified in global rules
6. **Round estimates** — to reasonable numbers (0.5h, 1h, 2h, 4h, 6h, 8h, 12h, 16h, 24h, 32h)
7. **Document assumptions and risks** — collected from agent results
8. **ALWAYS create estimation.md** — primary output at `.project-meta/estimation/estimation.md`
9. **ALWAYS use TeamCreate** before spawning estimator agents
10. **Shutdown team after completion** — send shutdown requests, then TeamDelete

## Error Handling

**If no task files found:**
- Inform user that no files found in `.project-meta/estimation/`
- Ask them to add task files (.md, .xlsx, or .docx)
- Stop execution

**If task description is unclear:**
- Agent notes: "Needs clarification: [specific question]"
- Provide range with wider pessimistic estimate

**If no screenshots for a task:**
- Agent notes: "No visual reference provided"
- Base estimate on description only
- Add 1.2x uncertainty multiplier to pessimistic

**If codebase research unavailable:**
- Note: "No codebase context available"
- Use standard estimates without reuse benefits

**If file format is unreadable:**
- Agent reports the error
- Continue with other readable files

## Example Task Estimation

**Task:** Create user management table with search, filters, and bulk actions

**Screenshots show:**
- Data table with 8 columns
- Search input
- 3 filter dropdowns
- Bulk selection checkbox
- Pagination
- Row actions dropdown

**Codebase research:**
- Similar product table exists at src/components/products-table
- Uses Tanstack Table
- Has existing filter components

**Estimation:**
```
Base: Complex component = 8h average

Analysis:
+ Similar table exists (can reuse pattern) -> 0.7x
+ Existing filter components -> already factored
- More columns than existing (8 vs 5) -> 1.1x
- Bulk actions (new feature) -> 1.2x
- Row actions dropdown (exists) -> 1.0x

Calculation:
8h x 0.7 x 1.1 x 1.2 = 7.4h -> 8h average

Estimates:
- Optimistic: 4h (heavy reuse, no issues)
- Average: 8h (normal pace)
- Pessimistic: 14h (edge cases, revisions)
```
