// INTENTIONALLY VULNERABLE — test fixture for scan.mjs. Never copy into a real app.
// Angular auto-sanitizes plain innerHTML bindings; the DomSanitizer bypass disables that.
import { DomSanitizer } from '@angular/platform-browser';

export function trustUserHtml(sanitizer: DomSanitizer, userHtml: string) {
  return sanitizer.bypassSecurityTrustHtml(userHtml);
}
