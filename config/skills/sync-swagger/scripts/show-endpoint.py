#!/usr/bin/env python3
"""Show old vs new definition of a single endpoint. Run after diff-endpoints.py flags a change."""

import json
import sys

if len(sys.argv) != 5:
    print('Usage: python3 show-endpoint.py <swagger-old.json> <swagger.json> <path> <method>', file=sys.stderr)
    print('Example: python3 show-endpoint.py swagger-old.json swagger.json /api/companies get', file=sys.stderr)
    sys.exit(1)

OLD_PATH = sys.argv[1]
NEW_PATH = sys.argv[2]
TARGET_PATH = sys.argv[3]
TARGET_METHOD = sys.argv[4].lower()

with open(OLD_PATH) as f:
    old = json.load(f)
with open(NEW_PATH) as f:
    new = json.load(f)

old_ep = old.get('paths', {}).get(TARGET_PATH, {}).get(TARGET_METHOD)
new_ep = new.get('paths', {}).get(TARGET_PATH, {}).get(TARGET_METHOD)

print('=== OLD ===')
print(json.dumps(old_ep, indent=2) if old_ep is not None else '(not present in old swagger)')
print()
print('=== NEW ===')
print(json.dumps(new_ep, indent=2) if new_ep is not None else '(not present in new swagger)')
