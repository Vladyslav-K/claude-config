#!/usr/bin/env python3
"""Phase 1b: Extract CSS from the bundle and scope every selector under a wrapper class.

A self-contained handoff bundle carries CSS in two layers:
  * GLOBAL design system (tokens, typography, resets, shared component classes) —
    duplicated verbatim inside every page's <style>.
  * PER-PAGE rules (a page's modal, form, special layout, its own @keyframes) —
    present in exactly ONE page's <style>.

This script scans the <style> blocks of EVERY page (not just one sample), counts in
how many pages each rule appears, and splits them:
  * rules present in >= --global-min-pages pages  -> demo.css (scoped, one copy)
  * rules unique to a single page                 -> --per-page-out JSON, keyed by the
    page's html path relative to the pages root. port_all_pages.py reads that JSON and
    injects each page's unique rules as an inline <style> in its page.tsx.

This is the fix for the "ported page looks broken / list collapses into one row"
class of bug: the old version parsed <style> from pages[0] only, so every page's
per-page CSS (e.g. `.ml-prov { display:flex; width:100% }`, `@keyframes mlStepIn`)
was silently dropped and the JSX rendered against undefined classes.

If --per-page-out is omitted, per-page rules are appended to demo.css instead (union
fallback — nothing is lost, but generic class names from different pages share one
global scope). Passing --per-page-out is recommended: it keeps demo.css to the shared
system and isolates each page's rules.

Also drops @font-face blocks (use production fonts via cascade) and appends a
Tailwind-preflight-counteraction block (see SKILL.md Pattern 8).

Usage:
  python3 transform_css.py --bundle-root public/demo-handoff/ --pages-subroot pages/ \
    --scope .demo-app --out src/app/demo/_styles/demo.css \
    --per-page-out src/app/demo/_styles/per_page_css.json

After running, manually swap font literals in --font-heading / --font-body to your
production CSS variables, e.g.:
  python3 -c "p='...demo.css'; s=open(p).read(); open(p,'w').write(s.replace(\"'Archivo', \", 'var(--font-archivo), '))"
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


def drop_font_face(css):
    return re.sub(r'@font-face\s*\{[^}]*\}\s*', '', css)


def split_rules(css):
    """Split CSS into a list of top-level units: `selector { ... }`, `@media { ... }`,
    `@keyframes { ... }`, or `@import ...;`. Whitespace and comments between rules are
    skipped (they carry no CSS)."""
    rules, i, n = [], 0, len(css)
    while i < n:
        m = re.match(r'\s+|/\*.*?\*/', css[i:], re.S)
        if m:
            i += len(m.group(0)); continue
        if css[i] == '@':
            m2 = re.match(r'@[\w-]+\s*[^;{]*', css[i:])
            if m2:
                at = m2.group(0); j = i + len(at)
                if j < n and css[j] == '{':
                    end = parse_block_end(css, j)
                    if end == -1: break
                    rules.append(css[i:end + 1]); i = end + 1; continue
                if j < n and css[j] == ';':
                    rules.append(css[i:j + 1]); i = j + 1; continue
        brace = css.find('{', i)
        if brace == -1: break
        end = parse_block_end(css, brace)
        if end == -1: break
        rules.append(css[i:end + 1]); i = end + 1
    return rules


def normalize(rule):
    return re.sub(r'\s+', ' ', rule).strip()


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
                        # Scope rules inside @media; leave @keyframes from/to frames alone.
                        if at.startswith('@media') or at.startswith('@supports'):
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


def unwrap_jsx_style(block):
    """Some templates already carry React-style <style>{'...'}</style> (a JS string
    literal) instead of plain <style>...</style>. Strip the `{'...'}` / `{"..."}` /
    `` {`...`} `` wrapper so we compare/scope real CSS, not the JS literal."""
    s = block.strip()
    m = re.match(r'^\{\s*([\'"`])(.*)\1\s*\}$', s, re.S)
    if m:
        return m.group(2).replace('\\`', '`').replace("\\'", "'").replace('\\"', '"')
    return block


def extract_style_css(html_path):
    """Return the concatenated <style> CSS for one page (font-face removed)."""
    with open(html_path) as f:
        html = f.read()
    m = re.search(r'<script type="__bundler/template">\s*\n?([^\n]+)', html)
    if not m:
        return ''
    template = json.loads(m.group(1))
    blocks = [unwrap_jsx_style(b) for b in re.findall(r'<style>(.*?)</style>', template, re.S)]
    return drop_font_face('\n'.join(blocks))


TAILWIND_COUNTERACT = """

