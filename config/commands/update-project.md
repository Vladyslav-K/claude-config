---
name: update-project
description: Audit project dependencies, surface breaking changes, propose an update plan, and execute updates only after explicit user approval.
---

# Update Project

## Additional context from user
$ARGUMENTS

## Purpose
Keep the project's dependencies fresh **without breaking working code**.

The flow is **research → report → plan → APPROVAL → execute → verify**. The command MUST stop after the plan and wait for the user. No silent updates, no surprise major bumps.

`$ARGUMENTS` may scope the run, e.g.:
- `only react` → focus on a single package
- `skip major` → patch + minor only
- `only major` → major bumps only
- `workspace web` → a specific monorepo workspace
- `include pre-release` → allow `alpha` / `beta` / `rc` / `next`

Empty arguments → full project scan, stable versions only.

---

## Phase 1: Detection

1. **Locate `package.json`** in the working directory.
   - If a monorepo (root has `workspaces` field, or `packages/`, `apps/`, `services/` with their own `package.json`) — collect ALL of them, list paths to the user, then continue.
2. **Detect package manager** from lockfile:
   - `bun.lockb` / `bun.lock` → bun
   - `pnpm-lock.yaml` → pnpm
   - `yarn.lock` → yarn (classic if no `.yarnrc.yml`, else berry)
   - `package-lock.json` → npm
   - none / multiple → ASK the user
3. **Read each `package.json`** — collect `dependencies`, `devDependencies`, `optionalDependencies`, `peerDependencies` separately.
4. **Run outdated check**:
   - bun: `bun outdated`
   - pnpm: `pnpm outdated --format json`
   - yarn classic: `yarn outdated --json` | yarn berry: `yarn outdated`
   - npm: `npm outdated --json`
5. Parse results into a list: `{ name, type, current, wanted, latest, location }`.
   - If a PM's output is human-only and parsing fails — fall back to `npm view <name> version` per package.
6. **If nothing is outdated** — report that and stop. No further phases.

---

## Phase 2: Research & Risk Analysis

For each outdated package:

1. **Compute semver diff**: `patch` / `minor` / `major`.
2. **For `major` bumps** — fetch the upgrade story:
   - **Use context7 first** — `mcp__context7__resolve-library-id` then `mcp__context7__query-docs` for the migration guide / breaking changes / upgrade notes.
   - **Fallback**: WebFetch the GitHub releases page (`https://github.com/<org>/<repo>/releases`) or the repo's `CHANGELOG.md`. Get repo URL via `npm view <name> repository.url`.
   - Extract: breaking changes, removed APIs, renamed exports, behavior changes, required code migrations.
3. **Check deprecation**: `npm view <name> deprecated`.
4. **Check security advisories**: `npm audit --json` (or `pnpm audit --json` / `yarn npm audit --json` / `bun audit` if supported). Treat any open advisory as priority regardless of the bump type.
5. **Map breaking changes to project code** — Grep for import paths and symbols mentioned in the changelog. Record affected files for the report.

Categorize each package into one of the buckets below. The bucket drives how it's handled in execution.

| Category | Criteria |
|---|---|
| SAFE | Patch, or minor with no notable changes |
| CAUTION | Minor with notable changes, or major where project usage is minimal/isolated |
| BREAKING | Major with breaking changes that touch project code |
| DEPRECATED | Package marked deprecated — needs a decision |
| SECURITY | Has open advisory — handle as priority regardless of bump type |

A "notable change" = anything in release notes labeled as breaking, deprecated, removed, behavior change, or any item the project's code currently depends on.

---

## Phase 3: Plan

Print a structured report to the user, in this exact order. Keep it terse — the user reads this before approving.

```
## Project Update Plan

Stack: <package manager> <version> | Scope: <root | monorepo: N packages>

### Security Advisories
- pkg@x.y.z → x.y.z+ — <severity> — <CVE / title>

### Breaking (major)
- pkg@A.B → C.D
  - Breaking changes: <bullet list, terse>
  - Affected files in this project: <list, max 10, "...and N more" if huge>
  - Migration: <link / 1-2 line summary>
  - Recommendation: update | hold | replace

### Deprecated
- pkg — <reason> — suggested replacement: <name>

### Caution
- pkg@A.B → A.C — <notable change summary>

### Safe
- N packages, patch + minor only — list compactly: `pkg1 (1.2.3 → 1.2.7), pkg2 (2.0.1 → 2.3.0), …`

### Proposed Order
1. Security fixes
2. Safe batch (single command)
3. Caution items (one by one with verification)
4. Breaking items (one by one + code migrations)
5. Deprecated (separate decision per item)

### Skipped
- pkg — reason (pinned, workspace, pre-release, user-excluded)
```

---

## Phase 4: HARD STOP — User Approval

After printing the plan, ask in Ukrainian:

> "План готовий. Підтверди, що оновлювати. Можеш сказати 'оновлюй все', 'тільки safe', 'пропусти react', 'не торкайся X' тощо."

