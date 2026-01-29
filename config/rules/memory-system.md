# Memory System

## Overview

This system maintains project context between sessions using files in `.project-meta/memory/` directory.

**SessionStart hook** automatically loads memory files into context at session start.

---

## Memory Files Structure

```
.project-meta/memory/
  project-overview.md   # ~800 words - project structure, tech stack, architecture
  changelog.md          # ~1500 words - history of changes (FIFO by date)
  recent-session.md     # ~1500 words - FULL last session context (primary file!)
```

### project-overview.md
- **Purpose:** Quick understanding of project
- **Contains:** Tech stack, architecture, folder structure, key patterns
- **Update:** Only on major architectural changes
- **Limit:** ~800 words

### changelog.md
- **Purpose:** Track project evolution
- **Contains:** Dated entries of significant changes
- **Update:** After meaningful feature/change completion
- **Limit:** ~1500 words (FIFO - oldest entries removed first)
- **Format:**
```markdown
### [YYYY-MM-DD] | priority: milestone
Major feature or architectural change...

### [YYYY-MM-DD] | priority: normal
Regular feature or fix...
```

### recent-session.md (PRIMARY FILE)
- **Purpose:** Complete context handoff between sessions
- **Contains:** Full task context, files changed, decisions made, next steps
- **Update:** When user triggers memory update
- **Limit:** ~1500 words (fully rewritten each time)

**This is the MOST IMPORTANT file** - it enables seamless session continuation.

---

## CRITICAL: User Commands (Multi-language)

**When user says ANY of these phrases, trigger memory update:**

### English
- `update memory`
- `save memory`
- `save context`
- `remember this`

### Ukrainian
- `онови пам'ять`
- `оновити пам'ять`
- `збережи пам'ять`
- `запам'ятай`
- `збережи контекст`

### Short forms
- `memory update`
- `save mem`
- `пам'ять`

---

## How to Update Memory

### Step 1: Prepare Context Summary

**BEFORE calling the memory-writer agent, YOU must prepare a comprehensive context summary.**

Gather and write out:

```markdown
## SESSION CONTEXT FOR MEMORY

### Task Overview
[What was the user's original request? What problem were we solving?]

### Approach & Decisions
[What approach did we take? Why? Any alternatives considered?]

### Work Completed
[List each change with explanation]
- Created `/path/to/file.tsx`: [What it does, why it was created]
- Modified `/path/to/other.ts`: [What changed, why]
- Deleted `/path/to/old.js`: [Why removed]

### Implementation Details
[Key technical details someone continuing this work should know]
- Used X library because...
- Followed Y pattern from existing code...
- API endpoint expects Z format...

### Issues Encountered
[Any problems, blockers, or workarounds]
- Issue: [description] → Solution: [how we solved it]
- Blocker: [what's blocking] → Need: [what's needed to unblock]

### Current State
- What's working: [list]
- What's not working: [list]
- What's incomplete: [list]

### Next Steps (Priority Order)
1. [HIGH] [Specific actionable task]
2. [MEDIUM] [Specific actionable task]
3. [LOW] [Specific actionable task]

### User Preferences Noted
[Any preferences user mentioned during session]
```

### Step 2: Call memory-writer Agent

```
Task tool:
  subagent_type: "memory-writer"
  run_in_background: false
  prompt: |
    Update memory files at: {CWD}/.project-meta/memory/

    Here is the complete session context:

    [PASTE YOUR CONTEXT SUMMARY HERE]

    Update the memory files following the agent's format guidelines.
```

### Step 3: Confirm to User

After agent completes:
- Verify files were updated correctly
- Tell user: "Пам'ять оновлено ✓"

---

## Context Summary Guidelines

### GOOD Context (Detailed, actionable):
```
### Task Overview
User wanted to add dark mode toggle to the header. The app already had
Tailwind dark mode configured but no UI to switch between modes.

### Work Completed
- Created `/src/components/theme-toggle.tsx`: Button component using
  next-themes to toggle between light/dark modes. Uses Lucide icons
  for sun/moon. Follows existing Button component pattern from Shadcn.
- Modified `/src/components/header.tsx`: Added ThemeToggle to the right
  side of header, next to user avatar.
- Modified `/src/app/layout.tsx`: Wrapped app in ThemeProvider from
  next-themes with defaultTheme="system".

### Issues Encountered
- Issue: Flash of wrong theme on page load
  → Solution: Added suppressHydrationWarning to html element

### Next Steps
1. [HIGH] Add theme preference to user settings page
2. [MEDIUM] Add system theme detection improvements
```

### BAD Context (Vague, unhelpful):
```
### Task Overview
Added dark mode

### Work Completed
- Created theme toggle component
- Modified some files

### Next Steps
- Finish the feature
```

---

## Creating Memory for New Project

**When user says ANY of these:**

### English
- `init memory`
- `create memory`
- `initialize memory`
- `setup memory`

### Ukrainian
- `створи пам'ять`
- `ініціалізуй пам'ять`
- `налаштуй пам'ять`
- `почни пам'ять`
- `нова пам'ять`

**Then:**

1. Create `.project-meta/memory/` directory
2. Explore project structure
3. Create initial files:
   - `project-overview.md` - document what you discover
   - `changelog.md` - start with init entry
   - `recent-session.md` - note initial setup

---

## Word Count Guidelines

| File | Target | Max |
|------|--------|-----|
| project-overview.md | 600 | 800 |
| changelog.md | 1200 | 1500 |
| recent-session.md | 1000 | 1500 |

**Total:** ~3000-4000 words max

When limit exceeded:
- `changelog.md` - remove oldest `priority: minor` entries first, then `normal`
- `recent-session.md` - prioritize most recent/relevant context
- `project-overview.md` - condense descriptions

---

## Format Rules

- Write memory files in **English**
- Use bullet points and tables for clarity
- Include file paths where relevant
- No code snippets (just describe changes)
- Be comprehensive but organized
- Use headers to structure information

---

## Why This System Works

1. **recent-session.md** = Your "working memory" - what you're actively doing
2. **changelog.md** = Your "long-term memory" - what happened over time
3. **project-overview.md** = Your "reference docs" - how the project works

The next session reads these files and immediately has context to continue work.
