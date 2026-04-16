---
name: sync-swagger
description: Sync project API types, services, and hooks with swagger.json. Updates existing APIs, adds new ones (types/services/hooks only), and fixes usage where APIs changed.
---

# Sync Swagger

## Additional context from user
$ARGUMENTS

## Purpose
Synchronize the frontend API layer (types, services, hooks) with the latest `swagger.json` snapshot. Detect differences, update existing code, add new endpoints — all while preserving **this project's** conventions.

**Flow: research → understand changes → apply all changes → verify → report what was done.**
Do NOT ask for confirmation mid-process. Just do the work and report results at the end.

---

## Execution Steps

### 0. Discover Project Structure (MANDATORY FIRST STEP)

Before anything else — **research this specific project** to understand how its API layer is organized. Do NOT assume any folder structure or naming conventions.

Use Explore agent / Glob / Grep to answer:

1. **Where is `swagger.json`?** — Check `.project-meta/tasks/swagger.json` first, then search broadly (`**/swagger.json`, `**/openapi.json`). If not found — ask the user.
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

### 1. Read Swagger Snapshot

Read the swagger.json found in step 0. Parse the OpenAPI spec. Build a mental map of ALL endpoints:
- Method + path
- operationId, summary, tag
- Request body schema (with all fields and types)
- Response schemas (success codes: 200, 201, etc.)
- Path parameters, query parameters

---

### 2. Read Current API Layer

Read ALL existing files in the API layer (locations found in step 0):
- All type/interface files
- All service files — extract the actual endpoint URLs and HTTP methods from code
- All hook files

Build a map of EXISTING endpoints by finding the actual HTTP calls in service code (e.g., `apiClient.get('/users')`, `fetch('/api/users')`, etc.)

---

### 3. Diff Analysis

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

---

### 4. Update EXISTING Endpoints (Category A)

For each changed endpoint, update in this order — **following the project's own conventions discovered in step 0**:

#### 4.1 Types
- Update interfaces/enums to match swagger schemas
- Add new fields, remove deleted fields, fix type changes
- Respect the project's existing naming and style conventions
- Update barrel exports if the project uses them

#### 4.2 Services
- Update method signatures if params/return types changed
- Update endpoint paths if changed
- Update barrel exports if the project uses them

#### 4.3 Hooks
- Update hook generic types if response/request types changed
- Update barrel exports if the project uses them

#### 4.4 Usage Sites
- Grep for usage of changed types/hooks across the entire codebase
- Fix type errors at usage sites (updated field names, removed fields, new required fields)
- Do NOT change business logic — only fix type compatibility

---

### 5. Add NEW Endpoints (Category B)

For each new endpoint, add ONLY infrastructure — do NOT integrate into UI:

#### 5.1 Types
- Create interfaces for request/response schemas
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

### 6. Verify

Run `format-and-check` script from `package.json` (typically combines format + lint + typecheck). Fix ALL issues until it passes clean.

---

### 7. Final Report

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

## Rules

1. **NEVER assume project structure** — always discover it first (step 0)
2. **NEVER change business logic** — only sync API layer and fix type compatibility
3. **NEVER integrate new APIs into UI** — only add types, services, hooks
4. **NEVER delete endpoints from code** that are missing from swagger — only flag them in report
5. **Ask ONLY if something is unclear** — otherwise just do the work and report at the end
6. **ALWAYS follow THIS PROJECT's conventions** for naming, file structure, patterns — match existing code exactly
7. **Swagger field names → match project convention** (if project uses camelCase, convert; if project keeps snake_case, keep)
8. **Preserve existing comments/docs** on types if present
9. **Run `format-and-check`** after all changes — fix until clean
10. **Map swagger schemas to TypeScript types correctly:**
    - `string` → `string` (check `format`: date-time → `string` or `Date` depending on project convention)
    - `number` / `integer` → `number`
    - `boolean` → `boolean`
    - `array` of X → `X[]`
    - `object` with properties → `interface` (or `type` — match project convention)
    - `enum` → `enum` or union type (match what the project already uses)
    - `$ref` → resolve to the referenced schema name
    - nullable fields → `Type | null` or `Type | undefined` (match project convention)
    - optional fields → `field?: Type`
