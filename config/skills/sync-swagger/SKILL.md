---
name: sync-swagger
description: Sync the project API layer (types, services, hooks) with swagger. Auto-detects mode — if a non-empty swagger-old.json baseline exists, apply only the precise swagger-to-swagger diff; otherwise do a full sync against swagger.json. Updates existing APIs, adds new ones (types/services/hooks only), fixes usage where APIs changed, and asks the user before any fix that changes the UI.
allowed-tools: Bash(python3 *)
---

# Sync Swagger

## Additional context from user
$ARGUMENTS

## Purpose
Synchronize the frontend API layer (types, services, hooks) with the latest swagger snapshot — all while preserving **this project's** conventions. The skill runs in one of two modes, chosen automatically:

- **DIFF MODE** — when a populated `swagger-old.json` baseline exists alongside `swagger.json`. Compute a precise **swagger-to-swagger diff** and apply only that delta to the codebase. Faster, more reliable, avoids false positives.
- **FULL MODE** — when only `swagger.json` exists (no usable baseline). Scan the project API layer, diff it against the swagger, update existing code, and add new endpoints.

**Flow (both modes): research → understand changes → apply API-layer changes and safe usage fixes → ask the user about UI-affecting changes → apply the decisions → verify → short report of what needs the user's attention.**
Do NOT ask for confirmation of routine API-layer work. The one mandatory stop is the UI decision step (**Shared: UI-Affecting Changes**): a UI-affecting fix is never applied silently and never left only as a line in the report.

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

Keep this categorised diff as **your own working checklist** — every item must be either applied (A, B, D, E) or flagged (C, F) by the end. **Do not print it to the user:** text written mid-turn is collapsed by the CLI, and the user reviews the resulting code changes in the IDE anyway. The user gets one short final report (D9) with only what the IDE diff does not show.

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
- Grep for usage of changed types/hooks/services across the entire codebase, including pages and components
- Split every affected usage site into two groups (criteria in **Shared: UI-Affecting Changes**):
  - **Safe fixes — apply right away.** What the user sees and does stays exactly the same: a renamed field read/written under its new name, an updated type annotation or generic, a changed query key, a renamed param passed through unchanged, a new required request field whose value the caller already has.
  - **UI-affecting — do not fix yet, collect.** The fix would change rendered output, a component's props contract, form fields, select/filter options, validation, navigation or other user-visible behavior. Record each item (file, what changed in the API, what breaks in the UI, possible fixes) for step D7.
- Do NOT change business logic on your own — anything beyond type compatibility is applied only after the user picks it in step D7

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

Do NOT delete anything from the codebase. Just collect the list for the final report so the user can decide. If a removed endpoint is still called from a page, the page's fallback behavior is a UI decision — add it to the D7 list.

### D7. Resolve UI-Affecting Changes

Run the **Shared: UI-Affecting Changes** procedure below for everything collected in D4.4 and D6.

### D8. Verify

Run the **Shared: Verify** procedure below.

### D9. Final Report

After ALL work is done, present a single summary as the final text of the turn (no tool calls after it). **The report MUST be written in Ukrainian (українською мовою).** All section headers, descriptions, and explanations — in Ukrainian. Only code identifiers, file paths, HTTP methods, and endpoint paths remain in English.

**The report is short and carries only what the IDE diff does not show.** The user reviews every code change in the IDE, so a list of routine work is noise. Do NOT list:
- changed or created files
- updated endpoints/schemas and what changed in them
- fixed usage sites
- added types, services, hooks, query keys, exports
- UI changes the user already chose in D7 — they are visible in the diff
- code snippets, JSON dumps, diff output

The report contains, in this order:
1. **Scope** — one line of counts.
2. **Потребує уваги** — only items that need the user's action or confirmation, one line each: a page left broken by the user's choice (file + consequence), a removed endpoint/schema that is still used in code, an ambiguous rename treated as remove + add, anything that could not be synced and why, pre-existing check-errors (count + files). An endpoint/schema that was removed from swagger and is not used in code is not reported.
3. **Checks** — one line with the result of `format` and `check-errors`, one line about the security scan of your changes.
4. **Baseline reminder** — one line about rolling `swagger-old.json` forward.

