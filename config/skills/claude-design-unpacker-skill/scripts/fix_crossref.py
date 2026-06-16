#!/usr/bin/env python3
"""Phase 2: Auto-add cross-kit imports for symbols referenced via JSX/call.

In the original bundle, kits put their components on `window` (via
Object.assign(window, ...)) so other kits can use them globally. After port,
those refs are unresolved. This script:

  1. Lists all exported names from every kit under --components.
  2. For each kit, scans for JSX usages (<X>) and function calls (X()) of
     names exported by ANOTHER kit.
  3. Generates a single `import { ... } from './<kit>'` line per source kit
     and inserts it after the React import.

Also handles the special case `window.DomainIcon` (and similar) → bare reference
plus import.

Usage:
  python3 fix_crossref.py --components src/app/demo/_components/
"""
import argparse, re, glob, os
from collections import defaultdict


def kit_path_from_file(file_path, components_root):
    """Return relative module path for import, e.g. './charts' or '../icons'."""
    rel = os.path.relpath(file_path, components_root)
    return './' + rel.replace('.tsx', '').replace(os.sep, '/')


def get_exports(path):
    with open(path) as f: src = f.read()
    fns = re.findall(r'^export function\s+(\w+)', src, re.M)
    consts = re.findall(r'^export const\s+(\w+)', src, re.M)
    return sorted(set(fns) | set(consts))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--components', required=True)
    args = ap.parse_args()

    root = args.components.rstrip('/')
    files = sorted(set(
        glob.glob(f'{root}/**/*.tsx', recursive=True) +
        glob.glob(f'{root}/*.tsx')
    ))

    # Index exports
    file_to_exports = {f: get_exports(f) for f in files}
    symbol_to_files = defaultdict(list)
    for f, exps in file_to_exports.items():
        for e in exps:
            symbol_to_files[e].append(f)

    total = 0
    for target in files:
        with open(target) as fh: src = fh.read()
        orig = src

        # Convert window.X (read) → X for any X exported somewhere
        for sym, source_files in symbol_to_files.items():
            if target in source_files: continue
            if re.search(rf'\bwindow\.{sym}\b', src):
                src = re.sub(rf'\bwindow\.{sym}\b', sym, src)

        # Now figure out what needs importing: any exported symbol from another file
        # that is referenced in this file but not defined locally and not imported.
        local_defs = set(file_to_exports.get(target, []))
        # also locally-defined non-exported
        local_defs |= set(re.findall(r'\bfunction\s+(\w+)\s*\(', src))
        local_defs |= set(re.findall(r'\bconst\s+([A-Z]\w*)\s*=', src))

        # Already-imported names
        imported = set()
        for im in re.finditer(r'^import\s*\{([^}]+)\}\s*from', src, re.M):
            for name in im.group(1).split(','):
                imported.add(name.strip())

        needed = defaultdict(list)  # source_file → [names]
        for sym, source_files in symbol_to_files.items():
            if sym in local_defs or sym in imported: continue
            if target in source_files: continue
            if not (re.search(rf'<{sym}\b', src) or re.search(rf'\b{sym}\s*\(', src) or re.search(rf'\b{sym}\b\.', src)):
                continue
            # Pick first source (could refine: prefer same-persona folder)
            chosen = source_files[0]
            # Refine: if target is in a persona dir, prefer same persona
            target_parts = os.path.relpath(target, root).split(os.sep)
            if len(target_parts) > 1:
                persona_dir = target_parts[0]
                same_persona = [s for s in source_files if os.path.relpath(s, root).startswith(persona_dir + os.sep)]
                if same_persona:
                    chosen = same_persona[0]
            needed[chosen].append(sym)

        # Generate import lines
        new_imports = []
        for source_file, names in needed.items():
            mod = kit_path_from_file(source_file, os.path.dirname(target))
            # Normalize: ensure './' or '../' prefix
            if not (mod.startswith('./') or mod.startswith('../')):
                mod = './' + mod
            new_imports.append(f"import {{ {', '.join(sorted(set(names)))} }} from '{mod}';")

        if new_imports:
            # Insert after React import
            insertion = '\n'.join(new_imports) + '\n'
            src = re.sub(
                r"(import React[^\n]+\n)",
                rf"\1{insertion}",
                src, count=1
            )

        if src != orig:
            with open(target, 'w') as fh: fh.write(src)
            print(f'patched {target}: +{len(new_imports)} import line(s)')
            total += 1

    print(f'\nTotal: {total} files patched')


if __name__ == '__main__':
    main()
