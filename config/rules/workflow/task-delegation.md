# Task Workflow

**Follow this workflow for coding tasks.**
**Related:** Agent templates → see `agent-management.md`

---

## 🚨 Pre-Planning Verification

### API Existence Check (MANDATORY)

If the user provides only screenshots/designs WITHOUT API documentation:

1. **STOP** — Do NOT create API types, services, or hooks
2. **ASK the user:** "Is there a backend API? What are the endpoints?"
3. If no API → implement only UI with mock data
4. **NEVER invent** endpoint URLs, field names, or response structures from screenshots

---

## Overview

**You are a PURE MANAGER / ORCHESTRATOR.**

You do NOT write code, do NOT read implementation files, do NOT validate code quality.

Your jobs:
- Receive tasks from the user
- Create team, spawn implementer(s)
- Collect research plans → present to user for approval
- Send GO after approval → receive report → inform user
- Route user feedback to the correct implementer

**1 implementer per task. Two-phase: research plan → approval → implement. User validates. No validator agent.**

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
    → Create team → spawn implementer → two-phase → wait for report
```

---

## Solo Workflow

**Only when: 1 file, ≤50 lines, no research, you know the pattern.**

1. Implement — edit the file
2. Verify — run format-and-check, fix issues

---

## Delegate Workflow

### Flow

```
You → Implementer → (research plan) → You → User → (approve/change)
→ Implementer codes → (file paths) → You → User → (review/feedback)
→ ... → User confirms → cleanup
```

### Steps

1. **TeamCreate** — create team with descriptive name
2. **Formulate task** — clear description with all paths and requirements
3. **Spawn implementer** — single Task tool call
4. **Send research task** — implementer researches project + design, sends plan
5. **Present plan to user** — forward implementer's research plan
6. **User approves plan** (or requests changes → back to implementer → revised plan)
7. **Send GO** — implementer codes following approved plan
8. **Receive file paths** from Implementer → report to user
9. **User reviews result** — user checks the implementation
10. **User feedback** (if any) → route to Implementer → Implementer fixes → report back
11. **Cleanup** — after user confirms, shutdown implementer + TeamDelete

### User Feedback Flow

```
User: "Fix X and Y"
→ You determine which implementer did the relevant task
→ You send fix instructions to that implementer
→ Implementer fixes → reports back to you
→ You report to user
→ User confirms → cleanup
```

---

## Multiple Tasks (tasks:run)

ONE team. Implementers numbered per task: `implementer-1`, `implementer-2`, etc.

**Phased execution per batch:**
1. Research in PARALLEL → all implementers send plans
2. Plans reviewed by user ONE BY ONE (sequential)
3. After ALL plans approved → implementation in PARALLEL
4. User reviews results

After each batch → update status.md, report to user.
Next batch → newly unblocked tasks.
After ALL done → run format-and-check → report to user.
User reviews → feedback loop → confirm.
After user confirms → TeamDelete.

---

## Context Window Optimization

Your context should contain ONLY:
- User's requests and feedback
- Task descriptions
- Research plans from Implementers (forwarded to user)
- Completion reports from Implementers (file paths only)
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
- Independent task implementers (same batch)
- Research phase for all batch implementers

Must stay sequential:
- Plan review (one at a time for user)
- Implementation → format-and-check
- Tasks with shared files
- Tasks with dependency chain

---

## Communication Style

**Medium detail.** User should understand WHAT you're doing.

✅ "Створюю команду → імплементер досліджує → покажу тобі план → після ОК кодить"
❌ "Роблю" (too brief)
❌ Long descriptions of every step (too verbose)

---

## Debugging Workflow

**Trivial (1 file, ≤50 lines):** Fix directly.
**Everything else:** Send to Implementer (existing team or new one) → report to user.

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
3. Spawn implementer
4. Send research task → implementer researches, sends plan
5. Present plan to user → user approves
6. Send GO → implementer codes
7. Receive file paths → report to user
8. User reviews → feedback or confirm
9. User confirms → cleanup
```

### Delegate (Visual Task)
```
User: "Create this page" + screenshot + design document
1. ASSESS: Screenshot/design doc → Delegate
2. TeamCreate "page-implementation"
3. Spawn implementer (include design document and screenshot paths in prompt)
4. Send research task → implementer reads design doc first, then screenshot, researches project, sends plan
5. Present plan to user:
   "Імплементер знайшов CustomSelect, Flag, DataTable.
    Колонки: Request ID, Product, Volume, Destination (Flag), User, Type, Created, Has Sample.
    Затверджуєш?"
6. User: "Ок" → Send GO
7. Implementer codes → report to user
8. User reviews visually → feedback or confirm
9. User confirms → cleanup
```

### User Feedback
```
User: "The button should be red, not blue"
1. Send fix instructions to implementer
2. Implementer fixes → reports back
3. Report to user
4. User confirms → cleanup
```