Omit an empty section entirely — no «немає» placeholders. If «Потребує уваги» is empty, the whole report is the scope line, the checks and the reminder.

```
## Синхронізація Swagger (diff-режим) завершена

Ендпоінти: змінено N, додано N, видалено N. Схеми: змінено N, додано N, видалено N.

### Потребує уваги:
- `DELETE /api/users/{id}` видалено зі swagger, але `useDeleteUser` досі викликається у `src/pages/users/UsersTable.tsx` — вирішіть, чи прибирати
- `UserDto`: неоднозначне перейменування `phone` → `phoneNumber`, оброблено як видалення + додавання — підтвердіть
- `src/pages/users/UserForm.tsx` лишився зламаним за вашим рішенням: форма не надсилає обовʼязкове `role`, запит впаде з 400
- Преіснуючі помилки check-errors: N у `file1`, `file2` — поза скоупом, не чіпав

format і check-errors — без помилок від синхронізації. Перевірка змін на вразливості: <результат одним реченням>.
Після перевірки замініть `swagger-old.json` на `swagger.json`, щоб наступний diff починався з нової базової версії.
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
- Grep for usage of changed types/hooks across the entire codebase, including pages and components
- Split every affected usage site into two groups, exactly as in D4.4 (criteria in **Shared: UI-Affecting Changes**):
  - **Safe fixes — apply right away** (renamed fields, type annotations, generics, query keys; the UI stays exactly the same)
  - **UI-affecting — do not fix yet, collect** for step F6, together with removed endpoints (Category C) that are still called from pages
- Do NOT change business logic on your own — anything beyond type compatibility is applied only after the user picks it in step F6

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

### F6. Resolve UI-Affecting Changes

Run the **Shared: UI-Affecting Changes** procedure below for everything collected in F4.4.

### F7. Verify

Run the **Shared: Verify** procedure below.

### F8. Final Report

After ALL work is done, present a single summary as the final text of the turn (no tool calls after it). **The report MUST be written in Ukrainian (українською мовою).** All section headers, descriptions, and explanations — in Ukrainian. Only code identifiers, file paths, HTTP methods, and endpoint paths remain in English.

Same rules as D9: only what the IDE diff does not show, no lists of routine work, empty sections omitted. There is no baseline reminder in full mode.

```
## Синхронізація Swagger завершена

Ендпоінти: оновлено N, додано N, є в коді, але відсутні у swagger N.

### Потребує уваги:
- `GET /api/reports` відсутній у swagger, але досі викликається у `src/pages/reports/ReportsPage.tsx` — вирішіть, чи прибирати
- `src/pages/users/UserForm.tsx` лишився зламаним за вашим рішенням: форма не надсилає обовʼязкове `role`, запит впаде з 400
- Преіснуючі помилки check-errors: N у `file1`, `file2` — поза скоупом, не чіпав

