// Safe patterns the scanner may still flag as candidates — triage must clear them.
// Test fixture for scan.mjs.
export const columns = [{ apiKey: 'department', label: 'Department' }];

export function goHome(router: { push: (p: string) => void }) {
  router.push('/home');
}

// must NOT be flagged at all: callback-form timers are safe
export function defer(fn: () => void) {
  setTimeout(fn, 300);
  setTimeout(() => fn(), 300);
}
