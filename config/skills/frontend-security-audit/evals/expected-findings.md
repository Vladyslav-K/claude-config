# Scanner regression expectations

Run `node ../scripts/scan.mjs .` from `evals/fixture/` after any change to the scanner's
patterns. The fixture is a deliberately-vulnerable mini-project; every file is planted.
This document is the oracle: what the scan **must** report, what it **must not**, and which
candidates are decoys that only triage (not the scanner) is expected to clear.

The scan must be **stable across re-runs** — running it twice yields identical counts.
(It excludes its own `.security-audit/` output; a second run that grows is the regression
this fixture exists to catch.)

## Expected candidate counts (36 total)

| category | count | notes |
|---|---|---|
| open-redirect | 4 | one real (`?next=`, `dynamic`); decoys: `/home` (`literal`), ternary-of-literals (`literal`), bare `pathname` (`template`) |
| secrets-hardcoded | 3 | `sk_live_…`, `sk-proj-…`, plus the `apiKey: 'department'` decoy (tagged `likelyFalsePositive`) |
| server-injection | 3 | all `serverHint: true` |
| dom-xss-source | 3 | `document.cookie`, `location.hash`, `decodeURIComponent` |
| secrets-env-public | 2 | real Stripe secret + Turnstile site-key decoy |
| xss-dangerous-html | 2 | `dangerouslySetInnerHTML` **and** Svelte `{@html}` |
| token-storage | 2 | literal key `'auth_token'` **and** identifier key `ACCESS_TOKEN_KEY` |
| postmessage-cors | 2 | `postMessage(…, '*')` + `onmessage` without origin check |
| ssrf | 2 | `fetch(target)`, `new URL(req.url)`; all `serverHint: true` |
| config-unsafe | 2 | `ignoreBuildErrors` **and** multi-line `hostname: '**'` |
| tabnabbing | 2 | `target="_blank"`, `window.open` |
| cookie-clientside | 2 | js-cookie `Cookies.set` **and** `document.cookie =` |
| graphql-server | 2 | `new ApolloServer` + `introspection: true` |
| xss-code-exec | 1 | `eval` only — callback timers excluded |
| prototype-pollution | 1 | unguarded `deepMerge` |
| xss-url-protocol | 1 | `javascript:void(0)` decoy |
| redos | 1 | the `/^([a-z0-9]+)+@…/` regex only |
| headers-missing | 1 | project check: fixture `next.config.js` has no `headers()` and no middleware |

`env-tracked` must be **absent**: the fixture is deliberately not a git repository, so the
check skips silently. In a real repo with a tracked `.env*` file it emits one `low` finding
per file (`.env.example`/`.sample`/`.template` excluded).

## Regression guards (the bugs these patterns were added to catch)

- **No self-ingestion.** Two consecutive runs report 36 both times. If the second run is
  larger, `.security-audit/` is being scanned again.
- **`redos` = 1, not 3.** The plain arithmetic in `src/merge.js` `scale()`
  (`(i + 1) * 2`, `(factor + 1) * doubled`) must **not** be flagged — only the regex literal.
- **`actions.ts` has `serverHint: true`** via its `'use server'` directive, even though its
  path (`app/actions.ts`) contains no `/api/` or `route.` segment. A Redux-style
  `store/actions/` path must **not** get `serverHint` from the path alone.
- **`xss-code-exec` = 1.** Callback-form `setTimeout(fn, …)` / `setTimeout(() => …, …)` in
  `src/decoys.ts` must **not** appear; only string-eval does.
- **`config-unsafe` catches the wildcard hostname** on its own line — the multi-line
  `remotePatterns` object would otherwise hide it from a single-line span.
- **`cookie-clientside` = 2** — the js-cookie `Cookies.set('session_token', …)` wrapper is
  caught, not just the raw `document.cookie =`.
- **`token-storage` catches the identifier-key call** — `localStorage.setItem(ACCESS_TOKEN_KEY, …)`
  in `src/token-store.ts`, where the token-ish word lives only in the constant's **name**.
  This was a real-world miss: a whole auth token layer slipped past the literal-key patterns.
- **`argKind` classification** (open-redirect breakdown must read `[1 dynamic, 1 template, 2 literal]`):
  a ternary of two plain string literals (`isAdmin ? '/admin' : '/profile'`) → `literal`;
  bare `pathname` → `template`; `params.get('next') ?? '/'` stays `dynamic`.
- **`likelyFalsePositive` tagging:** the `apiKey: 'department'` decoy carries the tag
  (low-entropy plain-word value); `sk_live_…` and `sk-proj-…` must **not** carry it.
  The console summary shows `[1 likely-FP: low-entropy]` on secrets-hardcoded.
- **`alsoIn` cross-references:** `src/cookies.js` line 6 (`document.cookie =`) appears in both
  `dom-xss-source` and `cookie-clientside` — each entry must point at the other. Same for the
  `.env` Stripe line shared by `secrets-hardcoded` and `secrets-env-public`.
- **`headers-missing` = 1** — emitted from reading the fixture's `next.config.js`, not from
  an rg pattern. If a `headers(` / `headers:` token is added to the config, it must disappear.

## Decoys — scanner flags them, triage must clear them

These are intentional false positives. They prove the catalog's "False positives" guidance
is exercised; the scanner is *supposed* to surface them, and a human/LLM triage clears them:

- `secrets-hardcoded` → `apiKey: 'department'` is a data field name (catalog §6); the scanner
  pre-tags it `likelyFalsePositive`, triage confirms with a glance.
- `secrets-env-public` → `NEXT_PUBLIC_TURNSTILE_SITE_KEY` is a public site key by design (§5).
- `open-redirect` → `router.push('/home')`, the ternary-of-literals, and bare `pathname` are
  static/internal destinations (§9) — pre-sorted away from `dynamic` by `argKind`.
- `xss-url-protocol` → `href="javascript:void(0)"` is a static no-op, not user-controlled (§3).
