#!/usr/bin/env python3
"""Phase 2: Rewrite the bundle's route helpers to Next.js semantics.

The bundle's _routePrefix() reads window.location.pathname to figure out depth
and _buildRoutes() returns URLs ending in .html. Both must change for Next:
  - _routePrefix → return hardcoded "/<demo>/<persona>/"
  - _buildRoutes r-helper → strip .html
  - readPersona → read from pathname instead of ?persona= query
  - withPersona → noop (persona is in pathname now)
  - drop window.SITE_ROUTES / window.buildRoutes (SSR-unsafe)

Usage:
  python3 patch_routes.py --file src/app/demo/_components/exec/uikit.tsx --route-prefix /demo/executive/ --persona-code exec
  python3 patch_routes.py --file src/app/demo/_components/admin/uikit.tsx --route-prefix /demo/admin/ --persona-code admin
"""
import argparse, re


def patch(path, route_prefix, persona_code):
    with open(path) as f: src = f.read()

    # 1) _routePrefix → hardcoded
    src = re.sub(
        r'export function _routePrefix\(\) \{[^}]*\}',
        f'export function _routePrefix() {{ return "{route_prefix}"; }}',
        src, flags=re.S
    )

    # 2) Strip .html in r-helper
    src = src.replace(
        'const r = (rel) => p + rel;',
        'const r = (rel) => (p + rel).replace(/\\.html$/, "");'
    )

    # 3) Drop window.SITE_ROUTES / window.buildRoutes assigns (SSR-unsafe)
    src = re.sub(r'^\s*window\.SITE_ROUTES\s*=.*$', '', src, flags=re.M)
    src = re.sub(r'^\s*window\.buildRoutes\s*=.*$', '', src, flags=re.M)

    # 4) readPersona reads from pathname
    persona_pattern = '|'.join(['executive', 'admin', 'hr', 'manager'])
    src = re.sub(
        r'export function readPersona\(\) \{.*?\n\}',
        f'''export function readPersona() {{
  if (typeof window === "undefined") return "{persona_code}";
  const m = window.location.pathname.match(/\\/demo\\/({persona_pattern})\\b/);
  if (!m) return "{persona_code}";
  const persona = m[1];
  return persona === "executive" ? "exec" : persona;
}}''',
        src, flags=re.S
    )

    # 5) withPersona — noop (persona is in pathname now)
    src = re.sub(
        r'export function withPersona\([^)]*\) \{.*?\n\}',
        'export function withPersona(href) { return href; }',
        src, flags=re.S
    )

    with open(path, 'w') as f: f.write(src)
    print(f'patched {path} → route_prefix={route_prefix}, persona_code={persona_code}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--file', required=True, help='uikit.tsx file to patch')
    ap.add_argument('--route-prefix', required=True, help='e.g. /demo/executive/')
    ap.add_argument('--persona-code', required=True, help='e.g. exec, admin')
    args = ap.parse_args()
    patch(args.file, args.route_prefix, args.persona_code)


if __name__ == '__main__':
    main()
