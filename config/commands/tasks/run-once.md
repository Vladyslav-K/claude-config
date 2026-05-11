---
name: tasks-run-once
description: Execute the next available task from .project-meta/tasks/tasks.md, then enter testing/fixing mode. Does NOT continue to the next task.
---

# Task Execution (Single Task Mode)

## Additional context from user before start task
$ARGUMENTS

## Purpose
Execute **exactly ONE task** from `.project-meta/tasks/tasks.md` — the next available one. Follow the general workflow from `.claude/rules/task-execution.md`. After completing the task — STOP, report, and enter **testing & fixing mode**. Do NOT proceed to the next task.

---

## Step 1: Read and Parse

Read tasks.md and status.md **IN PARALLEL** (two Read calls, one message):

```
From tasks.md: ID, Title, What, Deps, Type, Design/Screenshot paths
From status.md: current status per task
Merge → task list with statuses
Count: total, done, pending, blocked
```

## Step 2: Find Next Available Task

1. Find all tasks with status `pending`
2. Filter out tasks with unmet deps (deps not `done`)
3. Order by ID (lowest first)
4. **Pick the FIRST available task** — this is the only task you will execute

If no tasks are available → report to user and stop.

## Step 3: Execute the Task

For the selected task, follow the execution flow from `task-execution.md`:
1. Update status.md → `research`
2. **Research:** Read design docs, screenshots, codebase (per task-execution.md steps)
3. **Plan (visual/complex):** Present plan, wait for approval. Simple code tasks → skip
4. Update status.md → `running`
5. **Implement** → **Self-review** → **format-and-check**
6. Update status.md → `done`, update progress %

## Step 4: Report and Enter Testing Mode (MANDATORY)

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

### Status
5. **Progress** — how many tasks are done out of total (done/total)

### Testing Mode Message
End with:
> 🧪 Задача виконана. Тестуй результат — якщо є зауваження чи баги, пиши, виправлю. Коли буде все ок — запусти `/tasks:run-once` для наступної задачі.

---

## 🚨 CRITICAL: Single Task Mode Rules

1. **Execute EXACTLY ONE task** — do NOT continue to the next task after completion
2. **After the task is done — you are in TESTING & FIXING MODE:**
   - If the user reports issues → fix them immediately
   - If the user asks for changes → implement them
   - Run format-and-check after every fix
   - Stay on this task until the user is satisfied
3. **NEVER auto-continue** to the next task — the user must explicitly run `/tasks:run-once` again
4. **This command = one task cycle.** Each invocation handles one task, period.

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

1. **ONE task per invocation** — complete it, report, enter testing mode, DONE
2. **Follow `task-execution.md`** for research/plan/implement/review cycle
3. **Update status.md after EACH state change**
4. **NEVER modify tasks.md** — read-only after planning
5. **NEVER proceed to the next task** — user must run the command again
6. **When in doubt about complexity → present a plan**
7. **NEVER skip the report step** — even for simple tasks
8. **Testing mode after completion** — user feedback → fix → re-verify
