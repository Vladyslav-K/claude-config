---
name: project-meta-init
description: Initialize project folder structure for task management, estimation, and session memory. Creates .project-meta/ with all required subfolders and wires up auto-loaded session memory via .claude/CLAUDE.md.
---

# Project Meta Initialization

Create the folder structure used by `/tasks:plan`, `/tasks:run`, `/estimate`, and the session memory system.

## Structure

```
.project-meta/
├── tasks/
│   └── plan/
│       └── screenshots/     # Task descriptions + design documents + screenshots
├── estimation/
│   └── screenshots/         # Task files + screenshots for estimation
└── memory/
    └── recent-session.md    # Short-term: last session summary (overwritten each time)

.claude/
└── CLAUDE.md                # Auto-loaded every session; imports recent-session.md
```

## Execute

```bash
mkdir -p .project-meta/tasks/plan/screenshots
mkdir -p .project-meta/estimation/screenshots
mkdir -p .project-meta/memory
mkdir -p .claude
touch .project-meta/memory/recent-session.md

if [ ! -f .claude/CLAUDE.md ]; then
  printf '@../.project-meta/memory/recent-session.md\n' > .claude/CLAUDE.md
elif ! grep -qF '@../.project-meta/memory/recent-session.md' .claude/CLAUDE.md; then
  printf '\n@../.project-meta/memory/recent-session.md\n' >> .claude/CLAUDE.md
fi
```

After creating, report what was created and remind usage:
- `/tasks:plan` — add .md files to `tasks/plan/`, screenshots to `tasks/plan/screenshots/`
- `/tasks:run` — execute planned tasks sequentially
- `/estimate` — add task files to `estimation/`, screenshots to `estimation/screenshots/`
- Say "збережи сесію" at end of session — I'll overwrite `recent-session.md` with a summary; next session it auto-loads via `.claude/CLAUDE.md`

## Notes
- Idempotent — safe to run multiple times
- Existing files will NOT be deleted or overwritten; the `@`-import line is appended to an existing `.claude/CLAUDE.md` only if missing
- `.project-meta/` is typically gitignored
