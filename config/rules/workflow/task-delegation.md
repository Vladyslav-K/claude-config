# Task Delegation Workflow

**CRITICAL: Follow this workflow for coding tasks to preserve context and maximize session length.**

---

## Overview

Instead of writing code directly, you delegate work to specialized agents:
- `codebase-searcher` - for research and file reading
- `frontend-worker` - for frontend code (UI, components, styling, client-side logic)
- `backend-worker` - for backend code (API, database, auth, server-side logic)
- `code-reviewer` - for detailed code verification

This saves tokens in your main session, allowing longer conversations.

**Important:** Delegation is not mandatory for ALL tasks. See "Delegation Criteria" below.

---

## Delegation Criteria

### When to DELEGATE

Delegate to agents when:
- **Code volume:** More than ~30 lines of code to write/modify
- **New components:** Creating new files, components, pages
- **Complex logic:** Business logic, state management, API integration
- **Multiple files:** Changes touching 3+ files
- **Research needed:** Need to find patterns across codebase

### When to DO IT YOURSELF

Handle directly when:
- **Small fixes:** Less than ~20 lines of code
- **Simple bugs:** Typos, missing imports, obvious errors
- **Single file edits:** Quick modifications to one file
- **Config changes:** Updating configs, env variables
- **Already know the answer:** No research needed

### Decision Tree

```
Is task clear without research?
├─ NO → codebase-searcher first
└─ YES → More than ~30 lines of code?
          ├─ NO → Do it yourself
          └─ YES → Frontend or Backend?
                    ├─ Frontend → frontend-worker
                    └─ Backend → backend-worker
```

---

## Frontend vs Backend Worker

**Simple rule:** Where does the code RUN?
- Runs in **browser/client** → `frontend-worker`
- Runs on **server** → `backend-worker`

### Use `frontend-worker` for:
- UI components (React, Vue, etc.)
- Styling (Tailwind, CSS)
- Client-side state management
- Form handling and validation (UI side)
- Client-side routing
- Animations and interactions
- Accessibility implementation
- **API calls FROM frontend** (fetch, axios, tanstack query, SWR)
- **API hooks and services** that call backend endpoints
- Any code in Next.js `app/` pages that runs on client
- Type definitions for API responses (client-side)

### Use `backend-worker` for:
- **Creating/modifying API endpoints** (controllers, routes)
- Database schemas and migrations (Prisma)
- Server-side services and business logic
- Authentication/Authorization implementation ON SERVER
- Server-side validation (DTOs, pipes)
- Middleware implementation
- Background jobs and queues
- Server-side integrations (Stripe webhooks, email sending)
- Next.js API routes (`app/api/`) or Route Handlers
- Any code that runs on Node.js server

### Key Distinction

| Task | Worker | Why |
|------|--------|-----|
| "Add fetch call to get users" | frontend | Code runs in browser |
| "Create GET /users endpoint" | backend | Code runs on server |
| "Add tanstack query hook for products" | frontend | Client-side data fetching |
| "Add products table to database" | backend | Database/server operation |
| "Handle API errors in UI" | frontend | Error handling in browser |
| "Add error handling to endpoint" | backend | Server-side error handling |

### Mixed Tasks
If task involves both frontend and backend:
1. Split into separate subtasks
2. Delegate backend first (create endpoint)
3. Then delegate frontend (call that endpoint from UI)

---

## Parallel Execution

**Run agents in parallel when tasks are independent.**

No limit on parallel agents. Prioritize efficiency and speed.

**Examples:**
- Need UI patterns + API hooks + types → 3 parallel codebase-searcher
- Need to create 3 independent components → 3 parallel frontend-worker
- Research + implementation of unrelated feature → parallel

**Don't parallelize when:**
- Task B depends on result of Task A
- Same file will be modified by multiple agents

---

## Communication Style

**Use medium detail level when informing user about actions.**

✅ Good: "Делегую задачу — створення таблиці юзерів для адміна"
✅ Good: "Досліджую кодбазу → знайшов патерни → делегую імплементацію"

❌ Too verbose: "Зараз я делегую задачу frontend-worker агенту, який створить компонент UsersTable з колонками id, name, email, role, createdAt, використовуючи Tanstack Table..."

❌ Too brief: "Делегую" (without context what)

**Rule:** User should understand WHAT you're doing, not HOW in detail.

---

## CRITICAL: Memory System Integration

**Agents MUST receive memory context if it exists.**

