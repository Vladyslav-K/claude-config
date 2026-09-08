#!/usr/bin/env python3
"""Show the full definition of a single component schema.

Two files (diff mode):  show-schema.py <swagger-old.json> <swagger.json> <SchemaName>  -> OLD and NEW
One file (full mode):   show-schema.py <swagger.json> <SchemaName>                     -> definition only
Documentation-only keys (description, example, title) are stripped; referenced schema names are listed."""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from swagger_common import collect_refs, load_spec, schemas, strip_doc

if len(sys.argv) not in (3, 4):
    print('Usage: python3 show-schema.py <swagger-old.json> <swagger.json> <SchemaName>', file=sys.stderr)
    print('   or: python3 show-schema.py <swagger.json> <SchemaName>', file=sys.stderr)
    print('Example: python3 show-schema.py swagger-old.json swagger.json UserDto', file=sys.stderr)
    sys.exit(1)

spec_paths = sys.argv[1:-1]
schema_name = sys.argv[-1]


def show(label, definition):
    print(f'=== {label} ===')
    if definition is None:
        where = f'{label.lower()} swagger' if label in ('OLD', 'NEW') else 'this swagger'
        print(f'(not present in {where})')
        return
    print(json.dumps(strip_doc(definition), indent=2, ensure_ascii=False))
    refs = sorted(collect_refs(definition))
    print(f'refs: {", ".join(refs) if refs else "-"}')


if len(spec_paths) == 2:
    show('OLD', schemas(load_spec(spec_paths[0])).get(schema_name))
    print()
    show('NEW', schemas(load_spec(spec_paths[1])).get(schema_name))
else:
    show('SCHEMA', schemas(load_spec(spec_paths[0])).get(schema_name))