format і check-errors — без помилок від синхронізації. Перевірка змін на вразливості: <результат одним реченням>.
```

---

## Shared: UI-Affecting Changes

An API change often breaks pages: a component reads a field that no longer exists, a form does not send a newly required field, a select renders removed enum members, a prop type no longer matches. Leaving this unfixed ships a broken app; fixing it silently changes the UI without the user's consent. So every such fix goes through the user — as a question, not as a side note in the report.

**UI-affecting** — the fix would change any of:
- **Rendered output:** a displayed field was removed; a value changed type or format (`string` → object, number → string, date format), so it renders differently; a table/list column lost its data
- **Component props contract:** a prop has to be removed, made required, or change type because of the API, so parent components must pass something new
- **Forms and inputs:** a newly required request field has no input or known value on the page; a removed field still has an input; validation constraints changed; enum members changed in selects, filters, tabs or badges
- **Behavior and flow:** changed status codes or response shape alter success/error handling, pagination, redirects, or conditional rendering driven by a changed field or enum
- **Removed endpoints still called from a page:** the call stays in code (rule 6), but what the page should do instead is the user's decision

**Not UI-affecting** (apply as safe fixes in D4.4/F4.4): renamed fields carrying the same data, type annotations, generics, query keys, imports, barrel exports, optionality changes the existing render already handles.

When unsure which group an item belongs to — treat it as UI-affecting.

**Procedure:**
1. Finish all API-layer work and safe fixes first, so the questions come once, after the sync, as one batch.
2. For every collected item, read the page/component and work out 2-3 concrete fixes for this specific case.
3. Ask via AskUserQuestion — up to 4 questions per call; if there are more items, make several consecutive calls. Merge items with the same page and the same root cause into one question. Do not print the questions as text and do not use the `preview` field.
4. Each question is self-contained, because the user does not see your analysis: the file path of the page/component, what changed in the API, what breaks in the UI now, and the consequence of each option in its `description`.
5. The most suitable option goes first with "(Recommended)". A typical set:
   - a minimal fix that keeps the current UI as close as possible (read the value from its new location, render a fallback)
   - adapting the UI to the new API (remove the column/field, add an input for the new required field, update select options)
   - leave the code as is — state explicitly that the page stays broken and check-errors keeps failing
6. Apply exactly what the user chose. New UI elements follow the project's existing components and styles. If an "Other" answer is ambiguous — ask a follow-up question instead of guessing.
7. If nothing was collected — skip this step silently.

## Shared: Verify

Run `format` (Prettier), then `check-errors` (lint + tsc) from `package.json` — with the **full, unmodified output** (no `tail`/`head`, no output-limiting flags). If these scripts don't exist but can be created → add them; if the project is too specific → use available equivalents (`prettier --write`, `eslint`, `tsc --noEmit`).

Fix every error caused by the sync (new types, changed signatures, broken usage sites) until they are gone. If an error sits at a UI-affecting usage site that was not part of the UI decision step — run **Shared: UI-Affecting Changes** for it before fixing. Errors the user explicitly chose to leave stay in place and go into the report section «Потребує уваги». **Pre-existing errors in files the sync did not touch are not yours to fix** — leave them, list them in the final report (count + files) and let the user decide. Then run the security checklist from the global CLAUDE.md on your own changes.

---

## Shared: Rules

1. **Detect the mode first** — check `swagger.json` (required) and whether `swagger-old.json` holds a real snapshot; never run the diff flow on an empty/placeholder baseline
2. **In diff mode, the diff is the source of truth** — do NOT re-derive changes by reading project code; trust the swagger-to-swagger diff
3. **NEVER assume project structure** — always discover it first (Step 0)
4. **NEVER change business logic or UI on your own** — sync the API layer and apply safe type-compatibility fixes; every UI-affecting fix goes through the user via AskUserQuestion (**Shared: UI-Affecting Changes**), never silently and never only as a note in the report
5. **NEVER integrate new APIs into UI** — only add types, services, hooks
6. **NEVER delete endpoints/schemas from code** that are missing from swagger — only flag them in the report
7. **NEVER modify `swagger-old.json` yourself** — it is the user's baseline; the user decides when to roll it forward
8. **Ask ONLY about UI-affecting changes, unclear items, or a missing `swagger.json`** — otherwise just do the work and report at the end
9. **ALWAYS follow THIS PROJECT's conventions** for naming, file structure, patterns — match existing code exactly
10. **Swagger field names → match project convention** (if project uses camelCase, convert; if project keeps snake_case, keep) — in diff mode apply this consistently to both sides of the diff so renames are detected correctly
11. **Preserve existing comments/docs** on types if present
12. **Run `format`, then `check-errors`** after all changes (full output, no truncation) — fix what the sync broke, report pre-existing errors without touching them
13. **No intermediate output and a short final report** — the user reviews all code changes in the IDE; the report has no lists of files, endpoints, usage sites or added code, only the scope counts, what needs the user's attention, and the check results

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
- **Enum narrowing vs widening**: added enum members are safe; removed enum members can break exhaustive switches — if any usage site relies on a removed member, fix it as a safe fix when the member only appears in types, or treat it as UI-affecting when it drives rendered options, labels or conditional rendering.
- **Shared schemas**: if a schema used by many endpoints changed, update the schema once, then ensure every consumer endpoint's types/services/hooks still compile.
