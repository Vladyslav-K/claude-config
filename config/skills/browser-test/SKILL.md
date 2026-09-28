---
name: browser-test
description: Test finished changes in a real headless Chromium through the Playwright MCP and save the evidence — report.md with steps and screenshots, plus findings.md with every bug or finding outside the task's scope — into .project-meta/qa/<run>/. Logs in with accounts from .project-meta/qa/accounts.md and records every account or entity the test creates there. Called by the QA task of /run-tasks once per plan, covering all done tasks; outside /run-tasks only when the user explicitly asks to test — «протестуй», «перевір у браузері», «прогони тест», «зроби QA». Never run it on your own initiative.
---

# Browser Test

## Additional context
$ARGUMENTS

Arguments from the caller: the scenario source (a `### Task N` subsection, a `qa.md`, or "ad-hoc" with a description of the change), the run slug, and any setup (roles, data) from the plan.

## Purpose

Run a test scenario in the real app, record what actually happened, fix what is clearly broken in the code under test, and hand the user a report they can verify quickly. Only what you observed in the browser counts as passed.

## When It Runs

- **`/run-tasks`** — only in the `QA` task at the end of the plan (scenario = the whole `qa.md`, one pass over every done task). Regular tasks are not run in the browser.
- **Ad-hoc** — only when the user asks to test in the current request ("зроби X і протестуй"). No request → no browser test; the regular completion report tells the user how to check.
- A change with nothing observable in the browser (types, config, tooling, refactor without UI effect) → skip, and write one line with the reason instead of a report.

## Files

```
.project-meta/qa/
├── accounts.md                  # Test accounts and created entities (user + you)
├── .auth/<account-id>.json      # Saved browser sessions, one per account
├── _artifacts/                  # MCP output dir (files saved without an explicit name)
└── DD-MM-YYYY-<slug>/           # One folder per tested task / QA pass / ad-hoc test
    ├── report.md
    ├── findings.md              # Bugs and findings outside the task's scope
    ├── findings/NN-<slug>.png   # Screenshots for findings.md
    └── screens/01-<step>.png
```

- **Slug:** lowercase English kebab-case. QA pass of `/run-tasks` → `qa-<goal-summary>`; ad-hoc → `<short-summary>`. The date is the day the folder was created, in DD-MM-YYYY (`currentDate` `2026-09-25` → `25-09-2026`); every other date in this skill uses the same format.
- **Re-run** of the same QA pass or ad-hoc test (after a fix, in testing mode, on another day) reuses its existing folder: empty `screens/` first, then write the new run; `report.md` describes the latest run and keeps one line per previous run in «Історія прогонів». `findings.md` and `findings/` are never emptied: new findings are appended (see «findings.md»).
- `.project-meta/` is in the user's global gitignore on the host. `.auth/` and `accounts.md` hold live credentials and tokens, and screenshots show real data of the environment: never copy them anywhere else.

---

## Step 1: Preflight

1. **MCP.** Load the tools with ToolSearch `select:mcp__playwright__browser_run_code_unsafe,mcp__playwright__browser_navigate,mcp__playwright__browser_snapshot,mcp__playwright__browser_find,mcp__playwright__browser_click,mcp__playwright__browser_type,mcp__playwright__browser_fill_form,mcp__playwright__browser_select_option,mcp__playwright__browser_press_key,mcp__playwright__browser_wait_for,mcp__playwright__browser_take_screenshot,mcp__playwright__browser_resize,mcp__playwright__browser_console_messages,mcp__playwright__browser_network_requests,mcp__playwright__browser_storage_state,mcp__playwright__browser_set_storage_state,mcp__playwright__browser_handle_dialog,mcp__playwright__browser_close`. If the `playwright` server is missing or failed to connect (typical for a session on the host, outside the dev container), stop: the test did not run — say so in the report, with the reason. Never replace it with "the code looks right".
2. **App URL.** Take the port from the project `CLAUDE.md`, then the `dev` script in `package.json` (`-p`, `--port`), then the framework default (Next 3000, Vite 5173). Check with `curl -s -o /dev/null -w '%{http_code}' http://localhost:<port>`.
3. **Dev server.** If nothing answers, start the project's `dev` script yourself (the package manager comes from the lock file) in its own process group, so it can be stopped completely:
   ```bash
   setsid nohup <pm> run dev > /tmp/dev-<project>.log 2>&1 < /dev/null & echo $! > /tmp/dev-<project>.pid
   ```
   Poll the URL until it answers (up to ~90 s); on timeout read the log and report the blocker. Remember that you started it. A server that was already running is never touched.