/* Counteract Tailwind 4 preflight which makes form-element fonts inherit from the
   parent (16px Archivo). The original handoff bundle ran without Tailwind, so
   form-elements had UA default font (~13.3px). Revert inside the demo wrapper so they
   match. Inline font-family still wins via specificity. */
{scope} button,
{scope} input,
{scope} select,
{scope} optgroup,
{scope} textarea {{
  font: revert;
  letter-spacing: revert;
  font-feature-settings: revert;
  font-variation-settings: revert;
}}
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--bundle-root', required=True)
    ap.add_argument('--pages-subroot', default='', help='sub-path inside bundle-root where per-persona HTMLs live (e.g. pages/). Must match port_all_pages.py so per-page CSS keys line up. Empty = scan bundle-root.')
    ap.add_argument('--scope', default='.demo-app', help='wrapper class (default: .demo-app)')
    ap.add_argument('--out', required=True, help='output CSS path (global design system)')
    ap.add_argument('--per-page-out', default=None, help='write page-unique CSS as JSON keyed by html rel-path; feed to port_all_pages.py --per-page-css. If omitted, per-page rules are appended to --out (union fallback).')
    ap.add_argument('--global-min-pages', type=int, default=2, help='a rule appearing in >= this many pages is global -> demo.css; rules unique to one page become per-page (default 2)')
    args = ap.parse_args()

    pages_root = os.path.join(args.bundle_root.rstrip('/'), args.pages_subroot.strip('/'))
    pages = sorted(glob.glob(f'{pages_root.rstrip("/")}/**/*.html', recursive=True))
    if not pages:
        raise SystemExit(f'No .html files under {pages_root}')
    print(f'Scanning <style> across {len(pages)} pages under {pages_root}')

    # Parse every page -> ordered, page-deduped (normalized, raw) rule list.
    page_rules = {}          # rel_key -> [(normalized, raw), ...]
    page_order = []          # rel_keys in scan order (first = de-facto sample)
    norm_pagecount = {}      # normalized -> number of pages containing it
    for html in pages:
        rel = os.path.relpath(html, pages_root).replace('.html', '')
        css = extract_style_css(html)
        if not css:
            continue
        seen, ordered = set(), []
        for raw in split_rules(css):
            nr = normalize(raw)
            if not nr or nr in seen:
                continue
            seen.add(nr); ordered.append((nr, raw))
        page_rules[rel] = ordered
        page_order.append(rel)
        for nr, _ in ordered:
            norm_pagecount[nr] = norm_pagecount.get(nr, 0) + 1

    global_norms = {nr for nr, c in norm_pagecount.items() if c >= args.global_min_pages}

    # Global rules in first-seen order across pages (sample page first).
    global_pieces, added = [], set()
    for rel in page_order:
        for nr, raw in page_rules[rel]:
            if nr in global_norms and nr not in added:
                global_pieces.append(scope_selectors(raw, args.scope))
                added.add(nr)

    # Per-page rules (unique to one page), in that page's order.
    per_page = {}
    for rel in page_order:
        uniq = [raw for nr, raw in page_rules[rel] if norm_pagecount[nr] == 1]
        if uniq:
            per_page[rel] = '\n'.join(scope_selectors(raw, args.scope) for raw in uniq)

    result = '\n\n'.join(global_pieces)

    if args.per_page_out:
        os.makedirs(os.path.dirname(args.per_page_out), exist_ok=True)
        with open(args.per_page_out, 'w') as f:
            json.dump(per_page, f, indent=2)
        print(f'Global rules: {len(global_pieces)} -> {args.out}')
        print(f'Per-page rules: {sum(1 for _ in per_page)} pages -> {args.per_page_out}')
    else:
        # Union fallback: nothing is lost, but per-page rules share the global scope.
        extra = []
        for rel in page_order:
            for nr, raw in page_rules[rel]:
                if nr not in global_norms and nr not in added:
                    extra.append(scope_selectors(raw, args.scope)); added.add(nr)
        if extra:
            result += '\n\n/* Page-unique rules (no --per-page-out given; merged here) */\n'
            result += '\n\n'.join(extra)
        print(f'No --per-page-out: merged ALL {len(global_pieces) + len(extra)} rules into {args.out}')
        print('  (recommended: pass --per-page-out to isolate page-unique rules)')

    result += TAILWIND_COUNTERACT.format(scope=args.scope)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, 'w') as f:
        f.write(result)
    print(f'Wrote {args.out} ({len(result)} chars)')
    print('\nNEXT: swap font literals to production CSS variables in the output CSS.')


if __name__ == '__main__':
    main()
