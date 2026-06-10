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

Usage:
  python3 verify_css.py --root src/app/demo/

Notes:
  * Demo output is style-isolated, so it must not rely on production CSS — an undefined
    class here is a real defect, not a false positive from some global stylesheet.
  * Dynamic `className={...}` is not statically analyzable and is skipped (reported as a
    count so you know coverage isn't total).
"""
import argparse, re, glob, os

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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', required=True, help='output tree, e.g. src/app/demo/')
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

    total = len(missing_classes) + len(missing_anims)
    if total == 0:
        print('OK — every className and animation resolves to a definition.')
    else:
        print(f'FOUND {total} file(s) with undefined references — likely lost per-page CSS.')
    if dynamic_total:
        print(f'(note: {dynamic_total} dynamic className={{...}} sites not statically checked)')

    if total:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
