# Scripts for the handoff-bundle-port skill

These scripts implement the 6 phases described in `../SKILL.md`. Each is a standalone Python script using only the stdlib (no `pip install`). All accept CLI args — run any with `-h` for usage.

## Path variables

The scripts make no assumptions about where you call them from or where your project lives. Throughout this README, these placeholders are used — **set them once for your session** based on the user's discovery answers:

| Variable | Meaning |
|---|---|
| `SKILL_DIR` | Absolute path to this skill's folder (the parent of `scripts/`). Resolve from where this `SKILL.md` lives — could be `~/.claude/skills/handoff-bundle-port/`, a plugin path, or a project-local path. |
| `BUNDLE_ROOT` | Source folder containing the handoff HTML files. Anywhere — `public/...`, `docs/...`, an absolute path outside the repo. |
| `PAGES_SUBROOT` | Sub-path inside `BUNDLE_ROOT` where the per-persona HTMLs live (often `pages/`, sometimes empty). |
| `OUT_ROOT` | Target folder for ported `page.tsx` files — `src/app/<some-name>/` or `app/(group)/<some-name>/`. |
| `ROUTE_PREFIX` | URL prefix matching `OUT_ROOT` — `/demo/`, `/preview/`, `/showcase/`. |
| `WRAPPER_CLASS` | CSS class for the demo isolation wrapper — `.demo-app`, `.handoff-app`, etc. |
| `COMPONENTS_IMPORT` | TS-path-alias root for kit imports — `@/app/demo/_components`, etc. |
| `ASSETS_PREFIX` | URL prefix for extracted logo assets — `/demo-images/`, `/preview-assets/`. |

## Suggested execution order

Example — adapt every variable to your project. **Do NOT copy this verbatim** without changing the values.

