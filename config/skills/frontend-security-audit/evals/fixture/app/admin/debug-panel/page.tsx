// Decoy for dev-surface: the page is hidden outside development, so it must carry envGated.
// Test fixture for scan.mjs.
'use client';

import { notFound } from 'next/navigation';
import { apiClient } from '../../../src/api/client';

export default function DebugPanelPage() {
  if (process.env.NODE_ENV === 'production') notFound();
  return <button onClick={() => apiClient.delete('/api/dev/seed')}>Wipe seed data</button>;
}
