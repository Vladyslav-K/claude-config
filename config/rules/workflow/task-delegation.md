# Task Workflow

**Follow this workflow for coding tasks.**

---

## Overview

You handle all code writing and editing directly. The only agent you delegate to:
- Built-in `Explore` agent — for deep codebase research (read-only)

All implementation, bug fixes, refactoring, verification, and memory updates — you do yourself.

---

## Research Criteria

### When to DELEGATE research to Explore agent

Delegate to `Explore` agent when:
- **Unknown patterns:** Need to find how project does something
- **Large codebase:** Need to search across many files
- **Multiple examples:** Need 2-3 similar implementations for reference
- **Type definitions:** Need to find interfaces/types across the project

### When to SEARCH yourself

Handle directly when:
- **Known location:** You already know which file to read
- **Simple lookup:** One file, one grep, one glob
- **Already researched:** You have context from earlier in session

### Decision Tree

```
Is task clear without research?
├─ NO → Need to search many files?
│        ├─ YES → Explore agent (choose thoroughness)
│        └─ NO → Search yourself (Glob/Grep/Read)
└─ YES → Implement directly
```

### Thoroughness Guide

Choose the right level based on task scope:

| Level | When to use | Example |
|-------|------------|---------|
| `"quick"` | Find one specific file/pattern | "Find Button component" |
| `"medium"` | Understand a feature area, find 2-3 patterns | "How are forms built in this project?" |
| `"very thorough"` | Deep analysis across multiple areas, architecture understanding | "Full auth system analysis with all related components, hooks, types" |

**Default to `"very thorough"` for implementation research** — it's better to gather more context than to miss critical patterns.

---

## Execution Order

**Default: sequential.** Finish research → implement → verify.

**But: parallelize independent operations when safe.**

### What CAN run in parallel

| Operation | Condition |
|-----------|-----------|
| Multiple Read/Glob/Grep calls | Always safe |
| Multiple Write/Edit to DIFFERENT files | Always safe |
| Multiple memory file writes | Always safe (different files) |
| Multiple independent tasks (tasks:run) | Only if NO shared files AND NO dependency between them |

### What MUST stay sequential

| Operation | Why |
|-----------|-----|
| Research → Implementation | Need research results to write code |
| Implementation → format-and-check | Need files written before checking |
| Tasks with shared files | File conflict risk |
| Tasks with dependency chain | Later task needs earlier task's output |

### Rule of thumb

**Before parallelizing, check:**
1. Do these operations touch the SAME files? → Sequential
2. Does one operation NEED the result of another? → Sequential
3. Neither? → **Run in parallel for speed**

---

## Communication Style

**Use medium detail level when informing user about actions.**

✅ Good: "Досліджую UI компоненти → імплементую button"
✅ Good: "Шукаю патерни в кодбазі → створюю компонент"

❌ Too verbose: Long detailed descriptions of every step

❌ Too brief: "Роблю" (without context what)

**Rule:** User should understand WHAT you're doing, not HOW in detail.

---

## CRITICAL: Memory System Integration

**Explore agent MUST receive memory context if it exists.**

Before delegating to Explore, check if memory exists and include in prompt:

```markdown
## PROJECT MEMORY (READ FIRST)
Memory files exist at: {CWD}/.project-meta/memory/
- project-overview.md - project architecture and key concepts
- project-structure.md - file tree with descriptions
- recent-session.md - context from last session

Read these files FIRST to understand project context before proceeding.
```

---

## Workflow Steps

### Step 1: Research Phase (Explore agent)

1. Read and understand user's task
2. Check if memory exists: `.project-meta/memory/`
3. Delegate research to `Explore` agent with memory paths

**Explore agent invocation:**
```
Task tool:
  subagent_type: "Explore"
  description: "Research [what you're looking for]"
  prompt: |
    ## PROJECT MEMORY (READ FIRST)
    Memory files exist at: {CWD}/.project-meta/memory/
    Read these files FIRST to understand project context.

    ## RESEARCH TASK
    [What you need to find — be specific about what information you need]

    ## THINK DEEPLY ABOUT:
    - What exact files and patterns are relevant to this task?
    - What is the minimum set of information needed to implement correctly?
    - Are there edge cases or non-obvious dependencies?

    ## WHAT TO RETURN
    1. FULL CODE of similar components (not summaries - actual code)
    2. Exact import paths used in this project
    3. Type/interface definitions that will be needed
    4. Actual file paths (absolute paths)
    5. Code style patterns observed

    Return actual code snippets I can use as reference.
```

**Thoroughness:** Use `"very thorough"` for implementation research, `"medium"` for quick lookups.

### Step 2: Implementation (YOU do this)

**After research, implement the task directly using Write/Edit tools.**

Follow this checklist:
- Use patterns discovered during research
- Follow existing project conventions
- Handle edge cases and error states
- Use proper TypeScript types
- Follow accessibility requirements

### Step 3: Verification (YOU do this)

After implementation:
1. **Run format-and-check** (or format, lint, typecheck)
2. **Fix any issues** found by linters/formatters
3. **Re-read modified files** to verify correctness if needed

---

## Quality Checklist

Use this checklist when verifying your own work:

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

## Debugging Workflow

### Small Bugs
- Typos in code
- Missing imports
- Wrong prop names
- Simple logic errors (wrong condition, off-by-one)
- CSS tweaks (spacing, colors)

→ Fix directly, no research needed.

### Larger Bugs
- Fundamental architecture mistake
- Wrong data flow/state management approach
- Multiple interconnected bugs

→ Research with Explore agent first, then fix.

---

## Common Mistakes to Avoid

### Research Phase
- ❌ "Find card components and tell me how they work"
- ✅ "Find card components - return FULL CODE of 2 best examples"

### Implementation Phase
- ❌ Guessing patterns without research
- ✅ Using actual patterns found in codebase
- ❌ Ignoring existing conventions
- ✅ Following project's established patterns

### Verification Phase
- ❌ Only running lint/typecheck without reviewing
- ✅ Running format-and-check AND reading the output
- ❌ Skipping verification entirely
- ✅ Fixing all issues before reporting done

---

## Example Full Workflow

```
User: "Add a new button component"

1. RESEARCH (Explore agent, "very thorough"):
   "PROJECT MEMORY at .project-meta/memory/ - read first.
    Find existing button patterns, UI components structure,
    design system conventions. Return FULL CODE of examples."

2. COMMUNICATE: "Досліджую UI компоненти → створюю button"

3. IMPLEMENT (directly):
   - Create/edit files using Write/Edit tools
   - Follow patterns from research
   - Apply project conventions

4. VERIFY:
   - Run format-and-check
   - Fix any issues
   - Confirm to user
```
