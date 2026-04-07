---
name: fix-warnings
description: Run format-and-check, lint, typecheck — find and fix all WARNINGS across the project. Errors are not the focus (fix them only if trivial).
---

# Fix Warnings

## Additional context from user
$ARGUMENTS

## Purpose
Find and fix all **warnings** in the project by running format, lint, and typecheck scripts.

**Primary focus: WARNINGS.** Errors are secondary — fix them only if they are trivial and blocking the warning analysis.

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
2. **lint** — capture warnings
3. **typecheck** — capture warnings (if any — most TS issues are errors, but some compiler options produce warnings)

If `format-and-check` combines all three — run it once, then re-run individual scripts to isolate remaining warnings.

### 3. Parse Warnings

From the output of each command:
- **Extract ONLY warnings** — lines with `warning`, `Warning`, severity `warn`, `⚠`
- **Note errors but don't prioritize them** — they are for `/fix-errors`
- Group warnings by file and lint rule / type
- Create a mental checklist of all warnings to fix

### 4. Fix Warnings

For each warning:
1. **Read the file** containing the warning
2. **Understand the context** — what rule is violated? Why does this warning exist?
3. **Assess impact** — is this a simple fix (unused variable, missing dep array) or does it cascade?
4. **Fix it** — apply the minimal correct fix that preserves functionality

#### Safety Rules
- **NEVER change business logic** to fix a warning — adjust the code minimally
- **NEVER delete functional code** to silence a warning — fix the root cause
- **Prefer proper fixes over suppressions** — but if a warning is a false positive, a single-line disable comment with explanation is acceptable
- If a warning fix requires changing more than 3-5 files or restructuring logic → **STOP and ASK the user what to do**
- If you're unsure whether a fix is safe → **ASK the user**
- **Unused variables that ARE used elsewhere** — check carefully before removing
- **React Hook dependency warnings** — verify the correct deps, don't blindly add everything

### 5. Verify

After all fixes:
1. Re-run all check scripts
2. If new warnings appeared (fixing one thing created another) → fix those too
3. Repeat until **zero warnings** from all scripts
4. Errors may still exist — that's OK, they are for `/fix-errors`

### 6. Report

Provide a summary:
- Total warnings found (by category: lint rule / type)
- Total warnings fixed
- What was changed (brief per-file summary)
- Any warnings you chose to ask about instead of fixing
- Confirm: "All warnings resolved."

---

## Edge Cases

- **Circular fixes:** If fixing warning A creates warning B and fixing B recreates A → ASK the user
- **False positive warnings:** If a warning is clearly incorrect → add a targeted disable comment with an explanation why
- **Hook dependency warnings:** Be extra careful — verify each dependency. Adding wrong deps can cause infinite re-renders
- **Massive warning count (50+):** Group by rule, show the list, propose a fix strategy, then proceed
