#!/usr/bin/env python3
"""Phase 6: Curl every ported page.tsx route and assert HTTP 200.

Requires a dev server running on --base-url. Discovers all page.tsx routes under
--pages-root and curls each. Prints a summary.

Usage:
  python3 smoke_test.py --base-url http://localhost:3000 --pages-root src/app/demo/
"""
import argparse, subprocess, glob


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base-url', default='http://localhost:3000')
    ap.add_argument('--pages-root', required=True, help='e.g. src/app/demo/')
    ap.add_argument('--app-root', default='src/app', help='used to compute URL path')
    args = ap.parse_args()

    pages = sorted(glob.glob(f'{args.pages_root.rstrip("/")}/**/page.tsx', recursive=True))
    print(f'Found {len(pages)} pages\n')

    ok, fail = [], []
    for p in pages:
        # src/app/demo/foo/bar/page.tsx → /demo/foo/bar
        url_path = p.replace(args.app_root.rstrip('/'), '').replace('/page.tsx', '')
        if '[' in url_path:  # dynamic-route page — skip
            continue
        url = args.base_url.rstrip('/') + url_path
        try:
            r = subprocess.run(
                ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', '-m', '15', url],
                capture_output=True, text=True, timeout=30
            )
            code = r.stdout.strip()
            if code == '200':
                ok.append(url_path)
            else:
                fail.append((code, url_path))
        except Exception as e:
            fail.append(('ERR', url_path))

    print(f'OK: {len(ok)} / {len(ok) + len(fail)}')
    print(f'FAIL: {len(fail)}')
    for code, path in fail:
        print(f'  {code}  {path}')

    if fail:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
