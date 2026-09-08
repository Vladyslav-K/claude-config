---
name: sync-swagger
description: Sync the project API layer (types, services, hooks) with swagger. Auto-detects mode — if a non-empty swagger-old.json baseline exists, apply only the precise swagger-to-swagger diff; otherwise do a full sync against swagger.json. Updates existing APIs, adds new ones (types/services/hooks only), and fixes usage where APIs changed.
allowed-tools: Bash(python3 *)
---

# Sync Swagger

## Additional context from user
$ARGUMENTS

## Purpose
Synchronize the frontend API layer (types, services, hooks) with the latest swagger snapshot — all while preserving **this project's** conventions. The skill runs in one of two modes, chosen automatically:

- **DIFF MODE** — when a populated `swagger-old.json` baseline exists alongside `swagger.json`. Compute a precise **swagger-to-swagger diff** and apply only that delta to the codebase. Faster, more reliable, avoids false positives.
- **FULL MODE** — when only `swagger.json` exists (no usable baseline). Scan the project API layer, diff it against the swagger, update existing code, and add new endpoints.

**Flow (both modes): research → understand changes → apply all changes → verify → report what was done.**
Do NOT ask for confirmation mid-process. Just do the work and report results at the end.

---

## Mode Detection (MANDATORY FIRST STEP)

Before anything else, locate the swagger files and decide which mode to run.

1. **Find `swagger.json`** (the new version — required by both modes). Check `.project-meta/swagger/swagger.json` first, then search broadly (`**/swagger.json`, `**/openapi.json`). If not found — **STOP and ask the user**.
2. **Find `swagger-old.json`** (the baseline). Check `.project-meta/swagger/swagger-old.json` first, then search broadly (`**/swagger-old.json`).
3. **Decide the mode by checking whether `swagger-old.json` actually contains a swagger snapshot** (not just whether the file exists — an empty file or `{}` placeholder must NOT trigger diff mode). Use this deterministic check:

```bash
python3 -c "
import json, os, sys
p = sys.argv[1]
ok = os.path.exists(p) and os.path.getsize(p) > 2
if ok:
    try:
        data = json.load(open(p))
        ok = isinstance(data.get('paths'), dict) and len(data['paths']) > 0
    except Exception:
        ok = False
print('DIFF' if ok else 'FULL')
" <path-to-swagger-old.json>
```

4. **Route to the correct flow:**
   - Output `DIFF` → `swagger-old.json` holds a real baseline → run **DIFF MODE FLOW** below.
   - Output `FULL` (or `swagger-old.json` not found at all) → run **FULL MODE FLOW** below.

Follow exactly one flow end-to-end. Do not interleave steps from the other mode.

---

## Step 0 — Discover Project Structure (BOTH MODES)

Before applying anything — **research this specific project** to understand how its API layer is organized. Do NOT assume any folder structure or naming conventions.

Use Explore agent / Glob / Grep to answer:

1. **Where are API types defined?** — Search for directories/files containing API interfaces, DTOs, enums (e.g., `types/`, `models/`, `interfaces/`, `api/`, `generated/`).
2. **Where are API service functions?** — Search for files that make HTTP calls (axios, fetch, ky, got, etc.). Understand the HTTP client used.
3. **Where are API hooks defined?** — Search for React Query / SWR / custom hooks that wrap service calls. Identify the data-fetching library used.
4. **What are the naming conventions?** — Read 2-3 existing files from each layer (types, services, hooks) to learn:
   - File naming pattern (kebab-case? camelCase? by domain? by feature?)
   - Type naming pattern (e.g., `UserResponse`, `IUser`, `TUser`, `UserDto`)
   - Service naming pattern (e.g., `userService.getAll()`, `getUsers()`, `api.users.list()`)
   - Hook naming pattern (e.g., `useUsers()`, `useGetUsers()`, `useUserQuery()`)
   - Export pattern (barrel `index.ts`? direct imports? re-exports?)
   - Query key pattern (factory? string arrays? constants?)
