# Task Delegation Workflow

**CRITICAL: Follow this workflow for ALL coding tasks to preserve context and maximize session length.**

---

## Overview

Instead of writing code directly, you delegate work to specialized agents:
- `codebase-searcher` - for all research and file reading
- `frontend-worker` - for all code writing
- `code-reviewer` - for detailed code verification (has access to full conversation!)

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

**Note:** `code-reviewer` works in isolated context. Tell it to read `.project-meta/tasks/tasks.md` to get task requirements.

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

### Step 3: Verification (DELEGATE to code-reviewer)

**Delegate verification to code-reviewer. It reads task definitions and verifies code.**

#### A. Delegate to code-reviewer

```markdown
Task tool:
  subagent_type: "code-reviewer"
  prompt: |
    Verify the implementation of [task description].

    Files to review:
    - [list of created/modified files]

    Read .project-meta/tasks/tasks.md to get full requirements.
    Verify all requirements from Context section are implemented.
```

**Important:** code-reviewer works in isolated context. It must read tasks.md itself to get requirements.

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

#### Verification Checklist:
```
- [ ] Delegated to code-reviewer with file list
- [ ] Told code-reviewer to read tasks.md for requirements
- [ ] Read verification report
- [ ] Verdict: APPROVE → done, NEEDS REVISION → fix and re-verify
- [ ] format-and-check passes
```

**Why this approach:** code-reviewer reads files in isolated context (saves main session tokens). User can do separate verification session if needed.

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
- ✅ Using code-reviewer for detailed verification
- ❌ Assuming frontend-worker did it right
- ✅ code-reviewer reads tasks.md for requirements
- ❌ Skipping verification entirely
- ✅ Re-verify after fixes until APPROVE

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

3. VERIFY (code-reviewer):
   a. Delegate to code-reviewer:
      "Verify /src/components/ui/button.tsx
       Read .project-meta/tasks/tasks.md for requirements."
      → code-reviewer reads tasks.md, reads created file, verifies
   b. Read code-reviewer's report:
      → APPROVE: done!
      → NEEDS REVISION: delegate fix to frontend-worker, re-verify
   c. Run format-and-check
   d. Confirm to user
```
