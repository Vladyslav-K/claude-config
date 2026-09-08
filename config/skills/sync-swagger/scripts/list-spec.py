#!/usr/bin/env python3
"""List every endpoint (grouped by tag) and every component schema of ONE swagger snapshot.

Usage: list-spec.py <swagger.json> [tag]
Meant for full mode, where there is no baseline to diff against and the swagger is too large to read as a file."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from swagger_common import endpoints, load_spec, operation_summary, schema_usage, schemas

if len(sys.argv) not in (2, 3):
    print('Usage: python3 list-spec.py <swagger.json> [tag]', file=sys.stderr)
    sys.exit(1)

spec = load_spec(sys.argv[1])
tag_filter = sys.argv[2] if len(sys.argv) == 3 else None

by_tag = {}
for key, operation in endpoints(spec).items():
    tags = operation.get('tags') or ['(no tag)']
    for tag in tags:
        if tag_filter and tag != tag_filter:
            continue
        by_tag.setdefault(tag, []).append((key, operation))

total = sum(len(items) for items in by_tag.values())
print(f'=== ENDPOINTS ({total}) ===')
for tag in sorted(by_tag):
    print(f'[{tag}]')
    for key, operation in sorted(by_tag[tag]):
        op_id = operation.get('operationId', '-')
        print(f'  {key} | operationId={op_id} | {operation_summary(operation)}')

if tag_filter:
    sys.exit(0)

usage = schema_usage(spec)
all_schemas = schemas(spec)
print()
print(f'=== SCHEMAS ({len(all_schemas)}) ===')
for name in sorted(all_schemas):
    definition = all_schemas[name]
    if 'enum' in definition:
        shape = f'enum[{len(definition["enum"])}]'
    else:
        shape = f'fields={len(definition.get("properties", {}))}'
    entry = usage.get(name, {'endpoints': [], 'schemas': []})
    print(f'  {name} | {shape} | used by {len(entry["endpoints"])} endpoints, {len(entry["schemas"])} schemas')
