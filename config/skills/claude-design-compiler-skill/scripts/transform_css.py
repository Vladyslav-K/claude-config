#!/usr/bin/env python3
"""Phase 1b: Extract CSS from the bundle and scope every selector under a wrapper class.

Parses all <style> blocks from a sample HTML, drops @font-face blocks, scopes every
rule (and rules inside @media) under the given --scope class, and writes a single CSS
file. Also appends a Tailwind-preflight-counteraction block to revert form-element
font properties (see SKILL.md Pattern 8).

Usage:
  python3 transform_css.py --bundle-root public/demo-handoff/ --scope .demo-app --out src/app/demo/_styles/demo.css

After running, manually swap font literals in --font-heading / --font-body to your
production CSS variables, e.g.:
  sed -i.bak "s/'Archivo', /var(--font-archivo), /g" src/app/demo/_styles/demo.css
"""
import argparse, json, re, glob, os


def parse_block_end(text, start):
    depth, i = 0, start
    while i < len(text):
        c = text[i]
        if c == '{': depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0: return i
        i += 1
    return -1


def scope_selectors(css, scope='.demo-app'):
    def transform_sel(sel):
        sel = sel.strip()
        if not sel: return sel
        parts = [p.strip() for p in sel.split(',')]
        out = []
        for p in parts:
            if p == ':root' or p in ('html, body', 'html', 'body'):
                out.append(scope)
            elif p.startswith('html['):
                out.append(scope + p[4:])
            elif p.startswith('html '):
                out.append(scope + ' ' + p[5:])
            elif p.startswith('body '):
                out.append(scope + ' ' + p[5:])
            elif p.startswith('@'):
                out.append(p)
            else:
                out.append(scope + ' ' + p)
        return ', '.join(out)

    def transform(text):
        out, i, n = [], 0, len(text)
        while i < n:
            m = re.match(r'\s+|/\*.*?\*/', text[i:], re.S)
            if m:
                out.append(m.group(0)); i += len(m.group(0)); continue
            if text[i] == '@':
                m2 = re.match(r'@[\w-]+\s*[^;{]*', text[i:])
                if m2:
                    at = m2.group(0); j = i + len(at)
                    if j < n and text[j] == '{':
                        end = parse_block_end(text, j)
                        body = text[j+1:end]
                        if at.startswith('@media'):
                            body = transform(body)
                        out.append(at + '{' + body + '}')
                        i = end + 1; continue
                    elif j < n and text[j] == ';':
                        out.append(at + ';'); i = j + 1; continue
            end = text.find('{', i)
            if end == -1: out.append(text[i:]); break
            sel = text[i:end]
            block_end = parse_block_end(text, end)
            if block_end == -1: out.append(text[i:]); break
            body = text[end+1:block_end]
            out.append(transform_sel(sel) + ' {' + body + '}')
            i = block_end + 1
        return ''.join(out)

    return transform(css)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--bundle-root', required=True)
    ap.add_argument('--scope', default='.demo-app', help='wrapper class (default: .demo-app)')
    ap.add_argument('--out', required=True, help='output CSS path')
    args = ap.parse_args()

    pages = sorted(glob.glob(f'{args.bundle_root.rstrip("/")}/**/*.html', recursive=True))
    if not pages:
        raise SystemExit(f'No .html files under {args.bundle_root}')
    sample = pages[0]

    with open(sample) as f:
        html = f.read()
    template = json.loads(re.search(r'<script type="__bundler/template">\s*\n?([^\n]+)', html).group(1))

    style_blocks = re.findall(r'<style>(.*?)</style>', template, re.S)
    print(f'Found {len(style_blocks)} <style> blocks')

    pieces = []
    for s in style_blocks:
        # drop @font-face
        s = re.sub(r'@font-face\s*\{[^}]*\}\s*', '', s)
        pieces.append(scope_selectors(s, args.scope))
    result = '\n\n'.join(pieces)

    # Append Tailwind preflight counteraction (see SKILL.md Pattern 8)
    result += f'\n\n/* Counteract Tailwind 4 preflight which makes form-element fonts\n'
    result += '   inherit from the parent (16px Archivo). Original handoff bundle ran\n'
    result += '   without Tailwind, so form-elements had UA default font (~13.3px). Revert\n'
    result += '   inside the demo wrapper so they match. Inline font-family still wins via\n'
    result += '   specificity 1000. */\n'
    result += f'{args.scope} button,\n'
    result += f'{args.scope} input,\n'
    result += f'{args.scope} select,\n'
    result += f'{args.scope} optgroup,\n'
    result += f'{args.scope} textarea {{\n'
    result += '  font: revert;\n'
    result += '  letter-spacing: revert;\n'
    result += '  font-feature-settings: revert;\n'
    result += '  font-variation-settings: revert;\n'
    result += '}\n'

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, 'w') as f:
        f.write(result)
    print(f'Wrote {args.out} ({len(result)} chars)')
    print('\nNEXT: swap font literals to production CSS variables, e.g.:')
    print(f"  sed -i.bak \"s/'Archivo', /var(--font-archivo), /g\" {args.out}")
    print(f"  sed -i.bak \"s/'Roobert', /var(--font-roobert), /g\" {args.out}")


if __name__ == '__main__':
    main()
