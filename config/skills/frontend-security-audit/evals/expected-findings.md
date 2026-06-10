# Scanner regression expectations

Run `node ../scripts/scan.mjs .` from `evals/fixture/` after any change to the scanner's
patterns. The fixture is a deliberately-vulnerable mini-project; every file is planted.
This document is the oracle: what the scan **must** report, what it **must not**, and which
candidates are decoys that only triage (not the scanner) is expected to clear.

The scan must be **stable across re-runs** — running it twice yields identical counts.
(It excludes its own `.security-audit/` output; a second run that grows is the regression
this fixture exists to catch.)

## Expected candidate counts (32 total)

| category | count | notes |
|---|---|---|
| secrets-hardcoded | 3 | `sk_live_…`, `sk-proj-…`, plus the `apiKey: 'department'` decoy |
| server-injection | 3 | all `serverHint: true` |
| dom-xss-source | 3 | `document.cookie`, `location.hash`, `decodeURIComponent` |
| secrets-env-public | 2 | real Stripe secret + Turnstile site-key decoy |
| xss-dangerous-html | 2 | `dangerouslySetInnerHTML` **and** Svelte `{@html}` |
| open-redirect | 2 | one real (`?next=`), one decoy (`/home`) |
| postmessage-cors | 2 | `postMessage(…, '*')` + `onmessage` without origin check |
| ssrf | 2 | `fetch(target)`, `new URL(req.url)`; all `serverHint: true` |
| config-unsafe | 2 | `ignoreBuildErrors` **and** multi-line `hostname: '**'` |
| tabnabbing | 2 | `target="_blank"`, `window.open` |
| cookie-clientside | 2 | js-cookie `Cookies.set` **and** `document.cookie =` |
| graphql-server | 2 | `new ApolloServer` + `introspection: true` |
| xss-code-exec | 1 | `eval` only — callback timers excluded |
| token-storage | 1 | `localStorage.setItem('auth_token', …)` |
| prototype-pollution | 1 | unguarded `deepMerge` |
| xss-url-protocol | 1 | `javascript:void(0)` decoy |
| redos | 1 | the `/^([a-z0-9]+)+@…/` regex only |

## Regression guards (the bugs these patterns were added to catch)

- **No self-ingestion.** Two consecutive runs report 32 both times. If the second run is
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

## Decoys — scanner flags them, triage must clear them

These are intentional false positives. They prove the catalog's "False positives" guidance
is exercised; the scanner is *supposed* to surface them, and a human/LLM triage clears them:

- `secrets-hardcoded` → `apiKey: 'department'` is a data field name (catalog §6).
- `secrets-env-public` → `NEXT_PUBLIC_TURNSTILE_SITE_KEY` is a public site key by design (§5).
- `open-redirect` → `router.push('/home')` is a static internal path (§9).
- `xss-url-protocol` → `href="javascript:void(0)"` is a static no-op, not user-controlled (§3).
