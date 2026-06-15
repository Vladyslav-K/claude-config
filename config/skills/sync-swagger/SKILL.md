---
name: sync-swagger
description: Sync the project API layer (types, services, hooks) with swagger. Auto-detects mode — if a non-empty swagger-old.json baseline exists, apply only the precise swagger-to-swagger diff; otherwise do a full sync against swagger.json. Updates existing APIs, adds new ones (types/services/hooks only), and fixes usage where APIs changed.
disable-model-invocation: true
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

### D1. Read Both Swagger Snapshots

Read BOTH files:
- `swagger-old.json` → the **baseline** OpenAPI spec
- `swagger.json` → the **new** OpenAPI spec

For each spec, build a mental map of ALL endpoints AND schemas:
- **Endpoints:** method + path, operationId, summary, tag, request body schema, response schemas (success codes), path/query parameters
- **Schemas/components:** every definition under `components.schemas` — name, fields, types, enums, refs

Do this independently for both specs — do NOT merge yet.

### D2. Compute the Swagger Diff (CORE STEP)

Compare `swagger-old.json` (baseline) vs `swagger.json` (new). **This is the heart of diff mode.**

**⚡ Run the bundled Python scripts via the Bash tool** — swagger files are too large for the Read tool (~300KB+), so always compute the diff programmatically. The scripts live in this skill's `scripts/` directory and take the swagger paths as command-line arguments — there is nothing to edit inside the scripts.

> **Resolving the scripts path.** This skill is installed at `~/.claude/skills/sync-swagger/`, so its scripts are at `~/.claude/skills/sync-swagger/scripts/`. If the skill lives somewhere else (e.g. a project-local `.claude/skills/`), use that location's absolute path instead. Below, `<scripts>` stands for the absolute path to this skill's `scripts/` directory.

#### Script 1: Compare endpoints (new / removed / changed)

```bash
python3 <scripts>/diff-endpoints.py <path-to-swagger-old.json> <path-to-swagger.json>
```

#### Script 2: Compare schemas (new / removed / changed)

```bash
python3 <scripts>/diff-schemas.py <path-to-swagger-old.json> <path-to-swagger.json>
```

#### Script 3: Show detailed diff for a specific endpoint

Use this AFTER scripts 1-2 identify changed endpoints. Pass the target path and HTTP method as the 3rd and 4th arguments:

```bash
python3 <scripts>/show-endpoint.py <path-to-swagger-old.json> <path-to-swagger.json> /api/companies get
```

#### Script 4: Show detailed diff for a specific schema

Use this AFTER script 2 identifies changed schemas. Pass the schema name as the 3rd argument:

```bash
python3 <scripts>/show-schema.py <path-to-swagger-old.json> <path-to-swagger.json> UserDto
```

**Execution order:** Run Script 1 + Script 2 in parallel → then Script 3/4 only for items that changed.

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

**Output a structured diff summary before touching any code.** Example format:

```
CHANGED endpoints:
- PATCH /users/{id}
  - request body: removed "age", added "birthDate: string (date)", renamed "name" -> "fullName"
  - response: added "updatedAt: string (date-time)"
- GET /orders
  - query params: added "status: enum[pending,completed,cancelled]" (optional)

NEW endpoints:
- POST /orders/{id}/cancel -> returns OrderDto

REMOVED endpoints (flag only):
- DELETE /legacy/sessions

CHANGED schemas:
- UserDto: added "avatar?: string", removed "age"
- OrderStatus enum: added "refunded"

NEW schemas:
- CancelOrderRequest { reason: string }

REMOVED schemas (flag only):
- LegacySession
```

### D3. Map Diff to Code Locations

For EACH item in the diff, find WHERE in the project code it lives. Only touch the files that correspond to the diff — do NOT scan everything.

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

After ALL work is done, present a single summary. **The report MUST be written in Ukrainian (українською мовою).** All section headers, descriptions, and explanations — in Ukrainian. Only code identifiers, file paths, HTTP methods, and endpoint paths remain in English.

```
## Синхронізація Swagger (diff-режим) завершена

### Підсумок swagger diff:
- Змінені ендпоінти: N
- Нові ендпоінти: N
- Видалені ендпоінти: N (позначені, не видалені з коду)
- Змінені схеми: N
- Нові схеми: N
- Видалені схеми: N (позначені, не видалені з коду)

### Оновлені ендпоінти (з точною дельтою):
- [METHOD /path] — що змінилось (наприклад, "перейменовано name→fullName у тілі запиту; додано updatedAt у відповідь")
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

### Наступні кроки:
- Замініть `swagger-old.json` на `swagger.json` після перевірки цієї синхронізації, щоб наступний diff починався з нової базової версії.
```

---

# FULL MODE FLOW

> Run this flow when Mode Detection returned `FULL` (only `swagger.json` exists, no usable baseline).
>
> Here there is no baseline to diff against, so the source of truth is the swagger compared against the project's current API code.

### F1. Read Swagger Snapshot

Read the `swagger.json` found in Mode Detection. Parse the OpenAPI spec. Build a mental map of ALL endpoints:
- Method + path
- operationId, summary, tag
- Request body schema (with all fields and types)
- Response schemas (success codes: 200, 201, etc.)
- Path parameters, query parameters

### F2. Read Current API Layer

Read ALL existing files in the API layer (locations found in Step 0):
- All type/interface files
- All service files — extract the actual endpoint URLs and HTTP methods from code
- All hook files

Build a map of EXISTING endpoints by finding the actual HTTP calls in service code (e.g., `apiClient.get('/users')`, `fetch('/api/users')`, etc.)

### F3. Diff Analysis

Compare swagger endpoints vs existing endpoints. Categorize into:

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

After ALL work is done, present a single summary. **The report MUST be written in Ukrainian (українською мовою).** All section headers, descriptions, and explanations — in Ukrainian. Only code identifiers, file paths, HTTP methods, and endpoint paths remain in English.

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
```

---

## Shared: Verify

Run `format` (Prettier), then `check-errors` (lint + tsc) from `package.json` — with the **full, unmodified output** (no `tail`/`head`, no output-limiting flags). Fix ALL issues until both pass clean. If these scripts don't exist but can be created → add them; if the project is too specific → use available equivalents (`prettier --write`, `eslint`, `tsc --noEmit`).

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
12. **Run `format`, then `check-errors`** after all changes (full output, no truncation) — fix until clean

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
- **`$ref` resolution**: when comparing endpoints, resolve `$ref` on both sides before diffing so you are comparing actual shapes, not reference strings.
- **Required flag changes**: a field going from optional to required (or vice versa) is a meaningful diff — update TypeScript optionality (`?`) and fix call sites that now must pass the field.
- **Enum narrowing vs widening**: added enum members are safe; removed enum members can break exhaustive switches — flag removed members in the report if any usage site relies on them.
- **Shared schemas**: if a schema used by many endpoints changed, update the schema once, then ensure every consumer endpoint's types/services/hooks still compile.
