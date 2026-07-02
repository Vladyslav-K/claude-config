---
name: frontend-security-audit
description: >-
  Full-project frontend security audit and remediation. Scans an ENTIRE codebase
  (not just new/changed code) for client-side and Next.js server-surface
  vulnerabilities — XSS, DOM-XSS, leaked secrets / NEXT_PUBLIC_ keys, insecure
  token storage, open redirects, reverse tabnabbing, postMessage/CORS flaws,
  prototype pollution, ReDoS, server-side injection/SSRF in route handlers and
  server actions, unsafe Next.js config, missing CSP/security headers, and
  vulnerable dependencies. Built to scale to large/bloated codebases (100k+ LOC)
  via a deterministic grep-first scanner plus triage. Use this whenever the user
  wants to "audit", "security-check", "harden", "find vulnerabilities in", "scan
  for XSS / leaked secrets", "make secure", or "pentest" a frontend project, app,
  or repo as a whole — or asks "is my app/frontend secure?", "can hackers attack
  this?", "check the whole project for security issues". Trigger even when the
  user names a single class (e.g. "check for XSS everywhere") but means the whole
  project. NOT for reviewing one specific new diff/PR (use a code review for
  that) and NOT for backend-only services with no frontend.
---

# Frontend Security Audit

Audit a whole frontend codebase for vulnerabilities and remediate them, at any
size. The hard problem is **scale**: you can't read 100k+ lines into context. The
solution is a pipeline that spends cheap deterministic compute to narrow the
search space, and spends model judgment only where it pays off.

```
recon → scan (script) → deps+secrets audit → triage → baseline report (stop) → fix (after OK) → verify → separate final report
```

## Operating principles

- **Grep-first, read-narrow.** The bundled scanner finds candidates across the
  entire tree in seconds. You only open files the scanner flagged. Never attempt
  to read the whole codebase.
- **Candidates ≠ vulnerabilities.** Grep over-matches by design. Every candidate
  is triaged against `references/vulnerability-catalog.md` before it counts. On
  real codebases most candidates in noisy categories (open-redirect, dom-xss-source,
  redos) are false positives — clearing them confidently is the job.
- **Report-first (default).** Produce the report and **stop**. Do not change code
  until the user approves. This matches "don't guess when unsure" — a wrong "fix"
  to working security-sensitive code is worse than the finding.
- **The main agent writes every fix.** Subagents are used only for read-only
  triage (see Scaling). No agent writes code.
- **Trace to the source.** A sink is only dangerous if attacker-controlled data
  reaches it. If all inputs are literals/enums/validated data, it's a false positive.

## Phase 0 — Recon & scope

Establish what you're auditing before scanning. Read, don't guess:

1. `package.json` — framework (Next.js/Vite/CRA/Vue/etc.), package manager (lockfile),
   notable libs (axios, lodash, a markdown/HTML renderer, an LLM SDK), and the
   `lint`/`typecheck`/`format`/`check-errors` scripts you'll run in verification.
2. Source roots and what to **exclude**: build output is excluded automatically, but
   ask the user about large **vendored / demo / generated** directories (e.g. a
   handoff-bundle demo folder). Scanning verbatim third-party code produces noise and
   isn't the user's code to fix — confirm before including it.
3. Confirm the server surface in scope. Default for Next.js: **include** route
   handlers (`app/**/route.ts`), server actions (`'use server'`), `middleware.ts`,
   and `next.config.*`. These ship in the frontend repo and carry the highest-impact
   bugs (injection, SSRF, auth). If the user said client-only, skip categories
   `server-injection`/`ssrf` and the server half of `cookie-clientside`.
