// INTENTIONALLY VULNERABLE — test fixture for scan.mjs. Never copy into a real app.
// The code from the URL is exchanged with nothing tying it to the browser that began sign-in.
import { exchangeCode } from '../../../src/sso';

interface SsoCallbackPageProps {
  searchParams: Promise<{ code?: string }>;
}

export default async function SsoCallbackPage({ searchParams }: SsoCallbackPageProps) {
  const { code } = await searchParams;
  const session = await exchangeCode(code ?? '');
  return <p>{session.email}</p>;
}