5. **What is the HTTP client?** — axios, fetch, ky, ofetch, etc. Understand how requests are configured (base URL, interceptors, auth headers).
6. **What is the data-fetching library?** — React Query (TanStack Query), SWR, RTK Query, Apollo, or custom.

**Store all findings as your "Project API Conventions" reference for all subsequent steps.**

---

# DIFF MODE FLOW

> Run this flow when Mode Detection returned `DIFF` (a populated `swagger-old.json` baseline exists).
>
> The baseline `swagger-old.json` is assumed to be **100% in sync** with the project code. The delta between it and `swagger.json` is exactly what the code is currently missing. The diff — not the project code — is the source of truth.

### D1. Locate Both Swagger Snapshots

You work with two files:
- `swagger-old.json` → the **baseline** OpenAPI spec
- `swagger.json` → the **new** OpenAPI spec

Do **not** open them with the Read tool — they are usually far too large (300KB+). Everything you need about endpoints (method + path, operationId, tag, request/response schemas, parameters) and schemas (fields, types, enums, refs) comes from the scripts in D2. If you need an inventory of the new spec beyond the diff, use `list-spec.py <path-to-swagger.json>` (described in the FULL MODE flow).

### D2. Compute the Swagger Diff (CORE STEP)

Compare `swagger-old.json` (baseline) vs `swagger.json` (new). **This is the heart of diff mode.**

**⚡ Run the bundled Python scripts via the Bash tool.** The scripts live in this skill's `scripts/` directory and take the swagger paths as command-line arguments — there is nothing to edit inside the scripts. `swagger_common.py` in the same directory is a shared helper imported by the others; never run it directly.

> **Resolving the scripts path.** This skill is installed at `~/.claude/skills/sync-swagger/`, so its scripts are at `~/.claude/skills/sync-swagger/scripts/`. If the skill lives somewhere else (e.g. a project-local `.claude/skills/`), use that location's absolute path instead. Below, `<scripts>` stands for the absolute path to this skill's `scripts/` directory.

All scripts ignore documentation-only keys (`description`, `summary`, `example(s)`, `title`, `tags`, `deprecated`, `x-*`) when deciding what changed, and report endpoints/schemas where only those keys changed in a separate **DOC-ONLY** section — skip that section, it has no code impact.

#### Script 1: Compare endpoints (new / removed / changed / doc-only)

```bash
python3 <scripts>/diff-endpoints.py <path-to-swagger-old.json> <path-to-swagger.json>
```

For every changed endpoint it prints a field-level diff (`+` added, `-` removed, `~` changed, dotted paths; parameters are matched by `in:name`). New/removed endpoints come with their request/response schema names. An endpoint whose *referenced schema* changed is not listed here — that comes from Script 2.

#### Script 2: Compare schemas (new / removed / changed / doc-only) with "used by"

```bash
python3 <scripts>/diff-schemas.py <path-to-swagger-old.json> <path-to-swagger.json>
```

Every changed/new/removed schema comes with a `used by ->` line: the endpoints and the other schemas that reference it. This is your map from a schema change to the services/hooks that must be re-checked (step D3).

#### Script 3: Show a specific endpoint

Use only when the field-level diff from Script 1 is not enough to understand the change:

```bash
python3 <scripts>/show-endpoint.py <path-to-swagger-old.json> <path-to-swagger.json> /api/companies get
```

#### Script 4: Show a specific schema

Use only when the field-level diff from Script 2 is not enough:

```bash
python3 <scripts>/show-schema.py <path-to-swagger-old.json> <path-to-swagger.json> UserDto
```

**Execution order:** Run Script 1 + Script 2 in parallel → Script 3/4 only for items whose diff you cannot act on from the summary alone. Do not dump every changed item — the field-level diff is usually sufficient.

