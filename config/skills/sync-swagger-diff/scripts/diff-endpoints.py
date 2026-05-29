#!/usr/bin/env python3
"""Compare endpoints between two swagger snapshots: new / removed / changed."""

import json
import sys

if len(sys.argv) != 3:
    print('Usage: python3 diff-endpoints.py <swagger-old.json> <swagger.json>', file=sys.stderr)
    sys.exit(1)

OLD_PATH = sys.argv[1]
NEW_PATH = sys.argv[2]

with open(OLD_PATH) as f:
    old = json.load(f)
with open(NEW_PATH) as f:
    new = json.load(f)


def get_endpoints(spec):
    endpoints = {}
    for path, methods in spec.get('paths', {}).items():
        for method, details in methods.items():
            if method in ('get', 'post', 'put', 'patch', 'delete', 'options', 'head'):
                key = f'{method.upper()} {path}'
                endpoints[key] = details
    return endpoints


old_eps = get_endpoints(old)
new_eps = get_endpoints(new)
old_keys = set(old_eps.keys())
new_keys = set(new_eps.keys())

added = sorted(new_keys - old_keys)
removed = sorted(old_keys - new_keys)
common = sorted(old_keys & new_keys)

print('=== NEW ENDPOINTS ===')
for ep in added:
    tags = new_eps[ep].get('tags', [])
    op_id = new_eps[ep].get('operationId', 'N/A')
    print(f'  {ep} | tags={tags} | operationId={op_id}')

print()
print('=== REMOVED ENDPOINTS ===')
for ep in removed:
    tags = old_eps[ep].get('tags', [])
    op_id = old_eps[ep].get('operationId', 'N/A')
    print(f'  {ep} | tags={tags} | operationId={op_id}')

print()
print(f'=== COMMON ENDPOINTS: {len(common)} ===')
changed = []
for ep in common:
    if json.dumps(old_eps[ep], sort_keys=True) != json.dumps(new_eps[ep], sort_keys=True):
        changed.append(ep)

print(f'Changed: {len(changed)}')
for ep in changed:
    print(f'  {ep}')
