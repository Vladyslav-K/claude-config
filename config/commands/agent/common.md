---
name: agent:common
description: Shared foundation rules for ALL team agents. Project memory, common mistakes, code conventions, chain communication protocol.
---

# Agent Common Rules

## FIRST: Read Project Context

### Project Memory
If the directory exists, read ALL files in `.project-meta/memory/`:
- `project-overview.md` — project architecture and key concepts
- `project-structure.md` — file tree with descriptions
- `recent-session.md` — context from last session
- `changelog.md` — history of changes

### Known Mistakes
Read `.claude/rules/common-mistakes.md` if it exists.
These are REAL mistakes from previous implementations. You MUST avoid ALL of them.

---

## Code Rules

- ALL code, comments, and file names must be in **English**
- Do NOT leave comments unrelated to code (no task descriptions, no change notes)
- Do NOT create test files unless explicitly specified in the task
- Do NOT add unnecessary comments or documentation
- Do NOT add features, refactor code, or make "improvements" beyond what was asked
- Do NOT add error handling, fallbacks, or validation for scenarios that can't happen
- Follow existing project code patterns EXACTLY — find similar code and use as a template
- Use the **same libraries and patterns** the project already uses
- NEVER install new packages without checking the latest stable version first

---

## Post-Implementation

After finishing your work:
1. Check what **package manager** the project uses (lockfile: `package-lock.json` → npm, `pnpm-lock.yaml` → pnpm, `bun.lockb` → bun)
2. Run the project's format/lint/typecheck scripts:
   - First try: `format-and-check` script in package.json
   - If not exists: run `format`, `lint`, `typecheck` separately
   - Do NOT use `npx` commands — use scripts from package.json
3. Fix ALL issues found by these scripts

---

## Chain Communication Protocol

You are part of a chain workflow where agents communicate DIRECTLY via `SendMessage`.

### Key Rules
- Use `SendMessage` with `type: "message"` to send to another agent by **NAME**
- Include a `summary` field (5-10 words) with each message
- When passing the TASK through the chain, paste it **UNCHANGED** — do not modify, summarize, or reinterpret
- If you receive a task from the orchestrator (team lead), pass it forward unchanged to the next agent

### Message Format Convention
Always structure your messages with clear sections using markdown headers:
```
## TASK (from orchestrator — DO NOT modify)
[Original task, unchanged]

## YOUR OUTPUT
[Your role-specific output: research, analysis, report, etc.]
```

---

## File Operations Safety

- NEVER delete files unless explicitly told to
- NEVER modify files outside the scope of your task
- Be careful with imports — use exact paths from the project, not invented ones
- If creating a NEW page/route, you MUST integrate with existing layout (page titles, sidebar, routing)
