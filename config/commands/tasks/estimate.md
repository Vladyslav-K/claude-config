---
name: tasks-estimate
description: Estimate frontend tasks from .project-meta/tasks/estimation/. Reads task files (xlsx/md), analyzes screenshots, researches codebase, and provides optimistic/average/pessimistic estimates.
---

# Task Estimation

## Additional context from user before start task
$ARGUMENTS

## Purpose
Analyze frontend tasks from estimation folder, review associated screenshots and designs, research existing codebase, and provide time estimates in optimistic/average/pessimistic format.

## IMPORTANT: Scope Limitation
**You ONLY estimate FRONTEND tasks.** Skip any tasks related to:
- Backend API development
- Database migrations/schemas
- DevOps/infrastructure
- Mobile native development
- Any non-frontend work

If a task has both frontend and backend parts, estimate ONLY the frontend portion.

## Input Location
`.project-meta/tasks/estimation/` directory containing:
- **Root files:** Task lists in `.xlsx` or `.md` format with columns for estimates
- **screenshots/ folder:** Images or folders with images related to tasks

## Output
- Updated task files with filled estimates (optimistic/average/pessimistic or min/ave/max)
- Comments explaining estimate reasoning where needed

## Execution Steps

### Step 1: Read Estimation Files (YOU do this)

**Read ALL files in `.project-meta/tasks/estimation/` root:**
```
1. Use Glob to find all files in estimation root (not recursive)
2. Read each .xlsx or .md file
3. Identify:
   - Task names/IDs
   - Task descriptions
   - Requirements/acceptance criteria
   - Estimate columns to fill (may be: opt/avg/pess, min/ave/max, best/likely/worst)
4. Filter out non-frontend tasks
```

**CRITICAL:** Read files yourself, don't delegate. You need full understanding of scope.

### Step 2: Scan Screenshots (YOU do this)

**Read screenshots for visual context:**
```
1. Use Glob to find all files in .project-meta/tasks/estimation/screenshots/
2. Group screenshots by task (folder name or file prefix matches task name/ID)
3. Read each screenshot relevant to frontend tasks
4. Note UI complexity, components needed, interactions visible
```

**Screenshot matching rules:**
- If task is "user-profile", look for:
  - `screenshots/user-profile/` folder (read ALL files inside)
  - `screenshots/user-profile.png` file
  - `screenshots/user-profile-*.png` files
- Folder contents override file name matching

### Step 3: Research Codebase (DELEGATE to codebase-searcher)

**If you are in a project directory, delegate research:**

```
Task tool:
  subagent_type: "codebase-searcher"
  prompt: |
    ## PROJECT MEMORY (READ FIRST)
    If exists: .project-meta/memory/ - read for project context.

    ## RESEARCH FOR ESTIMATION
    I need to estimate these frontend tasks:
    [LIST FRONTEND TASKS HERE]

    ## FIND FOR EACH TASK
    1. Does similar component/feature already exist?
    2. What existing components can be reused?
    3. What patterns are used in this project?
    4. What's the complexity of similar existing features?
    5. Are there any custom implementations vs library usage?

    ## RETURN FORMAT
    For each task:
    - Existing similar code: [paths and brief description]
    - Reusable components: [list]
    - Estimated complexity vs existing features: [comparison]
    - Technical considerations: [any complexity factors]
```

**Run multiple codebase-searcher agents in parallel** if tasks cover different areas.

### Step 4: Estimate Each Task (YOU do this)

For EACH frontend task:

```
1. Review task description and requirements
2. Review associated screenshots
3. Consider codebase research findings:
   - Existing components to reuse → reduces estimate
   - New patterns to implement → increases estimate
   - Similar existing features → use as baseline
4. Calculate estimates in hours:
   - Optimistic: Everything goes smoothly, can reuse existing code
   - Average: Normal development pace, some minor issues
   - Pessimistic: Complex edge cases, integration issues, revisions
```

### Step 5: Fill Estimates (YOU do this)

**Update the estimation file(s):**
- For .xlsx files: Use openpyxl to write estimates
- For .md files: Edit directly

**Include brief reasoning** where the task is complex or estimate is high.

