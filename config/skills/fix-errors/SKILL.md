---
name: fix-errors
description: Run format then check-errors — find and fix all ERRORS across the project. Warnings are ignored.
disable-model-invocation: true
---

# Fix Errors

## Additional context from user
$ARGUMENTS

## Purpose
Find and fix all **errors** (NOT warnings) in the project by running the project's `format` and `check-errors` scripts.

**Warnings are completely IGNORED in this command.** Only errors matter.

---

## Execution Steps

### 1. Detect Package Manager & Scripts

1. Read `package.json` in the project root
2. Identify the package manager: check for `bun.lockb` → bun, `pnpm-lock.yaml` → pnpm, `yarn.lock` → yarn, else → npm
3. Find the two verification scripts:
   - `format` — Prettier formatting
   - `check-errors` — runs lint + tsc (type checking)
4. Determine the run command (`bun run`, `pnpm run`, `yarn`, `npm run`)
5. **If `format` / `check-errors` don't exist but can be created** (the project already has Prettier / ESLint / `tsc`) → add them to `package.json`. **If the project is too specific to add them** → run the available equivalents directly (e.g. `prettier --write .`, then `eslint .` and `tsc --noEmit`).

### 2. Run format, then check-errors

Order matters — formatting first, then the error check:

1. **`format`** — run first so formatting changes don't pollute the error output
2. **`check-errors`** — run with the **full, unmodified output**. Never pipe through `tail`/`head`, never add flags that limit the output — capture everything.

### 3. Parse Errors

From the `check-errors` output:
- **Extract ONLY errors** — lines with `error`, `Error`, severity `error`, exit code != 0
- **IGNORE all warnings** — lines with `warning`, `Warning`, severity `warn`, `⚠`
- Group errors by file and type (lint rule / type error)
- Create a mental checklist of all errors to fix

### 4. Fix Errors

For each error:
1. **Read the file** containing the error
2. **Understand the context** — what does the code do? What broke?
3. **Assess impact** — is this a simple fix (unused import, missing type) or does it cascade?
4. **Fix it** — apply the minimal correct fix that preserves functionality

#### Safety Rules
- **NEVER change business logic** to fix a type error — fix the type instead
- **NEVER delete functional code** to silence an error — fix the root cause
- **NEVER add `// @ts-ignore`, `// eslint-disable`, `any` type** — fix properly
- If a fix requires changing more than 3-5 files or restructuring logic → **STOP and ASK the user what to do**
- If you're unsure whether a fix is safe → **ASK the user**

### 5. Verify

After all fixes:
1. Re-run `format`, then `check-errors` (full output, no truncation)
2. If new errors appeared (fixing one thing broke another) → fix those too
3. Repeat until **zero errors**
4. Warnings may still exist — that's OK, we ignore them

### 6. Report

Provide a summary:
- Total errors found (by category: lint / type)
- Total errors fixed
- What was changed (brief per-file summary)
- Any errors you chose to ask about instead of fixing
- Confirm: "All errors resolved. Warnings were ignored."

---

## Edge Cases

- **Circular fixes:** If fixing error A creates error B and fixing B recreates A → ASK the user
- **Third-party type errors:** If errors come from `node_modules` or generated files → report but don't fix, ASK the user
- **Config errors:** If the lint/typecheck config itself has issues → report and ASK
- **Massive error count (50+):** Show the list first, propose a fix strategy, then proceed