Before delegating to ANY agent, check if memory exists and include in prompt:

```markdown
## PROJECT MEMORY (READ FIRST)
Memory files exist at: {CWD}/.project-meta/memory/
- project-overview.md - project architecture and key concepts
- project-structure.md - file tree with descriptions
- recent-session.md - context from last session

Read these files FIRST to understand project context before proceeding.
```

**Always include this section in prompts to codebase-searcher and frontend-worker.**

---

## Workflow Steps

### Step 1: Research Phase (codebase-searcher)

1. Read and understand user's task
2. Check if memory exists: `.project-meta/memory/`
3. Delegate research to `codebase-searcher` with memory paths

**codebase-searcher prompt template:**
```markdown
## PROJECT MEMORY (READ FIRST)
Memory files exist at: {CWD}/.project-meta/memory/
Read these files FIRST to understand project context.

## RESEARCH TASK
[What you need to find]

## WHAT TO RETURN
1. FULL CODE of similar components (not summaries - actual code)
2. Exact import paths used in this project
3. Type/interface definitions that will be needed
4. Actual file paths (absolute paths)
5. Code style patterns observed

Return actual code snippets I can use as reference.
```

**Run multiple codebase-searcher agents in parallel** if you need different types of information.

### Step 2: Implementation (frontend-worker)

**frontend-worker prompt MUST include:**
```markdown
## PROJECT MEMORY (READ FIRST)
Memory files exist at: {CWD}/.project-meta/memory/
Read these files FIRST to understand project context.

## TASK
[User's EXACT original request - copy word for word]

## CONTEXT
[Why this task is needed, what problem it solves]

## FILES TO MODIFY/CREATE
[Exact paths with what should happen to each]
- /path/to/file.tsx - modify: add X functionality
- /path/to/new-file.tsx - create: new component for Y

## EXISTING CODE PATTERNS (CRITICAL)
[Paste ACTUAL code snippets from codebase-searcher research]

## TECHNICAL REQUIREMENTS
[Specific requirements: types, props, imports]

## CODE STYLE RULES (from project)
[List specific rules discovered from research]

## WHAT NOT TO DO
[Explicit prohibitions]

## EXPECTED RESULT
[Describe exactly what finished code should do]

## POST-TASK
After completing, run: format-and-check (or format, lint, typecheck)
Fix any issues found.
```

**Run multiple frontend-worker agents in parallel** if tasks don't conflict.

### Step 3: Verification (code-reviewer)

**Delegate verification to code-reviewer with FULL context.**

#### A. Delegate to code-reviewer

**CRITICAL:** Provide complete information, don't just say "read tasks.md".

```markdown
Task tool:
  subagent_type: "code-reviewer"
  prompt: |
    ## TASK REQUIREMENTS
    [Copy the EXACT requirements from user's request]
    [Include ANY clarifications user made during conversation]

    ## WHAT WAS IMPLEMENTED
    [Brief description of what agent created]

    ## FILES TO REVIEW
    - [list of created/modified files with their purpose]

    ## SPECIFIC CHECKS
    - [List specific things to verify based on requirements]
    - [Any edge cases or special requirements user mentioned]

    ## ADDITIONAL CONTEXT
    Read .project-meta/tasks/tasks.md for full task definition if exists.

    Verify ALL requirements are implemented correctly.
    Return verdict: APPROVE or NEEDS REVISION with specific issues.
```

**Why full context:** code-reviewer works in isolated context. It doesn't see our conversation. Providing complete requirements prevents missed verification points.

#### B. Review the Report

Read code-reviewer's report:
- **APPROVE** → update status, proceed to next task
- **NEEDS REVISION** → delegate fixes to frontend-worker, then re-verify

#### C. Run Quality Checks

- Execute `format-and-check` (or equivalent)
- If issues found → delegate fixes to frontend-worker

#### D. Confirm or Re-delegate

- If all good → confirm to user
- If issues → fix and re-verify

---

## Quality Checklist

Use this checklist when verifying agent results:

```
## Code Quality
- [ ] All requirements from user's request are implemented
- [ ] Code compiles without errors (TypeScript)
- [ ] No console.log, debugger, or commented-out code
- [ ] Types are properly defined (no `any` unless justified)
- [ ] Follows existing project patterns

## UI/Styling (if applicable)
- [ ] Matches design specs (±2px tolerance)
- [ ] Responsive behavior works
- [ ] Dark mode supported (if project uses it)
- [ ] Accessibility basics (semantic HTML, ARIA where needed)

## Integration
- [ ] Imports are correct and from right locations
- [ ] No circular dependencies introduced
- [ ] Works with existing state/data flow

## Final
- [ ] format-and-check passes
- [ ] No new warnings introduced
```

