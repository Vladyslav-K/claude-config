#!/usr/bin/env python3
"""Phase 6: Static check that no ported page references a CSS class or @keyframes
that is defined nowhere.

This is the regression guard for the "per-page CSS got dropped during the port" bug.
A page can render with a perfectly valid JSX tree, pass typecheck and lint, and still
look broken — because the browser silently ignores a `className`/`animation` that
points at a rule which never made it into the output. Neither tsc nor eslint catches
that. This script does, by diffing what the code USES against what the CSS DEFINES.

It scans the output tree (--root) and collects:
  * DEFINED classes  — `.name` selectors in any *.css and inside any inline <style>{`...`}</style>
  * DEFINED keyframes — `@keyframes name` in the same places
  * USED classes      — tokens inside static `className="..."`
  * USED animations   — the keyframe name in `animation: 'name ...'` / `animation-name: 'name'`

Anything used but not defined is reported. Exit code 1 if findings (so it can gate CI).

It also has a BLIND SPOT by construction: page-level rules — a page's background,
text color, min-height, flex layout — come from the bundle's per-page `body`/`html`/
`:root` rules, which transform_css.py scopes to the wrapper (e.g. `.demo-app { background:
navy; color:#fff; min-height:100vh }`) and port_all_pages.py injects per page. Those
rules carry NO className and NO animation, so the class/keyframe diff above can never
see them. If such a rule is dropped (e.g. an older transform_css that didn't map
body→wrapper, or a per-page-CSS key that didn't line up at inject time), the page
renders invisibly — white text on a light surface, content not full-height/centred —
while tsc, eslint AND the class/keyframe audit all stay green. That is exactly how a
dark full-screen onboarding page shipped broken once.

To close that blind spot, pass --per-page-css (the JSON transform_css.py wrote with
--per-page-out). For every page that has page-unique CSS, this verifies the rules were
actually injected into that page's page.tsx <style>. A page-unique rule present in the
JSON but absent from the ported page = a silent page-level drop — reported, exit 1.

Usage:
  python3 verify_css.py --root src/app/demo/
  python3 verify_css.py --root src/app/demo/ --per-page-css src/app/demo/_styles/per_page_css.json

Notes:
  * Demo output is style-isolated, so it must not rely on production CSS — an undefined
    class here is a real defect, not a false positive from some global stylesheet.
  * Dynamic `className={...}` is not statically analyzable and is skipped (reported as a
    count so you know coverage isn't total).
"""
import argparse, re, glob, os, json

# animation sub-values that are keywords, not keyframe names
ANIM_KEYWORDS = {
    'none', 'inherit', 'initial', 'unset', 'revert',
    'ease', 'ease-in', 'ease-out', 'ease-in-out', 'linear', 'step-start', 'step-end',
    'infinite', 'normal', 'reverse', 'alternate', 'forwards', 'backwards', 'both',
    'running', 'paused',
}


def style_blocks(tsx):
    """Return the CSS text of every inline <style>...</style> in a tsx file."""
    return re.findall(r'<style>\s*\{?\s*[`\'"]?(.*?)[`\'"]?\s*\}?\s*</style>', tsx, re.S)


def collect_defined(css_files, tsx_files):
    classes, keyframes = set(), set()
    blobs = []
    for p in css_files:
        with open(p) as f:
            blobs.append(f.read())
    for p in tsx_files:
        with open(p) as f:
            blobs.extend(style_blocks(f.read()))
    for css in blobs:
        classes.update(re.findall(r'\.(-?[A-Za-z_][\w-]*)', css))
        keyframes.update(re.findall(r'@keyframes\s+([\w-]+)', css))
    return classes, keyframes


def used_in(tsx):
    classes, dynamic = set(), 0
    for m in re.findall(r'className="([^"]*)"', tsx):
        for tok in m.split():
            if tok:
                classes.add(tok)
    dynamic += len(re.findall(r'className=\{', tsx))
    anims = set()
    for name in re.findall(r"""animation(?:-name)?\s*:\s*['"`]?\s*(-?[A-Za-z_][\w-]*)""", tsx):
        if name not in ANIM_KEYWORDS:
            anims.add(name)
    return classes, anims, dynamic


def top_level_rules(css):
    """Split CSS into top-level units (selector{...}, @media{...}, @keyframes{...}),
    brace-aware so nested at-rules stay whole."""
    rules, i, n, depth, start = [], 0, len(css), 0, 0
    while i < n:
        c = css[i]
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                rules.append(css[start:i + 1])
                start = i + 1
        i += 1
    return [r.strip() for r in rules if r.strip()]