**Replace** `<scripts>` with the absolute path to this skill's `scripts/` directory, and `<path-to-swagger-old.json>` / `<path-to-swagger.json>` with the actual paths found in Mode Detection.

---

Categorize every difference into:

#### A. CHANGED endpoints
Endpoints that exist in both specs but differ. For each, record exactly what changed:
- Request body schema: added/removed/renamed fields, changed types, changed `required`, changed enums
- Response schema: added/removed/renamed fields, changed types, changed `required`, changed enums
- Path parameters: added/removed/renamed, changed types
- Query parameters: added/removed/renamed, changed types, changed `required`
- Path itself changed (e.g., `/users/{id}` → `/users/{userId}`)
- HTTP method changed
- Response status codes changed (e.g., 200 → 201)

#### B. NEW endpoints
Endpoints present in new swagger but NOT in old swagger.

#### C. REMOVED endpoints
Endpoints present in old swagger but NOT in new swagger. **Flag in final report but do NOT delete from code.**

#### D. CHANGED schemas (components)
Schemas referenced by endpoints that changed independently (e.g., a shared `User` schema gained a field). Track these separately because they may affect many endpoints at once.

#### E. NEW schemas
New reusable schemas that appeared in new swagger.

#### F. REMOVED schemas
Schemas no longer in new swagger. Flag in report.

Keep this categorised diff as **your own working checklist** — every item must be either applied (A, B, D, E) or flagged (C, F) by the end. **Do not print it to the user:** text written mid-turn is collapsed by the CLI, and the user reviews the resulting code changes in the IDE anyway. The user gets one final report (D8) describing what was done.

### D3. Map Diff to Code Locations

For EACH item in the diff, find WHERE in the project code it lives. Only touch the files that correspond to the diff — do NOT scan everything.

For changed schemas start from the `used by ->` lines of Script 2: they name every endpoint and schema that consumes the changed schema, so you know which services/hooks to re-check without grepping blindly.

For each changed/removed endpoint or schema:
- Grep by operationId, path, or schema name to find:
  - The type/interface file
  - The service method
  - The hook
  - All usage sites of the affected types/hooks

For each new endpoint or schema:
- Determine the target file based on domain/tag grouping (match existing project pattern)
- If the domain file already exists — add into it
- If not — create a new file following the exact naming convention of the project

### D4. Apply CHANGED endpoints (Category A) and CHANGED schemas (Category D)

For each changed endpoint/schema, update in this order — **following the project's own conventions discovered in Step 0**:

#### D4.1 Types
- Update interfaces/enums to match the NEW swagger schema
- Apply the exact delta from D2: add new fields, remove deleted fields, rename renamed fields, fix type changes, update enum members
- Respect the project's existing naming and style conventions
- Update barrel exports if the project uses them

#### D4.2 Services
- Update method signatures if params/return types changed
- Update endpoint paths if changed (e.g., `/users/{id}` → `/users/{userId}`)
- Update HTTP method if changed
- Update barrel exports if the project uses them

#### D4.3 Hooks
- Update hook generic types if response/request types changed
- Update query keys if path/params changed
- Update barrel exports if the project uses them

#### D4.4 Usage Sites
- Grep for usage of changed types/hooks/services across the entire codebase
- Fix type errors at usage sites:
  - Renamed fields: update all reads/writes to the new name
  - Removed fields: remove references (if code uses a removed field, replace with equivalent or mark clearly)
  - New required fields in requests: add to callers where required
  - Changed enum values: update consumers
- Do NOT change business logic — only fix type compatibility driven by the swagger diff

### D5. Add NEW endpoints (Category B) and NEW schemas (Category E)

For each new endpoint/schema, add ONLY infrastructure — do NOT integrate into UI:

#### D5.1 Types
- Create interfaces for request/response/shared schemas
- Add to existing domain file if the domain already exists, or create a new file
- **Follow the exact naming/style conventions found in Step 0** — do NOT invent your own

