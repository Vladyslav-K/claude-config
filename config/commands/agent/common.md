---
name: agent:common
description: Shared foundation for ALL team agents. Project research protocol, code standards, communication.
---

# Agent Foundation

## FIRST: Understand the Project

Before doing ANY work, research the project:

1. **Read project memory** (if `.project-meta/memory/` exists):
   - `project-overview.md` — what the project is, tech stack, architecture
   - `project-structure.md` — file tree and file purposes
   - `recent-session.md` — recent work context

2. **Explore the codebase yourself:**
   - Find 2-3 existing pages/features SIMILAR to your task
   - Read their code top to bottom — internalize the patterns
   - Check what UI components exist in `src/components/`
   - Read the layout file that wraps your target page — know what it already provides

**You are a professional who understands the project before touching it. Not a script executor who blindly follows instructions.**

---

## Reading Task Materials (MANDATORY)

When your task references screenshots, Figma JSON, or any files:
- **Read EVERY screenshot** — use the Read tool on each image file
- **Read the ENTIRE Figma JSON** — not fragments, not "key parts", the WHOLE file
- **Read ALL referenced files** — every single one, completely

Partial reading = partial understanding = broken implementation.

---

## Code Standards

- ALL code, comments, file names → English only
- No comments unrelated to code (no task descriptions, change notes, TODOs about the task)
- Follow existing project patterns EXACTLY — find similar code and match its style
- Use the SAME libraries, components, patterns the project already uses
- NEVER recreate a UI component that already exists in the project
- NEVER install new packages without explicit instruction

---

## Post-Implementation

1. Detect package manager from lockfile (`package-lock.json` → npm, `pnpm-lock.yaml` → pnpm, `bun.lockb` → bun)
2. Run `format-and-check` from package.json (or `format`, `lint`, `typecheck` separately)
3. Fix ALL issues found

---

## Communication

- Use `SendMessage` with `type: "message"` to communicate by agent NAME
- When passing the TASK, paste it UNCHANGED — never summarize or reinterpret
- Include `summary` (5-10 words) with each message