def norm_css(s):
    return re.sub(r'\s+', ' ', s).strip()


def check_per_page_injection(root, per_page_path):
    """For each page that has page-unique CSS in transform_css.py's --per-page-out JSON,
    confirm those rules actually landed in the ported page's inline <style>. This is the
    one check that catches dropped page-level body/html/:root rules (background, color,
    min-height, flex) — the class/keyframe audit is blind to them because they carry no
    className/animation. port_all_pages.py injects per-page CSS verbatim, so a coarse
    normalized-substring match per top-level rule is enough and false-positive-safe.
    Returns [(rel, [missing_rule_signature, ...]), ...]."""
    with open(per_page_path) as f:
        per_page = json.load(f)
    findings = []
    for rel, css in sorted(per_page.items()):
        if not css or not css.strip():
            continue
        page = os.path.join(root, rel, 'page.tsx')
        if not os.path.exists(page):
            findings.append((rel, ['page.tsx not found — page-unique CSS had nowhere to go']))
            continue
        with open(page) as f:
            injected = norm_css('\n'.join(style_blocks(f.read())))
        missing = [norm_css(r)[:70] for r in top_level_rules(css) if norm_css(r) not in injected]
        if missing:
            findings.append((rel, missing))
    return findings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', required=True, help='output tree, e.g. src/app/demo/')
    ap.add_argument('--per-page-css', default=None, help="transform_css.py's --per-page-out JSON. When given, verify every page-unique rule (incl. page-level body/html/:root background/color/layout) was actually injected into its page.tsx — the one drop the className/keyframe audit cannot see.")
    args = ap.parse_args()

    root = args.root.rstrip('/')
    css_files = sorted(glob.glob(f'{root}/**/*.css', recursive=True))
    tsx_files = sorted(glob.glob(f'{root}/**/*.tsx', recursive=True))
    if not tsx_files:
        raise SystemExit(f'No .tsx under {root}')

    defined_classes, defined_keyframes = collect_defined(css_files, tsx_files)
    print(f'Scanned {len(tsx_files)} tsx + {len(css_files)} css')
    print(f'Defined: {len(defined_classes)} classes, {len(defined_keyframes)} keyframes\n')

    missing_classes, missing_anims, dynamic_total = [], [], 0
    for p in tsx_files:
        with open(p) as f:
            tsx = f.read()
        classes, anims, dyn = used_in(tsx)
        dynamic_total += dyn
        bad_c = sorted(c for c in classes if c not in defined_classes)
        bad_a = sorted(a for a in anims if a not in defined_keyframes)
        rel = os.path.relpath(p, root)
        if bad_c:
            missing_classes.append((rel, bad_c))
        if bad_a:
            missing_anims.append((rel, bad_a))

    if missing_classes:
        print('=== Undefined classes (used in className, no CSS rule anywhere) ===')
        for rel, cs in missing_classes:
            print(f'  {rel}: {" ".join(cs)}')
        print()
    if missing_anims:
        print('=== Undefined animations (no matching @keyframes) ===')
        for rel, a in missing_anims:
            print(f'  {rel}: {" ".join(a)}')
        print()

    not_injected = []
    if args.per_page_css:
        if not os.path.exists(args.per_page_css):
            raise SystemExit(f'--per-page-css not found: {args.per_page_css}')
        not_injected = check_per_page_injection(root, args.per_page_css)
        if not_injected:
            print('=== Page-unique CSS NOT injected into the ported page (silent page-level drop) ===')
            for rel, rules in not_injected:
                print(f'  {rel}:')
                for r in rules:
                    print(f'      - {r}')
            print()
        else:
            print('Per-page injection: every page-unique rule is present in its page.tsx.\n')

    total = len(missing_classes) + len(missing_anims) + len(not_injected)
    if total == 0:
        print('OK — every className and animation resolves, and all page-unique CSS was injected.'
              if args.per_page_css else
              'OK — every className and animation resolves to a definition.')
    else:
        print(f'FOUND {total} file(s) with undefined references or un-injected page-unique CSS — likely lost CSS.')
    if not args.per_page_css:
        print('(note: page-level body/html/:root rules are NOT covered without --per-page-css)')
    if dynamic_total:
        print(f'(note: {dynamic_total} dynamic className={{...}} sites not statically checked)')

    if total:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