4. **Monorepo / separate-backend topology.** If a separate backend app sits next to the
   frontend (`apps/api` beside `apps/web`, a NestJS/Express service, any non-Next server),
   that backend is **out of scope** for a *frontend* audit — note it and scan only the web
   app. If **several** frontend apps live in the monorepo (`apps/web` + `apps/admin`),
   confirm with the user which to audit — or scan each with its own findings dump. The consequence: with the real server elsewhere, a client-heavy Next app often has
   **no** route handlers / `middleware.ts` / `'use server'` files, so `server-injection` and
   `ssrf` candidates inside it are all-false-positive (a browser `fetch` is not SSRF). Confirm
   with `find <web> -name 'route.ts' -o -name 'middleware.ts'` plus the scanner's `'use server'`
   set before spending triage budget on server categories.
5. **Read the high-value files during recon, regardless of scanner hits.** Some findings come
   from *configuration and architecture*, not a grep sink: read `next.config.*` (headers/CSP,
   image config, rewrites), the auth/token layer (axios/fetch client, interceptors, where the
   token lives), and `.env*`. Two of the most impactful findings — **missing security headers**
   and **token-in-localStorage** — surface from reading these, not from a candidate line.

## Phase 1 — Run the scanner

```bash
node <skill>/scripts/scan.mjs <source-root> --out .security-audit/findings.json
# exclude vendored/demo dirs the user opted out of (repeatable):
#   --exclude '**/demo/**' --exclude '**/demo-v2/**'
# narrow to one category while iterating:  --only open-redirect
```

It needs `ripgrep` (`rg`). If missing, tell the user to install it
(`brew install ripgrep` / `apt install ripgrep`) — it's the engine that makes this
scale. The script prints a severity summary and writes full findings (file:line +
matched line + which pattern hit + `serverHint`) to the JSON, plus a
`categories/<id>.json` slice per non-empty category — triage from the slices, not
the full JSON, on big result sets.

Scanner behavior worth knowing:

- It deliberately **ignores `.gitignore`** (`--no-ignore-vcs`): a gitignored `.env`
  still feeds `NEXT_PUBLIC_*` into the bundle and gitignored generated code still
  ships. Build artifacts are excluded by built-in globs; exclude project-specific
  generated dirs with `--exclude`.
