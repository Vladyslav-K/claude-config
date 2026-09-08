"""Shared helpers for the sync-swagger scripts: loading specs, stripping documentation-only keys,
field-level diffing and $ref lookups. Not meant to be run directly."""

import json
import re

HTTP_METHODS = ('get', 'post', 'put', 'patch', 'delete', 'options', 'head')

# Keys that never affect generated types/services/hooks. Changes limited to these keys are reported
# separately as "doc-only" so they do not hide real changes.
DOC_KEYS = {'description', 'summary', 'example', 'examples', 'title', 'externalDocs', 'tags', 'deprecated'}

REF_PREFIX = '#/components/schemas/'
MAX_REPR = 160


def load_spec(path):
    with open(path) as f:
        return json.load(f)


def strip_doc(value, parent_key=None):
    """Return a copy of value without documentation-only keys.

    Keys directly under `properties` are field names, so they are never stripped even when a field
    happens to be called `title` or `description`.
    """
    if isinstance(value, dict):
        if parent_key == 'properties':
            return {k: strip_doc(v) for k, v in value.items()}
        return {
            k: strip_doc(v, k)
            for k, v in value.items()
            if k not in DOC_KEYS and not k.startswith('x-')
        }
    if isinstance(value, list):
        return [strip_doc(v) for v in value]
    return value


def compact(value):
    text = json.dumps(value, sort_keys=True, ensure_ascii=False)
    if len(text) > MAX_REPR:
        return text[: MAX_REPR - 3] + '...'
    return text


def diff_values(old, new, path=''):
    """Field-level diff of two JSON values. Returns a list of human-readable lines.

    `+` added, `-` removed, `~` changed. Paths are dotted; list items are compared as sets when the
    list holds scalars (enum, required) and positionally otherwise.
    """
    lines = []
    if isinstance(old, dict) and isinstance(new, dict):
        for key in sorted(set(old) | set(new)):
            child = f'{path}.{key}' if path else key
            if key not in old:
                lines.append(f'+ {child}: {compact(new[key])}')
            elif key not in new:
                lines.append(f'- {child}: {compact(old[key])}')
            else:
                lines.extend(diff_values(old[key], new[key], child))
        return lines

    if isinstance(old, list) and isinstance(new, list):
        # Lists of named objects (parameters, servers) are compared by name, not by position
        old_named = keyed_by_name(old)
        new_named = keyed_by_name(new)
        if old_named is not None and new_named is not None:
            return diff_values(old_named, new_named, path)
        scalars = all(not isinstance(v, (dict, list)) for v in old + new)
        if scalars:
            added = [v for v in new if v not in old]
            removed = [v for v in old if v not in new]
            if added:
                lines.append(f'+ {path}: added {compact(added)}')
            if removed:
                lines.append(f'- {path}: removed {compact(removed)}')
            return lines
        if len(old) != len(new):
            lines.append(f'~ {path}: list length {len(old)} -> {len(new)}')
        for index, (o, n) in enumerate(zip(old, new)):
            lines.extend(diff_values(o, n, f'{path}[{index}]'))
        return lines

    if old != new:
        lines.append(f'~ {path}: {compact(old)} -> {compact(new)}')
    return lines


def keyed_by_name(items):
    """Turn [{"name": "id", "in": "path", ...}] into {"path:id": {...}}; None when items are not all named dicts."""
    if not items or not all(isinstance(v, dict) and 'name' in v for v in items):
        return None
    keyed = {}
    for item in items:
        key = f"{item['in']}:{item['name']}" if 'in' in item else str(item['name'])
        keyed[key] = {k: v for k, v in item.items() if k not in ('name', 'in')}
    return keyed


def same(old, new):
    return json.dumps(old, sort_keys=True) == json.dumps(new, sort_keys=True)


def endpoints(spec):
    """Return {"GET /path": operation} for every operation in the spec."""
    result = {}
    for path, methods in spec.get('paths', {}).items():
        if not isinstance(methods, dict):
            continue
        for method, operation in methods.items():
            if method in HTTP_METHODS:
                result[f'{method.upper()} {path}'] = operation
    return result


def schemas(spec):
    return spec.get('components', {}).get('schemas', {})


def collect_refs(value, found=None):
    """Collect names of every `#/components/schemas/<Name>` reference inside value."""
    if found is None:
        found = set()
    if isinstance(value, dict):
        ref = value.get('$ref')
        if isinstance(ref, str) and ref.startswith(REF_PREFIX):
            found.add(ref[len(REF_PREFIX):])
        for v in value.values():
            collect_refs(v, found)
    elif isinstance(value, list):
        for v in value:
            collect_refs(v, found)
    return found


def schema_usage(spec):
    """Return {schema_name: {"endpoints": [...], "schemas": [...]}} — who references each schema."""
    usage = {}

    def bucket(name):
        return usage.setdefault(name, {'endpoints': [], 'schemas': []})

    for key, operation in endpoints(spec).items():
        for name in sorted(collect_refs(operation)):
            bucket(name)['endpoints'].append(key)

    for owner, definition in schemas(spec).items():
        for name in sorted(collect_refs(definition)):
            if name != owner:
                bucket(name)['schemas'].append(owner)

    return usage


def ref_name(value):
    """Short label for a schema object: the referenced name, `Name[]` for arrays, or the raw type."""
    if not isinstance(value, dict):
        return '?'
    ref = value.get('$ref')
    if isinstance(ref, str):
        return ref[len(REF_PREFIX):] if ref.startswith(REF_PREFIX) else ref
    if value.get('type') == 'array':
        return f"{ref_name(value.get('items', {}))}[]"
    for combinator in ('allOf', 'oneOf', 'anyOf'):
        if combinator in value:
            return f"{combinator}({', '.join(ref_name(v) for v in value[combinator])})"
    return value.get('type', 'object')


def first_json_schema(content):
    """Pick the schema from a `content` map, preferring application/json."""
    if not isinstance(content, dict) or not content:
        return None
    media = content.get('application/json') or next(iter(content.values()))
    return media.get('schema') if isinstance(media, dict) else None


def operation_summary(operation):
    """One-line request/response summary: `req: X | res: 200->Y, 201->Z`."""
    parts = []
    body = first_json_schema(operation.get('requestBody', {}).get('content'))
    if body is not None:
        parts.append(f'req: {ref_name(body)}')
    responses = []
    for code, response in sorted(operation.get('responses', {}).items()):
        if not re.match(r'^2\d\d$', str(code)):
            continue
        schema = first_json_schema(response.get('content')) if isinstance(response, dict) else None
        responses.append(f'{code}->{ref_name(schema) if schema is not None else "void"}')
    if responses:
        parts.append(f"res: {', '.join(responses)}")
    params = [p.get('name') for p in operation.get('parameters', []) if isinstance(p, dict)]
    if params:
        parts.append(f"params: {', '.join(str(p) for p in params)}")
    return ' | '.join(parts)
