// INTENTIONALLY VULNERABLE — test fixture for scan.mjs. Never copy into a real app.
import { exec } from 'node:child_process';

export async function GET(req: Request) {
  const url = new URL(req.url);
  const target = url.searchParams.get('target') ?? '';
  exec(`ping -c 1 ${target}`);
  const res = await fetch(target);
  return Response.json(await res.json());
}
