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

**READ: `.claude/rules/workflow/task-delegation.md` for full workflow.**

**Summary:**
1. **Research** → Delegate to `codebase-searcher` when needed (include memory paths!)
2. **Implement** → YOU write and edit code directly
3. **Verify** → Run format-and-check, fix any issues

**Available agents:** Only `codebase-searcher` (research).
All code writing, editing, review, and memory updates — YOU do directly.

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

