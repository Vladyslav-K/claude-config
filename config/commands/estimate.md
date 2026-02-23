---
name: estimate
description: Estimate frontend tasks from .project-meta/estimation/. Read task files, screenshots, and codebase to produce time estimates.
---

# Task Estimation

## Additional context from user before start task
$ARGUMENTS

## Purpose
Estimate frontend tasks by reading task files, analyzing screenshots/design documents, and researching the codebase.

**ONLY FRONTEND tasks are estimated.** Skip backend, DevOps, mobile native, database tasks.

## Input
`.project-meta/estimation/` directory:
- **Root:** Task lists (.md, .xlsx, .docx)
- **screenshots/:** Images and design documents

## Output
`.project-meta/estimation/estimation.md`

---

## Execution Steps

### 1. Scan Input Folder

```
1. Glob: .project-meta/estimation/*.{md,xlsx,docx}
2. Glob: .project-meta/estimation/screenshots/**/*
3. Group screenshots/design docs by task name (same matching rules as /tasks:plan)
4. Build map: { taskFile → [matched screenshot paths] }
```

If no task files found → inform user, stop.

### 2. Read Project Context
Read `.project-meta/memory/` files (if exist) for tech stack and patterns.

### 3. Read Task Files
- `.md` → Read directly
- `.xlsx` → Python + openpyxl
- `.docx` → Python + python-docx

### 4. Analyze Designs
For each task with design docs/screenshots:
1. Read design document (`*__design.md`) FIRST
2. Read screenshot for visual verification
3. Note: components, form fields, tables, charts, states, responsive hints

### 5. Research Codebase
Per task: find similar components, reuse potential, relevant libraries, hooks, types.

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
| Complex form validation | 1.2x - 1.3x |
| State management complexity | 1.2x - 1.4x |
| First-time patterns for project | 1.3x - 1.5x |

**Formula:** Base × Multipliers = Final (round to 0.5h, 1h, 2h, 4h, 6h, 8h, 12h, 16h, 24h, 32h)

### 7. Write estimation.md

```markdown
# Task Estimation

Generated: YYYY-MM-DD HH:MM
Source files: [list]

## Summary

| # | Task | Type | Opt | Avg | Pess | Notes |
|---|------|------|-----|-----|------|-------|
| 1 | [name] | [type] | Xh | Xh | Xh | |

Frontend tasks: X | Skipped (non-frontend): Y

**Totals:** Optimistic: XXh | Average: XXh | Pessimistic: XXh

---

## Detailed Estimates

### 1. [Task Name]
**Source:** [file] | **Type:** frontend
**Estimate:** Opt: Xh | Avg: Xh | Pess: Xh
**Reasoning:**
- Base: [task type] = [hours]
- Multipliers: [which and why]
- Reuse: [existing code]
- Risks: [what increases pessimistic]
**Codebase context:** [relevant files/patterns]

---

## Assumptions
## Risks
## Clarifications Needed
```

### 8. Write Back to xlsx (if applicable)
If original .xlsx has estimate columns (opt/min, avg/ave, pess/max) → write values back with openpyxl.

### 9. Report Summary
Total tasks, total hours (opt/avg/pess), clarifications needed.

---

## Error Handling

- **Unclear task:** Note "Needs clarification", use wider pessimistic range
- **No design docs:** Note "No visual reference", add 1.2x uncertainty
- **Unreadable file:** Report error, skip, continue
- **No codebase patterns:** Note "No codebase context", standard estimates

---

## Rules

1. **Estimate ONLY frontend tasks**
2. **Read project memory FIRST**
3. **Research codebase per task** — find reuse potential
4. **Use exact methodology** — base × multipliers, round properly
5. **Include reasoning for every estimate**
6. **Flag unclear tasks**
