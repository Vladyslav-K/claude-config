---
name: tasks-plan-full
description: Deep task planning with full codebase research, API analysis, component inventory, and blocker detection. Produces a detailed implementation plan.
---

# Task Planning (Full)

## Additional context from user before start task
$ARGUMENTS

**How to use arguments:**
- `/tasks:plan-full` — full deep analysis of all tasks
- `/tasks:plan-full focus only on tasks 1-3` — limit scope
- `/tasks:plan-full we use REST API at /api/v1, auth is JWT` — provide context
- `/tasks:plan-full skip API research, backend is not ready yet` — adjust behavior

## Purpose
Read task descriptions from `.project-meta/tasks/plan/`, perform **deep codebase research**, and create a comprehensive implementation plan with detailed analysis of each task — existing components, API endpoints, dependencies, blockers, and step-by-step implementation guidance.

**KEY PRINCIPLE:** This is the THOROUGH planning mode. You research EVERYTHING now so that `/tasks:run` can execute with full context and minimal surprises.

## Input

**Task files:** `.project-meta/tasks/plan/*.md`
**Design docs/screenshots:** `.project-meta/tasks/plan/screenshots/`

**Matching rules (screenshots -> tasks):**
- Task "user-profile" matches:
  - `screenshots/user-profile/` folder (all files inside)
  - `screenshots/user-profile.png`, `screenshots/user-profile-*.png`
  - `screenshots/user-profile*__design.md`
- Folder contents override file name matching
- One file can relate to multiple tasks

## Output

```
.project-meta/tasks/
├── tasks.md          # Detailed task plan
└── status.md         # Status tracking
```

---

## Execution Steps

### 1. Read ALL Task Files
Read every .md file from `.project-meta/tasks/plan/` root. Understand the full scope.

### 2. List and Analyze Screenshots
Glob `.project-meta/tasks/plan/screenshots/**/*` -> group by task name.
For screenshots: list them but DON'T read images at this stage.
For design docs (`*__design.md`): **READ them fully** — extract every UI element, field, action, state.

### 3. Deep Codebase Research (MANDATORY)

Use Explore agents and direct reads to research the project:

#### 3a. Project Structure
- Identify framework, key directories, routing patterns
- Find package.json / config files — understand available libraries
- Identify state management, styling approach, API layer patterns

#### 3b. Existing Components Inventory
For each task that involves UI:
- Search for existing components that can be reused (forms, tables, modals, buttons, layouts)
- Read their API — props, variants, slots
- Note exact import paths
- Identify shared layouts, wrappers, providers that new pages must use

#### 3c. API Research
- Search for existing API services, hooks, types in the codebase
- Find API base URL configuration, auth headers setup
- If swagger/openapi spec exists — read it
- Map which endpoints already exist vs which are needed
- If NO API docs and tasks require API:
  1. **ASK:** "What are the API endpoints for these tasks? Or should I plan with mock data?"
  2. **WAIT for answer** before proceeding
  3. **NEVER invent** endpoint URLs, field names, or response structures

#### 3d. Patterns and Conventions
- Find 2-3 similar existing pages/features as reference
- Note the patterns: how pages are structured, how forms are built, how tables work
- Identify validation patterns, error handling, loading states
- Check i18n setup and existing translations structure

### 4. Blocker Analysis (MANDATORY)

For EACH task, check:
- **Missing API:** endpoints not found and not documented -> BLOCKER
- **Missing components:** UI requires components that don't exist and aren't in the design system -> NOTE
- **Missing designs:** task references screens that have no screenshot/design doc -> BLOCKER
- **Unclear requirements:** ambiguous descriptions with multiple interpretations -> BLOCKER (list specific questions)
- **Technical blockers:** missing dependencies, incompatible library versions, unimplemented auth -> BLOCKER
- **Missing translations:** i18n keys needed but translation files not set up -> NOTE

### 5. Build Detailed Task Plan

For EACH task, compile:

