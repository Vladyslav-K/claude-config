---
name: sync-swagger-diff
description: Sync project API layer using diff between two swagger snapshots (swagger-old.json vs swagger.json). Detects exact changes between versions and applies only those changes to types, services, hooks, and usage sites.
---

# Sync Swagger Diff

## Additional context from user
$ARGUMENTS

## Purpose
Synchronize the frontend API layer (types, services, hooks) with the latest swagger by **comparing two swagger snapshots**:
- `swagger-old.json` — the previous version that is already **100% in sync** with the project code (the baseline).
- `swagger.json` — the new version. The delta between them is what the project code is currently missing.

Instead of scanning the whole project to detect what's out of sync, we compute a precise **swagger-to-swagger diff** and apply only that delta to the codebase. This is faster, more reliable, and avoids false positives.

**Flow: research → compute swagger diff → apply the diff to code → verify → report what was done.**
Do NOT ask for confirmation mid-process. Just do the work and report results at the end.

---

## Execution Steps

### 0. Discover Project Structure (MANDATORY FIRST STEP)

Before anything else — **research this specific project** to understand how its API layer is organized. Do NOT assume any folder structure or naming conventions.

Use Explore agent / Glob / Grep to answer:

1. **Where are the swagger files?**
   - `swagger-old.json` — baseline, already synced with project. Check `.project-meta/tasks/swagger-old.json` first, then search broadly (`**/swagger-old.json`).
   - `swagger.json` — new version. Check `.project-meta/tasks/swagger.json` first, then search broadly.
   - **If either file is missing — STOP and ask the user where they are.** Do NOT proceed without both files.
2. **Where are API types defined?** — Search for directories/files containing API interfaces, DTOs, enums (e.g., `types/`, `models/`, `interfaces/`, `api/`, `generated/`).
3. **Where are API service functions?** — Search for files that make HTTP calls (axios, fetch, ky, got, etc.). Understand the HTTP client used.
4. **Where are API hooks defined?** — Search for React Query / SWR / custom hooks that wrap service calls. Identify the data-fetching library used.
5. **What are the naming conventions?** — Read 2-3 existing files from each layer (types, services, hooks) to learn:
   - File naming pattern (kebab-case? camelCase? by domain? by feature?)
   - Type naming pattern (e.g., `UserResponse`, `IUser`, `TUser`, `UserDto`)
   - Service naming pattern (e.g., `userService.getAll()`, `getUsers()`, `api.users.list()`)
   - Hook naming pattern (e.g., `useUsers()`, `useGetUsers()`, `useUserQuery()`)
   - Export pattern (barrel `index.ts`? direct imports? re-exports?)
   - Query key pattern (factory? string arrays? constants?)
6. **What is the HTTP client?** — axios, fetch, ky, ofetch, etc. Understand how requests are configured (base URL, interceptors, auth headers).
7. **What is the data-fetching library?** — React Query (TanStack Query), SWR, RTK Query, Apollo, or custom.
8. **Read project memory** — Check `.project-meta/memory/persistent.md` if it exists.

**Store all findings as your "Project API Conventions" reference for all subsequent steps.**

---

### 1. Read Both Swagger Snapshots

Read BOTH files found in step 0:
- `swagger-old.json` → parse as the **baseline** OpenAPI spec
- `swagger.json` → parse as the **new** OpenAPI spec

For each spec, build a mental map of ALL endpoints AND schemas:
- **Endpoints:** method + path, operationId, summary, tag, request body schema, response schemas (success codes), path/query parameters
- **Schemas/components:** every definition under `components.schemas` — name, fields, types, enums, refs

Do this independently for both specs — do NOT merge yet.

---

### 2. Compute the Swagger Diff (CORE STEP)

Compare `swagger-old.json` (baseline) vs `swagger.json` (new). **This is the heart of this command.** The diff itself — not the project code — is the source of truth for what needs to change.

**⚡ Use these Python scripts via Bash tool** — swagger files are too large for Read tool (~300KB+), so always compute the diff programmatically.

#### Script 1: Compare endpoints (new / removed / changed)

