---
name: tasks-run
description: Execute tasks from .project-meta/tasks/tasks.md sequentially. Research, plan, implement, and verify each task yourself.
---

# Task Execution

## Additional context from user before start task
$ARGUMENTS

## Purpose
Execute tasks from `.project-meta/tasks/tasks.md` sequentially. Follow the general workflow from `.claude/rules/task-execution.md` for each task.

---

## Step 1: Read and Parse

Read tasks.md and status.md **IN PARALLEL** (two Read calls, one message):

```
From tasks.md: ID, Title, What, Deps, Type, Design/Screenshot paths
From status.md: current status per task
Merge → task list with statuses
Count: total, done, pending, blocked
```

## Step 2: Find Available Tasks

1. Find all tasks with status `pending`
2. Filter out tasks with unmet deps (deps not `done`)
3. Order by ID (lowest first)

## Step 3: Execute Tasks Sequentially

For EACH available task, follow the execution flow from `task-execution.md`:
1. Update status.md → `research`
2. **Research:** Read design docs, screenshots, codebase (per task-execution.md steps)
3. **Plan (visual/complex):** Present plan, wait for approval. Simple code tasks → skip
4. Update status.md → `running`
5. **Implement** → **Self-review** → **format-and-check**
6. Update status.md → `done`, update progress %, report to user

Then check for newly unblocked tasks → pick next → repeat.

**Continue even through autocompact** — status.md tracks progress on disk.

## Step 4: Final Summary

After ALL tasks:
1. Final format-and-check
2. Report: all tasks done, all files created/modified
3. If blocked tasks remain → create `.project-meta/tasks/blocked-report.md`

---

## status.md Updates

1. Find row by task ID → replace status
2. Update "Updated:" date (YYYY-MM-DD only, no time — use `currentDate` from session context)
3. Recalculate progress: `done_count/total (percentage%)`

**Status values:** `pending` → `research` → `running` → `done` / `blocked`

---

## blocked-report.md Format (only if needed)

```markdown
# Blocked Tasks Report
Generated: YYYY-MM-DD HH:mm

## Summary
- Total: N | Completed: X | Blocked: Y | Remaining: Z

## Blocked Tasks

### Task [ID]: Title
**Reason:** Why blocked
**Next steps:** What needs to happen to unblock
```

---

## Rules

1. **Execute SEQUENTIALLY** — one task at a time, fully complete before next
2. **Follow `task-execution.md`** for research/plan/implement/review cycle
3. **Update status.md after EACH state change**
4. **NEVER modify tasks.md** — read-only after planning
5. **Continue through autocompact** — status.md persists on disk
6. **When in doubt about complexity → present a plan**
