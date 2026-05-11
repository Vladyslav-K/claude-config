# Frontend Conventions

## Project-First Principle (overrides everything below)
Every rule in this file is a **default that applies only when the project has no established convention of its own**. If the project already uses a different pattern — follow the project. Your job is to match the codebase, not to push these defaults onto it.

Check before applying any default below:
- Does the existing code use a different pattern? → follow the existing pattern
- Does the linter/formatter config disagree? → follow the linter
- Is the project a different stack (Vue, Angular, older React, etc.)? → ignore framework-specific defaults below

---

## Defaults when the project has no established convention

### Component Conventions (defaults)
- Define components using `function` keyword
- Methods inside components as `const`
- Prefer `interface` over `type` for object structures
- Server Components by default; `'use client'` only for event listeners, browser APIs, state, client-only libs

### Naming (defaults)
- Files/directories: kebab-case (`user-profile.tsx`)
- Components/Types/Interfaces: PascalCase
- Variables/Functions/Props: camelCase
- Handlers: `handle*`; Booleans: `is*`/`has*`/`can*`; Hooks: `use*`; Constants: UPPERCASE

### Code Style (defaults, linter overrides)
Spaces, semicolons, single quotes, trailing commas, strict equality, ~80 char lines.

### Stack Defaults (new greenfield only)
Next.js App Router + Server Components, Shadcn UI + Radix + Tailwind, Zod + React Hook Form, i18next, DOMPurify, Jest + RTL when asked.