4. **Folder.** `mkdir -p .project-meta/qa/<run>/screens`. If `accounts.md` does not exist, create it from the template in «accounts.md» below.
5. **Warm-up.** The dev server compiles a page on its first request, and that time lands on `browser_navigate`. Collect the page paths of the scenario and request them all in one Bash call with `run_in_background: true`, then go on without waiting for it:
   ```bash
   printf '%s\n' /items /items/new /settings | xargs -P 4 -I{} curl -s -o /dev/null --max-time 120 -w '%{http_code} {} %{time_total}s\n' 'http://localhost:<port>{}'
   ```
   Only plain page paths: no query strings, tokens, magic links, API endpoints or any URL whose GET changes data. A dynamic segment (`/items/[id]`) only with an ID the scenario already names.

## Step 2: Scenario

The scenario uses the one format shared by `## Testing`, `qa.md` and this skill:

```markdown
Передумови: сторінка, роль / акаунт, потрібні дані.

1. **Назва кроку**: що зробити. Очікується: що має бути видно.
2. ...

Крайні випадки:
- ...
```

- QA pass of `/run-tasks` — take the scenario as given; add the `Test Setup` of every task the scenario covers (passed by the caller, or from `tasks.md`) to the prerequisites of its scenarios. Scenarios that cover `visual` / `mixed` tasks get the design comparison from Step 4.
- Ad-hoc — write the scenario first, in this format, into the «Сценарій» section of `report.md`. Every step relies on behaviour you saw in the code; cover the edge cases of the change (empty state on first visit, errors, validation, roles, direct URL), not only the happy path.
- If the scenario itself is wrong (the code follows the requirements, the step does not) — correct the scenario (and the `## Testing` subsection it came from) instead of the code, and name it in the report.

## Step 3: Log In

1. Collect the accounts the scenario needs (by role or by ID from `accounts.md`).
2. For each account: if `.auth/<account-id>.json` exists — `browser_set_storage_state` with it, open a protected page and check that the app did not send you to the login screen. A valid session → use it.
3. Otherwise log in through the UI with the credentials from `accounts.md`. A one-time code, magic link or 2FA you cannot receive → ask the user for it in plain text (open question), with the login it is for. Then save the session: `browser_storage_state` → `.project-meta/qa/.auth/<account-id>.json`.
4. No account for a required role → create it through the app if an available account can do that and the scenario allows it (see «accounts.md»); otherwise ask the user.
5. Switch accounts inside a scenario with `browser_set_storage_state` (it clears the previous session).
6. Never take a screenshot of a login form with typed credentials.

## Step 4: Run

Most of the run time is the model's turn after every tool call, so a scenario runs as one Playwright script in one call instead of one call per click. The step-by-step tools are for learning a page before its script and for diagnosing a failure.

1. **Selectors first.** Take roles, labels and texts from the scenario (UI texts are exact) and from the code under test. If that is not enough — one `browser_snapshot` of the page, or `browser_find` for a single element. Prefer `getByRole`, `getByLabel`, `getByText` with the scenario's texts.
2. **One script per scenario** — `browser_run_code_unsafe` with `code`, built on the skeleton below. The script:
   - runs the steps in order; after every step it waits for the page to settle (`settle` in the skeleton: loaders gone, finite animations finished), then saves `screens/NN-<step-slug>.png` by an absolute path (project root + `.project-meta/qa/<run>/screens/`) with `animations: 'disabled'`, and with `fullPage: true` when the checked content is below the fold; the numbering is continuous through the whole run;
   - before the first script, looks up the project's own loader, spinner and skeleton components in its code and adds their selectors to `loaders`; an element that is not a loader but matches `loaders` (it stays in `pending` on a finished page) is excluded from the selector, otherwise every step waits 10 s for it;
   - returns for every step what it actually saw: URL, the checked texts, counts, field values, visible / disabled states, and `pending` — what was still loading or animating when `settle` gave up;
   - collects console errors and responses with status ≥ 400 through `page.on` and returns them;
   - stops at the first failed step and returns its error and a `-fail` screenshot, because later steps depend on it; independent checks (a list of pages or roles) go on after a failure;
   - fits in about a minute: every wait has an explicit timeout of up to 10 s, navigation up to 30 s; a longer scenario is split into several scripts by its steps. A call that runs over 120 s is moved to the background by Claude Code — do not touch the browser until its notification arrives;
   - never contains passwords or tokens — the session comes from Step 3; a native `confirm` / `alert` is handled with `page.once('dialog', (d) => d.accept())` before the action that opens it.
