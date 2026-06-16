#!/usr/bin/env python3
"""Phase 2: Fix mangled React hook names (useState2, useEffect2, etc).

Some Babel pipelines mangle hook names with numeric suffixes (relict of how the
demo bundle was originally compiled). Find/replace them back to canonical names.

Usage:
  python3 fix_mangled_hooks.py --components src/app/demo/_components/
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
    hooks = ['useState', 'useEffect', 'useRef', 'useMemo', 'useCallback', 'useLayoutEffect', 'useContext', 'useReducer']
    total = 0
    for f in files:
        with open(f) as fh: src = fh.read()
        new = src
        for h in hooks:
            new = re.sub(rf'\b{h}(\d+)\b', h, new)
        if new != src:
            with open(f, 'w') as fh: fh.write(new)
            print(f'patched {f}')
            total += 1
    print(f'\nTotal: {total} files patched')


if __name__ == '__main__':
    main()