**DO NOT proceed without an explicit confirmation.** Wait for the user.

If the user approves only part of the plan — proceed with that part, leave the rest untouched. If anything in the user's reply is ambiguous — ASK before acting.

---

## Phase 5: Execution

Process the approved groups in this order. Verify (Phase 6) between groups.

### 5.1 Security fixes — first
- npm: `npm audit fix` (NEVER `--force`)
- pnpm / yarn / bun: update the flagged versions explicitly with `<pm> add <pkg>@<safe-version>`
- Re-run audit afterwards, report what's left.

### 5.2 Safe batch — single command
Use the PM's update-respecting-range command:
- bun: `bun update`
- pnpm: `pnpm up`
- yarn classic: `yarn upgrade` | berry: `yarn up`
- npm: `npm update`

### 5.3 Caution items — one at a time
For each:
1. `<pm> add <pkg>@<target>` (forces explicit upgrade past the range).
2. Run format-and-check + tests.
3. If broken → revert that one update (`<pm> add <pkg>@<previous>`), report, ASK how to proceed.
4. If green → continue to the next.

### 5.4 Breaking items — one at a time, with code migration
For each:
1. Apply the version bump.
2. Run format-and-check + build + tests.
3. If broken → apply the documented migration steps to the affected files identified in Phase 2.5.
4. Re-run checks until green, OR until the migration is non-trivial — then STOP and report to the user.
5. NEVER stack multiple major bumps before verifying.

### 5.5 Deprecated — per-item decision
- If the user pre-approved a replacement → install replacement, remove old, refactor imports.
- Otherwise → STOP and ASK.

---

## Phase 6: Verification

After every group:
1. `format-and-check` (or fall back to `format` + `lint` + `typecheck`).
2. `test` script if present — run it.
3. `build` script if present and reasonably fast — run it.
4. If any check fails → report. Fix in place only for trivial issues; otherwise revert the last group and surface to the user.

---

## Phase 7: Final Report

```
## Update Result

Updated: N packages
- Safe: <count>
- Caution: <count>
- Breaking: <count>
- Security: <count>

Skipped / rolled back:
- pkg — reason

Code migrations applied:
- <files touched>

Final state:
- format-and-check: pass | fail
- tests: pass | fail | not run
- build: pass | fail | not run

Follow-up:
- <items the user should review manually>
```

---

## Safety Rules

- **NEVER** use `--force` / `--legacy-peer-deps` without asking. Surface peer-dep conflicts to the user instead.
- **NEVER** edit `package.json` by hand to bump versions. Use the package manager.
- **NEVER** edit the lockfile by hand. Let the PM regenerate it.
- **NEVER** skip Phase 4 (approval).
- **NEVER** stack multiple major bumps in one command.
- **NEVER** bump exact-pinned versions (e.g., `"react": "18.2.0"` without `^` / `~`) without asking — the user pinned them deliberately.
- **NEVER** touch `workspace:*` / `link:` / `file:` deps — they are local references.
- **NEVER** include pre-release versions (`alpha`, `beta`, `rc`, `next`, `canary`) unless `$ARGUMENTS` says otherwise.
- **NEVER** auto-replace a deprecated package. Suggest, ask, then act.
- **NEVER** continue past a failing build — stop, report, ask.

---

## Edge Cases

- **Monorepo:** list every `package.json` found at the start; let the user scope (e.g., `workspace:web`) or do all.
- **pnpm catalogs:** dependencies under `catalog:` are managed in `pnpm-workspace.yaml` — bump the catalog entry, not the per-package one.
- **Custom registries:** respect `.npmrc` / `.yarnrc.yml` — do not override.
- **Engines mismatch** (new pkg requires Node 22 but project on 18): surface, ask.
- **Peer-dep conflicts:** report them; do not silently `--force`.
- **`@types/*` packages:** bump in sync with their parent — flag mismatches.
- **`react` + `react-dom`** (and similar paired packages): treat as a unit, must move together.
- **Framework majors** (Next, Nuxt, Nest, Vite, Webpack, Vue, Angular, etc.): always BREAKING in plan terms, even when the SemVer diff looks small — codemods are often required. Use the framework's own migration guide via context7.
- **Tooling that owns config files** (eslint, prettier, tailwind, postcss, biome, vitest, jest): a major bump can require config rewrites — surface that in the plan.
- **Lockfile drift** (lockfile inconsistent with `package.json`): regenerate via the PM, never hand-edit.
- **Mixed lockfiles** (e.g., both `bun.lockb` and `yarn.lock` present): bad state — report and ASK before any update.

---

## Rules

1. **Plan before action. Always.**
2. **Stop and ask** at any decision point, not just Phase 4.
3. **One major bump at a time**, verified between each.
4. **Use context7 first** for migration docs; WebFetch as fallback.
5. **The package manager is the source of truth** — use its commands, not manual edits.
6. **Speak Ukrainian to the user**; commands and version names stay verbatim.
