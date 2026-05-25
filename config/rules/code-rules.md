# Code Rules

**Scope.** Discipline rules that apply to every piece of code I write or edit — regardless of project, stack, or task size. These are not stylistic preferences; they are non-negotiable constraints on what is allowed to ship and what is allowed to appear in the user's terminal. Treat every code edit as a checkpoint against this file.

**How to extend.** When a new rule about *writing code itself* needs to be permanent (banned syntax, language constraints, comment shape, error-handling form, etc.) — add it here. Stack/framework conventions go to `frontend-conventions.md`. Tool usage discipline goes to `tool-hygiene.md`. UI craftsmanship goes to `component-craftsmanship.md`.

---

## Comments

- Comments MUST look human-written — short and plain: `// Enums`, `// Types`, `// Helpers`.
  - BANNED patterns: `// --- Section ---`, `// === Section ===`, `// *** Section ***`, `// ~~~~~~~~`, any dashes/equals/stars/tildes used as decoration.
  - BANNED: verbose "AI-style" comments like `// Helper function to transform user data` — write `// Transform user data` or nothing at all.
  - If the comment just restates the code — delete it. Only comment for grouping sections or non-obvious logic.

## Files

- DON'T create `.md` files or tests unless explicitly ordered.

## Language

- Speak Ukrainian with user, ALL code/comments in English.
- **Russian is STRICTLY BANNED in any user-facing output.** The user is Ukrainian and explicitly refuses to see Russian in his terminal — russian is the language of the aggressor state. This covers EVERY artifact I generate that the user sees in the Claude Code UI:
  - session titles / conversation names
  - todo / task list items (TaskCreate descriptions, status lines)
  - plan headings and section names (EnterPlanMode / ExitPlanMode)
  - summaries, compaction summaries, recap blocks
  - status-line updates, progress messages, "thinking..." captions when I control them
  - any auto-generated description or label
  - Treat Ukrainian as the ONLY acceptable Cyrillic-script language in user-facing output. If I catch myself producing a Russian word (e.g., "Установить" instead of "Встановити", "правило" stays valid because it is also Ukrainian, "пользователь" instead of "користувач") — STOP and rewrite in Ukrainian before submitting.
  - **Exceptions (stay in English, NOT Ukrainian, NOT Russian):** git commit messages, PR titles/descriptions, code identifiers, code comments, file names — these go to shared/public repos and follow industry-standard English convention as before.

## Dependencies

- ALWAYS check package manager before running scripts.
- Before installing libraries, ALWAYS check latest stable version with the `ctx7` CLI (`ctx7 library <name>` → `ctx7 docs <id> <query>`); WebFetch is fallback when CLI cannot find the library. Do NOT call `mcp__context7__*` tools — the MCP server has been removed in favor of the CLI; full reference is the `context7-cli` skill.

## Error Handling

- NEVER write empty error handlers. If a function needs `try/catch` (or `.catch(...)`) — the handler MUST do something visible: log the error with context, return a fallback, re-throw (optionally wrapped with more context), show a user-facing message, or perform cleanup. An empty handler silently swallows bugs and is strictly worse than no handler — the error at least propagates and shows up in logs/console if left alone.
  - BANNED forms: `catch {}`, `catch (e) {}` with `e` never referenced, `catch { /* ignore */ }`, `catch (e) { /* noop */ }`, `.catch(() => {})`, `.catch(() => undefined)`, `.then(...).catch(noop)`, `Promise.allSettled(...)` results discarded without inspection.
  - Decision rule: if you cannot name in one short phrase what the handler does ("log and rethrow", "fall back to default X", "show toast and stay on page", "cleanup temp file") — DELETE the `try/catch` entirely and let the error propagate. The handler exists to do work; if it does no work, it has no reason to exist.
  - Rare legitimate "intentionally ignore" cases (best-effort cleanup, optional telemetry, etc.) STILL require at minimum a `console.debug`/`logger.warn` call AND a one-line comment naming WHY ignoring is safe here. No silent ignores.
  - This rule covers stubs too: do not pre-create `try/catch` with an empty body planning to "fill it later". Either implement the handler now or do not write the `try/catch` until you need it.

## Icons & Inline SVG

- **Inline SVG in code is STRICTLY FORBIDDEN without prior discussion.** An icon must be ONE of two things:
  - a `.svg` asset file under `assets/icons/` (or the project's equivalent — `public/icons/`, `static/icons/`, `src/icons/`, `src/assets/icons/`), imported as a resource
  - a component from an icon library installed in the project (`lucide-react`, `@heroicons/react`, `react-icons`, `@tabler/icons-react`, `@phosphor-icons/react`, `@mui/icons-material`, etc.) — chosen to match what the project already uses
- BANNED forms — every one of these requires asking first, never written silently:
  - JSX inline SVG: `<svg viewBox="..."><path d="..." /></svg>` inside a component file
  - SVG composed by hand from `<path>`, `<circle>`, `<g>`, `<rect>`, `<polyline>`, `<polygon>`, etc. assembled in React (or Vue / Svelte / Angular — the rule is framework-agnostic)
  - SVG as a string constant: `const ICON = '<svg>...</svg>'`
  - SVG injected via `dangerouslySetInnerHTML` (or framework equivalent — `v-html`, `[innerHTML]`, `{@html ...}`)
  - SVG encoded as base64 / data-URL embedded in JS/TS code: `const icon = 'data:image/svg+xml;base64,...'` or `data:image/svg+xml;utf8,...`
  - SVG-as-CSS-mask or SVG-as-background with the SVG body written inline in CSS / `style={{}}` / styled-components / Tailwind arbitrary values
  - Importing SVG as a React component (e.g., SVGR) AND then editing the underlying file to be hand-written by me — the file must come from a designer / library / export, not from me typing path data
- **Why this is strict.** Silently inlining SVG into code (a) bypasses the project's icon system and breaks visual consistency, (b) bloats components with non-component concerns, (c) makes icons impossible to swap without a code change and PR, (d) is the most common path to "AI-looking" code that pollutes the codebase and leaks the fact AI wrote it. The bar is: an icon ships as an asset or as a library component — NEVER as hand-written SVG markup in component code.
- **What to do when the icon you need is missing.** Do NOT inline. Stop and ASK, in this order:
  1. Check the project's installed icon library — is there a close match? If yes, propose it: "Я використаю `<ChevronRightIcon>` з `lucide-react` — підтверди?"
  2. Check the project's `assets/icons/` (or equivalent) — is there an existing custom `.svg`? If yes, use it.
  3. If neither exists — ASK: "Іконки `<name>` немає ні в бібліотеці (`<library-name>`), ні в `assets/icons/`. Варіанти: (a) додай .svg файл — скажи звідки взяти, (b) використати найближчу — пропоную `<closest-name>`, (c) щось інше. Як робимо?"
  4. Wait for the user's answer. NEVER proceed with an inline SVG as a "temporary" fix. There is no "temporary" — inline SVG that ships once stays.
- **Exceptions** exist but require explicit discussion in chat first — e.g., a unique illustration that is genuinely one-off and not an icon (hero artwork, empty-state illustration), a chart rendered dynamically from data via a chart library (`recharts`, `visx`, `nivo`, `d3`), a programmatic shape generator (sparklines, gauges). Those are not "icons" and live outside this rule's strict ban, but if there is any doubt whether the case is an exception — ASK before writing the SVG. Default position is always "this is banned until I confirm otherwise".
