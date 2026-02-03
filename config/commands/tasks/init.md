---
name: tasks-init
description: Initialize task management system from files in .project-meta/tasks/init/. Creates tasks.md with full context and status.md for tracking.
---

# Task Initialization

## Additional context from user before start task
$ARGUMENTS

## Purpose
Read task description files from `.project-meta/tasks/init/`, analyze them, and create a structured task management system using Markdown format for better readability and token efficiency.

## Input
Files or folders with files in `.project-meta/tasks/init/` directory (usually .md files with free-form task descriptions)

## Output
- `.project-meta/tasks/tasks.md` — Markdown file with full task context (READ ONLY after creation)
- `.project-meta/tasks/status.md` — human-readable status table (will be updated during execution)

## Execution Steps

**CRITICAL: Follow the delegation workflow to save tokens and extend session length.**

### Step 1: Read Init Files (YOU do this)
Read all files from `.project-meta/tasks/init/` yourself using Read tool.

### Step 2: Analyze Content (YOU do this)
Extract individual tasks from free-form descriptions:
- Unique ID (sequential number)
- Short title
- Files that will be created/modified
- Dependencies on other tasks

### Step 3: Research Codebase (DELEGATE to codebase-searcher)

**Delegate research to `codebase-searcher` agent:**
```
Task tool:
  subagent_type: "codebase-searcher"
  prompt: |
    ## PROJECT MEMORY (READ FIRST)
    If exists: .project-meta/memory/ - read for project context.

    ## RESEARCH TASK
    Find patterns and code examples for these tasks:
    [LIST TASKS HERE]

    ## WHAT TO RETURN
    1. FULL CODE of similar components (not summaries)
    2. Exact import paths used in this project
    3. Type/interface definitions
    4. Code style patterns
    5. Actual file paths
```

**Run multiple codebase-searcher agents in parallel** if researching different areas.

### Step 4: Create Files (DELEGATE to frontend-worker)

**Delegate file creation to `frontend-worker` agent:**
```
Task tool:
  subagent_type: "frontend-worker"
  prompt: |
    ## PROJECT MEMORY (READ FIRST)
    If exists: .project-meta/memory/ - read for project context.

    ## TASK
    Create task management files for this project.

    ## FILES TO CREATE
    1. .project-meta/tasks/tasks.md - task definitions
    2. .project-meta/tasks/status.md - status tracking

    ## TASKS DATA
    [PASTE ANALYZED TASKS WITH RESEARCH CONTEXT]

    ## FORMAT REQUIREMENTS
    [PASTE FORMAT FROM THIS SKILL]

    ## POST-TASK
    Verify files were created correctly.
```

### Step 5: Verify (YOU do this - CRITICAL)

**⚠️ You MUST read the created files! Don't assume agent did it right!**

