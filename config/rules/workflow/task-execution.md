# Task Execution Workflow

**Single-context, sequential execution. You ARE the implementer.**

---

## Overview

You research, plan, build, and self-review ALL tasks directly. No delegation to sub-agents for implementation.

**The only agent you use:** `Explore` (via Task tool with `subagent_type: "Explore"`) — for file search, grep, finding files across the codebase. But you READ the found files and MAKE DECISIONS yourself.

---

## Research Tools

| Tool | When to use |
|------|-------------|
| Glob/Grep | You know roughly where to look (specific path, pattern) |
| Explore agent | Broad search, finding files by pattern, codebase exploration |
| Read | After finding files — always read and analyze yourself |

**Rule:** Explore finds files. You read them. You decide.

---

## Task Complexity Levels

### Simple (1 file, ≤50 lines, pattern known)
→ Just do it → format-and-check

### Standard (multi-file, known patterns)
→ Brief research → implement → self-review → format-and-check

### Complex (new features, design specs, unknown territory)
→ Research → present plan to user → wait for approval → implement → self-review → format-and-check

---

## Execution Flow

### Step 1: Understand the Task
- Read all provided materials (design docs, screenshots, task descriptions)
- Follow reading order: design document → screenshot → task description

### Step 2: Research the Codebase
- Read project memory if `.project-meta/memory/` exists
- Use Explore agent or Glob/Grep to find relevant files
- Read and understand existing components, patterns, similar pages
- Catalog what can be reused

### Step 3: Plan (Complex Tasks)

For complex tasks, present a plan to the user:

```
## Research Plan

### Design Elements Found
[List ALL UI elements from design with specs]

### Existing Components to Reuse
[Component → path → purpose]

### New Code to Create
[File path → what it does]

### Layout Already Provides
[What NOT to duplicate]
```

Wait for user approval before proceeding.

### Step 4: Implement
- Build section by section
- Use existing components — never recreate what exists
- Match design exactly (pixel-perfect for visual tasks)
- Only build what the design shows

### Step 5: Self-Review
- Re-read design document/screenshot
- Verify every element from plan is implemented
- Check for additions not in design → remove
- Check for omissions from design → add

### Step 6: Verify
- Run format-and-check (or format, lint, typecheck)
- Fix ALL issues
- Report completed files to user

---

## Sequential Multi-Task Execution

When executing multiple tasks (e.g., via /tasks:run):

1. **Parse task list** — read tasks.md and status.md
2. **Find available tasks** — respect dependencies, order by ID
3. **Execute ONE task at a time:**
   - Research → plan (if complex) → user approves → implement → verify
   - Update status.md after each task
4. **Move to next task** — even through autocompact, continue the sequence
5. **After ALL tasks done** — run format-and-check once more, report to user

### Dependency Handling
- Skip tasks whose dependencies aren't met
- After completing a task, check if new tasks are unblocked
- If a task is blocked and can't proceed, mark as blocked and move on

---

## Context Window Management

**Your context is limited. Be strategic:**

- Use Explore agent for broad codebase searches (saves your context)
- Read only files you actually need
- Don't read entire directories — target specific files
- After implementing, you don't need to keep file contents in context
- Trust your work — don't re-read files you just wrote unless debugging

---

## User Feedback Loop

When user reports issues:
1. Read the relevant file(s)
2. Re-read the design if visual task
3. Fix the issues
4. Run format-and-check
5. Report what was fixed

---

## Pre-Planning Verification

### API Existence Check (MANDATORY)

If the user provides only screenshots/designs WITHOUT API documentation:

1. **STOP** — Do NOT create API types, services, or hooks
2. **ASK the user:** "Is there a backend API? What are the endpoints?"
3. If no API → implement only UI with mock data
4. **NEVER invent** endpoint URLs, field names, or response structures from screenshots

---

## Communication Style

**Medium detail.** User should understand WHAT you're doing.

✅ "Досліджую проект → покажу план → після ОК кодю → перевірю"
❌ "Роблю" (too brief)
❌ Long descriptions of every step (too verbose)

---

## Examples

### Simple Task
```
User: "Fix the typo in Button label"
1. Read the file
2. Fix the typo
3. Run format-and-check
```

### Standard Task
```
User: "Add a new button variant"
1. Find existing button component (Glob/Read)
2. Understand current variants
3. Add new variant following existing pattern
4. Update usages
5. Run format-and-check
```

### Complex Visual Task
```
User: "Create this page" + screenshot + design document
1. Read design document → read screenshot
2. Research project: components, patterns, layout
3. Extract ALL design elements
4. Present plan to user:
   "Знайшов CustomSelect, Flag, DataTable.
    Колонки: Request ID, Product, Volume, Destination, User, Type, Created.
    Створю page.tsx в app/(dashboard)/requests/.
    Затверджуєш?"
5. User: "Ок"
6. Implement section by section
7. Self-review against design
8. Run format-and-check
9. Report: "Створено /app/(dashboard)/requests/page.tsx"
```

### Multi-Task Execution
```
/tasks:run
1. Read tasks.md → 4 tasks, deps: 3→1, 4→2,3
2. Execute Task 1 (no deps): research → plan → approve → build → verify
3. Execute Task 2 (no deps): research → plan → approve → build → verify
4. Execute Task 3 (dep on 1 ✅): research → plan → approve → build → verify
5. Execute Task 4 (deps on 2✅, 3✅): research → plan → approve → build → verify
6. Final format-and-check → report all
```
