---
name: handoff-bundle-port
description: Port self-contained HTML handoff bundles into native React pages. Use when a client or designer delivers a folder of standalone HTML files where each file is a base64-packed React+CSS+fonts bundle with an inline bundler script (typically rendered today inside an iframe), and the deliverable is native Next.js App Router pages with isolated styles, scoped CSS, shared component kits extracted into TSX modules, and rewritten internal links. Triggers on phrases like "port handoff bundle", "convert iframe demo to React", "extract this design HTML into pages", "rebuild demo as React", "the client sent HTML mockups and I need them as real pages", "design files are self-contained HTML — port them", or "we have demo HTML, make them real routes".
---

# Skill: Port a self-contained HTML handoff bundle into native React pages

**Origin:** distilled from a session that ported 41 handoff HTML bundles (~60 MB) into 41 native Next.js pages with shared component kits, isolated CSS scope, and full SSR safety.

## When to use this skill

**YES — use this when:**
- The user shows you a folder of HTML files where each file is ~1 MB+ and looks base64-encoded inside
- Each HTML has a `<script type="__bundler/template">` block and a `<script type="__bundler/manifest">` block
- Each HTML self-contains React + CSS + fonts (no external assets) and unpacks at runtime via an inline bundler script
- The deliverable is "make these into real React pages instead of iframes"

**NO — skip this when:**
- The user delivers Figma + design tokens (no working HTML) — that's "design implementation", not a port
- The HTML files reference external `.css`/`.js`/font URLs (not self-contained) — that's a static-site copy, not a bundle port
- The user wants to keep the iframe wrapper around the HTML — no port needed

## Mental model

The handoff bundle is **not** a black box. Inside each `.html` file, despite the base64-shuffled appearance, lies:

1. Plain JSX/JS in a `<script type="text/babel">` block — the page's `App` component + its data
2. CSS in `<style>` tags — in two layers: the **shared design system** (tokens, typography, resets, common component classes), duplicated into every page, **plus per-page rules** unique to that page (its modal, form, special layout, its own `@keyframes`). Both must survive the port; the per-page layer is the one easily lost (see Pattern 10)
3. Cross-page shared components in additional `<script type="text/babel" src="UUID">` blocks. Sources live in `__bundler/manifest` as base64-gzip-encoded blobs
4. Fonts (woff2) and images (PNG/SVG) in the same manifest, also base64-encoded

Your job: extract those layers, drop the iframe runtime, wire them up as native React.

**You are not designing anything — you are unpacking and re-stitching.**

Two non-negotiable principles:

1. **Isolation.** Demo CSS and components live in a wrapper class (`.demo-app` or similar) that does not leak into the rest of the app. Production code never imports from demo.
2. **Verbatim port.** The handoff bundle is the canonical source. Do not refactor, "improve", or simplify any JSX during the port. The first deliverable is a 1:1 reproduction. Cleanup is a separate concern.

## Step 1 — Locate this skill and the bundle

This skill ships scripts under `scripts/` alongside this `SKILL.md`. The skill itself may live in any of:

- `~/.claude/skills/handoff-bundle-port/` — user-global skill folder
- `<plugin-dir>/skills/handoff-bundle-port/` — installed as part of a plugin
- Anywhere inside the current project (e.g. when iterating on the skill itself)

**Resolve `SKILL_DIR` at the start of the session** — it's the directory that contains this `SKILL.md`. All script invocations below use `${SKILL_DIR}/scripts/<name>.py`. Don't hardcode it.

The **bundle** (input) and **output target** are project-specific. Ask the user where they are — see "Discovery" below.

## Step 2 — Discovery (ask the user before running anything)

The exact paths differ per project. Confirm explicitly:

1. **Where do the handoff HTML files live?** Anywhere — could be `public/...`, `docs/...`, `client-handoff/...`, a separate folder outside the repo, etc. Call this `BUNDLE_ROOT`.
2. **Does the bundle have a sub-directory structure for pages?** Many bundles organize pages under `<bundle>/pages/<persona>/*.html`. Some are flat. If nested, note the sub-root.
3. **What's the target output directory inside the app?** Where should the ported `page.tsx` files live? Could be `src/app/demo/`, `app/(internal)/preview/`, `src/app/showcase/`, etc. Call this `OUT_ROOT`.
4. **What's the route prefix for the URLs?** Usually matches the output directory's URL — `/demo/`, `/preview/`, `/showcase/`. Call this `ROUTE_PREFIX`.
5. **Are there multiple personas / roles?** (e.g. `executive`, `admin`, `hr`, `manager`) — each persona usually has its own `SITE_ROUTES` and `ProductSidebar` variant. List them.
6. **Wrapper class name for isolation?** Default is `.demo-app`. If the project already uses `.demo-app` for something else, pick a non-clashing name (e.g. `.handoff-app`, `.preview-scope`). Call this `WRAPPER_CLASS`.
7. **Fonts strategy:** reuse production fonts via CSS-variable cascade (recommended — one font pipeline, no faux-bold artifacts), or decode subset woff2 from the bundle? If reusing, get the production CSS variable names (e.g. `--font-archivo`, `--font-roobert`).
8. **Any debug overlays to skip?** Common pattern: `TweaksPanel` for live-tweaking design tokens — not part of the product surface. The user names these or you discover them in inventory.
9. **Where to put images (logos) extracted from the bundle?** Default `public/<scope>-images/`. The path must be web-accessible so demo pages can `<img src="...">` reference it.
10. **TypeScript stance for ported code:** exclude the demo output from `tsconfig` + ESLint (recommended), or fully type it?
11. **Final cleanup:** delete the source bundle once done, or keep as backup?

Capture these as variables. Throughout this document, the placeholders are:

| Placeholder | Meaning | Examples |
|---|---|---|
| `${SKILL_DIR}` | Absolute path to this skill's folder | `~/.claude/skills/handoff-bundle-port` |
| `${BUNDLE_ROOT}` | Bundle source folder | `public/demo-handoff/`, `/Users/me/client-bundles/v2/` |
| `${PAGES_SUBROOT}` | Sub-path inside bundle for pages | `pages/`, `` (empty if flat) |
| `${OUT_ROOT}` | App folder for ported page.tsx files | `src/app/demo/`, `app/(internal)/preview/` |
| `${ROUTE_PREFIX}` | URL prefix | `/demo/`, `/preview/` |
| `${WRAPPER_CLASS}` | CSS wrapper class | `.demo-app`, `.handoff-app` |
| `${COMPONENTS_IMPORT}` | TS-path-alias root for kit imports | `@/app/demo/_components`, `@/showcase/_components` |
| `${ASSETS_PREFIX}` | URL prefix for extracted logos | `/demo-images/`, `/preview-assets/` |

## Step 3 — Architecture you produce

```
${OUT_ROOT}/
  page.tsx                 # sitemap (port of original sitemap.html)
  layout.tsx               # <div className="..."> wrapper; imports the scoped CSS
  _styles/
    demo.css               # design tokens + base classes, scoped under ${WRAPPER_CLASS}
    sitemap.css            # sitemap-only styles, scoped separately
  _components/
    <persona-a>/
      uikit.tsx            # ProductShell, Sidebar, TopBar, etc. + SITE_ROUTES
      charts.tsx           # Btn, gauges, hero panels
    <persona-b>/
      uikit.tsx, charts.tsx
    icons.tsx              # domain icons / glyph helpers
    glyphs.tsx
    extras.tsx             # schema/data tables
    ...                    # other kits the inventory reveals
  <persona>/<path>/page.tsx  # one file per surface

public/<assets-prefix>/    # logos
```

**Hard rule:** the entire `${OUT_ROOT}` tree is excluded from `tsconfig.json` and `eslint.config.mjs`. Files carry `'use client'`, `/* eslint-disable */`, `// @ts-nocheck` headers — they are verbatim handoff JSX, not first-class production code.

## The six phases

Each phase calls a script with `${SKILL_DIR}/scripts/<name>.py`. Every script has `--help`.

### Phase 0 — Inventory

```bash
python3 ${SKILL_DIR}/scripts/inventory.py --bundle-root ${BUNDLE_ROOT}
```