```bash
# === Set per-session ===
SKILL_DIR=/path/to/handoff-bundle-port           # wherever this skill lives
BUNDLE_ROOT=/path/to/handoff/bundle              # ask the user
OUT_ROOT=src/app/demo                            # ask the user
ROUTE_PREFIX=/demo/                              # ask the user
WRAPPER_CLASS=.demo-app                          # ask the user
COMPONENTS_IMPORT=@/app/demo/_components         # ask the user
ASSETS_PREFIX=/demo-images/                      # ask the user

# === Phase 0 — inventory ===
python3 ${SKILL_DIR}/scripts/inventory.py --bundle-root ${BUNDLE_ROOT}

# === Phase 1a — fonts (optional; usually skip in favor of production fonts) ===
# python3 ${SKILL_DIR}/scripts/extract_fonts.py --bundle-root ${BUNDLE_ROOT} --out ${OUT_ROOT}/_fonts/

# === Phase 1b — CSS scope (split global vs per-page) ===
python3 ${SKILL_DIR}/scripts/transform_css.py \
  --bundle-root ${BUNDLE_ROOT} \
  --pages-subroot ${PAGES_SUBROOT} \
  --scope ${WRAPPER_CLASS} \
  --out ${OUT_ROOT}/_styles/demo.css \
  --per-page-out ${OUT_ROOT}/_styles/per_page_css.json
# Scans <style> across ALL pages. Shared rules -> demo.css; page-unique rules ->
# per_page_css.json (injected per page in Phase 3). Do NOT drop --per-page-out, or
# generic class names from different pages collide in the global scope.

# Manual: swap font literals to production CSS variables — names depend on the project
# e.g. sed -i.bak "s/'Archivo', /var(--font-archivo), /g" ${OUT_ROOT}/_styles/demo.css

# === Phase 1c — layout.tsx ===
# Write manually; see SKILL.md "Phase 1c". One file, ~10 lines.

# === Phase 2 — port shared kits ===
python3 ${SKILL_DIR}/scripts/transform_kits.py --bundle-root ${BUNDLE_ROOT} --out ${OUT_ROOT}/_components/

# Manual: inspect ${OUT_ROOT}/_components/mapping.json and rename
# kit-<hash>.tsx files semantically based on the components inside them
# (e.g. kit-8f5d420d.tsx → executive/uikit.tsx)

# Per-persona route patch — one call per persona
for persona in executive admin; do
  code=$( [ "$persona" = "executive" ] && echo "exec" || echo "$persona" )
  python3 ${SKILL_DIR}/scripts/patch_routes.py \
    --file ${OUT_ROOT}/_components/${persona}/uikit.tsx \
    --route-prefix ${ROUTE_PREFIX}${persona}/ \
    --persona-code $code
done

# SSR-safety chain (order matters)
python3 ${SKILL_DIR}/scripts/patch_window.py        --components ${OUT_ROOT}/_components/ --assets-prefix ${ASSETS_PREFIX}
python3 ${SKILL_DIR}/scripts/fix_mangled_hooks.py   --components ${OUT_ROOT}/_components/
python3 ${SKILL_DIR}/scripts/fix_ssr.py             --components ${OUT_ROOT}/_components/
python3 ${SKILL_DIR}/scripts/fix_crossref.py        --components ${OUT_ROOT}/_components/

# === Phase 3 — pages ===
python3 ${SKILL_DIR}/scripts/port_all_pages.py \
  --bundle-root ${BUNDLE_ROOT} \
  --pages-subroot ${PAGES_SUBROOT} \
  --components ${OUT_ROOT}/_components/ \
  --components-import-root ${COMPONENTS_IMPORT} \
  --out-root ${OUT_ROOT} \
  --route-prefix ${ROUTE_PREFIX} \
  --per-page-css ${OUT_ROOT}/_styles/per_page_css.json \
  --skip-names TweaksPanel TweakSection TweakSlider TweakText useTweaks
  # --per-page-css injects each page's unique rules as an inline <style> on its
  # DemoPage wrapper. Adjust --skip-names based on what the bundle ships.

# === Phase 4 — sitemap (if the bundle has one) ===
python3 ${SKILL_DIR}/scripts/build_sitemap.py \
  --sitemap ${BUNDLE_ROOT}/sitemap.html \
  --out ${OUT_ROOT}/page.tsx \
  --styles-out ${OUT_ROOT}/_styles/sitemap.css

# === Phase 5 — cleanup (manual, confirm with user first) ===
# rm -rf ${OUT_ROOT}/[persona]                        # delete any old iframe router
# rm -rf ${BUNDLE_ROOT}                               # delete handoff source

# === Phase 6 — verify ===
# Static CSS audit FIRST — catches lost per-page CSS that tsc/eslint never see
python3 ${SKILL_DIR}/scripts/verify_css.py --root ${OUT_ROOT}

# Start dev server (whatever the project uses)
pnpm run dev &
sleep 5
python3 ${SKILL_DIR}/scripts/smoke_test.py --base-url http://localhost:3000 --pages-root ${OUT_ROOT}

# Project's format/lint/typecheck (whatever script it has — pnpm format-and-check, npm run check, etc.)
pnpm run format-and-check
```

## Important notes

- **CSS is split, then verified.** `transform_css.py` (Phase 1b) emits `per_page_css.json` alongside `demo.css`; `port_all_pages.py` (Phase 3) consumes it via `--per-page-css`. Use the same `--pages-subroot` for both so the per-page keys line up. Always finish with `verify_css.py` (Phase 6) — it fails if any `className`/`animation` resolves to nothing, which is the signature of dropped per-page CSS. If it flags an animation whose `@keyframes` isn't in any ported page, grep the whole bundle (it may live in a non-ported file) and add it by hand.
- **Order matters.** `fix_crossref.py` requires `_components/` to already exist with named exports — run it after `transform_kits.py` and after the manual rename step.
- **Manual renaming step is non-optional.** `transform_kits.py` writes files named `kit-<hash>.tsx` because it doesn't know what each kit semantically is. After running, read `mapping.json` and rename to meaningful names. Subsequent scripts depend on import paths looking right.
- **Idempotency caveat.** Most scripts are safe to re-run, but `patch_window.py` is NOT — wrapping already-wrapped lines may produce malformed output. When iterating: `git checkout ${OUT_ROOT}/_components/` and start the chain again.
- **Smoke-test loop.** After a failure, look at the dev server log — the SSR error usually names the function that throws. Cross-reference against SKILL.md's troubleshooting playbook (Patterns 1-9).
- **Project-specific details:** package manager (`pnpm` / `npm` / `yarn` / `bun`), format/lint/typecheck script names, dev server port (`3000` / `5173` / other), TS path alias (`@/` is common but not universal) — all vary. Adapt invocations to what the project actually uses.
