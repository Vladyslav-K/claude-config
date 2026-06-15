#!/usr/bin/env python3
"""Compare component schemas between two swagger snapshots: new / removed / changed."""

import json
import sys

if len(sys.argv) != 3:
    print('Usage: python3 diff-schemas.py <swagger-old.json> <swagger.json>', file=sys.stderr)
    sys.exit(1)

OLD_PATH = sys.argv[1]
NEW_PATH = sys.argv[2]

with open(OLD_PATH) as f:
    old = json.load(f)
with open(NEW_PATH) as f:
    new = json.load(f)

old_schemas = set(old.get('components', {}).get('schemas', {}).keys())
new_schemas = set(new.get('components', {}).get('schemas', {}).keys())

added = sorted(new_schemas - old_schemas)
removed = sorted(old_schemas - new_schemas)
common = sorted(old_schemas & new_schemas)

print('=== NEW SCHEMAS ===')
for s in added:
    print(f'  {s}')

print()
print('=== REMOVED SCHEMAS ===')
for s in removed:
    print(f'  {s}')

print()
print(f'=== COMMON SCHEMAS: {len(common)} ===')
changed = []
for s in common:
    if json.dumps(old['components']['schemas'][s], sort_keys=True) != json.dumps(new['components']['schemas'][s], sort_keys=True):
        changed.append(s)

print(f'Changed: {len(changed)}')
for s in changed:
    print(f'  {s}')
