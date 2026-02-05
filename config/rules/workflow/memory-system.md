# Memory System

## Overview

This system maintains project context between sessions using files in `.project-meta/memory/` directory.

**SessionStart hook** automatically loads memory files into context at session start.

---

## Memory Files Structure

```
.project-meta/memory/
  project-overview.md    # ~1000 words - project essence, purpose, key concepts
  project-structure.md   # NO LIMIT - file tree with short descriptions
  changelog.md           # ~1500 words - history of changes (FIFO by date)
  recent-session.md      # ~1500 words - FULL last session context (primary file!)
```

### project-overview.md
- **Purpose:** Deep understanding of project's essence and architecture
- **Contains:** Project purpose, business logic, tech stack, architecture decisions, key patterns, conventions, important integrations
- **Does NOT contain:** File/folder structure (moved to project-structure.md)
- **Update:** Only on major architectural changes or when project scope changes
- **Limit:** ~1000 words
- **Focus areas:**
  - What the project does and why it exists
  - Core business logic and domain concepts
  - Technology choices and reasoning
  - Architectural patterns used
  - Key conventions and rules
  - External integrations and dependencies
  - Environment setup notes

### project-structure.md
- **Purpose:** Quick reference for file locations and their purposes
- **Contains:** Full directory tree with one-line descriptions for each file/folder
- **Update:** **MANDATORY** when ANY files/folders are created, deleted, or moved during a session. This file becomes stale fast — treat it as a living document that must reflect the actual project state.
- **Limit:** NO LIMIT (scales with project size)
- **Format:**
```markdown
## Project Structure

```
project-root/
├── src/
│   ├── app/                    # Next.js App Router pages
│   │   ├── (auth)/             # Auth-related routes group
│   │   ├── api/                # API route handlers
│   │   └── layout.tsx          # Root layout with providers
│   ├── components/
│   │   ├── ui/                 # Shadcn UI components
│   │   └── features/           # Feature-specific components
│   ├── lib/                    # Utility functions and configs
│   ├── hooks/                  # Custom React hooks
│   └── types/                  # TypeScript type definitions
├── public/                     # Static assets
├── prisma/                     # Database schema and migrations
└── package.json                # Dependencies and scripts
```

### Key Files
| File | Purpose |
|------|---------|
| `src/lib/auth.ts` | Authentication configuration |
| `src/lib/db.ts` | Database client instance |
```
- **Guidelines:**
  - Include ALL directories, but only important files
  - One-line descriptions should explain PURPOSE, not content
  - Use Key Files table for critical configuration files
  - Update when adding new feature folders or restructuring

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

**You update memory files DIRECTLY using Write/Edit tools. No delegation to agents.**

### Step 1: Gather Context

Before writing, mentally gather:
- What was the user's original request?
- What approach was taken and why?
- What files were created/modified/deleted?
- Key technical details for next session
- Issues encountered and solutions
- Current state (working / not working / incomplete)
- Next steps in priority order
- User preferences noted during session

### Step 2: Check File Changes

**Before writing memory, build a list of ALL files created/deleted/moved during this session.**

Ask yourself:
- Did I create any NEW files? → List them
- Did I delete any files? → List them
- Did I move/rename any files? → List them

**If the answer to ANY of the above is YES → `project-structure.md` MUST be updated.**

### Step 3: Update Memory Files Directly

Write/edit memory files at `{CWD}/.project-meta/memory/` using Write or Edit tools:

1. **recent-session.md** (ALWAYS update) — full rewrite with current session context
2. **project-structure.md** (ALWAYS update if files were created/deleted/moved) — add new files to tree, remove deleted ones. **This is NOT optional** — stale structure kills navigation in future sessions.
3. **changelog.md** (if meaningful changes were made) — append new dated entry
4. **project-overview.md** (only on major architectural changes) — update relevant sections

**⚡ PARALLEL WRITES:** All memory files are independent. Write/Edit them in parallel (multiple tool calls in one message) to save time. For example, write `recent-session.md`, `project-structure.md`, and `changelog.md` simultaneously — they never conflict.

**⚠️ SELF-CHECK:** Before confirming to user, verify: "Did I create/delete files this session? If yes, did I update project-structure.md?" If you missed it — go back and update.

### Step 4: Confirm to User

After writing files:
- Tell user: "Пам'ять оновлено ✓"
- If project-structure.md was updated, mention: "Структуру оновлено"

### Template for recent-session.md

```markdown
# Recent Session

## Date
[YYYY-MM-DD]

## Task Overview
[What was the user's original request? What problem were we solving?]

## Approach & Decisions
[What approach did we take? Why? Any alternatives considered?]

## Work Completed
- Created `/path/to/file.tsx`: [What it does, why it was created]
- Modified `/path/to/other.ts`: [What changed, why]
- Deleted `/path/to/old.js`: [Why removed]

## Implementation Details
[Key technical details someone continuing this work should know]

## Issues Encountered
- Issue: [description] → Solution: [how we solved it]

## Current State
- What's working: [list]
- What's not working: [list]
- What's incomplete: [list]

## Next Steps (Priority Order)
1. [HIGH] [Specific actionable task]
2. [MEDIUM] [Specific actionable task]
3. [LOW] [Specific actionable task]

## User Preferences Noted
[Any preferences user mentioned during session]
```

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
2. Explore project structure thoroughly
3. Create initial files:
   - `project-overview.md` - document project essence, purpose, tech stack, architecture
   - `project-structure.md` - generate full directory tree with descriptions
   - `changelog.md` - start with init entry
   - `recent-session.md` - note initial setup

