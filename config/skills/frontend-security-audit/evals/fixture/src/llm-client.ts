// INTENTIONALLY VULNERABLE — test fixture for scan.mjs. Never copy into a real app.
// The flag runs the SDK in the browser, shipping the API key to every visitor.
import { createClient } from './sdk';

export const llm = createClient({
  dangerouslyAllowBrowser: true,
});
