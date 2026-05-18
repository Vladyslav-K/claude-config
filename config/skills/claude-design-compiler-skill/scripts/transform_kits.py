#!/usr/bin/env python3
"""Phase 2: Convert each unique babel kit to a TSX module.

Reads every .html, dedupes babel scripts by content hash, applies minimal
JS→TSX transforms, and writes each kit as a single .tsx file. Prints a
mapping table you should review and rename files in --out.

Usage:
  python3 transform_kits.py --bundle-root public/demo-handoff/ --out src/app/demo/_components/

The output naming is by content hash (e.g. kit-0a251eb0.tsx). After running,
inspect each file's components and consts and rename it semantically, e.g.:
  mv kit-8f5d420d.tsx exec/uikit.tsx
  mv kit-0a251eb0.tsx exec/charts.tsx

A mapping.json is written alongside listing each hash → components/consts/usage count.
"""
import argparse, json, re, base64, gzip, glob, hashlib, os
from collections import defaultdict


def transform_js_to_tsx(text):
    text = re.sub(r'^\s*const\s*\{\s*[^}]+\s*\}\s*=\s*React\s*;\s*$', '', text, flags=re.M)
    text = re.sub(r'^function\s+([A-Za-z_]\w*)\s*\(', r'export function \1(', text, flags=re.M)
    text = re.sub(r'^const\s+([A-Za-z_][\w]*)\s*=', r'export const \1 =', text, flags=re.M)
    head = "'use client';\n/* eslint-disable */\n// @ts-nocheck\nimport React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';\n\n"
    return head + text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--bundle-root', required=True)
    ap.add_argument('--out', required=True, help='output dir for kit TSX files')
    ap.add_argument('--skip-hashes', nargs='*', default=[], help='hashes to skip (e.g. debug overlays)')
    args = ap.parse_args()

    pages = sorted(glob.glob(f'{args.bundle_root.rstrip("/")}/**/*.html', recursive=True))
    hash_to_text = {}
    hash_count = defaultdict(int)
    for path in pages:
        with open(path) as f: html = f.read()
        manifest = json.loads(re.search(r'<script type="__bundler/manifest">\s*\n?([^\n]+)', html).group(1))
        tpl = json.loads(re.search(r'<script type="__bundler/template">\s*\n?([^\n]+)', html).group(1))
        for b in re.findall(r'<script type="text/babel" src="([^"]+)">', tpl):
            if b not in manifest: continue
            raw = base64.b64decode(manifest[b]['data'])
            if manifest[b].get('compressed'): raw = gzip.decompress(raw)
            text = raw.decode('utf-8', errors='replace')
            h = hashlib.sha1(text.encode()).hexdigest()[:12]
            hash_count[h] += 1
            if h not in hash_to_text: hash_to_text[h] = text

    os.makedirs(args.out, exist_ok=True)
    mapping = {}
    for h, text in hash_to_text.items():
        if h in args.skip_hashes:
            print(f'  skip {h}'); continue
        comps = sorted(set(re.findall(r'\bfunction\s+([A-Z]\w+)\s*\(', text)))
        consts = sorted(set(re.findall(r'\bconst\s+([A-Z_][A-Z0-9_]+)\s*=', text)))
        out_path = os.path.join(args.out, f'kit-{h}.tsx')
        with open(out_path, 'w') as f:
            f.write(transform_js_to_tsx(text))
        mapping[h] = {'file': out_path, 'usage': hash_count[h], 'components': comps, 'consts': consts}
        print(f'  {out_path}  ({hash_count[h]}x, {len(text)} chars)')
        if comps: print(f'    components: {", ".join(comps[:8])}')

    with open(os.path.join(args.out, 'mapping.json'), 'w') as f:
        json.dump(mapping, f, indent=2)
    print(f'\nmapping.json written. Rename kit-*.tsx files semantically based on components inside.')


if __name__ == '__main__':
    main()
