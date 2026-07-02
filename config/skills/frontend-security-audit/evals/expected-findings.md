# Scanner regression expectations

Run `node ../scripts/scan.mjs .` from `evals/fixture/` after any change to the scanner's
patterns. The fixture is a deliberately-vulnerable mini-project; every file is planted.
This document is the oracle: what the scan **must** report, what it **must not**, and which
candidates are decoys that only triage (not the scanner) is expected to clear.

The scan must be **stable across re-runs** — running it twice yields identical counts
(46 candidates in 15 scanned files both times). It excludes its own `.security-audit/`
output; a second run that grows is the regression this fixture exists to catch.

## Expected candidate counts (46 total)

| category | count | notes |
|---|---|---|
| open-redirect | 9 | real: `?next=` router.push, `navigate(params.get(…))`, `history.push(target)`, `document.location =` (all `dynamic`); decoys: `/home`, ternary-of-literals, object-form `{ pathname: '/checkout' }`, `navigate('/dashboard')` (all `literal`), bare `pathname` (`template`) |
| xss-dangerous-html | 6 | `dangerouslySetInnerHTML` raw + sanitized decoy (tagged `likelySanitized`) + `.mdx` copy, `srcDoc`, Svelte `{@html}`, Angular `bypassSecurityTrustHtml` |
| secrets-hardcoded | 3 | `sk_live_…`, `sk-proj-…`, plus the `apiKey: 'department'` decoy (tagged `likelyFalsePositive`) |
| server-injection | 3 | all `serverHint: true` |
| dom-xss-source | 3 | `document.cookie`, `location.hash`, `decodeURIComponent` |
| secrets-env-public | 2 | real Stripe secret + Turnstile site-key decoy |
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
| sdk-browser-key | 1 | `dangerouslyAllowBrowser: true` in `src/llm-client.ts` |
| headers-missing | 1 | project check: fixture `next.config.js` has no `headers()` and no middleware |

`env-tracked` must be **absent**: the fixture is deliberately not a git repository, so the
check skips silently. In a real repo with a tracked `.env*` file it emits one `low` finding
per file (`.env.example`/`.sample`/`.template` excluded).

## Regression guards (the bugs these patterns were added to catch)

- **No self-ingestion.** Two consecutive runs report 46 both times. If the second run is
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
- **react-router / bare-document sinks are caught** — `src/navigation.ts` plants
  `navigate(params.get('redirect'))`, `history.push(target)` and `document.location = url`;
  all three must appear in `open-redirect` **with** `argKind: 'dynamic'` (the classifier
  recognizes the new sinks, they're not left untagged).
- **`argKind` classification** (open-redirect breakdown must read `[4 dynamic, 1 template, 4 literal]`):
  a ternary of two plain string literals (`isAdmin ? '/admin' : '/profile'`) → `literal`;
  bare `pathname` → `template`; `params.get('next') ?? '/'` stays `dynamic`; the object form
  `router.push({ pathname: '/checkout', query: { step } })` → `literal` (destination is the
  literal pathname; query params are URL-encoded); `navigate('/dashboard')` → `literal`.
- **`xss-dangerous-html` new sinks:** `srcDoc={html}` in `app/page.tsx` and
  `bypassSecurityTrustHtml` in `src/legacy-widget.ts` each yield exactly one finding.
- **`.mdx` files are scanned** — `content/embed.mdx`'s `dangerouslySetInnerHTML` must appear;
  if it's missing, the mdx glob regressed.
- **`likelySanitized` tagging:** the `DOMPurify.sanitize(html)` line in `app/page.tsx`
  carries the tag; the raw `{{ __html: html }}` line directly above it must **not**.
  The console summary shows `[1 likely-sanitized]` on xss-dangerous-html.
- **Comments must not trip patterns.** Fixture comments are worded to avoid matchable
  text (e.g. "useNavigate sink", not the call form with a paren; "DomSanitizer bypass",
  not the method name). A count bump after editing comments usually means the comment
  itself matched — grep can't tell code from comments, by design.
- **`likelyFalsePositive` tagging:** the `apiKey: 'department'` decoy carries the tag
  (low-entropy plain-word value); `sk_live_…` and `sk-proj-…` must **not** carry it.
  The console summary shows `[1 likely-FP: low-entropy]` on secrets-hardcoded.
- **`alsoIn` cross-references:** `src/cookies.js` line 6 (`document.cookie =`) appears in both
  `dom-xss-source` and `cookie-clientside` — each entry must point at the other. Same for the
  `.env` Stripe line shared by `secrets-hardcoded` and `secrets-env-public`.
- **`headers-missing` = 1** — emitted from reading the fixture's `next.config.js`, not from
  an rg pattern. If a `headers(` / `headers:` token is added to the config, it must disappear.
- **`totals.filesScanned` = 15** and the console prints `46 in 15 scanned files` — the file
  counter runs over the same include/exclude globs as the categories.

## Decoys — scanner flags them, triage must clear them

These are intentional false positives. They prove the catalog's "False positives" guidance
is exercised; the scanner is *supposed* to surface them, and a human/LLM triage clears them:

- `secrets-hardcoded` → `apiKey: 'department'` is a data field name (catalog §6); the scanner
  pre-tags it `likelyFalsePositive`, triage confirms with a glance.
- `secrets-env-public` → `NEXT_PUBLIC_TURNSTILE_SITE_KEY` is a public site key by design (§5).
- `open-redirect` → `router.push('/home')`, the ternary-of-literals, the object-form
  `{ pathname: '/checkout' }`, `navigate('/dashboard')`, and bare `pathname` are
  static/internal destinations (§9) — pre-sorted away from `dynamic` by `argKind`.
- `xss-dangerous-html` → the `DOMPurify.sanitize(html)` render in `app/page.tsx` is sanitized
  at the point of insertion (§1) — pre-tagged `likelySanitized`, triage confirms the call
  actually wraps the sink value.
- `xss-url-protocol` → `href="javascript:void(0)"` is a static no-op, not user-controlled (§3).
