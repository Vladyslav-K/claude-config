## 🚨 #1 RULE — DESIGN IS THE ABSOLUTE SOURCE OF TRUTH 🚨

**When a task has design documents (`*__design.md`) and/or screenshots:**

1. **Design document defines EVERYTHING.** Every element, every column, every icon, every badge — if it's not described in the design document, it DOES NOT EXIST. Period.
2. **Screenshot is visual verification** of the design document — use it to confirm interpretation, not to invent elements.
3. **Existing codebase is ONLY for finding reusable components** (how to import, how to use). It NEVER defines what goes on the page.
4. **NEVER add UI elements from existing pages that are not in the design.** No avatars, no icons, no badges, no columns — NOTHING that the design document doesn't explicitly describe.
5. **For every element you plan to build — point to the exact line in the design document.** If you can't point to it — don't build it.

**Violation of this rule breaks the entire workflow. This is non-negotiable.**

---

## Code Rules

- DON'T leave any comments what not connected to code, like tasks description, changes notes, etc.
- DON'T create any .md or other text files if you are not ordered to do it.
- DON'T create tests if you are not ordered to do it.
- With me, you ALWAYS speak on Ukrainian, but ALL generated code, comments, files must be only on English language, if not ordered other language.
- DON'T add yourself in commits, all commits must clear.
- ALWAYS check what package manager project using before run scripts!!!
- Before install any new library in project, ALWAYS check latest stable version with context7 or in Web!!!
- For reading and editing xlsx files use openpyxl.

---

## Post-Task Requirements

- AFTER FINISHED TASK ALWAYS RUN NEXT SCRIPT - format-and-check - AND FIX ISSUES IF FOUNDED!!!
- If this command don't exist, use next scripts - format, lint, typecheck.
- DON'T use custom commands with npx for this, we have this commands in package.json!!!

---

## CRITICAL: Task Workflow

**READ:** `.claude/rules/workflow/task-execution.md` — execution model, research protocol, multi-task flow

**⚠️ YOU ARE THE IMPLEMENTER. You research, plan, build, and self-review directly. No delegation to agents.**

**For every task:**
1. Research the codebase (use Explore agent for file search, read files yourself)
2. For complex tasks → present a plan to user, wait for approval
3. Implement following the plan (or directly for simple tasks)
4. Self-review → run format-and-check → fix issues
5. Report what was done

**Multi-task execution:** Sequential, one task at a time. Complete fully before moving to next. Continue even through autocompact.

**Context management:** Use Explore agent (Task tool, subagent_type="Explore") for broad searches to save context. Read only the files you need. Make decisions yourself.

---

## CRITICAL: API Verification Before Planning

**When user provides screenshots/designs for a feature:**

1. **BEFORE creating API types/services/hooks** → ASK: "Is there a backend API for this? What are the endpoints?"
2. **If user doesn't provide API docs** → Do NOT create API tasks. Mark them as BLOCKED or ask.
3. **NEVER invent** endpoint URLs, field names, or response structures from screenshots alone.
4. **Why:** Hallucinating API structures causes cascading failures — wrong types → wrong hooks → empty/broken UI.

---

## Visual Task Methodology

**When building from designs (screenshots, Figma, design documents):**

### Source of Truth Hierarchy

| Priority | Source | Role |
|----------|--------|------|
| 1 (HIGHEST) | **Design document (`*__design.md`)** | Defines EVERY element: sizes, colors, text, spacing, states, structure |
| 2 | **Screenshot** | Visual verification of design document interpretation |
| 3 | **Task description** | Business requirements and scope |
| 4 (LOWEST) | **Existing codebase** | Component reference ONLY — shows HOW to use shared components |

**Reading order:** Design document first → Screenshot second → Task description → Codebase research.

**🚫 Existing pages are NOT templates.** They show which components exist and how to import them. They do NOT define what your page looks like. If a similar page has an avatar but the design does not — do NOT add an avatar.

**Rule: Build FROM the design, not from existing code. Use existing code only to find reusable components.**

### Pixel-Perfect Compliance

> **NEVER trust component defaults for visual styling. ALWAYS override with exact values from the design document via `className` or props.**

For each UI element:
1. **Colors** — Extract exact hex values. Apply via `text-[#hex]`, `bg-[#hex]`, `border-[#hex]`. NEVER use Tailwind named colors unless they match exactly.
2. **Spacing** — Convert design px to Tailwind: `gap:4` → `gap-1`, `gap:8` → `gap-2`, `gap:12` → `gap-3`, `gap:16` → `gap-4`, `gap:20` → `gap-5`, `gap:24` → `gap-6`. When no match, use arbitrary: `gap-[20px]`.
3. **Border radius** — `r:12` → `rounded-xl`, `r:16` → `rounded-2xl`, `r:50` → `rounded-full`. When unsure: `rounded-[12px]`.
4. **Typography** — Font weight, size, line height, letter spacing — all from design. Override component defaults if they differ.
5. **Shadows** — Exact values: `shadow-[0_1px_2px_0_#1018280D]`.
6. **Dimensions** — Exact width/height when specified: `w-10 h-10` for 40x40.

### Design Element Extraction (Research Phase)

Before coding a visual task, extract EVERY UI element from the design:
- For each section: elements, exact text, dimensions, colors
- For tables: EVERY column header, cell content format, row variations
- For interactive elements: type (link/button/dropdown), states (hover/active/disabled)
- For badges/tags: exact text, colors, border-radius
- **If in design → MUST be in code. If NOT in design → MUST NOT be in code.**

---

## Priority Hierarchy

**When information conflicts, follow this priority:**

### 1. User's Explicit Instruction (HIGHEST)
What user said in current chat > Everything else
```
User: "Make the button red"
-> Even if Figma shows blue button, make it red
```

### 2. Design Specs (Design Documents + Figma)
Design document dimensions > Your assumptions
```
Design doc: Card width 619px
-> Use 619px, don't round to 600px or 50%
```

### 3. Existing Codebase Patterns
How this project does things > General best practices
```
Project uses: import { Button } from '@/components/ui/button'
-> Use this, not: import Button from 'some-other-lib'
```

### 4. CLAUDE.md Rules
These rules > Default Claude behavior
```
Rule: "Use tabs for indentation"
-> Follow even if you prefer spaces
```

### 5. General Best Practices (LOWEST)
Only when nothing above applies
