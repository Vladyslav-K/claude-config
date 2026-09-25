---
name: browser-test
description: Test finished changes in a real headless Chromium through the Playwright MCP and save the evidence — report.md with steps and screenshots, plus a trace, plus findings.md with every bug or finding outside the task's scope — into .project-meta/qa/<run>/. Logs in with accounts from .project-meta/qa/accounts.md and records every account or entity the test creates there. Called by /run-tasks after every task and by its QA task for a regression pass; outside /run-tasks only when the user explicitly asks to test — «протестуй», «перевір у браузері», «прогони тест», «зроби QA». Never run it on your own initiative.
---

# Browser Test

## Additional context
$ARGUMENTS

Arguments from the caller: the scenario source (a `### Task N` subsection, a `qa.md`, or "ad-hoc" with a description of the change), the run slug, and any setup (roles, data) from the plan.

## Purpose

Run a test scenario in the real app, record what actually happened, fix what is clearly broken in the code under test, and hand the user a report they can verify quickly. Only what you observed in the browser counts as passed.

## When It Runs

- **`/run-tasks`** — after every task (scenario = the task's `### Task N` subsection in `## Testing`) and in the `QA` task (scenario = the whole `qa.md`, regression pass).
- **Ad-hoc** — only when the user asks to test in the current request ("зроби X і протестуй"). No request → no browser test; the regular completion report tells the user how to check.
- A change with nothing observable in the browser (types, config, tooling, refactor without UI effect) → skip, and write one line with the reason instead of a report.

## Files

```
.project-meta/qa/
├── accounts.md                  # Test accounts and created entities (user + you)
├── .auth/<account-id>.json      # Saved browser sessions, one per account
├── _artifacts/                  # MCP output dir (traces land here first)
└── DD-MM-YYYY-<slug>/           # One folder per tested task / QA pass / ad-hoc test
    ├── report.md
    ├── findings.md              # Bugs and findings outside the task's scope
    ├── findings/NN-<slug>.png   # Screenshots for findings.md
    ├── screens/01-<step>.png
    └── trace/                   # <name>.trace, <name>.network, resources/
```

- **Slug:** lowercase English kebab-case. `/run-tasks` task → `task-<N>-<short-summary>` (e.g. `task-3-items-search`); QA pass → `qa-<goal-summary>`; ad-hoc → `<short-summary>`. The date is the day the folder was created, in DD-MM-YYYY (`currentDate` `2026-09-25` → `25-09-2026`); every other date in this skill uses the same format.
- **Re-run** of the same task (after a fix, in testing mode, on another day) reuses its existing folder: empty `screens/` and `trace/` first, then write the new run; `report.md` describes the latest run and keeps one line per previous run in «Історія прогонів». `findings.md` and `findings/` are never emptied: new findings are appended (see «findings.md»).
- `.project-meta/` is in the user's global gitignore on the host. `.auth/`, `accounts.md` and traces hold live credentials and tokens: never copy them anywhere else and never suggest sharing a trace.

---

## Step 1: Preflight

1. **MCP.** Load the tools with ToolSearch `select:mcp__playwright__browser_navigate,mcp__playwright__browser_snapshot,mcp__playwright__browser_click,mcp__playwright__browser_type,mcp__playwright__browser_fill_form,mcp__playwright__browser_select_option,mcp__playwright__browser_press_key,mcp__playwright__browser_wait_for,mcp__playwright__browser_take_screenshot,mcp__playwright__browser_resize,mcp__playwright__browser_console_messages,mcp__playwright__browser_network_requests,mcp__playwright__browser_start_tracing,mcp__playwright__browser_stop_tracing,mcp__playwright__browser_storage_state,mcp__playwright__browser_set_storage_state,mcp__playwright__browser_handle_dialog,mcp__playwright__browser_close`. If the `playwright` server is missing or failed to connect (typical for a session on the host, outside the dev container), stop: the test did not run — say so in the report, with the reason. Never replace it with "the code looks right".
2. **App URL.** Take the port from the project `CLAUDE.md`, then the `dev` script in `package.json` (`-p`, `--port`), then the framework default (Next 3000, Vite 5173). Check with `curl -s -o /dev/null -w '%{http_code}' http://localhost:<port>`.
3. **Dev server.** If nothing answers, start the project's `dev` script yourself (the package manager comes from the lock file) in its own process group, so it can be stopped completely:
   ```bash
   setsid nohup <pm> run dev > /tmp/dev-<project>.log 2>&1 < /dev/null & echo $! > /tmp/dev-<project>.pid
   ```
   Poll the URL until it answers (up to ~90 s); on timeout read the log and report the blocker. Remember that you started it. A server that was already running is never touched.
4. **Folder.** `mkdir -p .project-meta/qa/<run>/screens .project-meta/qa/<run>/trace`. If `accounts.md` does not exist, create it from the template in «accounts.md» below.

## Step 2: Scenario

The scenario uses the one format shared by `## Testing`, `qa.md` and this skill:

```markdown
Передумови: сторінка, роль / акаунт, потрібні дані.

1. **Назва кроку**: що зробити. Очікується: що має бути видно.
2. ...

Крайні випадки:
- ...
```

- `/run-tasks` and QA pass — take the scenario as given; add the `Test Setup` of the task from `tasks.md` to the prerequisites.
- Ad-hoc — write the scenario first, in this format, into the «Сценарій» section of `report.md`. Every step relies on behaviour you saw in the code; cover the edge cases of the change (empty state on first visit, errors, validation, roles, direct URL), not only the happy path.
- If the scenario itself is wrong (the code follows the requirements, the step does not) — correct the scenario (and the `## Testing` subsection it came from) instead of the code, and name it in the report.

## Step 3: Log In

1. Collect the accounts the scenario needs (by role or by ID from `accounts.md`).
2. For each account: if `.auth/<account-id>.json` exists — `browser_set_storage_state` with it, open a protected page and check that the app did not send you to the login screen. A valid session → use it.
3. Otherwise log in through the UI with the credentials from `accounts.md`. A one-time code, magic link or 2FA you cannot receive → ask the user for it in plain text (open question), with the login it is for. Then save the session: `browser_storage_state` → `.project-meta/qa/.auth/<account-id>.json`.
4. No account for a required role → create it through the app if an available account can do that and the scenario allows it (see «accounts.md»); otherwise ask the user.
5. Switch accounts inside a scenario with `browser_set_storage_state` (it clears the previous session).

Log in before `browser_start_tracing`, so typed passwords do not land in the trace.

## Step 4: Run

1. `browser_start_tracing`.
2. For every step: act through `browser_snapshot` element refs; check the expectation against the snapshot (texts, states, values), not against a guess; then `browser_take_screenshot` with `filename: .project-meta/qa/<run>/screens/NN-<step-slug>.png` (`fullPage: true` when the checked content is below the fold). Numbering is continuous through the whole run.
3. After every scenario: `browser_console_messages` with `level: "error"` and `browser_network_requests` with a filter for the API host — unexpected errors and 4xx/5xx go to the report even if every step passed. Errors that come from code outside the task also go to `findings.md`.
4. **Findings outside the scope.** Anything broken or suspicious you notice along the way that the task did not touch (a bug on a neighbouring page, a broken layout, a wrong text, a failing request of another feature, a pre-existing ❌ from Step 5) goes to `findings.md` right away, before the next step — with a screenshot in `findings/`. Do not fix it and do not skip it.
5. **Visual tasks:** screenshot at the design's viewport and compare with the design material of the task; list every visible difference. Call it a visual comparison, not a pixel diff.
6. **Responsive requirements:** repeat the relevant steps after `browser_resize` (390×844 for mobile, 768×1024 for tablet when the task has it), then restore 1440×900.
7. **Statuses:** ✅ — observed as expected; ❌ — observed differently; ⚠️ — not checked, with the reason (needs an email, a code the user did not send, a third-party service, data the environment lacks). Never mark ✅ what you did not see.
8. `browser_stop_tracing`. Move the files from the paths in its response into `.project-meta/qa/<run>/trace/`: `<name>.trace`, `<name>.network` and the `resources/` folder (`mv -n`). Then `browser_close`.

**Safety on a real backend.** The app talks to a real API. Delete, bulk-change, send invites or emails, pay — only on entities this test created (recorded in `accounts.md`), or after the user's ok via AskUserQuestion. Emails for new accounts only by the template in `accounts.md`.

## Step 5: Failures

For every ❌:

1. Repeat the step once — rule out timing (wait for the element or the request, not a fixed sleep).
2. Find where the problem is born and name the cause: the code under test, a pre-existing bug outside it, the backend, test data, the environment, or a wrong scenario.
3. **Code under test, the fix is clear and inside the task's scope** → fix it, run `format` and `check-errors` (full output), re-run the failed scenario and the scenarios that touch the same code, record the run in «Історія прогонів». After 3 unsuccessful fix attempts for the same failure — stop and ask.
4. **Anything else** (backend, pre-existing bug, unclear expectation, scope change) → ask via AskUserQuestion: what you saw, the cause with evidence, the options (fix now / leave as a known issue / change the expectation). Record the answer where the caller keeps decisions (`Decisions` in `tasks.md` for `/run-tasks`). A cause outside the task's scope (pre-existing bug, backend, environment) also goes to `findings.md` together with the user's answer.
5. **Stop the dev server** you started in Step 1 once the run (with its fixes) is finished: `kill -TERM -- -$(cat /tmp/dev-<project>.pid)`, check that the port no longer answers. In the output say that you stopped it.

---

## accounts.md

The single source of test credentials for the project. The user fills in «Базові»; you append everything the tests create — nothing created during a test may be lost.

```markdown
# Тестові акаунти

Середовище: <URL застосунку і хост API, на якому живуть ці акаунти>
Email для нових акаунтів: <шаблон від юзера, наприклад name+qa-{n}@company.com>

## Базові
| ID | Роль | Логін | Пароль | Вхід | Нотатки |
|----|------|-------|--------|------|---------|

## Створені під час тестів
| ID | Роль | Логін | Пароль | Вхід | Створено | Де і звʼязки | Прогін |
|----|------|-------|--------|------|----------|--------------|--------|

## Створені сутності
| Сутність | Назва / ID | Створено | Ким (ID акаунта) | Прогін |
|----------|------------|----------|------------------|--------|
```

- `ID` — short, unique, lowercase (`admin`, `employee-01`); it names the session file `.auth/<ID>.json` and is how reports refer to the account.
- `Вхід` — `пароль`, `код на пошту`, `magic-link`, `SSO`. Codes and links come from the user at login time.
- **Write immediately.** A created account or entity (company, team, invite) gets its row right after the app confirms the creation — before the next step, so a crashed run loses nothing. Bulk creation (30 users) — one row per account as each one is created.
- **New credentials:** the email by the template in the file header; no template → ask the user once and write the answer into the header. Passwords — `openssl rand -base64 18`, adjusted to the form's validation rules.
- **Never delete rows.** An account or entity removed by a test gets `видалено DD-MM-YYYY` in its notes.
- **Secrets stay here.** Passwords from this file go only into the login form fields. They never appear in `report.md`, the chat, code, comments or commit messages — reports name accounts by `ID`.
- Accounts belong to the environment in the header: if the app now talks to a different API host, say so before using them.

## findings.md

Ukrainian. Every bug or finding outside the task's scope noticed during the run: pre-existing bugs, backend errors, problems of neighbouring features, suspicious behaviour. It is a list for the user to decide on later, not a to-do for you.

- Create it on the first finding of the run; no findings → no file.
- One finding — one entry, written right when you notice it. A finding already in the file is not duplicated: add the run number to its `Прогони`.
- On a re-run keep the old entries. A finding that no longer reproduces gets `не відтворюється в прогоні N`; never delete entries.
- Screenshots go to `findings/NN-<slug>.png` (own numbering), so a re-run that empties `screens/` does not lose them.
- Credentials never appear here — accounts by `ID`.

```markdown
# Знахідки поза скоупом: <назва задачі або флоу>

### 1. <коротка назва> — баг | бекенд | спостереження
Де: `/team` · роль admin · 1440×900
Що видно: <що саме не так, буквально>
Як відтворити: <кроки, якщо відрізняються від сценарію>
Причина: <механізм з file:line | 4xx/5xx з URL і статусом | не встановлено>
Доказ: ![01](findings/01-team-avatar.png)
Рішення юзера: <відповідь з AskUserQuestion | не питав — не впливає на сценарій задачі>
Прогони: 1, 2
```

## report.md

Ukrainian. Steps are written for a reader who does not open the code; UI texts, URLs and role names exactly as in the app.

```markdown
# QA: <назва задачі або флоу>
_Дата: DD-MM-YYYY · Прогін N_

**Результат:** ✅ 7 · ❌ 1 · ⚠️ 2
**Сценарій:** Task 3 з `done/DD-MM-YYYY/items.md` | `done/DD-MM-YYYY/qa.md` | ad-hoc (нижче)
**Середовище:** http://localhost:3000 · API <хост> · 1440×900
**Акаунти:** admin, employee-01

## Сценарій
<лише для ad-hoc: сценарій у спільному форматі>

## Кроки

### 1. Список ✅
Дія: відкрити `/items`.
Очікується: таблиця з 6 колонками.
Фактично: як очікується.
![01](screens/01-items-list.png)

### 2. Пошук ❌
Дія: ввести "abc" у Search.
Очікується: лишаються рядки з "abc".
Фактично: список не змінився, запит без параметра search.
![02](screens/02-search.png)

## Проблеми
- ❌ Крок 2 — причина: <механізм>. Статус: виправлено в прогоні 2 | чекає рішення юзера | відомий баг поза задачею (findings.md, #1)

## Консоль і мережа
- <неочікувані помилки консолі, 4xx/5xx з URL і статусом; "чисто", якщо нічого>

## Перевір сам
- ⚠️ Крок 5 — лист з інвайтом: пошту перевірити не можу.

## Створено під час тесту
- employee-01, employee-02, компанія "QA Company 1" — записано в `accounts.md`

## Історія прогонів
| Прогін | Дата | Результат | Що змінилось |
|--------|------|-----------|--------------|
| 1 | DD-MM-YYYY | ✅ 6 · ❌ 1 | — |
| 2 | DD-MM-YYYY | ✅ 7 | фікс параметра search |

## Трейс
З кореня проєкту на хості: `npx playwright show-trace .project-meta/qa/<run>/trace`
```

Omit empty sections.

## Output to the Caller

Close the skill with a short block in Ukrainian that the caller puts into its final report as is:

```
Браузерний тест: ✅ 7 · ❌ 0 · ⚠️ 2 — .project-meta/qa/<run>/report.md
Виправлено під час тесту: <коротко, або "нічого">
Чекає рішення: <❌, які лишились, або "нічого">
Перевір сам: <⚠️ кроки>
Знахідки поза скоупом: <N — .project-meta/qa/<run>/findings.md, коротко по кожній | "немає">
Створені акаунти: <ID або "нових немає">
Трейс: npx playwright show-trace .project-meta/qa/<run>/trace
Dev-сервер: <запускав і зупинив | вже працював>
```

If the test did not run (no MCP, the dev server did not start, a login the user could not provide) — the block says exactly that, and the caller must not describe the change as tested.

## Rules

1. **Never run on your own initiative** — only from `/run-tasks` or on the user's explicit request.
2. **Observed only** — ✅ means you saw it in the browser; the rest is ❌ or ⚠️ with a reason.
3. **Every created account and entity goes to `accounts.md` right away.**
4. **Credentials never leave `accounts.md` and `.auth/`** — not into reports, the chat, code or traces (log in before tracing).
5. **Destructive or outward-facing actions** only on the test's own entities or with the user's ok.
6. **Fix only the code under test and only when the cause is named**; everything else is a question to the user.
7. **Every finding outside the scope goes to `findings.md` right away** — not fixed, not skipped.
8. **Stop what you started** — the dev server you launched; never touch a server the user runs.