**After frontend-worker completes:**
1. **READ tasks.md** using Read tool (don't skip!)
   - Is the format correct? (headers, separators, metadata fields)
   - Are ALL tasks from init files included?
   - Does EACH task have full Context section?
   - Do Context sections include actual code patterns from research?

2. **READ status.md** using Read tool
   - Are all tasks listed in the table?
   - Are all statuses set to `pending`?
   - Is the format correct?

3. **If ANY issues found:**
   - Document SPECIFICALLY what's wrong
   - Re-delegate fix to frontend-worker with exact corrections
   - Re-verify after fix

**Don't proceed until YOU verified both files are correct!**

### Step 6: Show Summary
Report to user what was created.

## tasks.md Format

```markdown
# Tasks Plan

Goal: Overall goal from analyzed files
Sources: file1.md, file2.md
Created: YYYY-MM-DD

---

## Task 1: Short title
- Files: path/to/file.tsx, path/to/other.tsx
- Deps: none

### Context

FULL context including:
- What to do and why
- Technical details
- Code patterns to follow (actual code examples)
- Files to reference
- Step-by-step instructions

Example code from codebase:
```tsx
// actual code here without escaping
function Component({ prop }: Props) {
  return <div>{prop}</div>;
}
```

CODE STYLE:
- Use 'function' keyword for components
- Use spaces, semicolons, single quotes
- Use Tailwind CSS

WHAT NOT TO DO:
- Don't add unnecessary comments
- Don't create test files

---

## Task 2: Another task title
- Files: path/to/new.tsx
- Deps: 1

### Context

Full context for this task...

---
```

## Field Descriptions

- **Task N: Title** — unique ID and short title for display
- **Files** — comma-separated list of files to create/modify
- **Deps** — comma-separated task IDs that must complete first, or "none"
- **Context** — FULL context needed to execute task (you will only see this section when executing)

## Parsing Rules (for tasks-run)

1. Split file by `---` separators
2. Find task blocks starting with `## Task N:`
3. Extract metadata from `- Files:`, `- Deps:` lines
4. Everything after `### Context` until next `---` is the context

## status.md Format

```markdown
# Tasks Status
Updated: YYYY-MM-DD HH:mm

## Progress: 0/N (0%)

| # | Task | Status | Blocker |
|---|------|--------|---------|
| 1 | Task title | pending | |
| 2 | Task title | pending | |
```

**Status values:**
- `pending` — not started
- `running` — in progress
- `done` — completed
- `blocked` — cannot proceed (blocker field explains why)

## Context Section Guidelines

The Context section is CRITICAL — you will only see this when executing. Include:

1. **ACTION**: What operation (CREATE NEW FILE / MODIFY FILE / DELETE)
2. **PURPOSE**: Why this task is needed
3. **CURRENT CODE**: If modifying, show relevant existing code
4. **EXPECTED RESULT**: What the final code should do/look like
5. **CODE PATTERNS**: Real examples from the codebase (copy-paste actual code)
6. **CODE STYLE**: Specific rules for this project
7. **WHAT NOT TO DO**: Explicit prohibitions

Example Context structure:
```
CREATE NEW FILE: src/components/user-card.tsx

PURPOSE: Create reusable card component for displaying user info in admin dashboard.

EXISTING PATTERN (from src/components/product-card.tsx):
```tsx
import { Card, CardContent, CardHeader } from '@/components/ui/card';

interface ProductCardProps {
  product: Product;
}

function ProductCard({ product }: ProductCardProps) {
  return (
    <Card className="w-full">
      <CardHeader>{product.name}</CardHeader>
      <CardContent>{product.description}</CardContent>
    </Card>
  );
}

export { ProductCard };
```

CREATE THIS COMPONENT:
- Similar structure to ProductCard
- Props: user: User, onClick?: () => void
- Display: avatar, name, email, role badge
- Use existing Avatar and Badge components

IMPORTS TO USE:
- Card from '@/components/ui/card'
- Avatar from '@/components/ui/avatar'
- Badge from '@/components/ui/badge'
- User type from '@/types/user'

CODE STYLE:
- Use 'function' keyword
- Use Tailwind for styling
- Wrap onClick in useCallback if provided

WHAT NOT TO DO:
- Don't create new types, use existing User
- Don't add hover effects unless specified
- Don't add edit/delete buttons
```

## Important Rules

1. **DO NOT delete files from init/** — user manages them manually
2. **Include FULL context in Context section** — frontend-worker won't see conversation history
3. **DELEGATE research to codebase-searcher** — include actual code examples, not descriptions
4. **DELEGATE file creation to frontend-worker** — saves tokens
5. **VERIFY created files yourself** — read and check format/content
6. **Use exact file paths** — absolute or relative from project root
7. **One task per logical unit** — don't combine unrelated changes
8. **Order by dependencies** — tasks with no deps should come first
9. **Run agents in parallel when possible** — research for different areas simultaneously

## Example Output Summary

```
Initialized 8 tasks from 2 source files:

Source files:
- auth-feature.md
- dashboard.md

Tasks created:
1. AuthContext (no deps)
2. LoginForm (depends on: 1)
3. RegisterForm (depends on: 1)
4. API /auth/login (no deps)
5. API /auth/register (no deps)
6. Dashboard header (no deps)
7. Dashboard stats (depends on: 6)
8. Dashboard charts (depends on: 6)

Execution order recommendation:
1. Start with: 1, 4, 5, 6 (no dependencies)
2. Then: 2, 3 (after task 1)
3. Then: 7, 8 (after task 6)

Files created:
- .project-meta/tasks/tasks.md
- .project-meta/tasks/status.md
```