Output: frequency table of unique babel scripts (by content hash) + asset UUID list. Expected: 5-15 unique scripts shared across all pages.

### Phase 1a — Decode fonts (optional; skip if reusing production)

```bash
python3 ${SKILL_DIR}/scripts/extract_fonts.py --bundle-root ${BUNDLE_ROOT} --out ${OUT_ROOT}/_fonts/
```

**Important:** woff2 files from the bundle are typically **subset, single-weight** files (one per Unicode range). They are NOT variable fonts. Check with `python3 -c "with open('f.woff2','rb') as fh: print(b'fvar' in fh.read())"`. If False, declaring them for 4 weights in `next/font/local` will not give true weight variation — for cleanest result, swap to production variable fonts.

### Phase 1b — Extract and scope CSS

```bash
python3 ${SKILL_DIR}/scripts/transform_css.py \
  --bundle-root ${BUNDLE_ROOT} \
  --pages-subroot ${PAGES_SUBROOT} \
  --scope ${WRAPPER_CLASS} \
  --out ${OUT_ROOT}/_styles/demo.css \
  --per-page-out ${OUT_ROOT}/_styles/per_page_css.json
```

The script:
- Scans `<style>` blocks across **every** page (not one sample), unwrapping React-style `<style>{'...'}</style>` literals where present
- Counts how many pages each rule appears in, then **splits** them:
  - rules present in ≥ 2 pages (the shared design system) → `demo.css`, scoped once under `${WRAPPER_CLASS}`
  - rules unique to a single page (its modal/form/special layout, its own `@keyframes`) → `per_page_css.json`, keyed by the page's html path. Phase 3 injects these per page.
- Drops `@font-face` blocks (use production fonts via cascade)
- Scopes every rule under `${WRAPPER_CLASS}` (and rules inside `@media`)
- Appends a Tailwind-preflight counteraction (see Pattern 8 below)

**Why the split matters (do not skip `--per-page-out`):** earlier versions parsed `<style>` from `pages[0]` only, on the assumption that all CSS is one shared design system. It is not — each self-contained page also carries its own per-page rules. Taking one sample silently dropped every other page's per-page CSS (`.ml-prov`, `.wz`, `@keyframes mlStepIn`, …), so pages rendered against undefined classes and visibly broke (a flex list collapsing into one row is the classic symptom). The split keeps `demo.css` to the shared system and routes each page's unique rules back to that page. If you omit `--per-page-out`, the script merges everything into `demo.css` (nothing is lost, but generic class names from different pages then share one global scope — prefer the split).

**After:** swap font literals in `--font-heading` / `--font-body` to your production CSS variables.

### Phase 1c — Layout wrapper (manual)

Create `${OUT_ROOT}/layout.tsx`:

```tsx
import './_styles/demo.css';

export const metadata = { title: 'Demo' };

export default function Layout({ children }: { children: React.ReactNode }) {
  return <div className="${WRAPPER_CLASS-without-dot}">{children}</div>;
}
```

**Do not** declare `<html>`/`<body>` here — those come from the root layout. **Do not** load fonts here if reusing production via cascade.

Also exclude the output path from `tsconfig.json`:

```json
"exclude": ["node_modules", ".next", "${OUT_ROOT}/**/*"]
```

And from your ESLint config's `globalIgnores`.

### Phase 2 — Port shared kits

```bash
python3 ${SKILL_DIR}/scripts/transform_kits.py --bundle-root ${BUNDLE_ROOT} --out ${OUT_ROOT}/_components/
```

Writes one `kit-<hash>.tsx` per unique babel script + a `mapping.json` listing components/consts per file. **Inspect mapping.json and rename files semantically** (e.g. `kit-8f5d420d.tsx` → `executive/uikit.tsx`).

Then post-process (in this order):