#### D5.2 Services
- Add service methods following the project's existing pattern exactly
- Place in the appropriate file based on domain/tag grouping

#### D5.3 Hooks
- Add query/mutation hooks following the project's existing pattern exactly
- GET endpoints → read/query hooks
- POST/PATCH/PUT/DELETE endpoints → mutation hooks with appropriate cache invalidation
- Add query key entries following the project's key factory pattern

#### D5.4 Exports
- Update all barrel/index exports as the project convention requires

### D6. Flag REMOVED endpoints/schemas (Categories C and F)

Do NOT delete anything from the codebase. Just collect the list for the final report so the user can decide.

### D7. Verify

Run the **Shared: Verify** procedure below.

### D8. Final Report

After ALL work is done, present a single summary as the final text of the turn (no tool calls after it). **The report MUST be written in Ukrainian (українською мовою).** All section headers, descriptions, and explanations — in Ukrainian. Only code identifiers, file paths, HTTP methods, and endpoint paths remain in English.

**The report describes what was done, not how the code looks.** One line per item, in words: "перейменовано `name` → `fullName`, оновлено 3 місця використання". No before/after code snippets, no JSON dumps, no diff output — the user reads the actual diff in the IDE. Start with what could not be done or needs the user's decision (removed endpoints still in code, ambiguous renames, pre-existing errors), then what was done.

```
## Синхронізація Swagger (diff-режим) завершена

### Підсумок swagger diff:
- Змінені ендпоінти: N
- Нові ендпоінти: N
- Видалені ендпоінти: N (позначені, не видалені з коду)
- Змінені схеми: N
- Нові схеми: N
- Видалені схеми: N (позначені, не видалені з коду)

### Оновлені ендпоінти:
- [METHOD /path] — що змінилось одним рядком (наприклад, "перейменовано name→fullName у тілі запиту; додано updatedAt у відповідь")
- ...

### Оновлені схеми:
- [SchemaName] — що змінилось
- ...

### Виправлені місця використання:
- [шлях до файлу] — що виправлено (наприклад, "оновлено деструктуризацію: fullName замість name")
- ...

### Нові ендпоінти додані (лише types + services + hooks, БЕЗ UI):
- [METHOD /path] — опис
- ...

### Нові схеми додані:
- [SchemaName] — опис
- ...

### Позначені ВИДАЛЕНІ (є в коді, але відсутні у новому swagger):
- Ендпоінти: [METHOD /path] — потребує перегляду/видалення
- Схеми: [SchemaName] — потребує перегляду/видалення
- ...

### Змінені файли:
- [список всіх змінених файлів]

### Преіснуючі помилки check-errors (не чіпав):
- N помилок у [файли] — поза скоупом синхронізації, рішення за вами

### Наступні кроки:
- Замініть `swagger-old.json` на `swagger.json` після перевірки цієї синхронізації, щоб наступний diff починався з нової базової версії.
```

---

# FULL MODE FLOW

> Run this flow when Mode Detection returned `FULL` (only `swagger.json` exists, no usable baseline).
>
> Here there is no baseline to diff against, so the source of truth is the swagger compared against the project's current API code.

### F1. Inventory the Swagger Snapshot

Do not open `swagger.json` with the Read tool — it is usually far too large. Use the bundled scripts (same `<scripts>` path as in diff mode):

```bash
python3 <scripts>/list-spec.py <path-to-swagger.json>            # every endpoint grouped by tag + every schema with usage counts
python3 <scripts>/list-spec.py <path-to-swagger.json> <tag>      # endpoints of one tag only
python3 <scripts>/show-endpoint.py <path-to-swagger.json> /api/companies get   # one endpoint, doc keys stripped, refs listed
python3 <scripts>/show-schema.py <path-to-swagger.json> UserDto                # one schema, doc keys stripped, refs listed
```

