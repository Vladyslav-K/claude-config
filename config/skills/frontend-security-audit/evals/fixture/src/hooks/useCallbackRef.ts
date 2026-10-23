// Decoy for auth-callback-unbound: a hook whose name only contains the word is not a route.
// Test fixture for scan.mjs.
export function useCallbackRef<T>(fn: T): T {
  return fn;
}
