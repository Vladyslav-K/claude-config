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
Files in `.project-meta/tasks/init/` directory (usually .md files with free-form task descriptions)

## Output
- `.project-meta/tasks/tasks.md` — Markdown file with full task context (READ ONLY after creation)
- `.project-meta/tasks/status.md` — human-readable status table (will be updated during execution)

## Execution Steps

**YOU execute all steps yourself. Only use codebase-searcher for research if needed.**

1. **Read all files** from `.project-meta/tasks/init/`
2. **Analyze content** — extract individual tasks from free-form descriptions
3. **For each task determine:**
    - Unique ID (sequential number)
    - Short title
    - Full context (everything needed to execute the task independently)
    - Files that will be created/modified
    - Dependencies on other tasks
4. **Research codebase** (if needed) — use codebase-searcher agent to find:
    - Existing patterns relevant to tasks
    - Import paths used in project
    - Code style conventions
    - Include this context in each task's Context section
5. **Create tasks.md yourself** — use Write tool to create the file in structured Markdown format
6. **Create status.md yourself** — use Write tool to create file with initial statuses (all pending)
7. **Show summary** to user

**IMPORTANT:** You create all files. codebase-searcher only helps with reading/searching existing code.

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
2. **Include FULL context in Context section** — you won't see conversation history when executing
3. **Research codebase patterns** — include actual code examples, not descriptions
4. **Use exact file paths** — absolute or relative from project root
5. **One task per logical unit** — don't combine unrelated changes
6. **Order by dependencies** — tasks with no deps should come first

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