Start with `list-spec.py` to get the full inventory (method + path, operationId, tag, request/response schema names, parameter names). Open individual endpoints/schemas with the `show-*` scripts only when you are about to write or compare their types.

### F2. Read Current API Layer

Read ALL existing files in the API layer (locations found in Step 0):
- All type/interface files
- All service files — extract the actual endpoint URLs and HTTP methods from code
- All hook files

Build a map of EXISTING endpoints by finding the actual HTTP calls in service code (e.g., `apiClient.get('/users')`, `fetch('/api/users')`, etc.)

### F3. Diff Analysis

Compare swagger endpoints (from `list-spec.py`) vs existing endpoints (from the service code). For endpoints present in both, compare the swagger shape (`show-endpoint.py` / `show-schema.py`) with the project's types field by field. Categorize into:

#### A. EXISTING endpoints WITH CHANGES (update needed)
- Changed request body fields (added/removed/renamed/type changed)
- Changed response fields (added/removed/renamed/type changed)
- Changed path/query parameters
- Changed endpoint path or method

#### B. NEW endpoints (not in current codebase)
Endpoints in swagger that have no corresponding service method.

#### C. REMOVED endpoints (in code but not in swagger)
Endpoints in code that are no longer in swagger. **Flag in final report but do NOT delete.**

### F4. Update EXISTING Endpoints (Category A)

For each changed endpoint, update in this order — **following the project's own conventions discovered in Step 0**:

#### F4.1 Types
- Update interfaces/enums to match swagger schemas
- Add new fields, remove deleted fields, fix type changes
- Respect the project's existing naming and style conventions
- Update barrel exports if the project uses them

#### F4.2 Services
- Update method signatures if params/return types changed
- Update endpoint paths if changed
- Update barrel exports if the project uses them

#### F4.3 Hooks
- Update hook generic types if response/request types changed
- Update barrel exports if the project uses them

#### F4.4 Usage Sites
- Grep for usage of changed types/hooks across the entire codebase
- Fix type errors at usage sites (updated field names, removed fields, new required fields)
- Do NOT change business logic — only fix type compatibility

### F5. Add NEW Endpoints (Category B)

For each new endpoint, add ONLY infrastructure — do NOT integrate into UI:

#### F5.1 Types
- Create interfaces for request/response schemas
- Add to existing domain file if the domain already exists, or create a new file
- **Follow the exact naming/style conventions found in Step 0** — do NOT invent your own

#### F5.2 Services
- Add service methods following the project's existing pattern exactly
- Place in the appropriate file based on domain/tag grouping

#### F5.3 Hooks
- Add query/mutation hooks following the project's existing pattern exactly
- GET endpoints → read/query hooks
- POST/PATCH/PUT/DELETE endpoints → mutation hooks with appropriate cache invalidation
- Add query key entries following the project's key factory pattern

#### F5.4 Exports
- Update all barrel/index exports as the project convention requires

### F6. Verify

Run the **Shared: Verify** procedure below.

### F7. Final Report

After ALL work is done, present a single summary as the final text of the turn (no tool calls after it). **The report MUST be written in Ukrainian (українською мовою).** All section headers, descriptions, and explanations — in Ukrainian. Only code identifiers, file paths, HTTP methods, and endpoint paths remain in English.

Same rules as D8: describe what was done in words, one line per item, no before/after code, no JSON dumps. Start with what needs the user's decision, then what was done.

```
## Синхронізація Swagger завершена

### Оновлені ендпоінти:
- [METHOD /path] — що змінилось (наприклад, "додано поле X у відповідь, видалено поле Y")
- ...

### Виправлені місця використання:
- [шлях до файлу] — що виправлено (наприклад, "оновлено деструктуризацію для нового імені поля")
- ...

### Нові ендпоінти додані (лише types + services + hooks):
- [METHOD /path] — опис
- ...

### Позначені для перевірки (є в коді, але відсутні у swagger):
- [METHOD /path] — потребує перегляду/видалення
- ...

### Змінені файли:
- [список всіх змінених файлів]

### Преіснуючі помилки check-errors (не чіпав):
- N помилок у [файли] — поза скоупом синхронізації, рішення за вами
```