```bash
# Per-persona route patch (one call per persona)
python3 ${SKILL_DIR}/scripts/patch_routes.py --file ${OUT_ROOT}/_components/<persona>/uikit.tsx --route-prefix ${ROUTE_PREFIX}<persona>/ --persona-code <code>

# SSR-safety chain
python3 ${SKILL_DIR}/scripts/patch_window.py        --components ${OUT_ROOT}/_components/ --assets-prefix ${ASSETS_PREFIX}
python3 ${SKILL_DIR}/scripts/fix_mangled_hooks.py   --components ${OUT_ROOT}/_components/
python3 ${SKILL_DIR}/scripts/fix_ssr.py             --components ${OUT_ROOT}/_components/
python3 ${SKILL_DIR}/scripts/fix_crossref.py        --components ${OUT_ROOT}/_components/
```

### Phase 3 — Port pages

```bash
python3 ${SKILL_DIR}/scripts/port_all_pages.py \
  --bundle-root ${BUNDLE_ROOT} \
  --pages-subroot ${PAGES_SUBROOT} \
  --components ${OUT_ROOT}/_components/ \
  --components-import-root ${COMPONENTS_IMPORT} \
  --out-root ${OUT_ROOT} \
  --route-prefix ${ROUTE_PREFIX} \
  --per-page-css ${OUT_ROOT}/_styles/per_page_css.json \
  --skip-names TweaksPanel TweakSection TweakSlider TweakText useTweaks  # adjust list
```

