# Agent Management

**Agent orchestration, team setup, and 2-agent chain model.**
**For delegation decisions (solo vs delegate) → see `task-delegation.md`**

**Agent instructions are in skills:** `/agent:common`, `/agent:implementer`, `/agent:validator`

---

## Agent Types

| Type | Model | Use for |
|------|-------|---------|
| `Explore` | Haiku (fast) | File search, grep, simple lookups |
| `general-purpose` | Inherits chat model | Implementation, validation, deep analysis |

**Rule:** Just finding files → `Explore`. Anything that requires judgment → `general-purpose`.

**Search yourself (main context) ONLY when:** you already know the exact path, or it's a single glob/grep.

---

## 2-Agent Chain (Default Workflow)

Every delegated task uses exactly **2 agents**: Implementer + Validator.

Both agents research the project INDEPENDENTLY. No broken telephone — each agent sees the original task and forms their own understanding.

### Chain Flow

```
Orchestrator → Implementer (receives task)
                    │
                    ├─ Researches project independently
                    ├─ Reads ALL screenshots/Figma JSON
                    ├─ Implements
                    ├─ Self-reviews
                    └─ Reports file paths to → Orchestrator
                                                    │
                                    Orchestrator → Validator (receives original task + file paths)
                                                    │
                                                    ├─ Researches project independently
                                                    ├─ Reads ALL screenshots/Figma JSON
                                                    ├─ Reads implemented code
                                                    ├─ Compares independently
                                                    └─ Decision:
                                                        ├─ Issues? → Corrections → Implementer → fix → Validator (max 3 loops)
                                                        ├─ All OK? → ✅ Report → Orchestrator → User
                                                        └─ 3 fails? → ⚠️ Escalation → Orchestrator → User
```

### Key Principle: Blind Validation

The Validator NEVER sees the Implementer's self-assessment. Validator receives:
- Original task (from orchestrator)
- File paths (from orchestrator)
- Screenshots/Figma paths (from orchestrator)

Validator forms their OWN understanding of what the result should look like, THEN checks the code.

---

## 🚫 Orchestrator Prohibition

The orchestrator is a PURE MANAGER. FORBIDDEN from:
1. Reading code files — agents handle all code
2. Analyzing screenshots — agents do this independently
3. Validating work quality — Validator handles this
4. Relaying detailed messages between agents — keep agents independent

The orchestrator's ONLY jobs:
- Create team and spawn agents
- Send the task to Implementer
- Receive file paths from Implementer → forward original task + paths to Validator
- Receive final report from Validator → report to user
- Route user feedback to Implementer

---

## Agent Templates

**All agents invoke their skills as the FIRST action.**
**Spawn BOTH agents in a SINGLE message (parallel Task tool calls).**

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
    - After completion, send file paths to: orchestrator (team lead)
    - Corrections come from: validator
    - Send correction updates to: validator

    ## TASK
    {Full task description}

    ## SCREENSHOTS (if visual task)
    {Screenshot file paths — READ ALL of them}

    ## FIGMA JSON (if available)
    {Figma JSON file paths — READ THE ENTIRE file}
```

### Validator Template

```
Task tool:
  subagent_type: "general-purpose"
  team_name: "{team-name}"
  name: "validator"
  mode: "bypassPermissions"
  prompt: |
    You are the Validator. Team: "{team-name}".

    ## FIRST ACTION (MANDATORY)
    Invoke these skills using the Skill tool:
    1. Skill: "agent:common"
    2. Skill: "agent:validator"
    Then follow the loaded instructions.

    ## YOUR CHAIN
    - You receive the task + file paths from: orchestrator (team lead)
    - Send corrections to: implementer
    - Send final report to: orchestrator (team lead)

    ## WAIT
    Wait for the orchestrator to send you the task and file paths.
    Do NOT start until you receive a message.
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
- File paths if known
- Screenshot paths if visual task
- Figma JSON paths if available
- Any user constraints or preferences

### Step 3: Spawn BOTH Agents in ONE Message

Two parallel Task tool calls: Implementer + Validator.
Include the full task in Implementer's prompt. Validator waits for orchestrator message.

### Step 4: Send Task to Implementer

Send the task via `SendMessage` to "implementer". The implementer will:
- Research the project independently
- Read all task materials (screenshots, Figma JSON)
- Implement the task
- Self-review
- Send file paths back to YOU

### Step 5: Forward to Validator

When Implementer reports back with file paths:
- Send to "validator" via `SendMessage`: the ORIGINAL task + file paths + screenshot/Figma paths
- Do NOT include implementer's self-assessment

### Step 6: Wait for Validation

Validator works autonomously:
- Researches project independently
- Reads all task materials
- Reads implemented code
- Compares and validates
- If issues → sends corrections to Implementer directly (up to 3 rounds)
- If all OK → sends final report to YOU

### Step 7: Report to User

Pass Validator's summary to user. Do NOT read code yourself.

### Step 8: Handle User Feedback (if any)

User found issues:
1. Send fix instructions to **Implementer** via `SendMessage`
2. Implementer fixes → sends updated files to **Validator**
3. Validator re-checks → reports to you
4. Repeat until user satisfied

### Step 9: Cleanup

After user confirms everything is OK:
- Shut down Implementer and Validator
- Delete team via `TeamDelete`

---

## Multiple Tasks (tasks:run)

ONE team for all tasks. Agents numbered per task:
- `implementer-1`, `validator-1`
- `implementer-2`, `validator-2`

Independent tasks run in PARALLEL.
Dependent tasks run sequentially.

After each Validator reports → update status.md.
After ALL tasks done → run format-and-check → report to user.
After user confirms → TeamDelete.

---

## Memory Integration

If `.project-meta/memory/` exists, agents discover it via `/agent:common` skill instructions. No need to paste memory content in prompts — agents read it themselves.

---

## Escalation

If Validator escalates after 3 failed rounds:
1. Read the escalation report
2. Report to user with remaining issues
3. User decides: more guidance → send to Implementer, or accept as-is, or take over