```bash
python3 -c "
import json, sys

OLD_PATH = '<path-to-swagger-old.json>'
NEW_PATH = '<path-to-swagger.json>'

with open(OLD_PATH) as f:
    old = json.load(f)
with open(NEW_PATH) as f:
    new = json.load(f)

def get_endpoints(spec):
    endpoints = {}
    for path, methods in spec.get('paths', {}).items():
        for method, details in methods.items():
            if method in ('get', 'post', 'put', 'patch', 'delete', 'options', 'head'):
                key = f'{method.upper()} {path}'
                endpoints[key] = details
    return endpoints

old_eps = get_endpoints(old)
new_eps = get_endpoints(new)
old_keys = set(old_eps.keys())
new_keys = set(new_eps.keys())

added = sorted(new_keys - old_keys)
removed = sorted(old_keys - new_keys)
common = sorted(old_keys & new_keys)

print('=== NEW ENDPOINTS ===')
for ep in added:
    tags = new_eps[ep].get('tags', [])
    op_id = new_eps[ep].get('operationId', 'N/A')
    print(f'  {ep} | tags={tags} | operationId={op_id}')

print()
print('=== REMOVED ENDPOINTS ===')
for ep in removed:
    tags = old_eps[ep].get('tags', [])
    op_id = old_eps[ep].get('operationId', 'N/A')
    print(f'  {ep} | tags={tags} | operationId={op_id}')

print()
print(f'=== COMMON ENDPOINTS: {len(common)} ===')
changed = []
for ep in common:
    if json.dumps(old_eps[ep], sort_keys=True) != json.dumps(new_eps[ep], sort_keys=True):
        changed.append(ep)

print(f'Changed: {len(changed)}')
for ep in changed:
    print(f'  {ep}')
"
```

#### Script 2: Compare schemas (new / removed / changed)

```bash
python3 -c "
import json

OLD_PATH = '<path-to-swagger-old.json>'
NEW_PATH = '<path-to-swagger.json>'

with open(OLD_PATH) as f:
    old = json.load(f)
with open(NEW_PATH) as f:
    new = json.load(f)

old_schemas = set(old.get('components', {}).get('schemas', {}).keys())
new_schemas = set(new.get('components', {}).get('schemas', {}).keys())

added = sorted(new_schemas - old_schemas)
removed = sorted(old_schemas - new_schemas)
common = sorted(old_schemas & new_schemas)

print('=== NEW SCHEMAS ===')
for s in added:
    print(f'  {s}')

print()
print('=== REMOVED SCHEMAS ===')
for s in removed:
    print(f'  {s}')

print()
print(f'=== COMMON SCHEMAS: {len(common)} ===')
changed = []
for s in common:
    if json.dumps(old['components']['schemas'][s], sort_keys=True) != json.dumps(new['components']['schemas'][s], sort_keys=True):
        changed.append(s)

print(f'Changed: {len(changed)}')
for s in changed:
    print(f'  {s}')
"
```

#### Script 3: Show detailed diff for a specific endpoint

Use this AFTER scripts 1-2 identify changed endpoints. Replace `METHOD` and `/path` accordingly:

```bash
python3 -c "
import json

OLD_PATH = '<path-to-swagger-old.json>'
NEW_PATH = '<path-to-swagger.json>'
# Change these to the target endpoint:
TARGET_PATH = '/api/companies'
TARGET_METHOD = 'get'

with open(OLD_PATH) as f:
    old = json.load(f)
with open(NEW_PATH) as f:
    new = json.load(f)

old_ep = old['paths'][TARGET_PATH][TARGET_METHOD]
new_ep = new['paths'][TARGET_PATH][TARGET_METHOD]

print('=== OLD ===')
print(json.dumps(old_ep, indent=2))
print()
print('=== NEW ===')
print(json.dumps(new_ep, indent=2))
"
```

#### Script 4: Show detailed diff for a specific schema

Use this AFTER script 2 identifies changed schemas:

```bash
python3 -c "
import json

OLD_PATH = '<path-to-swagger-old.json>'
NEW_PATH = '<path-to-swagger.json>'
SCHEMA_NAME = 'UserDto'  # Change to target schema

with open(OLD_PATH) as f:
    old = json.load(f)
with open(NEW_PATH) as f:
    new = json.load(f)

old_s = old['components']['schemas'].get(SCHEMA_NAME, {})
new_s = new['components']['schemas'].get(SCHEMA_NAME, {})

print('=== OLD ===')
print(json.dumps(old_s, indent=2))
print()
print('=== NEW ===')
print(json.dumps(new_s, indent=2))
"
```

**Execution order:** Run Script 1 + Script 2 in parallel → then Script 3/4 only for items that changed.

**Replace `<path-to-swagger-old.json>` and `<path-to-swagger.json>`** with actual paths found in step 0.

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

---

### 3. Map Diff to Code Locations

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

---

### 4. Apply CHANGED endpoints (Category A) and CHANGED schemas (Category D)

For each changed endpoint/schema, update in this order — **following the project's own conventions discovered in step 0**:

