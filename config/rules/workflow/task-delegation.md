# Task Delegation Workflow

**CRITICAL: Follow this workflow for ALL coding tasks to preserve context and maximize session length.**

---

## Overview

Instead of writing code directly, you delegate work to specialized agents:
- `codebase-searcher` - for all research and file reading
- `frontend-worker` - for all code writing

This saves tokens in your main session, allowing longer conversations.

---

## CRITICAL: Memory System Integration

**Both agents MUST receive memory context if it exists.**

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

### Step 1: Research Phase (DELEGATE to codebase-searcher)

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

### Step 2: Implementation (DELEGATE to frontend-worker)

**NEVER write code yourself** - delegate ALL code writing to `frontend-worker`.

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

### Step 3: Verification (YOU do this - CRITICAL)

**This is NOT just running lint. You MUST verify the code matches requirements.**

#### Verification Process:

1. **Read the created/modified files yourself**
   - Use Read tool to examine what agent produced

2. **Compare against requirements**
   - Does the code match user's original request?
   - Does it follow the patterns you specified?
   - Are all features implemented correctly?
   - Is anything missing or added that shouldn't be?

3. **Run quality checks**
   - Execute `format-and-check` (or equivalent)
   - Fix any lint/type errors

4. **Report issues or confirm success**
   - If issues found → delegate fix to frontend-worker with SPECIFIC error details
   - If correct → confirm to user

#### Verification Checklist:
```
- [ ] Read all files created/modified by agent
- [ ] Code matches user's original request
- [ ] All specified features are implemented
- [ ] No extra features added that weren't requested
- [ ] Follows patterns from codebase-searcher research
- [ ] Code style matches project conventions
- [ ] No TypeScript errors
- [ ] No lint warnings
```

**If agent produced wrong result, document what's wrong and re-delegate with corrections.**

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
- ✅ Reading code and comparing to requirements
- ❌ Assuming agent did it right
- ✅ Verifying every requirement is met

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

---

## When NOT to Delegate

Do it yourself for:
- Reading a single specific file path user provided
- Very simple queries like "read package.json"
- Quick checks of 1-2 files you already know the path to

---

## Example Full Workflow

```
User: "Add a new button component"

1. RESEARCH (codebase-searcher):
   "PROJECT MEMORY at .project-meta/memory/ - read first.
    Find existing button patterns, UI components structure,
    design system conventions. Return FULL CODE of examples."

2. IMPLEMENT (frontend-worker):
   "PROJECT MEMORY at .project-meta/memory/ - read first.
    TASK: User asked: 'Add a new button component'
    [Full structured prompt with patterns from research]"

3. VERIFY (you):
   - Read /src/components/ui/button.tsx
   - Compare to requirements
   - Run format-and-check
   - Confirm or re-delegate fixes
```
