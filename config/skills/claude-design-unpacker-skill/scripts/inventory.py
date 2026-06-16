#!/usr/bin/env python3
"""Phase 0: Inventory unique babel scripts and assets across a handoff bundle.

Reads every .html under --bundle-root, extracts the __bundler/manifest and
__bundler/template scripts, decodes the babel scripts (base64+gzip), and groups
by content hash. Prints a frequency table and a list of asset UUIDs.

Usage:
  python3 inventory.py --bundle-root public/demo-handoff/

Output:
  Stdout: frequency table.
  /tmp/handoff-inventory.json: detailed per-page mapping.
"""
import argparse, json, re, base64, gzip, glob, hashlib
from collections import Counter, defaultdict


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--bundle-root', required=True, help='e.g. public/demo-handoff/')
    ap.add_argument('--out-json', default='/tmp/handoff-inventory.json')
    args = ap.parse_args()

    pages = sorted(glob.glob(f'{args.bundle_root.rstrip("/")}/**/*.html', recursive=True))
    print(f'Found {len(pages)} HTML files under {args.bundle_root}')

    hash_to_text = {}
    hash_to_count = defaultdict(int)
    page_to_hashes = {}
    asset_mimes = Counter()
    asset_uuids = set()

    for path in pages:
        with open(path) as f:
            html = f.read()
        m_mani = re.search(r'<script type="__bundler/manifest">\s*\n?([^\n]+)', html)
        if not m_mani:
            print(f'WARN no manifest: {path}'); continue
        manifest = json.loads(m_mani.group(1))
        for k, entry in manifest.items():
            mime = entry.get('mime', '?')
            asset_mimes[mime] += 1
            asset_uuids.add(k)

        m_tpl = re.search(r'<script type="__bundler/template">\s*\n?([^\n]+)', html)
        if not m_tpl:
            print(f'WARN no template: {path}'); continue
        tpl = json.loads(m_tpl.group(1))

        babels = re.findall(r'<script type="text/babel" src="([^"]+)">', tpl)
        hashes_for_page = []
        for b in babels:
            if b not in manifest: continue
            raw = base64.b64decode(manifest[b]['data'])
            if manifest[b].get('compressed'):
                raw = gzip.decompress(raw)
            text = raw.decode('utf-8', errors='replace')
            h = hashlib.sha1(text.encode()).hexdigest()[:12]
            hash_to_count[h] += 1
            hashes_for_page.append(h)
            if h not in hash_to_text:
                hash_to_text[h] = text
        page_to_hashes[path] = hashes_for_page

    print(f'\n=== Unique babel scripts (by content hash): {len(hash_to_text)} ===')
    for h, n in sorted(hash_to_count.items(), key=lambda x: -x[1]):
        text = hash_to_text[h]
        comps = sorted(set(re.findall(r'\bfunction\s+([A-Z]\w+)\s*\(', text)))
        consts = sorted(set(re.findall(r'\bconst\s+([A-Z_][A-Z0-9_]+)\s*=', text)))
        print(f'  [{h}] used {n}x — {len(text)} chars')
        if comps:
            print(f'    components: {", ".join(comps[:8])}{"..." if len(comps) > 8 else ""}')
        if consts:
            print(f'    consts: {", ".join(consts[:6])}')

    print(f'\n=== Asset mime types ===')
    for m, n in asset_mimes.most_common():
        print(f'  {n:>5}  {m}')
    print(f'\nUnique asset UUIDs: {len(asset_uuids)}')

    with open(args.out_json, 'w') as f:
        json.dump({
            'hash_to_count': hash_to_count,
            'page_to_hashes': page_to_hashes,
            'asset_uuids': sorted(asset_uuids),
            'asset_mimes': dict(asset_mimes),
        }, f, indent=2)
    print(f'\nDetailed inventory: {args.out_json}')


if __name__ == '__main__':
    main()
