#!/usr/bin/env python3
"""Phase 2: Wrap module-level window access in SSR guards.

Three patterns handled:
  1. Object.assign(window, { X, Y, ... }) — multi-line block, wrapped with typeof-window guard
  2. window.X = ...; (single-line assignment) — wrapped with typeof-window guard
  3. (window.APP_ASSETS || '...') — replaced with literal asset prefix

Pattern 3 needs --assets-prefix (e.g. /demo-images/).

NOT handled (manual rewrite required):
  - Multi-line window.X = expr where expr spans lines (e.g. arrow function body
    using .reduce). Wrapping with regex breaks syntax. See SKILL.md Pattern 7
    — rewrite the file as named exports manually.

Usage:
  python3 patch_window.py --components src/app/demo/_components/ --assets-prefix /demo-images/
"""
import argparse, re, glob


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--components', required=True, help='_components root dir')
    ap.add_argument('--assets-prefix', default='/demo-images/', help='replaces (window.APP_ASSETS || \'fallback\')')
    args = ap.parse_args()

    files = sorted(set(glob.glob(f'{args.components.rstrip("/")}/**/*.tsx', recursive=True) +
                        glob.glob(f'{args.components.rstrip("/")}/*.tsx')))

    # Pattern 1: Object.assign(window, {...});  (multi-line)
    pat_objassign = re.compile(r'^Object\.assign\(window,\s*\{[^}]+\}\s*\);', re.M | re.S)
    # Pattern 2: bare window.X = expr;
    pat_bare = re.compile(r'^(window\.[\w]+\s*=\s*[^;]+;)', re.M)
    # Pattern 3: (window.APP_ASSETS || 'fallback')
    pat_assets = re.compile(r"\(window\.APP_ASSETS\s*\|\|\s*['\"][^'\"]*['\"]\)")

    total = 0
    for f in files:
        with open(f) as fh: src = fh.read()
        orig = src

        # Pattern 1
        src = pat_objassign.sub(lambda m: f"if (typeof window !== 'undefined') {{\n{m.group(0)}\n}}", src)

        # Pattern 2 (skip lines already inside a guard)
        def wrap_bare(m):
            return f"if (typeof window !== 'undefined') {{ {m.group(1)} }}"
        # Only apply if line isn't already inside a brace block — we just naively wrap.
        # Already-wrapped lines won't match (they start with "if (typeof").
        src = pat_bare.sub(wrap_bare, src)

        # Pattern 3
        src = pat_assets.sub(f"'{args.assets_prefix}'", src)
        src = re.sub(r"window\.APP_ASSETS\b", f"'{args.assets_prefix}'", src)

        if src != orig:
            with open(f, 'w') as fh: fh.write(src)
            total += 1
            print(f'patched {f}')

    print(f'\nTotal: {total} files patched')

    # Warn about possible multi-line window.X = expr patterns we didn't handle
    print('\n=== Possible multi-line window.X = expr (manual rewrite needed) ===')
    for f in files:
        with open(f) as fh: src = fh.read()
        # Heuristic: any window.X = ... that opens a brace
        for m in re.finditer(r'^window\.[\w]+\s*=\s*[^{}\n]*\{', src, re.M):
            print(f'  {f}: {m.group(0)[:80]}...')


if __name__ == '__main__':
    main()
