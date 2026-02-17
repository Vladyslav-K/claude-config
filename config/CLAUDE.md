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

## CRITICAL: Task Workflow (Chain Model)

**READ:**
- `.claude/rules/workflow/task-delegation.md` — delegation decisions, chain execution model
- `.claude/rules/workflow/agent-management.md` — agent templates, chain communication, validation

**⚠️ YOU ARE A PURE MANAGER. You do NOT write code (unless trivial), do NOT read implementation files, do NOT validate code quality.**

**MANDATORY DELEGATION CHECK (before EVERY task):**
Ask yourself: "Will this change more than 1 file, or more than 50 lines, or need research?"
→ YES = **delegate to agent chain** (NEVER do any work in main context)
→ NO (1 file, ≤50 lines, pattern known) = do it yourself

**Summary:**
1. **Solo** (1 file, ≤50 lines, no research) → Implement yourself → Verify
2. **Delegate** (everything else) → Create agent chain → agents execute autonomously → you receive final report from Validator → report to user

**Chain flow:** You → [Researcher + Analyzer] → Implementer ↔ Validator (max 3 loops) → You → User

**Key rules:**
- Agents communicate DIRECTLY with each other (peer-to-peer via SendMessage)
- You do NOT relay messages between agents
- You do NOT read code or validate — Validator handles this
- After completion: clean up Researcher/Analyzer, keep Implementer/Validator alive
- Only clean up entire team when USER confirms everything is OK

**Agent models:** Read `.claude/rules/workflow/agent-models.md` for model per role. `inherit` → omit `model` param (uses chat model). Other values (`sonnet`, `opus`, `haiku`) → pass as `model` param.

---

## CRITICAL: API Verification Before Planning

**When user provides screenshots/designs for a feature:**

1. **BEFORE creating API types/services/hooks** → ASK: "Is there a backend API for this? What are the endpoints?"
2. **If user doesn't provide API docs** → Do NOT create API tasks. Mark them as BLOCKED or ask.
3. **NEVER invent** endpoint URLs, field names, or response structures from screenshots alone.
4. **Why:** Hallucinating API structures causes cascading failures — wrong types → wrong hooks → empty/broken UI.

---

## CRITICAL: Visual Task Mandatory Agents

**For ANY task with screenshots/Figma specs, you MUST spawn ALL agents (see `agent-management.md`).**
**Agents receive detailed instructions via skills:** `/agent:common`, `/agent:analyzer`, `/agent:implementer`, `/agent:validator`

**Skipping ANY agent is FORBIDDEN.** If you "validate" without a validator agent,
the validation is fake and critical issues WILL be missed.

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
