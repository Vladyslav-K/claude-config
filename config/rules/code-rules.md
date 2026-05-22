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
