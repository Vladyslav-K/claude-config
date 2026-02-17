# Agent Management

**Agent orchestration, team setup, and chain communication model.**
**For delegation decisions (when to delegate, solo vs delegate) → see `task-delegation.md`**

**Detailed agent instructions are in skills:** `/agent:common`, `/agent:researcher`, `/agent:analyzer`, `/agent:implementer`, `/agent:validator`

---

## Agent Types & Selection

### Two Levels of Research

| Level | Agent | Model | Use when |
|-------|-------|-------|----------|
| **Simple lookup** | `Explore` | Haiku (fast, cheap) | Find files, grep patterns, check what exists |
| **Deep analysis** | `general-purpose` | Inherits chat model | Understand flows, analyze architecture, expert decisions |

### When to use Explore (Haiku)

- Find where a component/function is located
- Grep for a pattern across codebase
- List files in a directory structure
- Check what imports/exports exist
- Simple "does X exist?" questions

### When to use general-purpose (inherits model) for research

- Understanding how a complex flow works
- Analyzing architecture decisions
- Expert opinion on implementation approach
- When research quality directly affects implementation quality

**Rule of thumb:** Research answer shapes implementation → `general-purpose`. Just finding files → `Explore`.

### When to SEARCH yourself (main context)

Handle directly ONLY when:
- **Known location:** You already know the exact file path
- **Single lookup:** One glob or one grep, takes 1 tool call
- **Already in context:** Information is already in current conversation

---

## Visual Task Workflow

### 4 Agents Required (NON-NEGOTIABLE)

For visual tasks (screenshots/Figma), ALL 4 agents are MANDATORY:

1. **Researcher** — explores codebase, finds patterns
2. **Analyzer** — reads screenshot + Figma JSON, produces design specs
3. **Implementer** — builds using research + analysis
4. **Validator** — fresh-eyes comparison, correction loop

Chain: `[Researcher + Analyzer] (parallel) → Implementer ↔ Validator (max 3 loops)`

For code tasks (no screenshots): 3 agents — skip Analyzer.

### 🚫 Orchestrator Prohibition (HARD RULE)

The orchestrator is a PURE MANAGER. FORBIDDEN from:
1. Reading code files — agents handle all code
2. Reading screenshots for analysis — Analyzer does this
3. Comparing code to design — Validator does this
4. Relaying messages between agents — agents communicate DIRECTLY
5. Validating work quality — Validator handles this autonomously

The orchestrator's ONLY jobs:
- Create team and spawn agents
- Formulate and send the task
- Wait for Validator's final report
- Report to user
- Route user feedback to Implementer

### Chain Gates (enforced BY agents, not orchestrator)

| Gate | Enforced by | Rule |
|------|-------------|------|
| GATE 1 | Implementer | Must receive ALL expected inputs before coding |
| GATE 2 | Validator | Must find 0 issues before reporting success |
| GATE 3 | Validator | Max 3 correction rounds, then escalate |

---

## Agent Templates (Skill-Based)

**All agents invoke their skills as the FIRST action.**
**All agents communicate DIRECTLY with each other via SendMessage.**
**Model selection:** Use model from `.claude/rules/workflow/agent-models.md` per agent role. `inherit` → omit `model` param. Other values → pass as `model` param.

### Spawning Agents

Spawn ALL agents in a SINGLE message (parallel Task tool calls).

Each agent's prompt follows this structure:

```
Task tool:
  subagent_type: "general-purpose"
  team_name: "{team-name}"
  name: "{role}"
  mode: "bypassPermissions"
  prompt: |
    You are a {ROLE} agent in a chain workflow. Team: "{team-name}".

    ## FIRST ACTION (MANDATORY — DO THIS BEFORE ANYTHING ELSE)
    Invoke these skills using the Skill tool:
    1. Skill: "agent:common"
    2. Skill: "agent:{role}"
    Then follow the loaded instructions.

    ## YOUR CHAIN
    - You receive from: {sender agent name(s)}
    - You send to: {recipient agent name(s)}

    ## TASK CONTEXT
    {Brief task description or "Will be sent via message"}

    ## SCREENSHOTS (if visual task)
    {Screenshot paths}

    ## FIGMA JSON (if available)
    {Figma JSON paths}
```

### Agent Configuration Reference

| Agent | name | Receives from | Sends to |
|-------|------|---------------|----------|
| Researcher | researcher | Orchestrator (message) | implementer |
| Analyzer | analyzer | Orchestrator (message) | implementer |
| Implementer | implementer | researcher [+ analyzer] | validator |
| Validator | validator | implementer | Orchestrator (final) OR implementer (corrections) |

---

## Validation System (Autonomous)

The Validator agent operates autonomously:
- Receives implementer's report directly
- Validates against task + screenshot (if visual)
- Sends corrections to implementer (up to 3 rounds)
- Only reports to orchestrator when DONE or ESCALATING

**The orchestrator does NOT validate. The orchestrator does NOT read code.**

### Validation Chain Flow

```
Implementer → Validator
                 │
                 ├─ Issues found? → Corrections → Implementer → fix → Validator (repeat, max 3)
                 ├─ All correct? → ✅ Success report → Orchestrator
                 └─ 3 rounds failed? → ⚠️ Escalation → Orchestrator
```

### Orchestrator's Role

1. Receive Validator's report (success or escalation)
2. Report to user
3. Route user feedback to Implementer (not Validator)
4. Never read code — trust the chain

---

## Common Mistakes System

### File Location

| File | Path | Who edits |
|------|------|-----------|
| **Common Mistakes** | `.claude/rules/common-mistakes.md` | Orchestrator updates when user reports mistakes |

### When to Update

After user reports a mistake:
1. Fix the issue
2. Read the file to check if rule already exists
3. Exists → add new example under existing rule
4. New → write full rule entry

### Entry Format

```markdown
## [Category]

### [General rule name]
[1-2 sentences: WHEN this rule applies and WHAT to do]
- Example: [specific incident]
```

Categories: Page Structure, Layout & Nesting, Colors, Typography, Spacing, Components, Text Content, Page Integration, Element Duplication, Role-Inappropriate UI, Functional Completeness

### Agent Integration

All agents read common-mistakes.md via the `/agent:common` skill at session start.