1. **What** — clear description of what needs to be built (from source + your research)
2. **Dependencies** — which tasks must be completed first and why
3. **Type** — visual / code / mixed
4. **Design refs** — matched screenshots and design docs
5. **Existing code to reuse** — specific components with import paths, existing hooks/services, utility functions
6. **Reference implementations** — similar existing pages/features to follow as patterns (with file paths)
7. **API endpoints** — exact endpoints needed (from swagger/existing code/user input), request/response structure
8. **New code to create** — list of new files with purpose:
   - New pages/routes
   - New components (if existing ones don't cover it)
   - New API services/hooks
   - New types/interfaces
9. **Implementation steps** — ordered list of concrete steps to build this task
10. **Blockers** — anything that prevents implementation (if any)
11. **Notes** — edge cases, gotchas, things to watch out for
12. **Estimated complexity** — simple / standard / complex (based on research)

### 6. Determine Task Order
- Tasks with no deps first
- Then by dependency chain
- Within same priority — simpler tasks first (build foundations before complex features)
- Group related tasks when it makes sense

### 7. Write tasks.md + status.md
Write both files with the detailed format below.

### 8. Show Comprehensive Summary

Report to user:
- Source files analyzed
- Codebase areas researched
- Design references matched
- Tasks created (with complexity breakdown)
- Blockers found (if any) — **highlight these prominently**
- Questions for user (if any)
- Recommended execution order explanation

---

## tasks.md Format (Full)

```markdown
# Tasks

Goal: Overall goal
Sources: file1.md, file2.md
Created: YYYY-MM-DD
Mode: full-analysis

---

## Task 1: Short title
- **What:** Detailed description of what needs to be built
- **Deps:** none
- **Type:** visual
- **Complexity:** standard
- **Design:** screenshots/list__design.md
- **Screenshots:** screenshots/list.png

### Existing Code to Reuse
- `src/components/ui/data-table.tsx` — base table component with sorting/pagination
- `src/hooks/use-pagination.ts` — pagination state management
- `src/services/api-client.ts` — configured axios instance

### Reference Implementation
- `src/app/(dashboard)/users/page.tsx` — similar list page, follow this pattern
- `src/app/(dashboard)/users/components/users-table.tsx` — table structure reference

### API
- `GET /api/v1/items` — list with pagination (params: page, limit, search)
- `DELETE /api/v1/items/:id` — delete single item
- Response: `{ data: Item[], meta: { total, page, limit } }`

### New Code
- `src/app/(dashboard)/items/page.tsx` — main list page (Server Component)
- `src/app/(dashboard)/items/components/items-table.tsx` — table with columns from design
- `src/types/item.ts` — Item interface
- `src/services/items.ts` — API service functions
- `src/hooks/use-items.ts` — React Query hook

### Implementation Steps
1. Create Item type from API response structure
2. Create API service with list/delete functions
3. Create React Query hook wrapping the service
4. Build table component following users-table pattern
5. Create page component with search + table
6. Add route to navigation (if needed)
7. Test all interactive states

### Blockers
- None

### Notes
- Design shows a "bulk delete" button — need to check if API supports bulk operations
- Table has 6 columns — verify all fit on standard viewport

---

## Task 2: Another title
- **What:** Detailed description
- **Deps:** 1 (needs Item type from Task 1)
- **Type:** mixed
- **Complexity:** complex

...
```

## status.md Format

```markdown
# Tasks Status
Updated: YYYY-MM-DD

## Progress: 0/N (0%)

| # | Task | Type | Complexity | Status | Blocker |
|---|------|------|------------|--------|---------|
| 1 | Task title | visual | standard | pending | |
| 2 | Another task | mixed | complex | pending | Missing API docs for /reports |
```

**Status values:** `pending` -> `research` -> `running` -> `done` / `blocked`

---

## Rules

1. **Research DEEPLY** — read existing code, understand patterns, find reusable pieces
2. **DO NOT delete files from plan/** — user manages them
3. **Every claim must be verified** — don't say "component exists" without finding it via Glob/Grep
4. **Include exact file paths** — every referenced component/service must have its real path
5. **One task per logical unit** — don't combine unrelated changes
6. **Verify API exists** before planning API tasks — if not found, mark as BLOCKER
7. **Highlight ALL blockers prominently** — user must see them immediately
8. **Use Explore agents for broad searches** — save context for analysis
9. **$ARGUMENTS from user are MANDATORY instructions** — apply them to the planning process
10. **Ask questions if ambiguous** — better to ask than to guess wrong
