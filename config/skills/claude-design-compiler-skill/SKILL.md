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
2. The full design-system CSS in `<style>` tags — tokens, typography, responsive rules
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
  --scope ${WRAPPER_CLASS} \
  --out ${OUT_ROOT}/_styles/demo.css
```

The script:
- Parses every `<style>` block from one sample HTML
- Drops `@font-face` blocks (use production fonts via cascade)
- Scopes every rule under `${WRAPPER_CLASS}` (and rules inside `@media`)
- Appends a Tailwind-preflight counteraction (see Pattern 8 below)

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
  --skip-names TweaksPanel TweakSection TweakSlider TweakText useTweaks  # adjust list
```

For each HTML:
1. Extracts the inline `<script type="text/babel">` (page's `App` + data)
2. Resolves identifier references against kit exports
3. Emits import statements per source kit
4. Rewrites internal `.html` links to Next routes
5. Strips `ReactDOM.createRoot(...).render(<App/>);`, replaces with default export
6. Injects noop stubs for skipped names

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
# Whatever the project uses — adapt to its package.json scripts:
pnpm run format-and-check   # or: pnpm format && pnpm lint && pnpm typecheck

# Smoke test all routes
python3 ${SKILL_DIR}/scripts/smoke_test.py --base-url http://localhost:3000 --pages-root ${OUT_ROOT}
```

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

## Decision log

1. **Reuse production fonts via cascade; don't decode subset woff2.** Bundle woff2 files are non-variable subsets — declaring them for weights 500/600/700 in `next/font/local` makes the browser render those weights with the 400 glyphs (no faux-bold), creating a visually different result from a variable font. Production usually ships proper variable fonts.

2. **`tsconfig` + `eslint` excludes for demo paths.** Demo code is verbatim handoff JSX — typing it is 0-value busywork. Excluding lets typecheck stay strict for production without polluting demo.

3. **Skip debug overlays (e.g. TweaksPanel).** Live-token-tweak overlays aren't part of the product surface. Render noop stubs in place — preserves page structure without the overlay.

4. **Persona variants are separate kits, not props.** Each persona has its own `SITE_ROUTES` constant. Unifying through a prop adds risk; separate folders keep isolation clean.

5. **Verbatim port first; refactor never.** Do not deduplicate or simplify any demo JSX. If the client ships an update, you re-port — refactors die instantly. Demo is a snapshot, not a codebase.

## Self-review checklist before reporting done

1. Smoke test: every page route returns HTTP 200
2. No `ReferenceError: window is not defined` in dev server logs
3. No `Hydration failed` warnings — open one page in browser, check console
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
| `transform_css.py` | 1b | Parse + scope CSS under wrapper class; inject Tailwind preflight counteraction |
| `transform_kits.py` | 2 | Convert each unique babel script to a TSX kit module |
| `patch_routes.py` | 2 | Rewrite `_routePrefix`, `_buildRoutes`, `readPersona`, `withPersona` for Next.js routing |
| `patch_window.py` | 2 | Wrap `Object.assign(window, ...)` and `window.X = ...` in SSR guards; replace `window.APP_ASSETS` |
| `fix_mangled_hooks.py` | 2 | Fix `useState2`/`useEffect2`/etc → `useState`/`useEffect` |
| `fix_ssr.py` | 2 | Fix `useState(window.innerWidth)` and localStorage-in-initializer patterns |
| `fix_crossref.py` | 2 | Auto-add cross-kit imports for symbols referenced via JSX/call |
| `port_all_pages.py` | 3 | For every `.html`, extract App, resolve imports, rewrite links, emit `page.tsx` |
| `build_sitemap.py` | 4 | Port `sitemap.html` to a React `page.tsx` with scoped CSS |
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
