---
name: estimate
description: Estimate frontend tasks from .project-meta/estimation/. Read task files, screenshots, and codebase to produce time estimates.
---

# Task Estimation

## Additional context from user before start task
$ARGUMENTS

## Purpose
Estimate frontend tasks by reading task files, analyzing screenshots/design documents, and researching the codebase for similar patterns.

**ONLY FRONTEND tasks are estimated.** Skip backend, DevOps, mobile native, database tasks. If a task has both frontend and backend parts, estimate ONLY the frontend portion.

## Input
`.project-meta/estimation/` directory containing:
- **Root files:** Task lists (.md, .xlsx, .docx)
- **screenshots/ folder:** Images and design documents related to tasks

## Output
`.project-meta/estimation/estimation.md` — estimation report

---

## Execution Steps

### 1. Scan Input Folder

```
1. Glob: .project-meta/estimation/*.{md,xlsx,docx} (root only)
2. Glob: .project-meta/estimation/screenshots/**/*
3. Group screenshots/design docs by task name:
   - Task "user-profile" matches:
     - screenshots/user-profile/ folder (all files inside)
     - screenshots/user-profile.png
     - screenshots/user-profile-*.png
     - screenshots/user-profile*__design.md
   - Folder contents override file name matching
   - `*__design.md` files are structured design specs from Figma
4. Build map: { taskFile → [matched screenshot paths] }
```

**If no task files found:** Inform user, stop.

### 2. Read Project Context

1. Read project memory files at `.project-meta/memory/` (if exists)
2. Get a high-level understanding of the project's tech stack and patterns

### 3. Read Task Files

- `.md` files: Read directly
- `.xlsx` files: Use Bash with Python + openpyxl:
  ```python
  from openpyxl import load_workbook
  wb = load_workbook('file.xlsx')
  for sheet_name in wb.sheetnames:
      ws = wb[sheet_name]
      for row in ws.iter_rows(values_only=True):
          print(row)
  ```
- `.docx` files: Use Bash with Python + python-docx

Extract individual tasks from each file.

### 4. Analyze Design Documents and Screenshots

For each task with design documents/screenshots:
1. Read design document (`*__design.md`) FIRST — structured specs
2. Read screenshot for visual verification
3. Note: UI components, form fields, interactive elements, tables, charts, states, responsive hints

### 5. Research Codebase

For each task, search for:
- Similar existing components or pages (reuse potential)
- Tech patterns (libraries for tables, forms, charts)
- Reusable hooks, utilities, types

Use Glob, Grep, or Explore agent to find relevant files. Read key files to understand complexity.

### 6. Estimate Each Task

#### Base Time Units

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

#### Multipliers

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

**Formula:** Base × Multipliers = Final (rounded to 0.5h, 1h, 2h, 4h, 6h, 8h, 12h, 16h, 24h, 32h)

### 7. Write estimation.md

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
**Source:** [file name]
**Type:** frontend
**Description:** [brief]
**Estimate:** Opt: Xh | Avg: Xh | Pess: Xh
**Reasoning:**
- Base: [task type] = [base hours]
- Multipliers: [which and why]
- Reuse: [existing code that reduces effort]
- Risks: [what increases pessimistic]
**Codebase context:**
- [relevant existing files/patterns found]
**Screenshots:** [paths analyzed, or "none"]

---

[...repeat for each task...]

## Assumptions
- [list]

## Risks
- [list]

## Clarifications Needed
- [task]: [question]
```

### 8. Write Back to xlsx (if applicable)

If original files were .xlsx and have estimate columns:
- Use Bash with Python + openpyxl
- Find estimate columns (opt/min, avg/ave, pess/max)
- Write values back

### 9. Report Summary

Report to user:
- Total tasks estimated
- Total hours (opt/avg/pess)
- Clarifications needed
- Reference: full details in estimation.md

---

## Error Handling

- **Unclear task:** Note "Needs clarification: [question]", use wider pessimistic range
- **No design doc or screenshots:** Note "No visual reference", add 1.2x uncertainty to pessimistic
- **Unreadable file format:** Report the error, skip that file, continue with others
- **No codebase patterns found:** Note "No codebase context", use standard estimates without reuse

---

## Rules

1. **Estimate ONLY frontend tasks** — skip backend, devops, mobile
2. **Read project memory FIRST** — understand project context
3. **Research codebase per task** — find similar patterns, reusable code
4. **Use exact methodology** — base units × multipliers, round properly
5. **Include reasoning for every estimate** — not just numbers
6. **Flag unclear tasks** — note what needs clarification
7. **Count ALL UI elements from design docs/screenshots** — don't miss interactive elements
8. **For .xlsx use openpyxl** — as per project rules

---

## Example

```
Task: User management table with search and filters
Base: Complex component = 8h avg
Multipliers:
  + Similar table exists (reuse) → 0.7x
  - More columns (8 vs 5) → 1.1x
  - Bulk actions (new) → 1.2x
Calc: 8h × 0.7 × 1.1 × 1.2 = 7.4h → 8h avg
Result: Opt 4h | Avg 8h | Pess 14h
```
