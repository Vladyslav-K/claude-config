#!/usr/bin/env python3
"""Show the full definition of a single endpoint.

Two files (diff mode):  show-endpoint.py <swagger-old.json> <swagger.json> <path> <method>  -> OLD and NEW
One file (full mode):   show-endpoint.py <swagger.json> <path> <method>                     -> definition only
Documentation-only keys (description, summary, example, tags) are stripped; referenced schema names are listed."""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from swagger_common import collect_refs, load_spec, strip_doc

if len(sys.argv) not in (4, 5):
    print('Usage: python3 show-endpoint.py <swagger-old.json> <swagger.json> <path> <method>', file=sys.stderr)
    print('   or: python3 show-endpoint.py <swagger.json> <path> <method>', file=sys.stderr)
    print('Example: python3 show-endpoint.py swagger-old.json swagger.json /api/companies get', file=sys.stderr)
    sys.exit(1)

spec_paths = sys.argv[1:-2]
target_path = sys.argv[-2]
target_method = sys.argv[-1].lower()


def lookup(spec):
    return spec.get('paths', {}).get(target_path, {}).get(target_method)


def show(label, operation):
    print(f'=== {label} ===')
    if operation is None:
        where = f'{label.lower()} swagger' if label in ('OLD', 'NEW') else 'this swagger'
        print(f'(not present in {where})')
        return
    print(json.dumps(strip_doc(operation), indent=2, ensure_ascii=False))
    refs = sorted(collect_refs(operation))
    print(f'refs: {", ".join(refs) if refs else "-"}')


if len(spec_paths) == 2:
    show('OLD', lookup(load_spec(spec_paths[0])))
    print()
    show('NEW', lookup(load_spec(spec_paths[1])))
else:
    show('ENDPOINT', lookup(load_spec(spec_paths[0])))
