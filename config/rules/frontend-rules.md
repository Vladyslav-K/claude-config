# Frontend Rules

## Project-First Principle
Always follow the project's existing libraries, patterns, and code style over these defaults.

## Component Conventions
- Define components using `function` keyword
- All methods inside components must be `const` — no raw function declarations in component body
- Prefer `interface` over `type` for object structures
- Default to Server Components. Use `'use client'` only for: event listeners, browser APIs, state management, client-only libs

## Naming
- Files/directories: **kebab-case** (`user-profile.tsx`, `auth-wizard/`)
- Components/Types/Interfaces: **PascalCase**
- Variables/Functions/Props: **camelCase**
- Handlers: `handle*` (`handleClick`, `handleSubmit`)
- Booleans: `is*`/`has*`/`can*` (`isLoading`, `hasError`)
- Hooks: `use*` (`useAuth`, `useForm`)
- Constants/Env: **UPPERCASE**

## Code Style Defaults
- Spaces for indentation, semicolons, single quotes, trailing commas
- Strict equality (`===`), line length ~80 chars
- NOTE: project linter/formatter config ALWAYS overrides these

## Stack Defaults (when project has no existing choice)
- Framework: Next.js (App Router, Server Components default)
- UI: Shadcn UI + Radix UI + Tailwind CSS
- Validation: Zod + React Hook Form
- i18n: i18next
- Sanitization: DOMPurify
- Testing: Jest + React Testing Library (only when asked)