---

## Shared: Verify

Run `format` (Prettier), then `check-errors` (lint + tsc) from `package.json` — with the **full, unmodified output** (no `tail`/`head`, no output-limiting flags). If these scripts don't exist but can be created → add them; if the project is too specific → use available equivalents (`prettier --write`, `eslint`, `tsc --noEmit`).

Fix every error caused by the sync (new types, changed signatures, broken usage sites) until they are gone. **Pre-existing errors in files the sync did not touch are not yours to fix** — leave them, list them in the final report (count + files) and let the user decide. Then run the security checklist from the global CLAUDE.md on your own changes.

---

## Shared: Rules

1. **Detect the mode first** — check `swagger.json` (required) and whether `swagger-old.json` holds a real snapshot; never run the diff flow on an empty/placeholder baseline
2. **In diff mode, the diff is the source of truth** — do NOT re-derive changes by reading project code; trust the swagger-to-swagger diff
3. **NEVER assume project structure** — always discover it first (Step 0)
4. **NEVER change business logic** — only sync the API layer and fix type compatibility
5. **NEVER integrate new APIs into UI** — only add types, services, hooks
6. **NEVER delete endpoints/schemas from code** that are missing from swagger — only flag them in the report
7. **NEVER modify `swagger-old.json` yourself** — it is the user's baseline; the user decides when to roll it forward
8. **Ask ONLY if something is unclear** (or if `swagger.json` is missing) — otherwise just do the work and report at the end
9. **ALWAYS follow THIS PROJECT's conventions** for naming, file structure, patterns — match existing code exactly
10. **Swagger field names → match project convention** (if project uses camelCase, convert; if project keeps snake_case, keep) — in diff mode apply this consistently to both sides of the diff so renames are detected correctly
11. **Preserve existing comments/docs** on types if present
12. **Run `format`, then `check-errors`** after all changes (full output, no truncation) — fix what the sync broke, report pre-existing errors without touching them
13. **No intermediate output and no code dumps in the report** — the user sees the diff in the IDE; the report says what was done, in words, one line per item

## Shared: TypeScript Type Mapping

Map swagger schemas to TypeScript types correctly:
- `string` → `string` (check `format`: date-time → `string` or `Date` depending on project convention)
- `number` / `integer` → `number`
- `boolean` → `boolean`
- `array` of X → `X[]`
- `object` with properties → `interface` (or `type` — match project convention)
- `enum` → `enum` or union type (match what the project already uses)
- `$ref` → resolve to the referenced schema name
- nullable fields → `Type | null` or `Type | undefined` (match project convention)
- optional fields → `field?: Type`

---

## Diff Heuristics (DIFF MODE only — important details)

- **Field renames**: a field is "renamed" rather than "removed + added" when the old and new fields share the same type and sit at the same position, and there is no other plausible match. If ambiguous — treat as remove + add and flag in the report for the user to confirm.
- **Type changes on same-name field**: always treat as a change (not remove + add), and update all usage sites accordingly.
- **`$ref` resolution**: the scripts compare references as strings and report schema changes separately (Script 2). A change inside a referenced schema therefore shows up under the schema, with its `used by ->` endpoints — treat each of those endpoints as changed even though Script 1 does not list them.
- **Required flag changes**: a field going from optional to required (or vice versa) is a meaningful diff — update TypeScript optionality (`?`) and fix call sites that now must pass the field.
- **Enum narrowing vs widening**: added enum members are safe; removed enum members can break exhaustive switches — flag removed members in the report if any usage site relies on them.
- **Shared schemas**: if a schema used by many endpoints changed, update the schema once, then ensure every consumer endpoint's types/services/hooks still compile.
