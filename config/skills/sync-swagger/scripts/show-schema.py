#!/usr/bin/env python3
"""Show old vs new definition of a single component schema. Run after diff-schemas.py flags a change."""

import json
import sys

if len(sys.argv) != 4:
    print('Usage: python3 show-schema.py <swagger-old.json> <swagger.json> <schema-name>', file=sys.stderr)
    print('Example: python3 show-schema.py swagger-old.json swagger.json UserDto', file=sys.stderr)
    sys.exit(1)

OLD_PATH = sys.argv[1]
NEW_PATH = sys.argv[2]
SCHEMA_NAME = sys.argv[3]

with open(OLD_PATH) as f:
    old = json.load(f)
with open(NEW_PATH) as f:
    new = json.load(f)

old_s = old.get('components', {}).get('schemas', {}).get(SCHEMA_NAME)
new_s = new.get('components', {}).get('schemas', {}).get(SCHEMA_NAME)

print('=== OLD ===')
print(json.dumps(old_s, indent=2) if old_s is not None else '(not present in old swagger)')
print()
print('=== NEW ===')
print(json.dumps(new_s, indent=2) if new_s is not None else '(not present in new swagger)')
