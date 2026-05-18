#!/usr/bin/env python3
"""Phase 1a: Decode woff2 fonts from a handoff bundle's manifest.

Reads one sample HTML, finds all font/woff2 entries in the manifest,
decodes base64+gzip, and writes them as files. Inspects the @font-face
declarations in the template to map UUIDs to human-readable names where
possible (e.g. archivo-latin.woff2 vs archivo-vietnamese.woff2).

Usage:
  python3 extract_fonts.py --bundle-root public/demo-handoff/ --out src/app/demo/_fonts/

Note:
  Bundle woff2 files are usually NOT variable — they are single-weight subsets.
  Prefer reusing production variable fonts via CSS cascade. See SKILL.md Phase 1a.
"""
import argparse, json, re, base64, gzip, glob, os


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--bundle-root', required=True)
    ap.add_argument('--out', required=True, help='output directory for woff2 files')
    args = ap.parse_args()

    # Use the first .html as the sample
    pages = sorted(glob.glob(f'{args.bundle_root.rstrip("/")}/**/*.html', recursive=True))
    if not pages:
        raise SystemExit(f'No .html files under {args.bundle_root}')
    sample = pages[0]
    print(f'Using sample: {sample}')

    with open(sample) as f:
        html = f.read()
    manifest = json.loads(re.search(r'<script type="__bundler/manifest">\s*\n?([^\n]+)', html).group(1))
    template = json.loads(re.search(r'<script type="__bundler/template">\s*\n?([^\n]+)', html).group(1))

    # Find @font-face blocks → discover UUID → unicode-range comment mapping
    blocks = re.findall(r'(/\*\s*([^*]+?)\s*\*/\s*)?@font-face\s*\{[^}]+url\("([^"]+)"\)[^}]+\}', template, re.S)
    # block: (comment_full, comment_text_or_empty, uuid)
    uuid_to_subset = {}
    for _full, comment, uuid in blocks:
        subset = comment.strip().lower() if comment else 'main'
        if uuid not in uuid_to_subset:
            uuid_to_subset[uuid] = subset

    # Find the font family name (assume single family)
    m = re.search(r"font-family:\s*'([^']+)'", template)
    family = m.group(1).lower() if m else 'font'

    os.makedirs(args.out, exist_ok=True)
    written = 0
    seen_uuids = set()
    for uuid, subset in uuid_to_subset.items():
        if uuid in seen_uuids: continue
        seen_uuids.add(uuid)
        if uuid not in manifest:
            print(f'  missing in manifest: {uuid}'); continue
        entry = manifest[uuid]
        if entry.get('mime') != 'font/woff2':
            continue
        raw = base64.b64decode(entry['data'])
        if entry.get('compressed'):
            raw = gzip.decompress(raw)
        out_file = os.path.join(args.out, f'{family}-{subset}.woff2')
        with open(out_file, 'wb') as f:
            f.write(raw)
        has_fvar = b'fvar' in raw
        print(f'  wrote {out_file} ({len(raw)} bytes, variable={has_fvar})')
        written += 1

    print(f'\nTotal: {written} woff2 files in {args.out}')
    print('\nIMPORTANT: if variable=False for all files, the bundle ships single-weight subsets.')
    print('Consider reusing production variable fonts instead — see SKILL.md Phase 1a.')


if __name__ == '__main__':
    main()