---

## Word Count Guidelines

| File | Target | Max |
|------|--------|-----|
| project-overview.md | 800 | 1000 |
| project-structure.md | - | NO LIMIT |
| changelog.md | 1200 | 1500 |
| recent-session.md | 1000 | 1500 |

**Total:** ~4000-5000 words (excluding project-structure.md)

When limit exceeded:
- `changelog.md` - remove oldest `priority: minor` entries first, then `normal`
- `recent-session.md` - prioritize most recent/relevant context
- `project-overview.md` - condense less critical details, keep core concepts
- `project-structure.md` - never reduce (scales with project)

---

## Format Rules

- Write memory files in **English**
- Use bullet points and tables for clarity
- Include file paths where relevant
- No code snippets (just describe changes)
- Be comprehensive but organized
- Use headers to structure information

---

## Generating project-structure.md

### What to Include

**Always include:**
- ALL directories (with purpose description)
- Configuration files in root (package.json, tsconfig.json, etc.)
- Entry points (layout.tsx, page.tsx, index.ts)
- Critical business logic files
- API routes and handlers
- Database schemas and migrations
- Type definition files

**Skip:**
- Individual component files in large component folders (describe folder purpose instead)
- Test files (unless testing patterns are important)
- Auto-generated files (.next/, node_modules/, dist/)
- Lock files (package-lock.json, pnpm-lock.yaml)

### Tree Generation Strategy

1. Start from project root
2. Go 2-3 levels deep for most directories
3. Go deeper (4-5 levels) for critical paths like `src/app/` or `src/features/`
4. Use `...` to indicate more files exist in large directories

### Description Guidelines

| Element Type | Description Focus |
|--------------|-------------------|
| Directory | What type of files it contains and why |
| Config file | What it configures |
| Page/Route | What page/feature it represents |
| Component | Only if critical (skip generic components) |
| Utility | What problem it solves |
| Type file | What domain it defines types for |

### Example of Good Structure Doc

```markdown
# Project Structure

## Directory Tree

```
my-app/
├── src/
│   ├── app/                        # Next.js App Router
│   │   ├── (auth)/                 # Auth-protected routes group
│   │   │   ├── dashboard/          # Main dashboard page
│   │   │   └── settings/           # User settings pages
│   │   ├── (public)/               # Public routes group
│   │   │   ├── login/              # Login page
│   │   │   └── signup/             # Registration page
│   │   ├── api/                    # API route handlers
│   │   │   ├── auth/               # Auth endpoints (login, logout, refresh)
│   │   │   └── users/              # User CRUD endpoints
│   │   ├── layout.tsx              # Root layout with providers
│   │   └── page.tsx                # Landing page
│   ├── components/
│   │   ├── ui/                     # Shadcn UI primitives (button, input, etc.)
│   │   ├── forms/                  # Form components with validation
│   │   └── layout/                 # Header, footer, sidebar, navigation
│   ├── features/                   # Feature-based modules
│   │   ├── auth/                   # Auth logic, hooks, context
│   │   └── users/                  # User management logic
│   ├── hooks/                      # Shared custom hooks
│   ├── lib/                        # Utilities and configurations
│   │   ├── auth.ts                 # NextAuth configuration
│   │   ├── db.ts                   # Prisma client instance
│   │   └── utils.ts                # Helper functions
│   └── types/                      # Global TypeScript types
├── prisma/
│   ├── schema.prisma               # Database schema definition
│   └── migrations/                 # Database migrations history
├── public/                         # Static assets (images, fonts)
├── package.json                    # Dependencies and scripts
├── tsconfig.json                   # TypeScript configuration
└── tailwind.config.ts              # Tailwind CSS configuration
```

## Key Files Reference

| File | Purpose | Notes |
|------|---------|-------|
| `src/lib/auth.ts` | NextAuth.js config | Credentials + Google OAuth providers |
| `src/lib/db.ts` | Prisma client | Singleton pattern for connection |
| `prisma/schema.prisma` | DB schema | User, Session, Account models |
| `src/middleware.ts` | Route protection | Redirects unauthenticated users |
```

---

## Why This System Works

1. **recent-session.md** = Your "working memory" - what you're actively doing
2. **changelog.md** = Your "long-term memory" - what happened over time
3. **project-overview.md** = Your "conceptual understanding" - WHY and HOW the project works
4. **project-structure.md** = Your "navigation map" - WHERE things are located

The separation of concepts (overview) from structure (file tree) allows:
- Faster file location lookups without wading through architecture explanations
- Deeper project understanding without cluttering with file paths
- Scalable structure documentation that grows with the project

The next session reads these files and immediately has context to continue work.
