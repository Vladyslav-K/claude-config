## 🚨 Design-First Development

**When a task has design documents (`*__design.md`) and/or screenshots:**

### Source of Truth (in order of priority)
1. **User's explicit instruction** in current chat — overrides everything
2. **Design document** (`*__design.md`) — defines EVERY element: sizes, colors, text, spacing, states
3. **Screenshot** — visual verification of design interpretation
4. **Task description** — business requirements and scope
5. **Existing codebase** — component reference ONLY (how to import/use, not what to build)

### Rules
- If it's not in the design — it DOES NOT exist. Don't build it.
- Existing pages are NOT templates. They show which components exist, not what your page looks like.
- For every element you build — point to the exact line in the design document.
- NEVER trust component defaults for visual styling. ALWAYS override with exact values from design via `className` or props.
- Extract exact hex values for colors, exact px for spacing, exact font specs from design.

### Before Coding a Visual Task
Extract EVERY UI element from the design:
- Each section: elements, text, dimensions, colors
- Tables: EVERY column header, cell content format, row variations
- Interactive elements: type, states (hover/active/disabled)
- Badges/tags: text, colors, border-radius
- **If in design → MUST be in code. If NOT in design → MUST NOT be in code.**

---

## Code Rules

- Comments: simple `// Comment` style only. NO decorative lines, NO ASCII art. Only for grouping or non-obvious logic.
- DON'T create .md files or tests unless explicitly ordered.
- Speak Ukrainian with user, ALL code/comments in English.
- ALWAYS check package manager before running scripts.
- Before installing libraries, ALWAYS check latest stable version with context7 or Web.
- For reading/editing `.xlsx` files — ALWAYS use `openpyxl` (Python). No other tool.

---

## Post-Task Requirements

- AFTER EVERY TASK: run `format-and-check` (or `format`, `lint`, `typecheck` if unavailable). Fix all issues.
- Use scripts from package.json, NOT custom npx commands.

---

## Task Workflow

**Full workflow:** `.claude/rules/workflow/task-execution.md`

**Core:** You ARE the implementer. Research → plan (if complex) → build → self-review → format-and-check.

**CRITICAL:** When user provides screenshots/designs WITHOUT API docs — ASK about API endpoints BEFORE creating types/services/hooks. NEVER invent API structures from screenshots.

---

## Memory System

### Session Memory (Short-term)

**File:** `.project-meta/memory/recent-session.md`

**"збережи сесію"** → write summary (date, what was done, files, current state, next steps). Overwrite each time.

**"продовжуємо."** → read `recent-session.md` FIRST before doing anything else.

---

### Persistent Memory (Long-term)

**File:** `.project-meta/memory/persistent.md`

Append-only project knowledge that persists across ALL sessions.

**Triggers:** "запам'ятай", "додай в пам'ять", "збережи в пам'ять", "remember this"

**When triggered:**
1. Read current `persistent.md`
2. Append: `## [YYYY-MM-DD] Brief title` + concise content
3. NEVER overwrite/delete existing entries
4. Confirm what was saved

**Auto-read (enforced by hooks):**
- On every chat start → read persistent.md BEFORE anything
- After every autocompact → re-read persistent.md

**Store:** Architecture decisions, project preferences, known issues, API quirks, business logic.
**Don't store:** Temporary progress (use recent-session), general coding rules (already in rules/).
