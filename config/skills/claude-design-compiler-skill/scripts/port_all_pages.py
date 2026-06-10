#!/usr/bin/env python3
"""Phase 3: Port every handoff HTML to a Next.js page.tsx.

For each .html under --bundle-root:
  1. Extract the inline <script type="text/babel"> (page-specific App + data)
  2. Scan for JSX components and identifier usages
  3. Resolve each unresolved identifier against exports from --components
  4. Emit import statements per source kit
  5. Rewrite internal .html links: resolve relatively, drop .html, prefix --route-prefix
  6. Strip ReactDOM.createRoot(...).render(...) — replace with default export
  7. Inject noop stubs for skipped names (e.g. TweaksPanel)
  8. Write to src/app/<route-prefix>/<persona>/<slug>/page.tsx

Usage:
  python3 port_all_pages.py \\
    --bundle-root public/demo-handoff/ \\
    --pages-subroot pages/ \\
    --components src/app/demo/_components/ \\
    --out-root src/app/demo/ \\
    --route-prefix /demo/ \\
    --skip-names TweaksPanel TweakSection TweakSlider TweakText useTweaks
"""
import argparse, json, re, os, glob


def get_exports(path):
    with open(path) as f: src = f.read()
    fns = re.findall(r'^export function\s+(\w+)', src, re.M)
    consts = re.findall(r'^export const\s+(\w+)', src, re.M)
    return sorted(set(fns) | set(consts))


def kit_label(kit_file, components_root):
    """Return path like 'exec/uikit' or 'icons' for import."""
    rel = os.path.relpath(kit_file, components_root).replace('.tsx', '')
    return rel.replace(os.sep, '/')


def extract_app_code(html_path):
    with open(html_path) as f: html = f.read()
    m = re.search(r'<script type="__bundler/template">\s*\n?([^\n]+)', html)
    if not m: return ''
    tpl = json.loads(m.group(1))
    inline = re.findall(r'<script type="text/babel"(?![^>]*\bsrc=)[^>]*>(.*?)</script>', tpl, re.S)
    return inline[-1] if inline else ''


def esc_template_literal(s):
    """Escape a CSS string so it is safe inside a JS template literal."""
    return s.replace('\\', '\\\\').replace('`', '\\`').replace('${', '\\${')


def default_export_block(per_page_css):
    """Emit the DemoPage default export. When the page has page-unique CSS, wrap <App/>
    in a fragment carrying an inline <style> — this covers every render state of App
    (early returns, sub-views) with one definition, the same shape used by edit-company."""
    if per_page_css and per_page_css.strip():
        css = esc_template_literal(per_page_css.strip())
        return (
            "\n\nexport default function DemoPage() {\n"
            "  return (\n"
            "    <>\n"
            "      <style>{`\n" + css + "\n`}</style>\n"
            "      <App />\n"
            "    </>\n"
            "  );\n"
            "}\n"
        )
    return "\n\nexport default function DemoPage() { return <App/>; }\n"