---

## Iteration Limit

**Maximum 2 attempts per agent for same task.**

After 2 failed attempts:
1. **STOP** delegating the same task
2. **ASK** user: "Агент не справляється з [task]. Варіанти: 1) Я зроблю сам, 2) Змінимо підхід, 3) Спростимо задачу"
3. **WAIT** for user's decision

**Why:** Prevents infinite loops and wasted tokens. If agent fails twice, the problem is likely in task definition or approach.

---

## Partial Fixes

**When agent result is 80% correct, 20% needs fixes:**

Delegate ONLY the fixes, not the entire task again.

```markdown
## TASK (PARTIAL FIX)
Previous implementation is mostly correct. Fix ONLY these issues:

## ISSUES TO FIX
1. [Specific issue with file path and line if possible]
2. [Another specific issue]

## DO NOT CHANGE
- [List files/parts that are correct]
- [Preserve existing logic in X]

## EXPECTED RESULT
After fixes, [describe what should work]
```

**Why:** More efficient than re-implementing. Agent keeps correct code, fixes only problems.

---

## Debugging Workflow

### Small Bugs (DO IT YOURSELF)
- Typos in code
- Missing imports
- Wrong prop names
- Simple logic errors (wrong condition, off-by-one)
- CSS tweaks (spacing, colors)

### Large Bugs (DELEGATE)
- Agent created wrong component/page entirely
- Fundamental architecture mistake
- Wrong data flow/state management approach
- Multiple interconnected bugs

**Rule of thumb:** If fix is <15 lines and you understand the problem → do it yourself.

---

## Error Recovery

When agent result is wrong:

1. **Document the failure** - What exactly was wrong?
2. **Identify root cause** - Was information missing in YOUR prompt?
3. **Fix your prompt** - Add missing info, don't just re-run same prompt
4. **Re-delegate with corrections:**

```markdown
## TASK (REVISION)
Previous attempt had these issues:
1. [Specific issue 1]
2. [Specific issue 2]

## FIXES REQUIRED
1. [Exact fix needed]
2. [Exact fix needed]

## KEEP UNCHANGED
[List what was correct]
```

**Remember:** Maximum 2 attempts, then ask user.

---

## Common Mistakes to Avoid

### Research Phase
- ❌ "Find card components and tell me how they work"
- ✅ "Find card components - return FULL CODE of 2 best examples"

### Delegation Phase
- ❌ "Use existing patterns" → Paste actual patterns
- ❌ "Follow project conventions" → List specific conventions
- ❌ "Create a component like X" → Show X's actual code
- ❌ Summarizing user's request → Copy it exactly

### Verification Phase
- ❌ Only running lint/typecheck
- ✅ Using code-reviewer with FULL context
- ❌ Telling reviewer "read tasks.md" without context
- ✅ Providing complete requirements to reviewer
- ❌ Skipping verification entirely
- ✅ Re-verify after fixes until APPROVE

### Iteration
- ❌ Re-delegating same prompt after failure
- ✅ Analyzing what was missing, improving prompt
- ❌ Delegating 5+ times for same task
- ✅ Stopping after 2 attempts, asking user

---

## Example Full Workflow

```
User: "Add a new button component"

1. ASSESS: ~50 lines, new component → DELEGATE

2. RESEARCH (codebase-searcher):
   "PROJECT MEMORY at .project-meta/memory/ - read first.
    Find existing button patterns, UI components structure,
    design system conventions. Return FULL CODE of examples."

3. COMMUNICATE: "Досліджую UI компоненти → делегую створення button"

4. IMPLEMENT (frontend-worker):
   "PROJECT MEMORY at .project-meta/memory/ - read first.
    TASK: User asked: 'Add a new button component'
    [Full structured prompt with patterns from research]"

5. VERIFY (code-reviewer):
   "TASK: Create button component with variants (primary, secondary, outline)
    User clarified: should support loading state and disabled state
    FILES: /src/components/ui/button.tsx
    CHECKS: variants work, loading shows spinner, disabled is not clickable"

6. RESULT:
   - APPROVE → format-and-check → confirm to user
   - NEEDS REVISION (attempt 1) → delegate fix → re-verify
   - NEEDS REVISION (attempt 2) → ask user for direction
```
