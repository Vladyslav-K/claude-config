// INTENTIONALLY VULNERABLE — test fixture for scan.mjs. Never copy into a real app.
// The token-ish word lives in the constant's NAME, not in the call-site literal — the
// regression this file guards: identifier-key storage calls must still be flagged.
const ACCESS_TOKEN_KEY = 'access_token';

export function saveAccess(token: string) {
  localStorage.setItem(ACCESS_TOKEN_KEY, token);
}