#### 4.1 Types
- Update interfaces/enums to match the NEW swagger schema
- Apply the exact delta from step 2: add new fields, remove deleted fields, rename renamed fields, fix type changes, update enum members
- Respect the project's existing naming and style conventions
- Update barrel exports if the project uses them

#### 4.2 Services
- Update method signatures if params/return types changed
- Update endpoint paths if changed (e.g., `/users/{id}` → `/users/{userId}`)
- Update HTTP method if changed
- Update barrel exports if the project uses them

#### 4.3 Hooks
- Update hook generic types if response/request types changed
- Update query keys if path/params changed
- Update barrel exports if the project uses them

#### 4.4 Usage Sites
- Grep for usage of changed types/hooks/services across the entire codebase
- Fix type errors at usage sites:
  - Renamed fields: update all reads/writes to the new name
  - Removed fields: remove references (if code uses a removed field, replace with equivalent or mark clearly)
  - New required fields in requests: add to callers where required
  - Changed enum values: update consumers
- Do NOT change business logic — only fix type compatibility driven by the swagger diff

---

### 5. Add NEW endpoints (Category B) and NEW schemas (Category E)

For each new endpoint/schema, add ONLY infrastructure — do NOT integrate into UI:

#### 5.1 Types
- Create interfaces for request/response/shared schemas
- Add to existing domain file if the domain already exists, or create a new file
- **Follow the exact naming/style conventions found in step 0** — do NOT invent your own

#### 5.2 Services
- Add service methods following the project's existing pattern exactly
- Place in the appropriate file based on domain/tag grouping

#### 5.3 Hooks
- Add query/mutation hooks following the project's existing pattern exactly
- GET endpoints → read/query hooks
- POST/PATCH/PUT/DELETE endpoints → mutation hooks with appropriate cache invalidation
- Add query key entries following the project's key factory pattern

#### 5.4 Exports
- Update all barrel/index exports as the project convention requires

---

### 6. Flag REMOVED endpoints/schemas (Categories C and F)

Do NOT delete anything from the codebase. Just collect the list for the final report so the user can decide.

---

### 7. Verify

Run `format-and-check` script from `package.json` (typically combines format + lint + typecheck). Fix ALL issues until it passes clean.

---

### 8. Final Report

After ALL work is done, present a single summary. **The report MUST be written in Ukrainian (українською мовою).** All section headers, descriptions, and explanations — in Ukrainian. Only code identifiers, file paths, HTTP methods, and endpoint paths remain in English.

```
## Синхронізація Swagger Diff завершена

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

## Rules

1. **TWO swagger files are required** — if either `swagger-old.json` or `swagger.json` is missing, STOP and ask the user
2. **The diff is the source of truth** — do NOT re-derive changes by reading project code; trust the swagger-to-swagger diff computed in step 2
3. **NEVER assume project structure** — always discover it first (step 0)
4. **NEVER change business logic** — only sync API layer and fix type compatibility driven by the diff
5. **NEVER integrate new APIs into UI** — only add types, services, hooks
6. **NEVER delete endpoints/schemas from code** that are missing from new swagger — only flag them in report
7. **NEVER modify `swagger-old.json` yourself** — it is the user's baseline; the user decides when to roll it forward
8. **Ask ONLY if something is unclear** — otherwise just do the work and report at the end
9. **ALWAYS follow THIS PROJECT's conventions** for naming, file structure, patterns — match existing code exactly
10. **Swagger field names → match project convention** (if project uses camelCase, convert; if project keeps snake_case, keep) — apply this consistently to both sides of the diff so renames are detected correctly
11. **Preserve existing comments/docs** on types if present
12. **Run `format-and-check`** after all changes — fix until clean
13. **Map swagger schemas to TypeScript types correctly:**
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

## Diff Heuristics (important details)

- **Field renames**: a field is "renamed" rather than "removed + added" when the old and new fields share the same type and sit at the same position, and there is no other plausible match. If ambiguous — treat as remove + add and flag in the report for the user to confirm.
- **Type changes on same-name field**: always treat as a change (not remove + add), and update all usage sites accordingly.
- **`$ref` resolution**: when comparing endpoints, resolve `$ref` on both sides before diffing so you are comparing actual shapes, not reference strings.
- **Required flag changes**: a field going from optional to required (or vice versa) is a meaningful diff — update TypeScript optionality (`?`) and fix call sites that now must pass the field.
- **Enum narrowing vs widening**: added enum members are safe; removed enum members can break exhaustive switches — flag removed members in the report if any usage site relies on them.
- **Shared schemas**: if a schema used by many endpoints changed, update the schema once, then ensure every consumer endpoint's types/services/hooks still compile.
