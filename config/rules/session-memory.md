# 🚨 Session Memory

**File:** `.project-meta/memory/recent-session.md`

Auto-loaded every session — the project's `.claude/CLAUDE.md` imports it via `@../.project-meta/memory/recent-session.md`, so its content is already in context without any manual read. If the project has no `.claude/CLAUDE.md` with this import, run `/project-meta-init` to set it up.

**Trigger "збережи сесію"** → overwrite `.project-meta/memory/recent-session.md` with a short summary:
- Date (YYYY-MM-DD)
- What was done
- Files touched
- Current state
- Next steps / blockers

Overwrite, don't append. Keep it concise — this is short-term context for the next session.

**Don't store here:** coding rules (already in `rules/`), long-term knowledge that must survive across projects (put those in `~/.claude/CLAUDE.md` manually).