For each HTML:
1. Extracts the inline `<script type="text/babel">` (page's `App` + data)
2. Resolves identifier references against kit exports
3. Emits import statements per source kit
4. Rewrites internal `.html` links to Next routes
5. Strips `ReactDOM.createRoot(...).render(<App/>);`, replaces with default export
6. Injects noop stubs for skipped names
7. If `--per-page-css` has CSS for this page, wraps the default export as `<><style>{`…`}</style><App/></>` — one inline `<style>` that covers every render state of `App` (early returns, sub-views). CSS is escaped for the template literal. Pages whose code has no `function App` are flagged with a `[WARN …]` so you inject their `<style>` manually.

### Phase 4 — Sitemap

```bash
python3 ${SKILL_DIR}/scripts/build_sitemap.py \
  --sitemap ${BUNDLE_ROOT}/sitemap.html \
  --out ${OUT_ROOT}/page.tsx \
  --styles-out ${OUT_ROOT}/_styles/sitemap.css \
  --scope .sitemap-app
```

### Phase 5 — Cleanup (manual)

1. Delete old iframe router if any (e.g. `${OUT_ROOT}/[persona]/[[...slug]]/page.tsx`)
2. Delete `${BUNDLE_ROOT}` if the user confirmed in discovery
3. Update project memory (`.claude/CLAUDE.md` or equivalent) with an entry describing the new architecture

### Phase 6 — Verify

```bash
# Static CSS audit — catches lost per-page CSS that tsc/eslint can't see.
# ALWAYS pass --per-page-css: without it the audit is blind to page-level
# body/html/:root rules (background, text color, min-height, flex) — see Pattern 10.
python3 ${SKILL_DIR}/scripts/verify_css.py --root ${OUT_ROOT} \
  --per-page-css ${OUT_ROOT}/_styles/per_page_css.json

# Whatever the project uses — adapt to its package.json scripts:
pnpm run format-and-check   # or: pnpm format && pnpm lint && pnpm typecheck

# Smoke test all routes
python3 ${SKILL_DIR}/scripts/smoke_test.py --base-url http://localhost:3000 --pages-root ${OUT_ROOT}
```

`verify_css.py` does two things. First it diffs what the ported code **uses** (`className="…"`, `animation: '…'`) against what the CSS **defines** (`.class` selectors and `@keyframes` in `*.css` + inline `<style>`). Anything used-but-undefined is a lost-CSS defect — exactly the failure mode tsc and eslint stay silent on. Second, with `--per-page-css`, it confirms every page-unique rule transform_css.py emitted was actually **injected** into its page's `page.tsx` `<style>`. That second check is the only thing that catches a dropped **page-level** rule — a page's `body`/`html`/`:root` background / text-color / min-height / flex, scoped to the wrapper (`.demo-app { background: navy; color:#fff }`). Those rules carry no `className` and no `animation`, so the first diff can never see them; a dark full-screen page once shipped invisible (white text on a light surface) for exactly this reason (see Pattern 10). **Run it with `--per-page-css` and resolve every finding before reporting done.** A finding usually means either (a) `--per-page-out`/`--per-page-css` wasn't wired through Phases 1b/3, (b) the per-page-CSS key didn't line up with the ported page path at inject time, or (c) the keyframe lives only in a non-ported file (see Pattern 10).

## SSR troubleshooting playbook

Page rendering in iframe-handoff has zero SSR. Once you port to Next.js App Router (where every page is SSR'd by default), module-level `window`/`document` access throws `ReferenceError: window is not defined` on the server. You will hit this 4-5 times during a port. The patterns:

### Pattern 1: `Object.assign(window, { X, Y, Z })` at module load

Original demo's way of exposing components globally so other inline scripts can use them.

**Fix:** wrap with guard. Handled automatically by `scripts/patch_window.py`.

### Pattern 2: `useState(typeof window !== 'undefined' ? window.innerWidth : 1280)`

Looks safe (it has a typeof guard), but on **client first render** (hydration) it evaluates to actual width, mismatching SSR. Classic hydration mismatch.

**Fix:** `useState(1280)` + sync inside `useEffect`. Handled by `scripts/fix_ssr.py`.

### Pattern 3: `useState(readFromLocalStorage)` initializer

Same problem — initializer runs on both server and client first render.

**Fix:** initialize with the default value (what an empty localStorage returns), read inside `useEffect`. Handled by `scripts/fix_ssr.py`.

### Pattern 4: Mangled hook names — `useState2`, `useEffect2`, etc.

The original bundle was compiled with Babel that mangled hook names with numeric suffixes.

**Fix:** find/replace globally. Handled by `scripts/fix_mangled_hooks.py`.

### Pattern 5: Cross-kit references through `window.X`

The original bundle puts every shared component on `window` so other kits use them globally without imports. After port, `window.DomainIcon` throws on SSR.

**Fix:** replace `window.X` → `X`, add import. Handled by `scripts/fix_crossref.py`.

### Pattern 6: `window.APP_ASSETS || './assets/'`

Demo bundle puts asset path on `window`.

**Fix:** replace expression with the literal `${ASSETS_PREFIX}`. Handled by `scripts/patch_window.py`.

### Pattern 7: Module-load globals via `window.X = ...` with multi-line bodies

If a global assignment spans multiple lines (e.g. arrow function body with `.reduce(...)`), naive `^window\.X = ...;$` wrapping breaks the syntax because the first `;` inside the arrow function closes the guard prematurely.

**Fix:** for files with this pattern (typically schema/data tables), **rewrite manually as named exports**. `scripts/patch_window.py` flags such files but doesn't attempt to fix them — manual rewrite is safer.

### Pattern 8: Tailwind preflight leaking into form elements

Tailwind 4 has a base layer rule:

```css
button, input, select, optgroup, textarea {
  font: inherit;
  letter-spacing: inherit;
}
```

This makes form-element fonts inherit from the parent. But the original handoff iframe runs without Tailwind, so form elements use UA default (~13.3px). Result: every button in the port looks bigger than the original.

**Fix:** counteract under the demo scope (auto-injected by `scripts/transform_css.py`):

```css
${WRAPPER_CLASS} button,
${WRAPPER_CLASS} input,
${WRAPPER_CLASS} select,
${WRAPPER_CLASS} optgroup,
${WRAPPER_CLASS} textarea {
  font: revert;
  letter-spacing: revert;
  font-feature-settings: revert;
  font-variation-settings: revert;
}
```

### Pattern 9: JSX expression collisions in sitemap text

Original docs may say `<code>/pages/{role}/</code>`. After `class=` → `className=` conversion, `{role}` becomes a JS expression in JSX and throws.

**Fix:** replace `{role}` → `[role]` (or wrap as `{'{role}'}` string literal). Handled by `scripts/build_sitemap.py` for known patterns; for custom ones, audit the generated `page.tsx`.

### Pattern 10: Lost per-page CSS — page renders against undefined classes

The most invisible failure of the whole port. The JSX is valid, tokens resolve, `tsc` and `eslint` are green — but a page looks structurally broken because a `className` or `animation` it uses points at a CSS rule that never made it into the output. The browser silently ignores the unknown class, so a `display:flex` row list collapses into inline text, a form loses its borders, a keyframe never animates.

**Root cause:** each handoff HTML is self-contained and carries the full design system **plus** its own per-page rules in `<style>`. If CSS is taken from one sample page (the old bug), or `--per-page-out`/`--per-page-css` aren't wired through, every other page's per-page rules are dropped.

**Fix:** the Phase 1b → Phase 3 split handles this automatically — `transform_css.py --per-page-out` captures page-unique rules, `port_all_pages.py --per-page-css` injects them. Always run `verify_css.py` (Phase 6) to confirm nothing is undefined.

**Sub-case — keyframe defined only in a non-ported file.** A page may reference an animation (e.g. `fadeIn`) whose `@keyframes` lives **only** in a bundle file you don't port (e.g. the bundle's own `demo.html` sitemap-navigator that has a non-standard structure). The split can't find it in any ported page's `<style>`, so it won't be injected — and `verify_css.py` will flag it as an undefined animation. Resolve manually: grep the **whole** bundle for `@keyframes <name>`, copy the body into the using page's inline `<style>` (or into `demo.css` if several pages use it). This is the one per-page case automation can't close on its own — that's exactly why the Phase 6 audit exists.

**Sub-case — page-level rule dropped (the invisible page).** The most dangerous variant, because nothing in the JSX *references* it. A page's own background, text color, full-height/centred layout often live in **per-page `body` / `html` / `:root` rules** — e.g. a dark full-screen onboarding ships `html, body { background: var(--navy) }` and `body { color: #fff; min-height: 100vh; display: flex; flex-direction: column }` on top of the shared (light) design system. `transform_css.py` scopes these to the wrapper (`html`/`body`/`:root` → `${WRAPPER_CLASS}`) and routes the page-unique ones to `per_page_css.json`; `port_all_pages.py` injects them into that page's `<style>`. If any link in that chain breaks — an older transform_css that didn't map `body`→wrapper, a per-page-CSS key that didn't line up with the ported page path, a flat per-persona invocation with a different `--pages-subroot` — the rule is silently dropped. The page then renders with its **content styled for a background that isn't there**: white text on a light surface (looks blank), or content stuck top-left instead of centred full-height. Because there is no `className` and no `animation` involved, the class/keyframe diff is blind to it and `tsc`/`eslint` are green. **Only `verify_css.py --per-page-css` catches it** — it checks that each page-unique rule actually landed in its `page.tsx`. Always pass `--per-page-css` in Phase 6. If flagged, confirm the page's wrapper-scoped background/color/layout rules are present in its injected `<style>` (or, equivalently, wrap that page's content in a local element carrying those styles).

## Decision log

1. **Reuse production fonts via cascade; don't decode subset woff2.** Bundle woff2 files are non-variable subsets — declaring them for weights 500/600/700 in `next/font/local` makes the browser render those weights with the 400 glyphs (no faux-bold), creating a visually different result from a variable font. Production usually ships proper variable fonts.

2. **`tsconfig` + `eslint` excludes for demo paths.** Demo code is verbatim handoff JSX — typing it is 0-value busywork. Excluding lets typecheck stay strict for production without polluting demo.

3. **Skip debug overlays (e.g. TweaksPanel).** Live-token-tweak overlays aren't part of the product surface. Render noop stubs in place — preserves page structure without the overlay.

4. **Persona variants are separate kits, not props.** Each persona has its own `SITE_ROUTES` constant. Unifying through a prop adds risk; separate folders keep isolation clean.

5. **Verbatim port first; refactor never.** Do not deduplicate or simplify any demo JSX. If the client ships an update, you re-port — refactors die instantly. Demo is a snapshot, not a codebase.

6. **CSS is global-shared + per-page-unique, not one sample.** A self-contained bundle duplicates the design system into every page and adds page-specific rules on top. Treating CSS as "one shared sheet, sample any page" drops every page's unique rules. The model: rules in ≥2 pages → `demo.css` (one copy); rules in exactly one page → that page's inline `<style>` via `per_page_css.json`. Per-page `<style>` goes on the `DemoPage` wrapper so it covers all of `App`'s render states. This mirrors how the original bundle worked (each page shipped its own `<style>`) and avoids generic-class collisions in the global scope. Note this layer also carries **page-level** rules (a page's own `body`/`html`/`:root` background, text color, min-height, flex) scoped to the wrapper — and those are the easiest to lose invisibly, since no `className`/`animation` points at them. `verify_css.py --per-page-css` is the backstop that proves nothing was dropped — run it *with* that flag, or page-level rules go unchecked.

## Self-review checklist before reporting done

1. `verify_css.py --root ${OUT_ROOT} --per-page-css ${OUT_ROOT}/_styles/per_page_css.json` is clean — no undefined classes/animations AND every page-unique rule (incl. page-level `body`/`html`/`:root` background/color/layout) was injected into its page (lost per-page CSS, including the "invisible page")
2. Smoke test: every page route returns HTTP 200
3. No `ReferenceError: window is not defined` in dev server logs
4. No `Hydration failed` warnings — open one page in browser, check console
4. Visual spot-check three pages: sidebar font, hero heading line breaks, sample chart. Compare to original handoff iframe (if still accessible) at a known good URL
5. `tsconfig` and `eslint` excludes for demo paths are in place
6. Production code does not import anything from the demo output folder
7. Project's format/lint/typecheck script is clean
8. Project memory (`.claude/CLAUDE.md` or equivalent) has an entry describing the new architecture
9. The `${BUNDLE_ROOT}` source folder is deleted (or explicitly kept with a rationale)

## Scripts reference

All scripts in `${SKILL_DIR}/scripts/`. Each is self-contained Python stdlib; each takes CLI args (`--help` for usage).

| Script | Phase | Purpose |
|---|---|---|
| `inventory.py` | 0 | Count unique babel scripts by content hash; list asset UUIDs |
| `extract_fonts.py` | 1a | Decode woff2 from manifest, save to disk |
| `transform_css.py` | 1b | Scan CSS across all pages; split global (→demo.css) vs per-page-unique (→per_page_css.json); scope under wrapper; inject Tailwind preflight counteraction |
| `transform_kits.py` | 2 | Convert each unique babel script to a TSX kit module |
| `patch_routes.py` | 2 | Rewrite `_routePrefix`, `_buildRoutes`, `readPersona`, `withPersona` for Next.js routing |
| `patch_window.py` | 2 | Wrap `Object.assign(window, ...)` and `window.X = ...` in SSR guards; replace `window.APP_ASSETS` |
| `fix_mangled_hooks.py` | 2 | Fix `useState2`/`useEffect2`/etc → `useState`/`useEffect` |
| `fix_ssr.py` | 2 | Fix `useState(window.innerWidth)` and localStorage-in-initializer patterns |
| `fix_crossref.py` | 2 | Auto-add cross-kit imports for symbols referenced via JSX/call |
| `port_all_pages.py` | 3 | For every `.html`, extract App, resolve imports, rewrite links, inject per-page `<style>`, emit `page.tsx` |
| `build_sitemap.py` | 4 | Port `sitemap.html` to a React `page.tsx` with scoped CSS |
| `verify_css.py` | 6 | Static audit: every `className`/`animation` used must resolve to a CSS rule/`@keyframes`; with `--per-page-css`, also verifies every page-unique rule (incl. page-level `body`/`html`/`:root` background/color/layout) was injected into its `page.tsx` (catches lost per-page CSS, including the "invisible page") |
| `smoke_test.py` | 6 | Curl every `page.tsx` route, report HTTP status |

## Quick start for the agent

When this skill is invoked:

1. **Locate yourself.** Resolve `${SKILL_DIR}` (this file's parent directory).
2. **Ask the discovery questions** (Step 2) and collect all path/name variables.
3. **Create a task list**, one task per phase.
4. **Run scripts in order** (Phases 0→6), substituting your variables.
5. **Manually fix any failures** using the troubleshooting playbook.
6. **Cleanup** (Phase 5) — only after smoke test passes.
7. **Verify** the project's format/lint/typecheck script.
8. **Report** results.

Never assume the user's project layout. Always read the answers from discovery into the variables, never hardcode.
