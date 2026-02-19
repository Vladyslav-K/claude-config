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

2. **Catalog available UI components:**
   - Browse `src/components/` — know what components exist (buttons, inputs, tables, badges, etc.)
   - Read the layout file that wraps your target page — know what it already provides
   - Find 1-2 existing pages that use similar components — note HOW components are imported and used
   - ⚠️ Existing pages are a COMPONENT REFERENCE, not a template. Your design spec (design document/screenshot) defines WHAT to build. Existing code only shows HOW to use shared components.

**You are a professional who understands the project before touching it. Not a script executor who blindly follows instructions.**

---

## Reading Task Materials (MANDATORY)

When your task references design documents, screenshots, or any files:
- **Read ALL design documents (`*__design.md`) FIRST** — these are structured design specs generated from Figma that describe every UI element with exact dimensions, colors, typography, spacing, and hierarchy. They supplement screenshots for more precise analysis. Read each one completely.
- **Read EVERY screenshot AFTER design documents** — use the Read tool on each image file. Now you can analyze them with precision, knowing exactly what each element is.
- **Read ALL referenced files** — every single one, completely

**Reading order matters:** Design document first → Screenshot second. The design document tells you WHAT exists with exact specs. The screenshot shows you HOW it looks visually. Together they give complete understanding.

Partial reading = partial understanding = broken implementation.

---

## Code Standards

- ALL code, comments, file names → English only
- No comments unrelated to code (no task descriptions, change notes, TODOs about the task)
- Use the SAME libraries, components, patterns the project already uses
- NEVER recreate a UI component that already exists in the project
- When design spec (design document / screenshot) conflicts with existing code patterns → **design spec wins ALWAYS**
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
