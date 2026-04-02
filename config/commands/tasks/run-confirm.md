---
name: tasks-run-confirm
description: Execute tasks from .project-meta/tasks/tasks.md one by one, stopping after each for user testing and confirmation before proceeding.
---

# Task Execution (Confirm Mode)

## Additional context from user before start task
$ARGUMENTS

## Purpose
Execute tasks from `.project-meta/tasks/tasks.md` **one at a time with mandatory user confirmation** between tasks. Follow the general workflow from `.claude/rules/task-execution.md` for each task. After completing a task — STOP, report, provide testing instructions, and wait for explicit user confirmation before proceeding.

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

## Step 3: Execute ONE Task

For the NEXT available task, follow the execution flow from `task-execution.md`:
1. Update status.md → `research`
2. **Research:** Read design docs, screenshots, codebase (per task-execution.md steps)
3. **Plan (visual/complex):** Present plan, wait for approval. Simple code tasks → skip
4. Update status.md → `running`
5. **Implement** → **Self-review** → **format-and-check**
6. Update status.md → `done`, update progress %

## Step 4: Stop and Report (MANDATORY after each task)

**After completing the task, you MUST STOP and provide:**

### Completion Report
1. **Task ID and title** that was completed
2. **What was done** — brief summary of changes (files created/modified, key decisions)
3. **Files changed** — list all created/modified files with short descriptions

### Testing Instructions
4. **How to test** — step-by-step instructions for the user to verify the task:
   - What to run (dev server, specific URL, etc.)
   - What to check visually or functionally
   - Expected behavior
   - Edge cases worth testing

### Next Task Preview
5. **Next task** — show ID and title of the next available task (if any)
6. **Remaining** — how many tasks are left (pending/total)

### Waiting Message
End with:
> ⏸️ Чекаю на підтвердження. Перевір результат і дай команду переходити до наступної задачі. Якщо є зауваження — пиши, виправимо.

---

## 🚨 CRITICAL: Confirm Mode Rules

1. **STOP after EVERY task** — do NOT auto-continue to the next task
2. **WAIT for explicit user confirmation** — the user must say to proceed (e.g., "далі", "наступна", "continue", "next", "ок, йдемо далі")
3. **While waiting — you are in FIX MODE:**
   - If the user reports issues → fix them immediately
   - If the user asks for changes → implement them
   - Stay on the CURRENT task until user confirms it's done
   - Run format-and-check after every fix
4. **Only after confirmation** → go back to Step 2, find next available task, repeat
5. **Continue through autocompact** — status.md tracks progress on disk

---

## status.md Updates

1. Find row by task ID → replace status
2. Update "Updated:" timestamp
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

1. **ONE task at a time** — complete, report, STOP, wait for confirmation
2. **Follow `task-execution.md`** for research/plan/implement/review cycle
3. **Update status.md after EACH state change**
4. **NEVER modify tasks.md** — read-only after planning
5. **Continue through autocompact** — status.md persists on disk
6. **When in doubt about complexity → present a plan**
7. **NEVER skip the stop-and-report step** — even for simple tasks
8. **Fix mode between tasks** — user feedback → fix → re-verify → wait again
