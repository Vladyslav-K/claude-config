#!/usr/bin/env python3
"""Phase 2: Fix SSR-unsafe useState initializers.

Two patterns:
  1. useState(typeof window !== 'undefined' ? window.innerWidth : 1280)
     → useState(1280)  (effect syncs real value after mount)
  2. useState(read)  where `read` reads localStorage
     → useState(<default>);  React.useEffect(() => { ... read inside ... }, []);

Both patterns cause hydration mismatches because the initializer runs on both
server and client first render; if client returns a different value, React
re-renders the whole subtree and the visual result is unpredictable.

Usage:
  python3 fix_ssr.py --components src/app/demo/_components/
"""
import argparse, re, glob


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--components', required=True)
    args = ap.parse_args()

    files = sorted(set(
        glob.glob(f'{args.components.rstrip("/")}/**/*.tsx', recursive=True) +
        glob.glob(f'{args.components.rstrip("/")}/*.tsx')
    ))
    total = 0
    for f in files:
        with open(f) as fh: src = fh.read()
        orig = src

        # Pattern 1
        src = re.sub(
            r"useState\(typeof window !== 'undefined' \? window\.innerWidth : (\d+)\)",
            r"useState(\1)",
            src
        )

        # Pattern 2: useState(read) where `read` is a reader function. Common form is
        # const [collapsed, setCollapsed] = React.useState(read);
        # We replace with the value `true` by default — caller should review.
        # We replace ONLY if there's a `const read = () => { ... window.localStorage ... }` above.
        if re.search(r'const\s+read\s*=\s*\(\)\s*=>\s*\{[^}]*window\.localStorage', src, re.S):
            src = re.sub(
                r'const \[([\w]+), set([\w]+)\] = React\.useState\(read\);',
                lambda m: (
                    f'const [{m.group(1)}, set{m.group(2)}] = React.useState(false);\n'
                    f'  React.useEffect(() => {{ try {{ const v = window.localStorage.getItem(KEY); '
                    f'if (v != null) set{m.group(2)}(v === "1"); }} catch {{}} }}, []);'
                ),
                src
            )

        if src != orig:
            with open(f, 'w') as fh: fh.write(src)
            print(f'patched {f}')
            total += 1
    print(f'\nTotal: {total} files patched')
    print('\nNOTE: useState(read) pattern default is now `false`. Review and flip to `true` if your sidebar should default to collapsed.')


if __name__ == '__main__':
    main()
