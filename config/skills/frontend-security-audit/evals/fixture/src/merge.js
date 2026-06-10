// INTENTIONALLY VULNERABLE — test fixture for scan.mjs. Never copy into a real app.
export function deepMerge(target, source) {
  for (const key of Object.keys(source)) {
    if (typeof source[key] === 'object') {
      target[key] = deepMerge(target[key] ?? {}, source[key]);
    } else {
      target[key] = source[key];
    }
  }
  return target;
}

export const EMAIL_RE = /^([a-z0-9]+)+@example\.com$/;

export function scale(i, factor) {
  // decoy: plain arithmetic must NOT be flagged as redos
  const doubled = (i + 1) * 2;
  return (factor + 1) * doubled;
}
