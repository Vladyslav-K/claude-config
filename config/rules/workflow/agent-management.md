# Agent Management

**Agent orchestration, team setup, and two-phase implementer model with human validation.**
**For delegation decisions (solo vs delegate) → see `task-delegation.md`**

**Agent instructions are in skills:** `/agent:common`, `/agent:implementer`

---

## Agent Types

| Type | Model | Use for |
|------|-------|---------|
| `Explore` | Haiku (fast) | File search, grep, simple lookups |
| `general-purpose` | Inherits chat model | Implementation, deep analysis |

**Rule:** Just finding files → `Explore`. Anything that requires judgment → `general-purpose`.

**Search yourself (main context) ONLY when:** you already know the exact path, or it's a single glob/grep.

---

## Two-Phase Implementer + Human Validation (Default Workflow)

Each delegated task gets exactly **1 agent**: the Implementer.

**Phase 1: Research** — Implementer studies the project and design, sends research plan.
**User approves or requests changes.**

**Phase 2: Build** — Implementer codes (only after approval), self-reviews, runs format-and-check.
**User validates the result.**

### Flow

```
Orchestrator → Implementer (receives task)
                    │
                    ├─ Phase 1: Research
                    │   ├─ Reads ALL screenshots/Figma JSON
                    │   ├─ Studies existing codebase
                    │   └─ Sends RESEARCH PLAN to → Orchestrator
                    │                                    │
                    │               Orchestrator → Presents plan to User
                    │                                    │
                    │               ├─ User approves → Orchestrator sends GO
                    │               └─ User wants changes → routes to Implementer
                    │                    └─ Implementer revises → sends again
                    │                         (repeat until approved)
                    │
                    ├─ Phase 2: Build (after approval)
                    │   ├─ Implements following approved plan
                    │   ├─ Self-reviews against design
                    │   ├─ Runs format-and-check
                    │   └─ Reports file paths to → Orchestrator
                    │                                    │
                    │               Orchestrator → Reports to User
                    │                                    │
                    │               User reviews the result
                    │                                    │
                    │               ├─ All OK → done
                    │               └─ Issues → Orchestrator routes to Implementer
                    │                    └─ Implementer fixes → reports back
                    │                         (repeat until user confirms)
                    │
                    User confirms all → cleanup
```

---

## 🚫 Orchestrator Prohibition

The orchestrator is a PURE MANAGER. FORBIDDEN from:
1. Reading code files — agents handle all code
2. Analyzing screenshots or Figma — agents do this independently
3. Validating work quality — the user handles this
4. Searching codebase — agents research independently

The orchestrator's ONLY jobs:
- Create team and spawn implementers
- Send tasks to implementers
- Collect research plans → present to user for approval
- Route user feedback (plan changes or implementation fixes) to correct implementer
- Keep team alive until user confirms everything is OK
- Shutdown and cleanup after user confirms

---

## Agent Template

### Implementer Template

```
Task tool:
  subagent_type: "general-purpose"
  team_name: "{team-name}"
  name: "implementer"
  mode: "bypassPermissions"
  prompt: |
    You are the Implementer. Team: "{team-name}".

    ## FIRST ACTION (MANDATORY)
    Invoke these skills using the Skill tool:
    1. Skill: "agent:common"
    2. Skill: "agent:implementer"
    Then follow the loaded instructions.

    ## YOUR CHAIN
    - You receive the task from: orchestrator (team lead)
    - FIRST send research plan to: orchestrator → user reviews
    - ONLY implement after orchestrator says "approved"
    - After completion, send file paths to: orchestrator (team lead)
    - Corrections come from: orchestrator (team lead) — these are USER feedback
    - After fixes, send updated file list to: orchestrator (team lead)

    ## TASK
    {Full task description}

    ## SCREENSHOTS (if visual task)
    {Screenshot file paths — READ ALL of them}

    ## FIGMA JSON (if available)
    {Figma JSON file paths — READ THE ENTIRE file}
```

---

## Step-by-Step Execution

### Step 1: Create Team
```
TeamCreate:
  team_name: "{descriptive-name}"
  description: "Working on {brief task summary}"
```

### Step 2: Formulate the Task

Write a clear task description with:
- What to build/change (requirements from user)
- Screenshot paths if visual task
- Figma JSON paths if available
- Any user constraints or preferences

### Step 3: Spawn Implementer

Single Task tool call with the implementer template.

### Step 4: Send Research Task

Send the task via `SendMessage` to "implementer" with instruction to research first and send plan.

The implementer will:
- Research the project independently
- Read all task materials (screenshots, Figma JSON)
- Send a research plan back to YOU

### Step 5: Present Plan to User

Forward the implementer's research plan to the user.
Wait for approval or feedback.

If user wants changes → route to implementer → get revised plan → present again.

### Step 6: Send GO

After user approves the plan, tell the implementer to proceed with implementation.

### Step 7: Report Results to User

When implementer reports file paths, inform the user:
- What task was completed
- Which files were created/modified
- Ask user to review

### Step 8: Handle User Feedback (if any)

User found issues:
1. Send fix instructions to implementer via `SendMessage`
2. Implementer fixes → sends updated file list to you
3. Report back to user
4. Repeat until user satisfied

### Step 9: Cleanup

After user confirms everything is OK:
- Send shutdown_request to implementer
- Delete team via `TeamDelete`

---

## Multiple Tasks (tasks:run)

ONE team for all tasks. Implementers numbered per task:
- `implementer-1`, `implementer-2`, etc.

**Phased execution within each batch:**
1. All implementers research in PARALLEL
2. Plans presented to user ONE BY ONE (sequential)
3. After ALL approved → implementation in PARALLEL
4. User reviews results

After each batch → next batch (newly unblocked tasks).
After ALL done → run format-and-check → report to user.
User reviews → feedback loop if needed → confirm.
After user confirms → TeamDelete.

---

## Memory Integration

If `.project-meta/memory/` exists, agents discover it via `/agent:common` skill instructions. No need to paste memory content in prompts — agents read it themselves.
