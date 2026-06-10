// INTENTIONALLY VULNERABLE — test fixture for scan.mjs. Never copy into a real app.
'use client';

import { useRouter, useSearchParams } from 'next/navigation';

const OPENAI_KEY = 'sk-proj-FAKE000000000000000000000000000000000000';

export default function Page() {
  const router = useRouter();
  const params = useSearchParams();

  const fragment = window.location.hash.slice(1);
  const html = decodeURIComponent(fragment);

  function handleLogin(token: string) {
    localStorage.setItem('auth_token', token);
    router.push(params.get('next') ?? '/');
  }

  function handleRun(expr: string) {
    eval(expr);
  }

  function handleOpenDocs(url: string) {
    window.open(url);
  }

  window.opener?.postMessage({ key: OPENAI_KEY }, '*');
  window.onmessage = (e) => handleRun(e.data);

  return (
    <main>
      <div dangerouslySetInnerHTML={{ __html: html }} />
      <a href="javascript:void(0)">legacy</a>
      <a href="https://example.com" target="_blank">
        external
      </a>
      <button onClick={() => handleLogin('abc')}>login</button>
      <button onClick={() => handleOpenDocs('https://example.com')}>docs</button>
    </main>
  );
}
