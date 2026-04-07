---
name: fix-errors
description: Run format-and-check, lint, typecheck — find and fix all ERRORS across the project. Warnings are ignored.
---

# Fix Errors

## Additional context from user
$ARGUMENTS

## Purpose
Find and fix all **errors** (NOT warnings) in the project by running format, lint, and typecheck scripts.

**Warnings are completely IGNORED in this command.** Only errors matter.

---

## Execution Steps

### 1. Detect Package Manager & Scripts

1. Read `package.json` in the project root
2. Identify the package manager: check for `bun.lockb` → bun, `pnpm-lock.yaml` → pnpm, `yarn.lock` → yarn, else → npm
3. Find available scripts: `format-and-check`, `format`, `lint`, `typecheck` (or similar names like `type-check`, `tsc`, `check-types`)
4. Determine the run command (`bun run`, `pnpm run`, `yarn`, `npm run`)

### 2. Run Checks (Sequential)

Run each available script **one at a time** and capture the output:

1. **format-and-check** (or `format` if no combined script) — run first, fix formatting issues
2. **lint** — capture errors only
3. **typecheck** — capture errors only

If `format-and-check` combines all three — run it once, then re-run individual scripts to isolate remaining errors.

### 3. Parse Errors

From the output of each command:
- **Extract ONLY errors** — lines with `error`, `Error`, severity `error`, exit code != 0
- **IGNORE all warnings** — lines with `warning`, `Warning`, severity `warn`, `⚠`
- Group errors by file and type (lint rule / type error / format error)
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
1. Re-run all check scripts
2. If new errors appeared (fixing one thing broke another) → fix those too
3. Repeat until **zero errors** from all scripts
4. Warnings may still exist — that's OK, we ignore them

### 6. Report

Provide a summary:
- Total errors found (by category: lint / type / format)
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