def port_page(html_path, persona, slug, kits, skip_names, route_prefix, out_path, components_root, components_import_root, pages_subroot, per_page_css=''):
    code = extract_app_code(html_path)
    if not code:
        return f'SKIP {html_path}: no code'

    used = sorted(set(re.findall(r'<([A-Z]\w+)', code)))
    locally = set(re.findall(r'\bfunction\s+([A-Z]\w+)\s*\(', code))
    locally |= set(re.findall(r'\bconst\s+([A-Z][A-Z0-9_]*)\s*=', code))
    locally |= set(re.findall(r'\bconst\s+([A-Z]\w+)\s*=\s*\(', code))

    persona_dir = persona  # exec or admin
    persona_alias = 'exec' if persona == 'executive' else persona

    imports = {}  # source_kit_path → [names]
    skip_used = set()

    # JSX components
    for name in used:
        if name in locally: continue
        if name in skip_names:
            skip_used.add(name); continue
        candidates = [k for k, exps in kits.items() if name in exps]
        if not candidates: continue
        # Prefer persona-specific
        chosen = None
        for c in candidates:
            label = kit_label(c, components_root)
            if label.startswith(persona_alias + '/'):
                chosen = c; break
        if not chosen: chosen = candidates[0]
        imports.setdefault(chosen, []).append(name)

    # ANY-reference usages of exported names (for lowercase helpers like iconFor and constants like COMPARE_OPTIONS)
    for kit_file, exps in kits.items():
        for name in exps:
            if name in locally or name in skip_names: continue
            already = any(name in v for v in imports.values())
            if already: continue
            if not re.search(rf'\b{re.escape(name)}\b', code): continue
            label = kit_label(kit_file, components_root)
            if label.startswith(persona_alias + '/') or '/' not in label:
                imports.setdefault(kit_file, []).append(name)

    # Build import lines
    import_lines = []
    for kit_file in sorted(imports):
        names = sorted(set(imports[kit_file]))
        label = kit_label(kit_file, components_root)
        import_lines.append(f"import {{ {', '.join(names)} }} from '{components_import_root}/{label}';")

    # Hook-style references for skipped names
    hooks_used = set()
    for name in skip_names:
        if re.search(rf'\b{name}\s*\(', code) and not re.search(rf'<{name}\b', code):
            hooks_used.add(name)

    # noop stubs for skipped names
    stubs = ''
    components_skipped = sorted(skip_used)
    if components_skipped or hooks_used:
        stubs = '\n// Debug overlay components — disabled in production demo\n'
        for n in components_skipped:
            stubs += f'const {n} = (_: any) => null;\n'
        for h in sorted(hooks_used):
            stubs += f'const {h} = (defaults: any) => [defaults, (_: any) => {{}}];\n'

    # Rewrite .html links
    def replace_href(m):
        url = m.group(1)
        rel = html_path[len(args.bundle_root.rstrip('/'))+1:]
        if pages_subroot and rel.startswith(pages_subroot):
            rel = rel[len(pages_subroot):].lstrip('/')
        rel = rel.rsplit('/', 1)[0]
        if url.startswith('./'):
            target = rel + '/' + url[2:]
        elif url.startswith('../'):
            parts = rel.split('/')
            tmp = url
            while tmp.startswith('../'):
                parts = parts[:-1]; tmp = tmp[3:]
            target = '/'.join(parts + [tmp])
        else:
            target = rel + '/' + url
        target = target.replace('.html', '').rstrip('/')
        quote = m.group(0)[0]
        return f"{quote}{route_prefix.rstrip('/')}/{target}{quote}"

    code = re.sub(r'["\'](\.\.?\/[^"\']*\.html)["\']', replace_href, code)
    code = re.sub(r"ReactDOM\.createRoot\([^)]+\)\.render\(<App\s*/>\);\s*", "", code)
    code = re.sub(r"ReactDOM\.render\(<App\s*/>,\s*[^)]+\);\s*", "", code)
    code = re.sub(r'^\s*const\s*\{\s*[^}]+\s*\}\s*=\s*React\s*;\s*$', '', code, flags=re.M)

    warn = ''
    if re.search(r'\bfunction\s+App\s*\(', code):
        code += default_export_block(per_page_css)
    elif per_page_css and per_page_css.strip():
        warn = ' [WARN: page-unique CSS not injected — no `function App`; add the <style> manually]'

    parts = [
        "'use client';",
        "/* eslint-disable */",
        "// @ts-nocheck",
        "",
        "import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';",
    ]
    parts.extend(import_lines)
    parts.append('')
    parts.append(stubs)
    parts.append(code.strip())
    parts.append('')

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w') as f:
        f.write('\n'.join(parts))
    return f'OK {out_path}{warn}'


def main():
    global args
    ap = argparse.ArgumentParser()
    ap.add_argument('--bundle-root', required=True)
    ap.add_argument('--pages-subroot', default='pages/', help='path inside bundle-root where per-persona HTMLs live')
    ap.add_argument('--components', required=True, help='_components root')
    ap.add_argument('--components-import-root', default='@/app/demo/_components', help='absolute import root for kit imports')
    ap.add_argument('--out-root', required=True, help='target src/app/<demo>/')
    ap.add_argument('--route-prefix', default='/demo/', help='URL prefix (default /demo/)')
    ap.add_argument('--skip-names', nargs='*', default=['TweaksPanel','TweakSection','TweakSlider','TweakText','TweakRow','TweakColor','TweakNumber','TweakRadio','TweakSelect','TweakButton','TweakToggle','useTweaks'])
    ap.add_argument('--per-page-css', default=None, help='JSON produced by transform_css.py --per-page-out: page-unique CSS keyed by html rel-path. Each page gets its rules injected as an inline <style>.')
    args = ap.parse_args()

    per_page_css = {}
    if args.per_page_css:
        with open(args.per_page_css) as f:
            per_page_css = json.load(f)
        print(f'Loaded page-unique CSS for {len(per_page_css)} pages\n')

    # Index kit exports
    kit_files = sorted(set(
        glob.glob(f'{args.components.rstrip("/")}/**/*.tsx', recursive=True) +
        glob.glob(f'{args.components.rstrip("/")}/*.tsx')
    ))
    kits = {f: get_exports(f) for f in kit_files}

    pages_root = os.path.join(args.bundle_root.rstrip('/'), args.pages_subroot.strip('/'))
    htmls = sorted(glob.glob(f'{pages_root}/**/*.html', recursive=True))
    print(f'Porting {len(htmls)} pages from {pages_root}\n')

    for html in htmls:
        rel = os.path.relpath(html, pages_root).replace('.html', '')
        parts = rel.split(os.sep)
        persona = parts[0]
        slug = '/'.join(parts[1:])
        out_path = os.path.join(args.out_root.rstrip('/'), persona, slug, 'page.tsx')
        msg = port_page(html, persona, slug, kits, set(args.skip_names),
                        args.route_prefix, out_path, args.components,
                        args.components_import_root, args.pages_subroot.strip('/'),
                        per_page_css.get(rel, ''))
        print(f'  {msg}')


if __name__ == '__main__':
    main()
