// Safe patterns the scanner may still flag as candidates — triage must clear them.
// Test fixture for scan.mjs.
export const columns = [{ apiKey: 'department', label: 'Department' }];

export function goHome(router: { push: (p: string) => void }) {
  router.push('/home');
}

// must classify as argKind 'literal': a ternary of two plain string literals is constant
export function goToArea(router: { push: (p: string) => void }, isAdmin: boolean) {
  router.push(isAdmin ? '/admin' : '/profile');
}

// must classify as argKind 'template': bare `pathname` is the current internal path
export function reload(router: { push: (p: string) => void }, pathname: string) {
  router.push(pathname);
}

// must NOT be flagged at all: callback-form timers are safe
export function defer(fn: () => void) {
  setTimeout(fn, 300);
  setTimeout(() => fn(), 300);
}
