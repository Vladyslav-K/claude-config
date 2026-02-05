---
name: tasks-estimate-small
description: Quick estimation for a small batch of tasks (1-5 tasks of any size) from .project-meta/tasks/estimation-small/. Reads .md files, analyzes codebase, creates estimation.md with detailed reasoning.
---

# Quick Task Estimation (Small Batch)

## Additional context from user before start task
$ARGUMENTS

## Purpose
Estimate a small batch of tasks (typically 1-5 tasks, but can be of any complexity/size). This is a lightweight flow for quick estimations without the full ceremony of the main estimation process. Tasks can range from simple fixes to complex features.

## IMPORTANT: Scope Limitation
**You ONLY estimate FRONTEND tasks.** Skip any tasks related to:
- Backend API development
- Database migrations/schemas
- DevOps/infrastructure
- Mobile native development
- Any non-frontend work

If a task has both frontend and backend parts, estimate ONLY the frontend portion.

## Input Location
`.project-meta/tasks/estimation-small/` directory containing:
- One or more `.md` files with task descriptions (tasks can be of any size/complexity)

## Output
- Create `.project-meta/tasks/estimation-small/estimation.md` with:
  - Task list with estimates (optimistic/average/pessimistic)
  - Detailed reasoning for each estimate
  - Summary with totals

## Execution Steps

### Step 1: Read Task Files (YOU do this)

**Read ALL .md files in `.project-meta/tasks/estimation-small/`:**
```
1. Use Glob to find all .md files in estimation-small folder
2. Read each file
3. Identify:
   - Task names/descriptions
   - Requirements/acceptance criteria
   - Any screenshots or design references mentioned
4. Filter out non-frontend tasks
```

**CRITICAL:** Read files yourself, don't delegate. You need full understanding of scope.

### Step 2: Research Codebase (DELEGATE to Explore agent)

**Delegate research to understand what already exists:**

```
Task tool:
  subagent_type: "Explore"
  description: "Research codebase for estimation"
  prompt: |
    ## PROJECT MEMORY (READ FIRST)
    If exists: .project-meta/memory/ - read for project context.

    ## RESEARCH FOR ESTIMATION
    I need to estimate these frontend tasks:
    [LIST FRONTEND TASKS HERE]

    ## THINK DEEPLY ABOUT:
    - What exact files and patterns are relevant to each task?
    - What is the real complexity based on existing codebase?
    - Are there reusable components that reduce effort?

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

**Use `"very thorough"` thoroughness** for comprehensive analysis.

### Step 3: Estimate Each Task (YOU do this)

For EACH frontend task:

```
1. Review task description and requirements
2. Consider codebase research findings:
   - Existing components to reuse → reduces estimate
   - New patterns to implement → increases estimate
   - Similar existing features → use as baseline
3. Calculate estimates in hours:
   - Optimistic: Everything goes smoothly, can reuse existing code
   - Average: Normal development pace, some minor issues
   - Pessimistic: Complex edge cases, integration issues, revisions
4. Write detailed reasoning explaining WHY this estimate
```

### Step 4: Create estimation.md (YOU do this)

**Create `.project-meta/tasks/estimation-small/estimation.md`** with this structure:

```markdown
# Task Estimation

Generated: [YYYY-MM-DD HH:MM]

## Summary

| # | Task | Opt | Avg | Pess |
|---|------|-----|-----|------|
| 1 | [Task name] | Xh | Xh | Xh |
| ... | ... | ... | ... | ... |

**Totals:**
- Optimistic: XX hours
- Average: XX hours
- Pessimistic: XX hours

---

## Detailed Estimates

### 1. [Task Name]

**Description:** [Brief task description]

**Estimate:** Opt: Xh | Avg: Xh | Pess: Xh

**Reasoning:**
- [Why this estimate]
- [What components can be reused]
- [What new things need to be built]
- [Risk factors that increase pessimistic estimate]

**Codebase context:**
- [Relevant existing files/patterns]
- [Reusable components found]

---

### 2. [Next Task]
...

---

## Assumptions
1. [List key assumptions that affect estimates]

## Risks
1. [List factors that could increase actual time]

## Notes
- [Any additional context or clarifications needed]
```

### Step 5: Report to User

After creating estimation.md, provide brief summary:
```
## Estimation Complete ✓

Created: .project-meta/tasks/estimation-small/estimation.md

### Quick Summary

| Task | Opt | Avg | Pess |
|------|-----|-----|------|
| ... | ... | ... | ... |

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
| Complex form validation | 1.2x - 1.3x |
| First-time patterns for project | 1.3x - 1.5x |

## Important Rules

1. **ONLY estimate frontend tasks** — skip backend, devops, mobile native
2. **Read task files yourself** — don't delegate task reading
3. **Use Explore agent for research** — to understand what exists
4. **Write detailed reasoning** — explain WHY for each estimate
5. **Round estimates** — to reasonable numbers (0.5h, 1h, 2h, 4h, 8h, etc.)
6. **Document assumptions** — especially for high estimates
7. **Consider project patterns** — existing code affects estimates significantly
8. **Include buffer** — pessimistic should account for unknowns

## Error Handling

**If task description is unclear:**
- Note in reasoning: "Needs clarification: [specific question]"
- Provide range with wider pessimistic

**If codebase research unavailable:**
- Note: "No codebase context available"
- Use standard estimates without reuse benefits

**If no tasks found:**
- Inform user that no .md files found in estimation-small folder
- Ask them to add task files
