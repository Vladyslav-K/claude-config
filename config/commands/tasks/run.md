---
name: tasks-run
description: Execute tasks from .project-meta/tasks/tasks.md sequentially. Research, plan, implement, and verify each task yourself.
---

# Task Execution

## Additional context from user before start task
$ARGUMENTS

## Purpose
Execute tasks from `.project-meta/tasks/tasks.md` sequentially. You research, plan, implement, and verify each task yourself in a single context.

---

## Execution Steps

### 1. Read and Parse

Read tasks.md and status.md **IN PARALLEL** (two Read calls, one message):

```
From tasks.md extract per task:
  - ID, Title
  - What (description)
  - Deps
  - Type (code/visual)
  - Design document paths (*__design.md)
  - Screenshot paths

From status.md:
  - Current status per task

Merge → list of tasks with statuses
Count: total, done, pending, blocked
```

### 2. Find Available Tasks

```
1. Find all tasks with status "pending"
2. Filter out tasks with unmet deps (deps not "done")
3. Order by ID (lowest first)
```

### 3. Execute Tasks Sequentially

For EACH available task, in order:

#### Phase 1: Research

1. Update status.md: task → `research`
2. Read ALL design documents (`*__design.md`) for this task
3. Read ALL screenshots for this task
4. Research codebase — find existing components, patterns, similar pages
5. Read project memory if `.project-meta/memory/` exists

For **visual tasks**, extract ALL design elements:
- Every section: elements, text, dimensions, colors
- Tables: column headers, cell formats, variations
- Interactive elements: types, states
- Badges/tags: colors, text, border-radius

#### Phase 2: Present Plan (for visual/complex tasks)

Present research plan to user:

```
## Task {N}: {title} — Research Plan

### Design Elements
[ALL UI elements with specs]

### Existing Components to Reuse
[Component → path → purpose]

### New Code to Create
[File → purpose]

### Layout Provides
[What NOT to duplicate]
```

**Wait for user approval.** If user requests changes, revise and present again.

For **simple code tasks** (no design, known pattern), skip plan and implement directly.

#### Phase 3: Implement

1. Update status.md: task → `running`
2. Build following the approved plan
3. Use existing components — never recreate
4. Match design exactly (pixel-perfect for visual tasks)
5. Only build what the design shows

#### Phase 4: Self-Review

1. Re-read design document/screenshot
2. Verify every planned element is implemented
3. Check: nothing added that's not in design, nothing missing that is

#### Phase 5: Verify & Update Status

1. Run format-and-check → fix ALL issues
2. Update status.md: task → `done`
3. Update progress percentage and timestamp
4. Report to user: task title + created/modified files

### 4. Continue to Next Task

After completing a task:
1. Check for newly unblocked tasks (deps now met)
2. Pick the next available task (lowest ID first)
3. Repeat Phase 1-5

**Continue even through autocompact** — the task list and status.md persist on disk.

### 5. Final Summary

After ALL tasks complete:
1. Run format-and-check one final time
2. Report full summary to user: all tasks done, all files created/modified
3. If any tasks blocked → create `.project-meta/tasks/blocked-report.md`

---

## status.md Updates

When updating:
1. Find row by task ID
2. Replace status value
3. Update "Updated:" timestamp
4. Recalculate progress: `done_count/total (percentage%)`

**Status values:** `pending` → `research` → `running` → `done` / `blocked`

---

## blocked-report.md Format (only if needed)

```markdown
# Blocked Tasks Report
Generated: YYYY-MM-DD HH:mm

## Summary
- Total: N tasks
- Completed: X
- Blocked: Y
- Remaining: Z

## Blocked Tasks

### Task [ID]: Title
**Status:** blocked
**Reason:** Why blocked
**Next steps:** What needs to happen to unblock

## Tasks Waiting on Blocked

| # | Task | Waiting for |
|---|------|-------------|
| 5 | Task title | Task 3 (blocked) |
```

---

## Important Rules

1. **Execute tasks SEQUENTIALLY** — one at a time, fully complete before next
2. **YOU do all research and implementation** — no agent delegation
3. **Use Explore agent only for file search** — you read files and decide
4. **Present plan for visual/complex tasks** — get user approval first
5. **Simple code tasks can skip planning** — implement directly
6. **Run format-and-check after EACH task**
7. **Update status.md after EACH state change**
8. **Continue through autocompact** — status.md tracks progress on disk
9. **NEVER modify tasks.md** — read-only after planning
10. **When in doubt about task complexity → present a plan**

---

## Example Execution Flow

```
Reading task index... (tasks.md + status.md in parallel)
Found 4 tasks: 0 done, 4 pending

Dependency analysis:
├─ Available now: Tasks #1, #2 (no deps)
├─ Waiting: Task #3 (deps: 1)
└─ Waiting: Task #4 (deps: 2, 3)

═══ Task #1: List Page ═══
status.md: #1 → research

[Read design doc, screenshot, research codebase]

"Task 1 (List Page) — план:
  Знайшов DataTable, Badge, AnimatedTabs.
  Колонки: ID, Product, Volume, User, Type, Created.
  Створю page.tsx в app/(dashboard)/list/.
  Затверджуєш?"

User: "Ок"

status.md: #1 → running
[Implement section by section]
[Self-review against design]
[format-and-check → fix issues]

status.md: #1 → done
Progress: 1/4 (25%)

"Task 1 готова. Створено: app/(dashboard)/list/page.tsx"

═══ Task #2: Detail Page ═══
[Same flow...]

═══ Task #3: Shared Components (dep on #1 ✅) ═══
[Now unblocked, same flow...]

═══ Task #4: Integration (deps on #2 ✅, #3 ✅) ═══
[Now unblocked, same flow...]

═══ Final ═══
format-and-check → ✅
Summary: 4/4 completed, 0 blocked
```

---

## Quick Reference

| Field | Format | Example |
|-------|--------|---------|
| Header | `## Task N: Title` | `## Task 3: List page` |
| What | `- What: description` | `- What: Create list page with table and filters` |
| Deps | `- Deps: N, M` or `none` | `- Deps: 1, 2` |
| Type | `- Type: code/visual` | `- Type: visual` |
| Design | `- Design: path` | `- Design: screenshots/list__design.md` |
| Screenshots | `- Screenshots: path` | `- Screenshots: screenshots/list.png` |
