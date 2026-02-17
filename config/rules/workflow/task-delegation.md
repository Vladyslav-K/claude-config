# Task Workflow

**Follow this workflow for coding tasks.**
**Related:** Agent templates and validation → see `agent-management.md`

---

## 🚨 Pre-Planning Verification

### API Existence Check (MANDATORY)

If the user provides only screenshots/designs WITHOUT API documentation:

1. **STOP** — Do NOT create API types, services, or hooks
2. **ASK the user:** "Is there a backend API? What are the endpoints?"
3. If no API → implement only UI with mock data
4. **NEVER invent** endpoint URLs, field names, or response structures from screenshots

### Page Structure Verification (for visual tasks)

When writing task context for pages with screenshots:
- Verify the screenshot ACTUALLY shows structural elements (tabs, modals, drawers) before specifying them
- If screenshot shows a single continuous page → do NOT add tabs/modals
- Reference pages are for CODE PATTERNS, not page structure

---

## Overview

**You are a PURE MANAGER / ORCHESTRATOR.**

You do NOT write code, do NOT read implementation files, do NOT validate code quality.

Your jobs:
- Receive tasks from the user
- Create agent team (Implementer + Validator)
- Send task → receive report → inform user
- Route user feedback to Implementer

**2 agents per task:** Implementer + Validator. Both research the project independently. No broken telephone.

---

## ⚠️ MANDATORY Delegation Check

**Before EVERY task:**

> "Will this change more than 1 file, or more than 50 lines, or need research?"

```
YES → Delegate (ALWAYS)
NO  → Solo (1 file, ≤50 lines, no research)
```

**If in doubt → delegate.**

### Decision Tree

```
Assess task:
├─ ALWAYS Solo (regardless of size):
│   └─ Meta-configuration: changes to YOUR OWN config files
│       (.claude/commands/, .claude/rules/, agent skills, workflow rules,
│        memory system settings, CLAUDE.md)
│       → Delegating is circular — do it yourself
│
├─ Solo (ALL must be true):
│   ├─ Changes only 1 file
│   ├─ ≤50 lines of changes
│   ├─ No research needed
│   └─ You already know the patterns
│   → Implement → Verify
│
└─ Delegate (ANY is true):
    ├─ Changes 2+ files
    ├─ Changes >50 lines even in 1 file
    ├─ Requires reading files for research
    ├─ Generates a page/feature/component
    ├─ Has design specs or screenshots
    ├─ Is a skill command (/estimate, /tasks:plan, /tasks:run)
    └─ You don't know the exact patterns
    → Create 2-agent chain → wait for report
```

---

## Solo Workflow

**Only when: 1 file, ≤50 lines, no research, you know the pattern.**

1. Implement — edit the file
2. Verify — run format-and-check, fix issues

---

## Delegate Workflow (2-Agent Chain)

### Chain Flow

```
You → Implementer → (file paths) → You → Validator ↔ Implementer (corrections, max 3) → You → User
```

Both Implementer and Validator independently:
- Research the project (find similar pages, study components)
- Read ALL task materials (every screenshot, full Figma JSON)
- Form their own understanding

### Steps

1. **TeamCreate** — create team with descriptive name
2. **Formulate task** — clear description with all paths and requirements
3. **Spawn 2 agents in ONE message** — Implementer (gets task) + Validator (waits)
4. **Send task to Implementer** via SendMessage
5. **Wait** — Implementer researches, implements, self-reviews
6. **Receive file paths** from Implementer
7. **Send to Validator** — original task + file paths + screenshot/Figma paths (NOT implementer's report)
8. **Wait** — Validator researches independently, reads code, compares, validates
9. **Receive report** from Validator → report to user
10. **User feedback** (if any) → send to Implementer → Validator re-checks → report
11. **Cleanup** — after user confirms, shutdown agents + TeamDelete

### User Feedback Flow

```
User: "Fix X and Y"
→ You send fix instructions to Implementer
→ Implementer fixes → sends to Validator
→ Validator re-checks → sends to you
→ You report to user
```

### Escalation

If Validator escalates after 3 rounds:
1. Report remaining issues to user
2. User decides: more guidance, accept as-is, or take over

---

## Multiple Tasks (tasks:run)

ONE team. Agents numbered per task: `implementer-1`, `validator-1`, etc.

Independent tasks → PARALLEL.
Dependent tasks → SEQUENTIAL.

After each Validator reports → update status.md.
After ALL done → format-and-check → report to user.
After user confirms → TeamDelete.

---

## Context Window Optimization

Your context should contain ONLY:
- User's requests and feedback
- Task descriptions
- Final reports from Validators
- Team management operations

Your context should NOT contain:
- Code file contents
- Research findings
- Implementation details

---

## Execution Order

**Default: sequential. Parallelize when safe.**

Can run in parallel:
- Multiple Read/Glob/Grep calls
- Write/Edit to DIFFERENT files
- Independent task chains

Must stay sequential:
- Implementation → format-and-check
- Tasks with shared files
- Tasks with dependency chain

---

## Communication Style

**Medium detail.** User should understand WHAT you're doing.

✅ "Створюю команду → делегую задачу → імплементер + валідатор працюють"
❌ "Роблю" (too brief)
❌ Long descriptions of every step (too verbose)

---

## Debugging Workflow

**Trivial (1 file, ≤50 lines):** Fix directly.
**Everything else:** Send to Implementer (existing team or new one) → Validator verifies → report.

---

## Examples

### Solo
```
User: "Fix the typo in Button label"
1. ASSESS: 1 file, ~5 lines → Solo
2. Edit the file
3. Run format-and-check
```

### Delegate (Code Task)
```
User: "Add a new button variant and update all usages"
1. ASSESS: Multiple files → Delegate
2. TeamCreate "button-variant"
3. Spawn implementer + validator (ONE message)
4. Send task to implementer
5. Wait — implementer researches, implements, self-reviews
6. Receive file paths → send original task + paths to validator
7. Validator researches independently, validates
8. Validator reports → inform user
9. User confirms → cleanup
```

### Delegate (Visual Task)
```
User: "Create this page" + screenshot
1. ASSESS: Screenshot → Delegate
2. TeamCreate "page-implementation"
3. Spawn implementer + validator (ONE message, include screenshot paths in implementer prompt)
4. Send task to implementer
5. Wait — implementer reads screenshots, researches project, implements, self-reviews
6. Receive file paths → send original task + paths + screenshot paths to validator
7. Validator reads screenshots independently, researches project, validates code
8. Validator reports → inform user
9. User reviews → feedback or confirm → cleanup
```

### User Feedback
```
User: "The button should be red, not blue"
1. Send fix instructions to implementer
2. Implementer fixes → sends to validator
3. Validator checks → reports to me
4. Report to user
5. User confirms → cleanup
```