3. **Statuses from the result.** Compare every step's actual values with «Очікується»: ✅ / ❌ come from this comparison, not from the script finishing without an error. A step the script did not reach is not ✅. A step with a non-empty `pending` is not ✅ until a re-take shows the finished state.
4. **Screenshot review.** After every script, open every screenshot it saved with `Read` before giving any status: the returned values alone are not evidence. A step is ✅ only when both its values and its screenshot match «Очікується». A screenshot with a loader or skeleton, a half-transparent modal or overlay, an empty block where content is expected, or a state that differs from the returned values was taken too early: find the signal the step missed (wait for the content itself, add the loader to `loaders`), fix the script and re-take the step. The same picture after the fix means the app never finishes → ❌ with the cause. Screenshots from the interactive tools are reviewed the same way.
5. **Script error or ❌.** Take `browser_snapshot` of the current state and continue this scenario step by step with the interactive tools (`browser_click`, `browser_fill_form`, …, `browser_take_screenshot` into the same numbering), then go to Step 5. A wrong selector is a script bug, not an app ❌: fix the selector and re-run the script from the failed step.
6. **No fixed waits.** Never `browser_wait_for` with `time`, never `page.waitForTimeout` or polling loops with sleeps. Playwright actions already wait for their element. Wait for a concrete signal: `browser_wait_for` with `text` / `textGone`; in scripts `locator.waitFor()`, `page.waitForURL()`, `page.waitForResponse()`. Wait for the content the step checks, not for its container: a dialog, a section or a page shell appears before its data, and Playwright counts an element with `opacity: 0` as visible, so a wait for a dialog resolves on the first frame of its fade-in.
7. **Console and network.** The errors the script returned, plus, for steps done with the interactive tools, `browser_console_messages` with `level: "error"` and `browser_network_requests` for the API host. Unexpected errors and 4xx/5xx go to the report even if every step passed; errors that come from code outside the task also go to `findings.md`.
8. **Findings outside the scope.** Anything broken or suspicious you notice along the way that the task did not touch (a bug on a neighbouring page, a broken layout, a wrong text, a failing request of another feature, a pre-existing ❌ from Step 5) goes to `findings.md` right away, before the next step — with a screenshot in `findings/`. Do not fix it and do not skip it.
9. **Visual tasks:** screenshot at the design's viewport, open it with `Read` and compare with the design material of the task; list every visible difference. Call it a visual comparison, not a pixel diff.
10. **Responsive requirements:** repeat the relevant steps at 390×844 for mobile and 768×1024 for tablet when the task has it — `page.setViewportSize()` inside the script or `browser_resize` — then restore 1440×900.
11. **Statuses:** ✅ — observed as expected; ❌ — observed differently; ⚠️ — not checked, with the reason (needs an email, a code the user did not send, a third-party service, data the environment lacks). Never mark ✅ what you did not see.
12. `browser_close` when the run is finished.

Script skeleton — replace the steps and extend `loaders`, keep `settle`, the error collection and the `finally`. A step is `act` (actions and the wait for its content) plus `read` (the values to return); `read` runs after `settle`, so the values and the screenshot show the same state:

