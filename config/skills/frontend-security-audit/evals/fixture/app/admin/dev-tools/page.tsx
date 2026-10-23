// INTENTIONALLY VULNERABLE — test fixture for scan.mjs. Never copy into a real app.
// Ships in every build: nothing hides the environment-wide wipe in production.
'use client';

import { apiClient } from '../../../src/api/client';

export default function DevToolsPage() {
  return <button onClick={() => apiClient.delete('/api/dev/seed')}>Wipe seed data</button>;
}
