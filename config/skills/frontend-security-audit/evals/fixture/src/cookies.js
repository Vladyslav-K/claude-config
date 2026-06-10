// INTENTIONALLY VULNERABLE — test fixture for scan.mjs. Never copy into a real app.
import Cookies from 'js-cookie';

export function persistSession(jwt) {
  Cookies.set('session_token', jwt, { expires: 7 });
  document.cookie = `refresh=${jwt}; path=/`;
}