```js
async (page) => {
  const dir = '<project root>/.project-meta/qa/<run>/screens';
  const steps = [];
  const errors = [];
  const onConsole = (m) => m.type() === 'error' && errors.push(`console: ${m.text()}`);
  const onResponse = (r) => r.status() >= 400 && errors.push(`${r.status()} ${r.request().method()} ${r.url()}`);
  page.on('console', onConsole);
  page.on('response', onResponse);
  const loaders = page
    .locator(
      '[aria-busy="true"], [role="progressbar"]:not([aria-valuenow]), .animate-spin, [data-slot="skeleton"], [class*="skeleton" i], [class*="spinner" i], [class*="loader" i]',
    )
    .filter({ visible: true });
  // Infinite animations (spinners, pulsing dots) never finish, so only finite ones are awaited.
  const animationsDone = () =>
    document
      .getAnimations()
      .every((a) => a.playState !== 'running' || a.effect?.getComputedTiming().iterations === Infinity);
  // UI libraries often start an enter transition one or two frames after mount.
  const nextFrames = () =>
    page.evaluate(() => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r))));
  const settle = async () => {
    const pending = [];
    await nextFrames();
    const loaded = await loaders
      .first()
      .waitFor({ state: 'hidden', timeout: 10000 })
      .then(() => true, () => false);
    if (!loaded) {
      pending.push(
        ...(await loaders.evaluateAll((els) =>
          els.map((e) => `loader <${e.tagName.toLowerCase()} class="${e.getAttribute('class') ?? ''}">`),
        )),
      );
    }
    await nextFrames();
    const animated = await page
      .waitForFunction(animationsDone, null, { timeout: 5000 })
      .then(() => true, () => false);
    if (!animated) pending.push('finite animations still running');
    return pending;
  };
  let current = { n: 0, slug: '' };
  const shot = (name) =>
    page.screenshot({ path: `${dir}/${String(current.n).padStart(2, '0')}-${name}.png`, animations: 'disabled' });
  const step = async (n, slug, act, read) => {
    current = { n, slug };
    await act();
    const pending = await settle();
    const actual = await read();
    await shot(slug);
    steps.push({ n, url: page.url(), actual, pending });
  };
  try {
    await step(
      1,
      'items-list',
      async () => {
        await page.goto('http://localhost:3000/items', { timeout: 30000 });
        await page.getByRole('row').nth(1).waitFor({ timeout: 10000 });
      },
      async () => ({ columns: await page.locator('thead th').allInnerTexts() }),
    );
    await step(
      2,
      'search',
      async () => {
        const response = page.waitForResponse((r) => r.url().includes('search=abc'), { timeout: 10000 });
        await page.getByPlaceholder('Search').fill('abc');
        await response;
      },
      async () => ({ rows: await page.getByRole('row').allInnerTexts() }),
    );
  } catch (e) {
    await shot(`${current.slug}-fail`).catch(() => {});
    steps.push({ n: current.n, url: page.url(), error: e.message.split('\n')[0] });
  } finally {
    page.off('console', onConsole);
    page.off('response', onResponse);
  }
  return { steps, errors };
}
```

A re-run of a scenario (after a fix, in Step 5) is the same script again, one call.

**Safety on a real backend.** The app talks to a real API. Delete, bulk-change, send invites or emails, pay — only on entities this test created (recorded in `accounts.md`), or after the user's ok via AskUserQuestion. Emails for new accounts only by the template in `accounts.md`. Scripts follow the same rule.

## Step 5: Failures

For every ❌:

1. Repeat the step once — rule out timing (wait for the element or the request, not a fixed sleep).
2. Find where the problem is born and name the cause: the code under test, a pre-existing bug outside it, the backend, test data, the environment, or a wrong scenario.
3. **Code under test, the fix is clear and inside the task's scope** → fix it, run `format` and `check-errors` (full output), re-run the scripts of the failed scenario and of the scenarios that touch the same code, record the run in «Історія прогонів». After 3 unsuccessful fix attempts for the same failure — stop and ask.
4. **Anything else** (backend, pre-existing bug, unclear expectation, scope change) → ask via AskUserQuestion: what you saw, the cause with evidence, the options (fix now / leave as a known issue / change the expectation). Record the answer where the caller keeps decisions (for `/run-tasks` — `Decisions` of the broken task in `tasks.md`). A cause outside the task's scope (pre-existing bug, backend, environment) also goes to `findings.md` together with the user's answer.
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
**Сценарій:** `done/DD-MM-YYYY/qa.md` | ad-hoc (нижче)
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
Dev-сервер: <запускав і зупинив | вже працював>
```

If the test did not run (no MCP, the dev server did not start, a login the user could not provide) — the block says exactly that, and the caller must not describe the change as tested.

## Rules

1. **Never run on your own initiative** — only from `/run-tasks` or on the user's explicit request.
2. **Observed only** — ✅ means you saw it in the browser: a snapshot or the values a script returned, and the step's screenshot opened with `Read`; the rest is ❌ or ⚠️ with a reason.
3. **Every created account and entity goes to `accounts.md` right away.**
4. **Credentials never leave `accounts.md` and `.auth/`** — not into reports, the chat, code or screenshots.
5. **Destructive or outward-facing actions** only on the test's own entities or with the user's ok.
6. **Fix only the code under test and only when the cause is named**; everything else is a question to the user.
7. **Every finding outside the scope goes to `findings.md` right away** — not fixed, not skipped.
8. **Stop what you started** — the dev server you launched; never touch a server the user runs.
9. **One script per scenario, no fixed waits** — the step-by-step tools only to learn a page or to diagnose a failure.
