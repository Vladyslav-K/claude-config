#!/usr/bin/env python3
"""Compare component schemas between two swagger snapshots: new / removed / changed (field-level) / doc-only,
with "used by" lists so changed schemas can be mapped to the endpoints they affect."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from swagger_common import diff_values, load_spec, same, schema_usage, schemas, strip_doc

if len(sys.argv) != 3:
    print('Usage: python3 diff-schemas.py <swagger-old.json> <swagger.json>', file=sys.stderr)
    sys.exit(1)

old = load_spec(sys.argv[1])
new = load_spec(sys.argv[2])

old_schemas = schemas(old)
new_schemas = schemas(new)

added = sorted(set(new_schemas) - set(old_schemas))
removed = sorted(set(old_schemas) - set(new_schemas))
common = sorted(set(old_schemas) & set(new_schemas))

new_usage = schema_usage(new)
old_usage = schema_usage(old)


def used_by(name, usage):
    entry = usage.get(name, {'endpoints': [], 'schemas': []})
    parts = []
    if entry['endpoints']:
        parts.append('endpoints: ' + ', '.join(entry['endpoints']))
    if entry['schemas']:
        parts.append('schemas: ' + ', '.join(entry['schemas']))
    return ' | '.join(parts) if parts else 'not referenced'


print(f'=== NEW SCHEMAS ({len(added)}) ===')
for name in added:
    fields = list(new_schemas[name].get('properties', {}).keys())
    print(f'  {name} | fields: {", ".join(fields) if fields else "-"}')
    print(f'    used by -> {used_by(name, new_usage)}')

print()
print(f'=== REMOVED SCHEMAS ({len(removed)}) ===')
for name in removed:
    print(f'  {name}')
    print(f'    was used by -> {used_by(name, old_usage)}')

changed = []
doc_only = []
for name in common:
    if same(old_schemas[name], new_schemas[name]):
        continue
    if same(strip_doc(old_schemas[name]), strip_doc(new_schemas[name])):
        doc_only.append(name)
    else:
        changed.append(name)

print()
print(f'=== CHANGED SCHEMAS ({len(changed)} of {len(common)} common) ===')
for name in changed:
    print(f'  {name}')
    for line in diff_values(strip_doc(old_schemas[name]), strip_doc(new_schemas[name])):
        print(f'    {line}')
    print(f'    used by -> {used_by(name, new_usage)}')

print()
print(f'=== DOC-ONLY CHANGES ({len(doc_only)}) === description/example/title only, no code impact')
for name in doc_only:
    print(f'  {name}')
