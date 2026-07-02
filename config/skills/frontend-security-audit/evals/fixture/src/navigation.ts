// INTENTIONALLY VULNERABLE — test fixture for scan.mjs. Never copy into a real app.
// react-router v6 useNavigate sink: a query-derived destination is an open redirect.
export function afterLogin(navigate: (to: string) => void, params: URLSearchParams) {
  navigate(params.get('redirect') ?? '/');
}

// react-router v5 / history-lib sink, same class.
export function retryCheckout(history: { push: (to: string) => void }, target: string) {
  history.push(target);
}

// bare document.location assignment — not covered by the window.location patterns.
export function hardRedirect(url: string) {
  document.location = url;
}