### Step 6: Summary Report

Provide summary to user:
```
## Estimation Summary

Total frontend tasks: X
Skipped (non-frontend): Y

| Task | Opt | Avg | Pess | Notes |
|------|-----|-----|------|-------|
| ... | ... | ... | ... | ... |

Total estimates:
- Optimistic: XX hours
- Average: XX hours
- Pessimistic: XX hours

Assumptions made:
- [list key assumptions]

Risks identified:
- [list estimation risks]
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

Apply these multipliers based on factors:

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
Base estimate × Multipliers = Final estimate

Example:
- Complex component (8h avg)
- New design patterns needed (1.4x)
- Responsive complexity (1.2x)
- Final: 8h × 1.4 × 1.2 = 13.4h → round to 14h average
```

## Important Rules

1. **ONLY estimate frontend tasks** — skip backend, devops, mobile native
2. **Read task files yourself** — don't delegate task reading
3. **Read screenshots yourself** — visual context is critical for UI estimates
4. **Use codebase-searcher for research** — to understand what exists
5. **For .xlsx use openpyxl** — as specified in global rules
6. **Round estimates** — to reasonable numbers (0.5h, 1h, 2h, 4h, 8h, etc.)
7. **Document assumptions** — especially for high estimates
8. **Consider project patterns** — existing code affects estimates significantly
9. **Include buffer** — pessimistic should account for unknowns
10. **Don't over-optimize** — optimistic shouldn't assume perfect conditions

## Screenshot Analysis Checklist

When reviewing screenshots, note:

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
+ Similar table exists (can reuse pattern) → 0.7x
+ Existing filter components → already factored
- More columns than existing (8 vs 5) → 1.1x
- Bulk actions (new feature) → 1.2x
- Row actions dropdown (exists) → 1.0x

Calculation:
8h × 0.7 × 1.1 × 1.2 = 7.4h → 8h average

Estimates:
- Optimistic: 4h (heavy reuse, no issues)
- Average: 8h (normal pace)
- Pessimistic: 14h (edge cases, revisions)
```

## Handling Different File Formats

### .xlsx Files

```python
# Use openpyxl to read and write
from openpyxl import load_workbook

wb = load_workbook('tasks.xlsx')
ws = wb.active

# Find estimate columns (may vary)
# Look for: opt/min, avg/ave, pess/max, etc.

# Write estimates to appropriate cells
ws['D2'] = 4  # Optimistic
ws['E2'] = 8  # Average
ws['F2'] = 14  # Pessimistic

wb.save('tasks.xlsx')
```

### .md Files (Table Format)

```markdown
| Task | Description | Opt | Avg | Pess | Notes |
|------|-------------|-----|-----|------|-------|
| User table | CRUD table for users | 4h | 8h | 14h | Reuse products-table pattern |
```

## Error Handling

**If task description is unclear:**
- Note in estimates: "Needs clarification: [specific question]"
- Provide range with wider pessimistic

**If no screenshots for a task:**
- Note: "No visual reference provided"
- Base estimate on description only
- Add 1.2x uncertainty multiplier to pessimistic

**If codebase research unavailable:**
- Note: "No codebase context"
- Use standard estimates without reuse benefits

## Output Example

```
## Estimation Complete

Analyzed: .project-meta/tasks/estimation/sprint-14.xlsx

### Summary

| # | Task | Type | Opt | Avg | Pess |
|---|------|------|-----|-----|------|
| 1 | User management table | Component | 4h | 8h | 14h |
| 2 | Dashboard charts | Feature | 6h | 12h | 20h |
| 3 | Profile settings page | Page | 3h | 6h | 10h |
| -- | API /users endpoint | Backend | - | - | - |

Frontend tasks: 3
Skipped (backend): 1

### Totals

| Estimate | Hours |
|----------|-------|
| Optimistic | 13h |
| Average | 26h |
| Pessimistic | 44h |

### Key Assumptions
1. Existing table pattern can be fully reused
2. Chart library already installed (recharts)
3. Profile form similar to existing settings forms

### Risks
1. Dashboard charts may need custom tooltips
2. User table bulk actions not done before in this project
```
