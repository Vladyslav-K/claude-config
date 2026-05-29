---
name: tasks-run
description: Execute the next available task from .project-meta/tasks/tasks.md, then enter testing/fixing mode. Does NOT continue to the next task.
disable-model-invocation: true
---

# Task Execution (Single Task Mode)

## Additional context from user before start task
$ARGUMENTS

## Purpose
Execute **exactly ONE task** from `.project-meta/tasks/tasks.md` — the next available one.
After completing the task — STOP, report, and enter **testing & fixing mode**. Do NOT proceed to the next task.

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

Follow the **Task Execution Cycle** (section below). Update status.md as you move through states:

1. Update status.md → `research`
2. **Research** (cycle step 1)
3. **Plan** (cycle step 2) — for visual/complex tasks present a plan and wait for approval; simple code tasks → skip
4. Update status.md → `running`
5. **Implement** (cycle step 3) → **Self-review** (cycle step 4) → **Verify** (cycle step 5)
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
> 🧪 Задача виконана. Тестуй результат — якщо є зауваження чи баги, пиши, виправлю. Коли буде все ок — запусти `/tasks-run` для наступної задачі.

---

## Task Execution Cycle

The research → plan → implement → review → verify cycle for a single task:

### 1. Research
- Read the task's full entry in tasks.md (What, Deps, Design, Existing Code to Reuse, Reference Implementation, API, New Code, Implementation Steps, Notes)
- Read matched design docs (`*__design.md`) **fully**; read screenshots for visual tasks
- Read the existing components/services/hooks the plan references — verify they exist and learn their API (props, signatures)
- Read 1-2 reference implementations to match the project's patterns
- Confirm API endpoints exist (swagger / existing code) — **never invent** endpoints, field names, or response shapes

### 2. Plan
- **Visual / complex tasks:** present a short implementation plan, then wait for approval before coding
- **Simple code tasks:** skip the plan and implement directly

### 3. Implement
- Follow THIS project's conventions exactly — file/folder structure, naming, styling approach
- Build per the Implementation Steps from tasks.md
- **Reuse existing components** — don't duplicate; if a variant is missing, extend the existing component, don't create a one-off
- **No raw components/icons inline** — components live in the components folder, icons as `.svg` in the icons folder
- **Visual tasks:** match the design pixel-perfect (layout, spacing, fonts, colors, element count); copy static text from the design **exactly** — don't rephrase or add elements/icons not in the design
- If a design references icons/images not present in the project → ASK the user for them, don't substitute "similar" ones

### 4. Self-review
- Re-check the result against the task requirements and design — every element present and correct
- No leftover TODOs, empty/placeholder handlers, disabled fields, or empty catch blocks (unless explicitly agreed with the user)
- Confirm every requirement of the task is fully met

### 5. Verify
- Run `format` (Prettier), then `check-errors` (lint + tsc) — with the **full, unmodified output** (no `tail`/`head`, no output-limiting flags)
- If `format` / `check-errors` don't exist but can be created → add them; if the project is too specific → use available equivalents (`prettier --write`, `eslint`, `tsc --noEmit`)
- Fix ALL issues until both pass clean — the task is not done while issues remain

---

## 🚨 CRITICAL: Single Task Mode Rules

1. **Execute EXACTLY ONE task** — do NOT continue to the next task after completion
2. **After the task is done — you are in TESTING & FIXING MODE:**
   - If the user reports issues → fix them immediately
   - If the user asks for changes → implement them
   - Run `format` then `check-errors` after every fix
   - Stay on this task until the user is satisfied
3. **NEVER auto-continue** to the next task — the user must explicitly run `/tasks-run` again
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
2. **Follow the Task Execution Cycle** (section above) for research/plan/implement/review/verify
3. **Update status.md after EACH state change**
4. **NEVER modify tasks.md** — read-only after planning
5. **NEVER proceed to the next task** — user must run the command again
6. **When in doubt about complexity → present a plan**
7. **NEVER skip the report step** — even for simple tasks
8. **Testing mode after completion** — user feedback → fix → re-verify
