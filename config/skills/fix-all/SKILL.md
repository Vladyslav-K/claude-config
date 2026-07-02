---
name: fix-all
description: Run format then check-errors — find and fix ALL errors AND warnings across the project.
---

# Fix All (Errors + Warnings)

## Additional context from user
$ARGUMENTS

## Purpose
Find and fix **all errors AND warnings** in the project by running the project's `format` and `check-errors` scripts.

**Fix errors FIRST, then warnings.** Errors take priority because they block builds and functionality.

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

### 3. Parse All Issues

From the `check-errors` output:
- **Extract errors** — lines with `error`, `Error`, severity `error`, exit code != 0
- **Extract warnings** — lines with `warning`, `Warning`, severity `warn`, `⚠`
- **Separate them into two groups:** ERRORS and WARNINGS
- Group each by file and type (lint rule / type error)

### 4. Phase 1 — Fix Errors

Process ALL errors first:

1. **Read the file** containing the error
2. **Understand the context** — what does the code do? What broke?
3. **Assess impact** — is this a simple fix or does it cascade?
4. **Fix it** — apply the minimal correct fix that preserves functionality

After all errors are fixed — re-run `check-errors` to verify zero errors remain and to get a fresh warning list.

### 5. Phase 2 — Fix Warnings

Process ALL warnings:

1. **Read the file** containing the warning
2. **Understand the context** — what rule is violated?
3. **Assess impact** — simple fix or cascading?
4. **Fix it** — minimal correct fix preserving functionality

After all warnings are fixed — re-run `check-errors` to verify zero warnings remain.

### 6. Safety Rules (for BOTH phases)
- **NEVER change business logic** to fix a type error or warning — fix the type/code minimally
- **NEVER delete functional code** to silence an issue — fix the root cause
- **NEVER add `// @ts-ignore`, `any` type** to fix errors — fix properly
- **For warnings:** targeted disable comments with explanation are acceptable for false positives
- If a fix requires changing more than 3-5 files or restructuring logic → **STOP and ASK the user what to do**
- If you're unsure whether a fix is safe → **ASK the user**

### 7. Final Verify

1. Re-run `format`, then `check-errors` one final time (full output, no truncation)
2. Confirm: zero errors AND zero warnings
3. If anything remains — fix or ask the user

### 8. Report

Provide a summary:

**Errors:**
- Total found → Total fixed
- Per-file changes summary

**Warnings:**
- Total found → Total fixed
- Per-file changes summary

**Result:** "All errors and warnings resolved." or list what remains with explanation.

---

## Edge Cases

- **Circular fixes:** If fixing issue A creates issue B and fixing B recreates A → ASK the user
- **Third-party type errors:** If errors come from `node_modules` or generated files → report but don't fix, ASK the user
- **Massive issue count (100+):** Show grouped list, propose a strategy, then proceed in batches
- **Error fixes that resolve warnings:** Track this — don't double-fix
- **Warning fixes that create errors:** Fix the new error immediately before continuing with warnings
