// INTENTIONALLY VULNERABLE — test fixture for scan.mjs. Never copy into a real app.
// Clears only this tab: other open tabs keep their in-memory session.
let accessToken: string | null = null;

export async function logout() {
  await fetch('/api/auth/logout', { method: 'POST', credentials: 'include' });
  accessToken = null;
}
