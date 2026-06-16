#!/usr/bin/env python3
"""Phase 4: Port sitemap.html to a React page.

Extracts <style> → scoped CSS file, <body> → JSX (class→className, escape {role}/{path}/{persona}
literal patterns), writes src/app/<demo>/page.tsx that imports the CSS.

Usage:
  python3 build_sitemap.py \\
    --sitemap public/demo-handoff/sitemap.html \\
    --out src/app/demo/page.tsx \\
    --styles-out src/app/demo/_styles/sitemap.css \\
    --scope .sitemap-app
"""
import argparse, re, os


def scope_css(css, scope):
    """Scope every top-level selector under `scope` (same approach as transform_css.py)."""
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


def html_to_jsx(s):
    s = s.replace('class=', 'className=')
    s = re.sub(r'<br\s*/?>', '<br/>', s)
    s = re.sub(r'<hr([^>]*?)\s*/?>', r'<hr\1/>', s)
    # Escape literal JSX-clashing placeholders in documentation text
    for ph in ['{role}', '{path}', '{persona}', '{slug}']:
        s = s.replace(ph, '[' + ph[1:-1] + ']')
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--sitemap', required=True, help='path to sitemap.html')
    ap.add_argument('--out', required=True, help='output page.tsx')
    ap.add_argument('--styles-out', required=True, help='output sitemap.css')
    ap.add_argument('--scope', default='.sitemap-app')
    args = ap.parse_args()

    with open(args.sitemap) as f: html = f.read()
    m_style = re.search(r'<style>(.*?)</style>', html, re.S)
    css = m_style.group(1) if m_style else ''
    m_body = re.search(r'<body>(.*?)</body>', html, re.S)
    body = m_body.group(1).strip() if m_body else ''

    scoped = scope_css(css, args.scope)
    jsx = html_to_jsx(body)

    os.makedirs(os.path.dirname(args.styles_out), exist_ok=True)
    with open(args.styles_out, 'w') as f: f.write(scoped)
    print(f'Wrote {args.styles_out} ({len(scoped)} chars)')

    # Compute relative import path from page.tsx to sitemap.css
    rel = os.path.relpath(args.styles_out, os.path.dirname(args.out))
    page = f"""import '{rel}';

export const metadata = {{
  title: 'Sitemap · Demo',
}};

export default function DemoSitemap() {{
  return (
    <div className="{args.scope.lstrip('.')}">
{jsx}
    </div>
  );
}}
"""
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, 'w') as f: f.write(page)
    print(f'Wrote {args.out} ({len(page)} chars)')


if __name__ == '__main__':
    main()
