#!/usr/bin/env python3
"""Compare endpoints between two swagger snapshots: new / removed / changed (field-level) / doc-only."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from swagger_common import diff_values, endpoints, load_spec, operation_summary, same, strip_doc

if len(sys.argv) != 3:
    print('Usage: python3 diff-endpoints.py <swagger-old.json> <swagger.json>', file=sys.stderr)
    sys.exit(1)

old = load_spec(sys.argv[1])
new = load_spec(sys.argv[2])

old_eps = endpoints(old)
new_eps = endpoints(new)

added = sorted(set(new_eps) - set(old_eps))
removed = sorted(set(old_eps) - set(new_eps))
common = sorted(set(old_eps) & set(new_eps))


def describe(key, operation):
    tags = ','.join(operation.get('tags', [])) or '-'
    op_id = operation.get('operationId', '-')
    return f'  {key} | tags={tags} | operationId={op_id} | {operation_summary(operation)}'


print(f'=== NEW ENDPOINTS ({len(added)}) ===')
for key in added:
    print(describe(key, new_eps[key]))

print()
print(f'=== REMOVED ENDPOINTS ({len(removed)}) ===')
for key in removed:
    print(describe(key, old_eps[key]))

changed = []
doc_only = []
for key in common:
    if same(old_eps[key], new_eps[key]):
        continue
    if same(strip_doc(old_eps[key]), strip_doc(new_eps[key])):
        doc_only.append(key)
    else:
        changed.append(key)

print()
print(f'=== CHANGED ENDPOINTS ({len(changed)} of {len(common)} common) ===')
for key in changed:
    print(f'  {key}')
    for line in diff_values(strip_doc(old_eps[key]), strip_doc(new_eps[key])):
        print(f'    {line}')

print()
print(f'=== DOC-ONLY CHANGES ({len(doc_only)}) === description/summary/example/tags only, no code impact')
for key in doc_only:
    print(f'  {key}')

print()
print('Note: an endpoint whose referenced schema changed is NOT listed here — see diff-schemas.py "used by".')
