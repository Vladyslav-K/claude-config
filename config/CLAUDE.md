**MEMORY SYSTEM ACTIVE:** Read `.claude/rules/workflow/memory-system.md` for project memory management. At session start, check if `.project-meta/memory/` exists and read its contents.

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

**READ:**
- `.claude/rules/workflow/task-delegation.md` — delegation decisions, solo/delegate workflow
- `.claude/rules/workflow/agent-management.md` — agent templates, visual task rules, validation system

**⚠️ MANDATORY DELEGATION CHECK (before EVERY task):**
Ask yourself: "Will this touch 2+ files OR require reading 5+ files for research?"
→ YES = **delegate to agent** (NEVER do heavy work in main context)
→ NO (1 file, ≤150 lines) = do it yourself

**Summary:**
1. **Solo** (1 file, ≤150 lines change) → Implement yourself → Verify
2. **Delegate** (2+ files / heavy research / skills / tasks:plan / tasks:run / estimate) → Agent does research + implementation → You validate → Verify

**Available agents:**
- `Explore` — built-in (Haiku model), ONLY for file search and simple lookups
- `general-purpose` (deep research) — for understanding flows, architecture, expert analysis
- `general-purpose` (implementation) — for writing code, creating features

**CRITICAL: NEVER specify `model` param when spawning agents. Omit it → agent inherits current chat model automatically. This ensures agents always use the same model as main chat, no matter what model is active.**

**CRITICAL: Validation** — After ANY delegated work, YOU personally validate the result:
- Read output files created by agent
- Compare with screenshots/design specs if available
- Check code patterns and types match project conventions
- Fix issues yourself or send corrections to agent

**Context Window Strategy** — Delegate heavy work to team agents to keep main context clean. Main chat handles orchestration + validation only.

---

## CRITICAL: API Verification Before Planning

**When user provides screenshots/designs for a feature:**

1. **BEFORE creating API types/services/hooks** → ASK: "Is there a backend API for this? What are the endpoints?"
2. **If user doesn't provide API docs** → Do NOT create API tasks. Mark them as BLOCKED or ask.
3. **NEVER invent** endpoint URLs, field names, or response structures from screenshots alone.
4. **Why:** Hallucinating API structures causes cascading failures — wrong types → wrong hooks → empty/broken UI.

---

## CRITICAL: Visual Task Mandatory Agents

**For ANY task with screenshots/Figma specs, you MUST spawn ALL 3 agents:**

1. **Analyzer** — reads screenshot + Figma JSON → produces element-by-element specs
2. **Implementer** — builds using analyzer's output + codebase patterns
3. **Validator** — fresh-eyes comparison of result vs design → reports every discrepancy

**Skipping ANY of these agents is FORBIDDEN.** If you "validate" without a validator agent,
the validation is fake and critical issues WILL be missed.

---

## CRITICAL: Figma-to-Code Rules

**When working with Figma JSON, screenshots, or design specs:**

**READ AND FOLLOW: `.claude/rules/workflow/figma-to-code.md`**

This file contains MANDATORY rules for:
- Exact dimension conversion (NO approximations ever!)
- Dimension tables with px and % calculations
- Color extraction
- Responsive design strategy
- Image/asset handling

**Failure to follow these rules results in incorrect implementations.**

---

## Priority Hierarchy

**When information conflicts, follow this priority:**

### 1. User's Explicit Instruction (HIGHEST)
What user said in current chat > Everything else
```
User: "Make the button red"
-> Even if Figma shows blue button, make it red
```

### 2. Figma/Design Specs
Figma dimensions > Your assumptions
```
Figma: Card width 619px
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