- Its output quotes vulnerable lines (and any found secrets) **verbatim** — make
  sure `.security-audit/` is gitignored and never committed. If you can't guarantee that
  (the repo must stay untouched, or `.security-audit/` isn't in `.gitignore`), point `--out`
  **outside the repo tree** (a temp dir) so the verbatim dump can never be committed.
  The scanner prints a `[warn]` when the dump lands in a git repo without a covering
  `.gitignore` entry — treat that warning as a hard stop and move the output.
- Two **deterministic project checks** run alongside the grep categories and land in the
  same output: `headers-missing` (a next.config with no `headers()`) and `env-tracked`
  (`.env*` files tracked in git). They cover the auto-checkable slice of catalog §20–§21;
  CSP quality, CSRF, IDOR and the other absence checks remain manual reading.
- **Triage accelerators in the JSON:** `argKind` on open-redirect entries;
  `likelyFalsePositive` on `secrets-hardcoded` entries whose value is a plain low-entropy
  word (`apiKey: 'department'`) — confirm with a glance and clear those in bulk;
  `likelySanitized` on `xss-dangerous-html` entries with a `sanitize*()` call on the same
  line — confirm the call wraps the sink value and is a real sanitizer, then clear; `alsoIn`
  when the same line tripped several categories — triage the line once, not per category.
  `totals.filesScanned` in the JSON feeds the report's "Scanned N files" line.

## Phase 2 — Dependency & secrets-in-git audit

These complement the source scan (see catalog §19–§20):

- **Dependencies:** run the project's audit (`pnpm audit` / `npm audit` / `yarn`). If it
  can't run (offline, private registry), record "audit: not run — <reason>" in the report
  rather than skipping silently.
  Prioritize critical/high in **prod** deps that reach the client bundle, and known
  XSS / prototype-pollution / ReDoS advisories. Judge impact by **where the code runs,
  not which package.json section it sits in** — build tools (`@svgr/webpack`, PostCSS
  plugins) often live in `dependencies`, and a build-time-only advisory that processes
  your own files is low practical impact. Scan `package.json` for typosquatting.
  When a version looks "wrong" (typosquat suspect, or suspiciously newer than you recall),
  **verify it against the registry before flagging** — `npm view <pkg> dist-tags.latest` and
  `npm view <pkg>@<ver> version`. Your memory of "the latest version" is frozen at the model's
  training cutoff; the registry is the source of truth, and a real, current release is not a
  finding. Only a version the registry lacks (or a name that isn't the real package) is one.
- **Secrets in git:** the scanner pre-emits tracked env files as `env-tracked` findings
  (git repos only). On top of that: read `.gitignore`, and if the source scan found a
  real secret, check whether it was ever committed with `git log -S` — and what the
  tracked env files contained **historically** (`git show <commit>:<file>`), not just now.

## Phase 3 — Triage

Read `references/vulnerability-catalog.md` once — it has, per category: how to confirm
a true positive, the common false positives, and the fix. Then go category by category
through `findings.json`:

- Start with **critical/high**, and within a category prefer entries with
  `serverHint: true` for the server categories.
- Let the scanner pre-sort the noisy navigation category: `open-redirect` candidates carry an
  `argKind` (`dynamic`/`template`/`literal`) and the summary prints the breakdown. Review the
  **`dynamic`** entries (and any untagged multi-line calls) first; constant and
  template-internal-route destinations are the bulk and almost always false positives. The same
  literal-vs-variable reasoning clears most `ssrf` and `dom-xss-source` noise by hand.
- For each candidate, decide **true positive / false positive / needs-human** using
  the catalog. Use the matched line first; open the file only when you need the
  data-flow context (trace the value to its source).
- Record a verdict + reason for every candidate you classify. False positives get a
  one-line reason (e.g. "`apiKey: 'department'` is a data field name, not a secret";
  "`NEXT_PUBLIC_TURNSTILE_SITE_KEY` is a public site key by design").
- Some issues are about **absence** and won't appear as grep findings — the scanner
  auto-emits two of them (`headers-missing`, `env-tracked`); check the rest of catalog §21
  (CSP **quality**, CSRF on cookie-auth route handlers, client-only auth guards / IDOR,
  dynamic `href`/`src` URL bindings, tokens in URLs, mixed content, `Math.random()` for
  tokens, missing SRI on CDN scripts, prod source maps) by reading the relevant files.
- **Think in chains, not just per-category.** A finding's severity isn't only its isolated
  category: a token in `localStorage` (a "needs-human" item) **plus** any XSS = token
  exfiltration → account takeover. When a low/medium finding amplifies a high one, say so and
  rate the combined impact.

## Phase 4 — Baseline report, then stop

Write a human-readable report (default path:
`.project-meta/files/security-audit-<date>-initial.md` if that directory exists, else
`.security-audit/report-initial.md`) and present a summary in chat. **Do not modify code yet.**

This is the **baseline report**: it captures the state *before* any fix. Once written,
**never edit or overwrite it** — not during the fix phase, not for the final report. The
user relies on it as the permanent pre-fix record of what was wrong. The Phase 7 final
report is always a **separate file** (see below); the two reports must coexist.

The report (and the chat summary) must **open with an at-a-glance severity table** —
confirmed counts per severity at the very top, before any prose, so the reader answers
"how bad is it?" in one glance. Detail comes after. Use this structure:

```markdown
# Frontend Security Audit — <project> — <date>

## At a glance

| Severity  | Confirmed |
| --------- | --------- |
| Critical  | <n>       |
| High      | <n>       |
| Medium    | <n>       |
| Low       | <n>       |
| Info      | <n>       |
| **Total** | **<n>**   |

Scanned <N files — from the scanner's totals.filesScanned> — <M> candidates → <K> confirmed,
<F> false positives, <H> need a human decision.

## Confirmed vulnerabilities
### [SEVERITY] <title> — <category>
- **Location:** `path:line` (+ others)
- **Why it's exploitable:** <attacker-controlled source → sink, concrete impact>
- **Fix:** <planned change, per catalog>
- **Risk if unfixed:** <impact>

## Needs a human decision (architectural / backend-dependent)
<token-storage migration, access-control/IDOR, breaking dep upgrades — explain the trade-off>

## Cleared (notable false positives)
<the scary-looking candidates that are safe, with the one-line reason>

## Dependencies
<audit results + recommended upgrades>
```

Then ask the user how to proceed: fix all confirmed, fix a subset, or hold. Present the
"needs a human decision" items as explicit choices — don't decide auth architecture for them.

## Phase 5 — Fix (only after approval)

Apply fixes the user approved, **one category at a time**, following the catalog's
remediation guidance. The main agent writes all edits.

- Prefer the minimal, idiomatic fix that matches the surrounding code (add
  `rel="noopener noreferrer"`, wrap with `DOMPurify.sanitize`, allow-list a redirect,
  block `__proto__` in a merge, add a `message`-listener origin check, scope a target
  origin, parameterize a query).
- **Do not** silently perform architectural rewrites (moving tokens to httpOnly
  cookies, changing the auth model, major dep major-version bumps). Those are the
  "needs a human decision" items — implement only the option the user chose.
- If a "fix" would change product behavior or you're unsure it's a true positive,
  stop and ask rather than guess.

## Phase 6 — Verify

After fixing, prove you didn't break anything and that findings are resolved:

1. Run the project's own checks (from Phase 0): `format`, then `check-errors`
   (lint + typecheck) — or the closest equivalents. Fix anything the checks surface.
   Do not truncate their output.
2. Re-run the scanner (`scan.mjs`) and confirm the fixed candidates are gone and no
   new ones appeared.
3. Do **not** run `dev`/`build` unless the user asks.

## Phase 7 — Final report (a new, separate file)

Write the final report to a **new file, separate from the Phase 4 baseline** — never edit
or overwrite the baseline. Default path:
`.project-meta/files/security-audit-<date>-final.md` if that directory exists, else
`.security-audit/report-final.md`. If a file with that name already exists, add a counter
(`-final-2.md`) rather than overwriting. The end state is two files side by side: the
baseline (`-initial`, pre-fix) and this final report (`-final`, post-fix).

Summarize: what was fixed (with file:line), what still needs a human decision and why,
residual risk, and recommended follow-ups (e.g. add a CSP, rotate an exposed key). Be
honest about what wasn't done. Open with the same at-a-glance severity table as Phase 4,
updated with a "Fixed" column. Finally, clean up after yourself: delete the scanner dump
(or say exactly where it lives) — `findings.json` quotes vulnerable lines and any found
secrets verbatim and shouldn't outlive the audit unnoticed.

## Scaling to large codebases

The scanner already handles any size (one `rg` pass, seconds on 200k+ LOC). The part
that grows is **triage**. For a big result set:

- Triage by severity and stop-loss: clear critical/high first; sample noisy
  medium categories before grinding every entry.
- **Optional read-only Explore fan-out:** spawn one `Explore` subagent per noisy
  category (or per directory) to classify its candidates against the catalog and
  return a structured verdict list (`file:line`, verdict, reason). This parallelizes
  the reading. **Explore agents only read and report — they never write fixes.** The
  main agent consolidates verdicts and performs all edits in Phase 5.
- Give each Explore agent the catalog section for its category and the path to its
  `categories/<id>.json` slice so it doesn't re-scan or read the full findings file.

## Files

- `scripts/scan.mjs` — the grep-first candidate scanner. Run it; read its JSON output.
- `references/vulnerability-catalog.md` — per-category confirm / false-positive / fix
  guidance (and §19–§21 for deps, git secrets, and absence-checks). Read before triage.
- `evals/fixture/` — intentionally-vulnerable mini-project with planted findings and
  decoys; `evals/expected-findings.md` lists what a scan of it must (and must not)
  report. Re-run it after any change to the scanner's patterns.
