# Task Execution Workflow

**You are the implementer. You read files, plan, build, and self-review yourself — none of this delegates to agents.**

Only agent you use: `Explore` (Agent tool, `subagent_type: "Explore"`) — for file search/grep. You READ found files and MAKE DECISIONS yourself.

**🔴 Agents NEVER write/edit code.** They lack thinking capability and produce terrible results. All code changes are made by you in the main context. Agents cannot replace the discovery → decide → implement loop.

---

## Research Tools

| Tool | When |
|------|------|
| Glob/Grep | You know roughly where to look |
| Explore agent | Broad search, codebase exploration |
| Read | After finding files — always read and analyze yourself |

---

## Task Complexity

| Level | Criteria | Flow |
|-------|----------|------|
| Simple | 1 file, ≤50 lines | Do it → format-and-check |
| Standard | Multi-file, known patterns | Research → implement → self-review → format-and-check |
| Complex | New features, design specs | Research → plan → user approval → implement → self-review → format-and-check |

---

## Execution Steps

1. **Understand** — Read all materials. Order: design document → screenshot → task description
2. **Research** — Find relevant files, understand patterns, catalog reusable components
3. **Plan (complex tasks only)** — Present to user:
   - Design elements found (with specs)
   - Existing components to reuse (path + purpose)
   - New code to create (path + what it does)
   - Wait for approval
4. **Implement** — Section by section. Use existing components. Match design exactly.
5. **Self-review** — Re-read design. Every element implemented? Anything extra? Anything missing?
6. **Verify** — Run format-and-check. Fix ALL issues. Report to user.

---

## API Verification (MANDATORY)

If user provides screenshots/designs WITHOUT API docs:
1. **STOP** — Do NOT create API types, services, or hooks
2. **ASK:** "Is there a backend API? What are the endpoints?"
3. If no API → UI with mock data only
4. **NEVER invent** endpoints, field names, or response structures from screenshots

---

## Multi-Task Execution

1. Read tasks.md + status.md
2. Execute ONE task at a time, respecting dependencies
3. Update status.md after each task
4. Continue through autocompact
5. After ALL done — final format-and-check, report to user

---

## In-Session Task Tracking

When you would otherwise reach for the built-in `TaskCreate` todo (multi-step / multi-file work that needs a checklist) — use **file-based tracking** instead. The built-in todo renders as a half-screen block that hides real work output; files do not.

- **Files:** `.project-meta/tasks/session-tasks.md` (list) + `.project-meta/tasks/session-status.md` (table).
- **Format:** mirrors `/tasks:plan-full`, trimmed for in-session use. Status flow: `pending` → `running` → `done` / `blocked`.
- **Built-in `TaskCreate` / `TaskUpdate` / `TaskList` / `TaskGet` / `TaskOutput` / `TaskStop` are BANNED** for this purpose. Do not load them via `ToolSearch` either.
- **Full protocol:** `.claude/rules/task-tracking.md`.

Threshold is identical to TaskCreate's: trivial one-shot edits skip the tracker.

---

## Context Management

- Use Explore agent for broad searches (saves your context)
- Read only files you need — don't read entire directories
- Don't re-read files you just wrote unless debugging

---

## Communication Style

**Medium detail.** User should understand WHAT you're doing.

✅ "Досліджую проект → покажу план → після ОК кодю → перевірю"
❌ "Роблю" (too brief)
❌ Long descriptions of every step (too verbose)
