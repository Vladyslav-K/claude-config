#!/usr/bin/env node
// Frontend security scanner: a grep-first candidate finder.
//
// It runs a battery of ripgrep patterns across a codebase and emits a compact,
// categorized list of CANDIDATE locations (file:line + the matched line). It does
// NOT confirm vulnerabilities — grep over-matches by design. A human or an LLM
// triages the output against references/vulnerability-catalog.md to separate true
// positives from false positives.
//
// Why a script: the same ~50 patterns run on every audit. Running them as code is
// deterministic, finishes in seconds even on 200k+ LOC, and costs zero model
// context. The model only spends tokens on triage and fixes, where judgment matters.
//
// Usage:
//   node scan.mjs [root] [--out findings.json] [--exclude <glob>]... [--only <cat>] [--git-history] [--quiet]
//
// Defaults: root = "." , out = "<root>/.security-audit/findings.json"
// Requires: ripgrep (`rg`) on PATH. Install: `brew install ripgrep` / `apt install ripgrep`.
//
// Besides the rg categories it runs deterministic project checks for "absence" and logic
// findings (headers-missing, env-tracked, auth-callback-unbound, logout-cross-tab, dev-surface)
// and tags findings with triage accelerators: `argKind` on open-redirect, `likelyFalsePositive`
// on low-entropy secrets, `likelySanitized` on HTML sinks with a same-line sanitizer call,
// `likelyEncoded` on API paths with a same-line encoder, `envGated` on dev surfaces,
// `likelyHandled` on cross-tab logout, `alsoIn` when one line trips several categories.
// `--git-history` adds secrets-git-history: the secret patterns over every commit on every ref.

import { spawn, spawnSync } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { basename, dirname, relative, resolve, join } from 'node:path';

// iac-risk runs only on infrastructure code: IaC-named directories, Terraform/Docker/CI files,
// and every directory that holds a cdk.json / Pulumi.yaml / serverless.yml / *.tf marker.
const IAC_DIR =
  /(^|\/)(infra|infrastructure|iac|cdk|terraform|pulumi|deploy|deployment|\.github\/workflows|\.circleci)\//i;
const IAC_FILE =
  /(^|\/)(Dockerfile[^/]*|[^/]+\.dockerfile|docker-compose[^/]*\.ya?ml|serverless\.ya?ml|\.gitlab-ci\.ya?ml|[^/]+\.(tf|tfvars|hcl))$/i;
const IAC_MARKER_GLOBS = ['cdk.json', 'Pulumi.y*ml', 'serverless.y*ml', '*.tf'];
// Terraform, Docker and shell files carry IaC but sit outside the frontend globs.
const IAC_EXTRA_GLOBS = ['*.{tf,tfvars,hcl,sh}', 'Dockerfile*', '*.dockerfile'];

// Each category is a cluster of related patterns plus a default severity and a one-line
// rationale. Patterns use Rust regex syntax (ripgrep) — NO lookahead/lookbehind/backrefs.
// Over-matching is intentional and acceptable; triage narrows it down.
const CATEGORIES = [
  {
    id: 'xss-dangerous-html',
    severity: 'high',
    why: 'Raw HTML insertion. If the value is user-controlled and unsanitized, this is stored/reflected XSS.',
    patterns: [
      'dangerouslySetInnerHTML',
      '\\.innerHTML\\s*[+]?=',
      '\\.outerHTML\\s*=',
      'insertAdjacentHTML\\s*\\(',
      'document\\.write(ln)?\\s*\\(',
      '\\sv-html\\s*=',
      '\\{@html\\b',
      '\\[innerHTML\\]\\s*=',
      // iframe srcdoc/srcDoc renders the given string as a full HTML document.
      '(?i)srcdoc\\s*[=:]',
      // Angular's DomSanitizer escape hatch — plain [innerHTML] is auto-sanitized by
      // Angular, so the bypass calls are where Angular XSS actually lives.
      'bypassSecurityTrust',
    ],
  },
  {
    id: 'xss-code-exec',
    severity: 'high',
    why: 'Dynamic code execution. With any untrusted input this is direct code injection.',
    patterns: [
      '\\beval\\s*\\(',
      'new\\s+Function\\s*\\(',
      'setTimeout\\s*\\(\\s*[\'"`]',
      'setInterval\\s*\\(\\s*[\'"`]',
      '\\bFunction\\s*\\(\\s*[\'"`]',
    ],
  },
  {
    id: 'xss-url-protocol',
    severity: 'medium',
    why: 'javascript:/data: URLs in href/src run script. Dangerous when the URL comes from user input.',
    patterns: [
      '[\'"`]\\s*javascript:',
      'href\\s*[=:]\\s*[`\'"]?\\s*javascript:',
      'data:text/html',
    ],
  },
  {
    id: 'dom-xss-source',
    severity: 'medium',
    why: 'Classic DOM-XSS sources. Risk only if the value flows into a sink (innerHTML, eval, href, etc.).',
    patterns: [
      'location\\.hash',
      'location\\.search',
      'document\\.referrer',
      'window\\.name',
      'document\\.cookie',
      'decodeURIComponent\\s*\\(',
    ],
  },
  {
    id: 'secrets-env-public',
    severity: 'critical',
    why: 'Client-exposed env vars (NEXT_PUBLIC_/VITE_/REACT_APP_) ship in the JS bundle. Never put secrets here.',
    patterns: [
      '(?i)NEXT_PUBLIC_[A-Z0-9_]*(KEY|TOKEN|SECRET|PASSWORD|PRIVATE|CREDENTIAL|AUTH)',
      '(?i)VITE_[A-Z0-9_]*(KEY|TOKEN|SECRET|PASSWORD|PRIVATE|CREDENTIAL)',
      '(?i)REACT_APP_[A-Z0-9_]*(KEY|TOKEN|SECRET|PASSWORD|PRIVATE|CREDENTIAL)',
    ],
  },
  {
    id: 'secrets-hardcoded',
    severity: 'critical',
    why: 'Hardcoded credentials in client code are visible to everyone. Rotate immediately if real.',
    patterns: [
      'AKIA[0-9A-Z]{16}',
      'AIza[0-9A-Za-z_\\-]{35}',
      'ghp_[0-9A-Za-z]{36}',
      'gho_[0-9A-Za-z]{36}',
      'xox[abprs]-[0-9A-Za-z-]{10,}',
      '(sk|rk)_live_[0-9A-Za-z]{16,}',
      '\\bsk-(proj|ant|or)-[A-Za-z0-9_-]{20,}',
      '\\bsk-[A-Za-z0-9]{40,}',
      'github_pat_[0-9A-Za-z_]{20,}',
      'glpat-[0-9A-Za-z_-]{20,}',
      'npm_[A-Za-z0-9]{30,}',
      '-----BEGIN [A-Z ]*PRIVATE KEY-----',
      'eyJ[A-Za-z0-9_-]{8,}\\.eyJ[A-Za-z0-9_-]{8,}\\.[A-Za-z0-9_-]{8,}',
      '(?i)(api[_-]?key|apikey|secret|client[_-]?secret|password|passwd|access[_-]?token|auth[_-]?token|private[_-]?key)\\s*[:=]\\s*[\'"][^\'"\\s$]{8,}[\'"]',
    ],
  },
  {
    id: 'sdk-browser-key',
    severity: 'critical',
    why: 'dangerouslyAllowBrowser exposes the API key to every visitor. Calls must be proxied server-side.',
    patterns: ['dangerouslyAllowBrowser'],
  },
  {
    id: 'token-storage',
    severity: 'high',
    why: 'Session tokens in localStorage/sessionStorage are readable by any XSS. Prefer httpOnly+Secure cookies.',
    patterns: [
      '(?i)(local|session)Storage\\.setItem\\s*\\(\\s*[\'"`][^\'"`]*(token|auth|jwt|session|secret|credential|refresh|password)',
      '(?i)(local|session)Storage\\.getItem\\s*\\(\\s*[\'"`][^\'"`]*(token|auth|jwt|session|refresh)',
      // Key passed as an identifier, not a literal: localStorage.setItem(ACCESS_TOKEN_KEY, …).
      // Real-world miss: the token-ish word lives in the constant's NAME, one line away.
      '(?i)(local|session)Storage\\.(getItem|setItem|removeItem)\\s*\\(\\s*[A-Za-z_$][A-Za-z0-9_$]*(token|auth|jwt|session|refresh|secret|credential)',
    ],
  },
  {
    id: 'open-redirect',
    severity: 'high',
    why: 'Navigation sinks. If the destination is user-controlled without an allow-list, this is an open redirect.',
    patterns: [
      'window\\.location\\s*=',
      'window\\.location\\.href\\s*=',
      'document\\.location\\s*=',
      'location\\.href\\s*=',
      'location\\.(assign|replace)\\s*\\(',
      'router\\.(push|replace)\\s*\\(',
      // react-router: v6 useNavigate()'s navigate(…) and v5 history.push/replace(…).
      // \bnavigate also catches Angular's router.navigate(…).
      '\\bnavigate\\s*\\(',
      'history\\.(push|replace)\\s*\\(',
      '\\bredirect\\s*\\(',
    ],
  },
  {
    id: 'tabnabbing',
    severity: 'medium',
    why: 'target="_blank" / window.open without rel="noopener noreferrer" lets the new page hijack the opener.',
    patterns: [
      'target\\s*[=:]\\s*[`\'"]_blank[`\'"]',
      'window\\.open\\s*\\(',
    ],
  },
  {
    id: 'postmessage-cors',
    severity: 'high',
    why: 'postMessage with "*" target or a message listener without origin checks leaks data / accepts spoofed input.',
    patterns: [
      'postMessage\\s*\\(',
      'addEventListener\\s*\\(\\s*[\'"`]message[\'"`]',
      '\\.onmessage\\s*=',
      'Access-Control-Allow-Origin',
    ],
  },
  {
    id: 'prototype-pollution',
    severity: 'high',
    why: 'Writing untrusted keys into __proto__/constructor.prototype or via home-grown deep-merge pollutes Object.',
    patterns: [
      '__proto__',
      'constructor\\s*\\[\\s*[\'"`]prototype',
      '\\.prototype\\s*\\[',
      '(?i)function\\s+(deep)?(merge|extend|assign|set)\\b',
      '(?i)(const|let|var)\\s+(deep)?(merge|extend|setin)\\s*=',
    ],
  },
  {
    id: 'redos',
    severity: 'medium',
    why: 'Nested/overlapping quantifiers on user input can hang the thread (catastrophic backtracking).',
    // Anchored to regex literals /…/ and new RegExp('…') so plain arithmetic like
    // `(a + 1) * b` doesn't flood triage. Dynamically-assembled RegExp is out of reach.
    patterns: [
      '/[^/\\n\\t ]*\\([^)]*[+*][^)]*\\)[+*][^/\\n]*/',
      '/[^/\\n\\t ]*\\([^)|]+\\|[^)]+\\)[+*][^/\\n]*/',
      'new\\s+RegExp\\s*\\(\\s*[\'"`][^\'"`]*\\([^)]*[+*][^)]*\\)[+*]',
    ],
  },
  {
    id: 'server-injection',
    severity: 'critical',
    why: 'Command/SQL/NoSQL/path injection in Next.js route handlers, server actions, or middleware.',
    patterns: [
      '\\bchild_process\\b',
      '\\bexec(Sync)?\\s*\\(',
      '\\bspawn(Sync)?\\s*\\(',
      '(?i)(query|sql|raw)\\s*\\(\\s*[`\'"][^`\'"]*\\$\\{',
      '\\$where',
      'fs\\.(readFile|writeFile|unlink|readFileSync|writeFileSync|createReadStream)\\s*\\(',
    ],
  },
  {
    id: 'ssrf',
    severity: 'high',
    why: 'Server-side fetch/axios with a user-controlled URL can reach internal services (SSRF).',
    patterns: [
      'fetch\\s*\\(\\s*[a-zA-Z_$][\\w.$]*\\s*[),]',
      'axios\\s*\\(\\s*\\{?\\s*url\\s*:',
      'axios\\.(get|post|put|delete|patch)\\s*\\(\\s*[a-zA-Z_$]',
      'new\\s+URL\\s*\\(\\s*[a-zA-Z_$]',
    ],
  },
  {
    id: 'config-unsafe',
    severity: 'high',
    why: 'Build/image/CSP escape hatches that silently disable safety checks.',
    patterns: [
      'ignoreBuildErrors\\s*:\\s*true',
      'ignoreDuringBuilds\\s*:\\s*true',
      'dangerouslyAllowSVG\\s*:\\s*true',
      'unoptimized\\s*:\\s*true',
      // remotePatterns entries are multi-line objects; match the wildcard hostname
      // line itself rather than trying to span lines from "remotePatterns".
      'hostname\\s*:\\s*[\'"`]\\*\\*?[\'"`]',
      'remotePatterns[\\s\\S]{0,40}[\'"`]\\*\\*?[\'"`]',
    ],
  },
  {
    id: 'cookie-clientside',
    severity: 'medium',
    why: 'Cookies set via document.cookie cannot be httpOnly. Server Set-Cookie must carry HttpOnly/Secure/SameSite.',
    patterns: [
      'document\\.cookie\\s*=',
      // js-cookie and similar wrappers write document.cookie under the hood.
      '(?i)\\bCookies\\.set\\s*\\(\\s*[\'"`][^\'"`]*(token|auth|jwt|session|refresh|secret)',
      '(?i)set-cookie',
    ],
  },
  {
    id: 'graphql-server',
    severity: 'medium',
    why: 'GraphQL server surface: introspection in prod exposes the schema; missing depth/complexity limits invite abusive queries.',
    patterns: [
      'new\\s+ApolloServer\\s*\\(',
      'createYoga\\s*\\(',
      'graphqlHTTP\\s*\\(',
      'introspection\\s*:\\s*true',
    ],
  },
  {
    id: 'cspt',
    severity: 'low',
    why: 'URL-derived values interpolated into API paths without encoding can retarget authenticated requests (client-side path traversal).',
    patterns: [
      // Multi-line calls put the path template on its own line.
      '^\\s*`/[^`]*\\$\\{',
      '\\.(get|post|put|patch|delete|request)\\s*(<[^(]*>)?\\s*\\(\\s*`[^`]*\\$\\{',
      'fetch\\s*\\(\\s*`[^`]*\\$\\{',
      '\\buseSWR\\w*\\s*\\(\\s*`[^`]*\\$\\{',
      // Request config objects: axios({ url }), RTK Query ({ url, method }).
      '\\burl\\s*:\\s*`[^`]*\\$\\{',
    ],
  },
  {
    id: 'iac-risk',
    severity: 'medium',
    why: 'Infrastructure code that opens admin ports to the internet, grants wildcard IAM, or pipes remote scripts into a shell.',
    iacOnly: true,
    patterns: [
      'Peer\\.anyIpv[46]\\(\\)',
      '0\\.0\\.0\\.0/0',
      '[\'"]::/0[\'"]',
      'resources\\s*:\\s*\\[\\s*[\'"]\\*[\'"]',
      '"Resource"\\s*:\\s*"\\*"',
      'actions\\s*:\\s*\\[\\s*[\'"]([a-z0-9-]+:)?\\*[\'"]',
      '"Action"\\s*:\\s*"([a-z0-9-]+:)?\\*"',
      '(curl|wget)[^|\\n]*\\|\\s*(sudo\\s+)?(ba)?sh\\b',
      '(npm (i|install)|pnpm (add|i|install))\\s+(-g|--global)\\b',
      'yarn global add ',
      'http_tokens\\s*=\\s*"optional"',
      '\\bpull_request_target\\b',
    ],
  },
];

// Paths that strongly hint server-side execution (where injection/SSRF actually bite).
// Deliberately no bare `actions/` segment — it matches Redux/Vuex client code; Next.js
// server actions are detected by their 'use server' directive instead (see below).
// `/pages/api/`, NOT a bare `/api/`: App-Router handlers are already caught by `/route.`
// and pages-router endpoints by `/pages/api/`, whereas a bare `/api/` wrongly tags the very
// common CLIENT api layer (`src/api/…` axios services/config) as server code — that false
// serverHint misleads triage into treating client localStorage/fetch as a server surface.
const SERVER_HINT = /(\/route\.(t|j)sx?$|\/pages\/api\/|\/middleware\.(t|j)sx?$|\.server\.|\/server\/)/i;

// Classify a navigation/redirect candidate by what its destination argument is, so triage
// can skip the (overwhelmingly safe) constant-destination calls and focus on dynamic ones:
//   'literal'  — a string literal, or a template literal with NO ${…} interpolation
//   'template' — a template literal WITH ${…} (usually an internal route + an id)
//   'dynamic'  — a variable / expression (`router.push(next)`) — the entries worth reviewing
// Heuristic over the matched source line; returns null when no nav call is recognizable.
function classifyNavArg(line) {
  const m = line.match(
    /(?:router\.(?:push|replace)|history\.(?:push|replace)|location\.(?:assign|replace)|window\.location\.href|window\.location|document\.location|location\.href|\bredirect|\bnavigate)\s*[=(]\s*/,
  );
  if (!m) return null;
  const rest = line.slice(m.index + m[0].length);
  const c = rest[0];
  if (c === undefined) return null;
  if (c === "'" || c === '"') return 'literal';
  if (c === '`') return rest.includes('${') ? 'template' : 'literal';
  // Object form (router.push({ pathname: '/x', query: {…} })): the destination is the
  // pathname value — query params are URL-encoded and can't change the target origin.
  if (c === '{') {
    const pm = rest.match(/^\{\s*pathname\s*:\s*(.)/);
    if (!pm) return 'dynamic';
    if (pm[1] === "'" || pm[1] === '"') return 'literal';
    if (pm[1] === '`') return rest.includes('${') ? 'template' : 'literal';
    return 'dynamic';
  }
  // A ternary of two plain string literals is a constant destination, not a dynamic one.
  if (/^[A-Za-z_$][\w.$]*\s*\?\s*(['"])[^'"]*\1\s*:\s*(['"])[^'"]*\2\s*[),]/.test(rest)) {
    return 'literal';
  }
  // Bare `pathname` (the usePathname/usePathname-style current internal path) — review-lite.
  if (/^pathname\s*[),]/.test(rest)) return 'template';
  return 'dynamic';
}

// Deterministic project-level checks for "absence" and logic findings grep can't express.
// They emit the same finding shape as the rg categories, so slices, summaries and triage
// treat them uniformly. Catalog guidance: §24 (headers, auth flows, session lifecycle),
// §23 (secrets in git), §20 (dev surfaces).
const PROJECT_CHECKS = [
  {
    id: 'headers-missing',
    severity: 'medium',
    why: 'No security headers configured: a frontend app without CSP/X-Frame-Options/nosniff is missing its strongest XSS and clickjacking mitigations.',
    run: checkHeadersMissing,
  },
  {
    id: 'env-tracked',
    severity: 'low',
    why: 'Env files tracked in git: even if current values are public, the first real secret added to the file gets committed forever.',
    run: checkEnvTracked,
  },
  {
    id: 'auth-callback-unbound',
    severity: 'medium',
    why: "An auth callback that exchanges a code from the URL without state/PKCE lets an attacker sign the victim into the attacker's account (login CSRF).",
    run: checkAuthCallbackUnbound,
  },
  {
    id: 'logout-cross-tab',
    severity: 'low',
    why: 'Logout that clears only the current tab leaves other open tabs signed in until the access token expires.',
    run: checkLogoutCrossTab,
  },
  {
    id: 'dev-surface',
    severity: 'low',
    why: 'Dev/debug routes, menu items and /api/dev calls shipped in production builds widen the attack surface; destructive dev actions must be env-gated.',
    run: checkDevSurface,
  },
];

const HISTORY_CHECK = {
  id: 'secrets-git-history',
  severity: 'critical',
  why: 'A secret added in any commit stays in history after removal: rotate it if real.',
};

// Files that can define routes, components or services, as opposed to data and config.
const CODE_FILE = /\.(tsx?|jsx?|mts|cts|mjs|cjs|vue|svelte|astro)$/i;
// Tests, mocks and stories never ship to users.
const TEST_FILE =
  /(^|\/)(__tests__|__mocks__|e2e|tests?|cypress|playwright)\/|\.(test|spec|stories)\.\w+$/i;

// A path segment or file name ending in "callback": sso/callback/page.tsx, OAuthCallback.tsx.
const CALLBACK_PATH = /(^|\/)[\w-]*callback(\/|\.)/i;
const CALLBACK_ROUTE_PATTERNS = ['(?i)\\bpath\\s*[:=]\\s*\\{?\\s*[\'"`][^\'"`]*callback'];
// Any of these anywhere in the code means some flow is bound to the browser that started it.
const AUTH_BINDING_PATTERNS = [
  '(?i)code[_-]?verifier',
  '(?i)code[_-]?challenge',
  '(?i)\\bpkce',
  '(?i)oauth[_-]?state',
  '\\.get\\(\\s*[\'"`]state[\'"`]\\s*\\)',
];
// Auth SDKs that may bind the flow and sync sessions across tabs themselves: triage reads
// their config instead of looking for hand-written code.
const AUTH_LIBRARIES = [
  'next-auth',
  '@auth/core',
  '@auth0/auth0-react',
  '@auth0/auth0-spa-js',
  '@auth0/nextjs-auth0',
  '@azure/msal-browser',
  '@clerk/clerk-react',
  '@clerk/nextjs',
  '@okta/okta-auth-js',
  '@supabase/supabase-js',
  '@workos-inc/authkit-nextjs',
  'aws-amplify',
  'better-auth',
  'firebase',
  'keycloak-js',
  'oidc-client-ts',
];

const LOGOUT_PATTERNS = ['(?i)\\b(log|sign)[_-]?out'];
const LOGOUT_DEFINITION =
  /(function\s+|(const|let|var)\s+|^\s*(export\s+)?(async\s+)?)(log|sign)[_-]?out\w*\s*[=(]/i;
const CROSS_TAB_PATTERNS = [
  'BroadcastChannel',
  'addEventListener\\s*\\(\\s*[\'"`]storage[\'"`]',
  '\\bonstorage\\b',
];
const SESSION_END_WORDS = /\b(log|sign)[_-]?out|(clear|end|forget|reset)[_-]?session/i;

const DEV_PATH = /(^|\/)(dev-tools|debug|playground|sandbox|seed|simulate|__dev)[^/]*(\/|$)/i;
const DEV_CONTENT_PATTERNS = [
  '[\'"`]/api/(dev|debug|test|internal)/',
  '(?i)\\b(href|to|path)\\s*[:=]\\s*\\{?\\s*[\'"`][^\'"`]*/(dev-tools|debug|playground|sandbox|seed|simulate|__dev)',
];
const ENV_GATE =
  /(NODE_ENV|APP_ENV|VERCEL_ENV)\b|\bis(Dev|Prod)\w*|import\.meta\.env\.(DEV|PROD|MODE)\b/;
const LAYOUT_FILES = ['layout.tsx', 'layout.jsx', 'layout.ts', 'layout.js'];

// The scanned root is often a subdir (src/); accept a parent as the project dir only when
// it actually holds package.json, so the walk never drifts into unrelated directories.
function findProjectDir(root) {
  let dir = root;
  for (let i = 0; i < 3; i++) {
    if (existsSync(join(dir, 'package.json'))) return dir;
    const parent = dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return root;
}

function checkHeadersMissing(root) {
  const names = ['next.config.ts', 'next.config.js', 'next.config.mjs', 'next.config.cjs'];
  const projectDir = findProjectDir(root);
  const dirs = projectDir === root ? [root] : [root, projectDir];
  let configPath = null;
  for (const dir of dirs) {
    const hit = names.map((n) => join(dir, n)).find((p) => existsSync(p));
    if (hit) {
      configPath = hit;
      break;
    }
  }
  if (!configPath) return []; // not a Next.js app — nothing to assert
  let src = '';
  try {
    src = readFileSync(configPath, 'utf8');
  } catch {
    return [];
  }
  if (/\bheaders\s*[(:]/.test(src)) return [];
  const configDir = dirname(configPath);
  const hasMiddleware = [
    'middleware.ts',
    'middleware.js',
    join('src', 'middleware.ts'),
    join('src', 'middleware.js'),
  ].some((n) => existsSync(join(configDir, n)));
  return [
    {
      file: configPath,
      line: 1,
      text: hasMiddleware
        ? 'next.config has no headers() — middleware exists; verify whether it sets CSP/security headers'
        : 'next.config has no headers() and there is no middleware — no CSP, X-Frame-Options, nosniff or Referrer-Policy is set at the app level',
      match: 'headers() absent',
      serverHint: false,
    },
  ];
}

function checkEnvTracked(root) {
  const projectDir = findProjectDir(root);
  const res = spawnSync('git', ['ls-files'], {
    cwd: projectDir,
    encoding: 'utf8',
    maxBuffer: 1024 * 1024 * 64,
  });
  if (res.error || res.status !== 0 || !res.stdout) return []; // not a git repo — skip
  return res.stdout
    .split('\n')
    .filter((f) => /(^|\/)\.env[^/]*$/.test(f) && !/\.(example|sample|template)$/i.test(f))
    .map((f) => ({
      file: join(projectDir, f),
      line: 1,
      text: `${f} is tracked in git — env files belong in .gitignore (only *.example variants should be committed)`,
      match: f,
      serverHint: false,
    }));
}

function relPath(root, file) {
  return relative(root, file).replace(/\\/g, '/');
}

function readText(file) {
  try {
    return readFileSync(file, 'utf8');
  } catch {
    return '';
  }
}

function detectAuthLibraries(projectDir) {
  let pkg;
  try {
    pkg = JSON.parse(readFileSync(join(projectDir, 'package.json'), 'utf8'));
  } catch {
    return [];
  }
  const deps = { ...pkg.dependencies, ...pkg.devDependencies };
  return AUTH_LIBRARIES.filter((name) => name in deps);
}

function checkAuthCallbackUnbound(root, ctx) {
  const locations = new Map();
  for (const file of listFiles(root, ctx.excludes) ?? []) {
    const rel = relPath(root, file);
    if (!CODE_FILE.test(rel) || TEST_FILE.test(rel) || !CALLBACK_PATH.test(rel)) continue;
    // React's own hook name, not a route.
    if (/(^|\/)use-?callback\.\w+$/i.test(rel)) continue;
    locations.set(file, { line: 1, match: 'callback route path' });
  }
  for (const m of rgMatches(root, CALLBACK_ROUTE_PATTERNS, ctx.excludes).matches) {
    if (!m.file || !CODE_FILE.test(m.file) || locations.has(m.file)) continue;
    if (TEST_FILE.test(relPath(root, m.file))) continue;
    locations.set(m.file, { line: m.line, match: m.matched });
  }
  if (locations.size === 0) return [];
  // API docs and env files may name PKCE fields the frontend never sends; only code and
  // package.json (a PKCE helper dependency) count as binding.
  const bound = rgMatches(root, AUTH_BINDING_PATTERNS, ctx.excludes).matches.some(
    (m) => m.file && (CODE_FILE.test(m.file) || basename(m.file) === 'package.json'),
  );
  if (bound) return [];
  return [...locations].map(([file, loc]) => {
    const finding = {
      file,
      line: loc.line,
      text: 'auth callback route, and no state/PKCE handling anywhere in the code — verify the flow is bound to the browser that started it',
      match: loc.match,
      serverHint: false,
    };
    if (ctx.authLibraries.length > 0) finding.authLibrary = ctx.authLibraries.join(', ');
    return finding;
  });
}

function checkLogoutCrossTab(root, ctx) {
  const logouts = rgMatches(root, LOGOUT_PATTERNS, ctx.excludes).matches.filter(
    (m) => m.file && CODE_FILE.test(m.file) && !TEST_FILE.test(relPath(root, m.file)),
  );
  if (logouts.length === 0) return [];
  const anchor = logouts.find((m) => LOGOUT_DEFINITION.test(m.raw)) ?? logouts[0];
  const listeners = rgMatches(root, CROSS_TAB_PATTERNS, ctx.excludes).matches.filter(
    (m) => m.file && CODE_FILE.test(m.file),
  );
  const finding = {
    file: anchor.file,
    line: anchor.line,
    text:
      listeners.length === 0
        ? 'logout exists, but nothing listens for cross-tab changes (no BroadcastChannel, no storage event) — logout in one tab likely leaves other tabs signed in'
        : 'logout exists and cross-tab listeners exist — verify one of them ends the session in every tab',
    match: anchor.matched,
    serverHint: false,
  };
  if (listeners.length > 0) {
    finding.crossTab = listeners.map((m) => `${m.file}:${m.line}`);
    const sessionFiles = [...new Set(listeners.map((m) => m.file))].filter((f) =>
      SESSION_END_WORDS.test(readText(f)),
    );
    if (sessionFiles.length > 0) {
      finding.likelyHandled = `listener in a file that also ends sessions (${sessionFiles.join(', ')}) — confirm it clears this tab's session`;
    }
  }
  if (ctx.authLibraries.length > 0) finding.authLibrary = ctx.authLibraries.join(', ');
  return [finding];
}

// A Next.js layout in the file's own or a parent directory gates every page below it.
function findEnvGate(root, file) {
  if (ENV_GATE.test(readText(file))) return 'env check in this file';
  let dir = dirname(file);
  const stop = resolve(root);
  while (resolve(dir).startsWith(stop)) {
    for (const name of LAYOUT_FILES) {
      const layout = join(dir, name);
      if (layout !== file && existsSync(layout) && ENV_GATE.test(readText(layout))) {
        return `env check in ${relPath(root, layout)}`;
      }
    }
    if (resolve(dir) === stop) break;
    dir = dirname(dir);
  }
  return null;
}

function checkDevSurface(root, ctx) {
  const byFile = new Map();
  for (const file of listFiles(root, ctx.excludes) ?? []) {
    const rel = relPath(root, file);
    if (!CODE_FILE.test(rel) || TEST_FILE.test(rel)) continue;
    const seg = rel.match(DEV_PATH);
    if (seg) {
      byFile.set(file, {
        line: 1,
        text: 'dev/debug route or module — confirm production builds do not serve it',
        match: `path segment: ${seg[2]}`,
      });
    }
  }
  // One finding per file: the first content hit replaces a path-only entry.
  for (const m of rgMatches(root, DEV_CONTENT_PATTERNS, ctx.excludes).matches) {
    if (!m.file || !CODE_FILE.test(m.file) || TEST_FILE.test(relPath(root, m.file))) continue;
    if (byFile.get(m.file)?.fromContent) continue;
    byFile.set(m.file, {
      line: m.line,
      text: truncate(m.raw, 240),
      match: truncate(m.matched, 80),
      fromContent: true,
    });
  }
  return [...byFile].map(([file, loc]) => {
    const finding = { file, line: loc.line, text: loc.text, match: loc.match, serverHint: false };
    const gate = findEnvGate(root, file);
    if (gate) finding.envGated = `${gate} — confirm it hides the surface in production`;
    return finding;
  });
}

const DEFAULT_EXCLUDES = [
  '**/node_modules/**',
  '**/.git/**',
  '**/.next/**',
  '**/dist/**',
  '**/build/**',
  '**/out/**',
  '**/coverage/**',
  '**/.turbo/**',
  // The scanner's own output quotes matched vulnerable lines verbatim — re-scanning it
  // would resurrect every old candidate as a phantom finding on the Phase-6 re-run.
  '**/.security-audit/**',
  // Task notes, QA artifacts and audit reports quote code and API docs; none of it ships.
  '**/.project-meta/**',
  '**/.vercel/**',
  '**/.netlify/**',
  '**/.svelte-kit/**',
  '**/.nuxt/**',
  '**/.output/**',
  '**/.astro/**',
  '**/.cache/**',
  '**/storybook-static/**',
  '**/playwright-report/**',
  '**/test-results/**',
  '**/*.min.*',
  '**/*.map',
  '**/pnpm-lock.yaml',
  '**/package-lock.json',
  '**/yarn.lock',
];

// Only scan code/config/text where frontend vulns live (plus dotenv files for secrets).
// mdx carries real JSX; mts/cts are TS module variants (next.config.mts, scripts).
const INCLUDE_GLOBS = [
  '*.{ts,tsx,mts,cts,js,jsx,mjs,cjs,vue,svelte,astro,mdx,html,htm,json,yml,yaml}',
  '.env*',
];

function parseArgs(argv) {
  const opts = { root: '.', out: null, excludes: [], only: null, quiet: false, gitHistory: false };
  const positional = [];
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--out') opts.out = argv[++i];
    else if (a === '--exclude') opts.excludes.push(argv[++i]);
    else if (a === '--only') opts.only = argv[++i];
    else if (a === '--git-history') opts.gitHistory = true;
    else if (a === '--quiet') opts.quiet = true;
    else if (a === '--help' || a === '-h') opts.help = true;
    else positional.push(a);
  }
  if (positional[0]) opts.root = positional[0];
  return opts;
}

// --no-ignore-vcs pins the semantics across ripgrep versions: since rg 14 a positive -g glob
// already overrides .gitignore, older versions skip ignored files. We always want gitignored
// files scanned — a gitignored .env still feeds NEXT_PUBLIC_* into the bundle and gitignored
// generated code still ships. Build dirs are excluded explicitly.
function rgBaseArgs(excludes, globs = INCLUDE_GLOBS) {
  const args = ['--hidden', '--no-ignore-vcs', '--no-messages'];
  for (const g of globs) args.push('-g', g);
  for (const g of [...DEFAULT_EXCLUDES, ...excludes]) args.push('-g', `!${g}`);
  return args;
}

function truncate(s, n) {
  return s.length > n ? `${s.slice(0, n)}…` : s;
}

function parseRgJson(stdout) {
  const matches = [];
  for (const line of (stdout ?? '').split('\n')) {
    if (!line) continue;
    let obj;
    try {
      obj = JSON.parse(line);
    } catch {
      continue;
    }
    if (obj.type !== 'match') continue;
    matches.push({
      file: obj.data.path?.text,
      line: obj.data.line_number,
      raw: (obj.data.lines?.text ?? '').replace(/\s+/g, ' ').trim(),
      // Which pattern hit, to speed up triage of multi-pattern categories.
      matched: (obj.data.submatches?.[0]?.match?.text ?? '').replace(/\s+/g, ' ').trim(),
    });
  }
  return matches;
}

// rg's output order across files is nondeterministic; sorting keeps "first match" stable.
function byFileAndLine(a, b) {
  if (a.file !== b.file) return a.file < b.file ? -1 : 1;
  return a.line - b.line;
}

function rgMatches(root, patterns, excludes, globs = INCLUDE_GLOBS) {
  const args = ['--json', ...rgBaseArgs(excludes, globs)];
  for (const p of patterns) args.push('-e', p);
  args.push('--', root);
  const res = spawnSync('rg', args, { encoding: 'utf8', maxBuffer: 1024 * 1024 * 512 });
  // rg exit codes: 0 = matches, 1 = no matches, 2 = error.
  if (res.status === 2) return { matches: [], error: res.stderr || 'rg error' };
  return { matches: parseRgJson(res.stdout).sort(byFileAndLine) };
}

// Returns null when rg fails, so callers can tell "no files" from "could not list".
function listFiles(root, excludes, globs = INCLUDE_GLOBS) {
  const args = ['--files', ...rgBaseArgs(excludes, globs), '--', root];
  const res = spawnSync('rg', args, { encoding: 'utf8', maxBuffer: 1024 * 1024 * 64 });
  if (res.error || res.status === 2) return null;
  return (res.stdout ?? '').split('\n').filter(Boolean).sort();
}

// Files carrying a 'use server' directive are server actions regardless of their path.
function collectUseServerFiles(root, excludes) {
  const args = ['--files-with-matches', ...rgBaseArgs(excludes)];
  args.push('-e', '^\\s*[\'"`]use server[\'"`]', '--', root);
  const res = spawnSync('rg', args, { encoding: 'utf8', maxBuffer: 1024 * 1024 * 64 });
  if (res.status === 2 || !res.stdout) return new Set();
  return new Set(res.stdout.split('\n').filter(Boolean));
}

function collectIacRoots(root, excludes) {
  const markers = listFiles(root, excludes, IAC_MARKER_GLOBS) ?? [];
  return [...new Set(markers.map((f) => `${dirname(f).replace(/\\/g, '/')}/`))];
}

function isIacPath(file, ctx) {
  const norm = file.replace(/\\/g, '/');
  if (ctx.iacRoots.some((dir) => norm.startsWith(dir))) return true;
  // The root's own name counts too, so scanning infra/ directly still runs the category.
  const rel = `${basename(ctx.root)}/${relPath(ctx.root, file)}`;
  return IAC_DIR.test(rel) || IAC_FILE.test(rel);
}

// Feeds the report's "Scanned N files" line — the frontend globs plus the IaC-only files.
function countScannedFiles(ctx) {
  const files = listFiles(ctx.root, ctx.excludes);
  if (files === null) return null;
  const iacExtra = listFiles(ctx.root, ctx.excludes, IAC_EXTRA_GLOBS) ?? [];
  return files.length + iacExtra.filter((f) => isIacPath(f, ctx)).length;
}

function ensureRg() {
  const probe = spawnSync('rg', ['--version'], { encoding: 'utf8' });
  if (probe.error || probe.status !== 0) {
    console.error(
      'ripgrep (rg) is required but was not found on PATH.\n' +
        'Install it: macOS `brew install ripgrep`, Debian/Ubuntu `apt install ripgrep`.',
    );
    process.exit(2);
  }
}

// Generic key/secret assignments whose value is an identifier-like word are field names
// ("apiKey: 'department'", "apiKey: 'jobLevel'"), not credentials — pre-tag so triage
// clears them in bulk. Real credentials virtually always carry digits/symbols/length.
// Provider-format matches (sk_live_…, AKIA…) never carry [:=]'…' in the matched text.
// For password/secret keywords only the strict lowercase-words rule applies — a plain
// dictionary password is weak but real, so it must stay untagged for triage.
function tagLowEntropySecret(finding, matched) {
  const kv = matched.match(/^([A-Za-z_-]+)\s*[:=]\s*['"]([^'"]+)['"]$/);
  if (!kv) return;
  const [, key, value] = kv;
  const plainWords = /^[a-z]+([_-][a-z]+)*$/.test(value);
  const identifierWord = /^[a-z][A-Za-z]*$/.test(value);
  const sensitiveKey = /pass|secret/i.test(key);
  if (value.length < 24 && (plainWords || (identifierWord && !sensitiveKey))) {
    finding.likelyFalsePositive = 'low-entropy value (identifier-like word, no digits)';
  }
}

function runCategory(cat, ctx) {
  const globs = cat.iacOnly ? [...INCLUDE_GLOBS, ...IAC_EXTRA_GLOBS] : INCLUDE_GLOBS;
  const { matches, error } = rgMatches(ctx.root, cat.patterns, ctx.excludes, globs);
  if (error) {
    console.error(`[warn] category "${cat.id}" produced an rg error and was skipped:\n${error}`);
    return [];
  }

  const seen = new Set();
  const findings = [];
  for (const { file, line: lineNo, raw, matched } of matches) {
    if (!file || !lineNo) continue;
    if (cat.iacOnly && !isIacPath(file, ctx)) continue;
    const key = `${file}:${lineNo}`;
    if (seen.has(key)) continue;
    seen.add(key);
    const finding = {
      file,
      line: lineNo,
      text: truncate(raw, 240),
      match: truncate(matched, 80),
      serverHint: SERVER_HINT.test(file.replace(/\\/g, '/')) || ctx.useServerFiles.has(file),
    };
    // open-redirect is the noisiest category — tag the destination kind so triage can jump
    // straight to the `dynamic` entries (constant/template internal routes are ~always safe).
    if (cat.id === 'open-redirect') {
      const argKind = classifyNavArg(raw);
      if (argKind) finding.argKind = argKind;
    }
    if (cat.id === 'secrets-hardcoded') tagLowEntropySecret(finding, matched);
    // A sanitizer call sharing the line with the HTML sink usually means the value is
    // cleaned at the point of insertion — pre-tag so triage confirms with a glance instead
    // of a file read. A hint, not a verdict: a hand-rolled sanitize*() can be a bare regex.
    if (cat.id === 'xss-dangerous-html' && /\bsanitiz\w*\s*\(/i.test(raw)) {
      finding.likelySanitized =
        'sanitizer call on the same line — confirm it wraps the sink value and is a real sanitizer (DOMPurify), not a regex replace';
    }
    // Same idea for API paths. encodeURI() is left out on purpose: it keeps `/` and `..` as is.
    if (cat.id === 'cspt' && /\bencode(?!URI\s*\()\w*\s*\(/i.test(raw)) {
      finding.likelyEncoded =
        'encoder call on the same line — confirm it wraps every interpolated segment and rejects "." / ".." (encoding leaves them as is)';
    }
    findings.push(finding);
  }
  return findings;
}

const HISTORY_SKIP =
  /(^|\/)(pnpm-lock\.yaml|package-lock\.json|yarn\.lock|bun\.lockb?)$|\.min\.|\.map$|(^|\/)\.security-audit\//;

// Walks the rg hits over `git log -p -U0`: commit and file headers set the context, hunk
// headers give the new-file line (with -U0 a hunk lists its removed lines, then its added ones).
function collectHistorySecrets(matches) {
  const found = new Map();
  let commit = null;
  let file = null;
  let hunk = null;
  for (const m of matches) {
    if (/^commit [0-9a-f]{40}$/.test(m.raw)) {
      commit = m.raw.slice(7);
      continue;
    }
    if (m.raw.startsWith('+++ ')) {
      file = m.raw.startsWith('+++ b/') ? m.raw.slice(6) : null;
      continue;
    }
    const h = m.raw.match(/^@@ -\d+(?:,(\d+))? \+(\d+)(?:,\d+)? @@/);
    if (h) {
      hunk = { removed: h[1] === undefined ? 1 : Number(h[1]), start: Number(h[2]), at: m.line };
      continue;
    }
    if (!commit || !file || !hunk || !m.raw.startsWith('+') || HISTORY_SKIP.test(file)) continue;
    const key = `${file}\0${m.matched}`;
    const prev = found.get(key);
    // git log lists newest commits first, so the last occurrence is where the secret was added.
    const finding = {
      file,
      line: hunk.start + (m.line - hunk.at - 1 - hunk.removed),
      commit,
      commits: (prev?.commits ?? 0) + 1,
      text: truncate(m.raw.slice(1).trim(), 240),
      match: truncate(m.matched, 80),
      serverHint: false,
    };
    tagLowEntropySecret(finding, m.matched);
    found.set(key, finding);
  }
  return [...found.values()].sort(byFileAndLine);
}

// Resolves to null when the project is not a git repository.
function scanGitHistory(root) {
  const cwd = findProjectDir(root);
  const probe = spawnSync('git', ['rev-parse', '--is-inside-work-tree'], { cwd, encoding: 'utf8' });
  if (probe.error || probe.status !== 0) return Promise.resolve(null);
  const patterns = CATEGORIES.find((c) => c.id === 'secrets-hardcoded').patterns;
  const rgArgs = ['--json', '--no-messages'];
  for (const p of ['^commit [0-9a-f]{40}$', '^\\+\\+\\+ ', '^@@ ', ...patterns]) {
    rgArgs.push('-e', p);
  }
  const gitArgs = ['log', '-p', '--all', '--no-color', '--no-ext-diff', '--no-textconv', '-U0'];
  return new Promise((done) => {
    const git = spawn('git', [...gitArgs, '--format=commit %H'], {
      cwd,
      stdio: ['ignore', 'pipe', 'ignore'],
    });
    const rg = spawn('rg', rgArgs, { stdio: ['pipe', 'pipe', 'ignore'] });
    let out = '';
    rg.stdout.setEncoding('utf8');
    rg.stdout.on('data', (chunk) => {
      out += chunk;
    });
    // rg exiting early closes the pipe; git's EPIPE is expected then, not a crash.
    rg.stdin.on('error', () => {});
    git.on('error', () => rg.stdin.end());
    rg.on('error', () => done([]));
    git.stdout.pipe(rg.stdin);
    rg.on('close', () => done(collectHistorySecrets(parseRgJson(out))));
  });
}

async function main() {
  const opts = parseArgs(process.argv.slice(2));
  if (opts.help) {
    console.log(
      'Usage: node scan.mjs [root] [--out file] [--exclude glob]... [--only category] [--git-history] [--quiet]',
    );
    process.exit(0);
  }
  ensureRg();

  const root = resolve(opts.root);
  const outPath = opts.out ? resolve(opts.out) : join(root, '.security-audit', 'findings.json');

  const knownIds = [...CATEGORIES, ...PROJECT_CHECKS, HISTORY_CHECK].map((c) => c.id);
  if (opts.only && !knownIds.includes(opts.only)) {
    console.error(`Unknown category "${opts.only}". Known: ${knownIds.join(', ')}`);
    process.exit(2);
  }
  const selected = opts.only ? CATEGORIES.filter((c) => c.id === opts.only) : CATEGORIES;
  const selectedChecks = opts.only
    ? PROJECT_CHECKS.filter((c) => c.id === opts.only)
    : PROJECT_CHECKS;
  const runHistory = opts.only ? opts.only === HISTORY_CHECK.id : opts.gitHistory;

  const ctx = {
    root,
    excludes: opts.excludes,
    useServerFiles: collectUseServerFiles(root, opts.excludes),
    iacRoots: collectIacRoots(root, opts.excludes),
    authLibraries: detectAuthLibraries(findProjectDir(root)),
  };
  const filesScanned = countScannedFiles(ctx);

  const categories = [];
  const bySeverity = { critical: 0, high: 0, medium: 0, low: 0 };
  let total = 0;

  for (const cat of selected) {
    const findings = runCategory(cat, ctx);
    total += findings.length;
    bySeverity[cat.severity] += findings.length;
    const entry = {
      category: cat.id,
      severity: cat.severity,
      why: cat.why,
      count: findings.length,
      serverHits: findings.filter((f) => f.serverHint).length,
      findings,
    };
    const likelyFalsePositives = findings.filter((f) => f.likelyFalsePositive).length;
    if (likelyFalsePositives > 0) entry.likelyFalsePositives = likelyFalsePositives;
    const likelySanitized = findings.filter((f) => f.likelySanitized).length;
    if (likelySanitized > 0) entry.likelySanitized = likelySanitized;
    // Surface the destination breakdown so a 150-candidate open-redirect category reads as
    // "N dynamic worth reviewing" instead of an undifferentiated wall.
    if (cat.id === 'open-redirect') {
      entry.argKinds = {
        dynamic: findings.filter((f) => f.argKind === 'dynamic').length,
        template: findings.filter((f) => f.argKind === 'template').length,
        literal: findings.filter((f) => f.argKind === 'literal').length,
      };
    }
    if (cat.id === 'cspt') {
      entry.files = new Set(findings.map((f) => f.file)).size;
      entry.likelyEncoded = findings.filter((f) => f.likelyEncoded).length;
    }
    categories.push(entry);
  }

  for (const check of selectedChecks) {
    const findings = check.run(root, ctx);
    total += findings.length;
    bySeverity[check.severity] += findings.length;
    const entry = {
      category: check.id,
      severity: check.severity,
      why: check.why,
      count: findings.length,
      serverHits: 0,
      findings,
    };
    const envGated = findings.filter((f) => f.envGated).length;
    if (envGated > 0) entry.envGated = envGated;
    const likelyHandled = findings.filter((f) => f.likelyHandled).length;
    if (likelyHandled > 0) entry.likelyHandled = likelyHandled;
    categories.push(entry);
  }

  if (runHistory) {
    const findings = await scanGitHistory(root);
    if (findings === null) {
      console.error('[warn] --git-history: not a git repository — commit history was not scanned');
    } else {
      total += findings.length;
      bySeverity[HISTORY_CHECK.severity] += findings.length;
      const entry = {
        category: HISTORY_CHECK.id,
        severity: HISTORY_CHECK.severity,
        why: HISTORY_CHECK.why,
        count: findings.length,
        serverHits: 0,
        findings,
      };
      const likelyFalsePositives = findings.filter((f) => f.likelyFalsePositive).length;
      if (likelyFalsePositives > 0) entry.likelyFalsePositives = likelyFalsePositives;
      categories.push(entry);
    }
  }

  // One source line can trip several categories (document.cookie → dom-xss-source AND
  // cookie-clientside). Cross-reference them so triage handles the line once.
  const byLocation = new Map();
  for (const c of categories) {
    for (const f of c.findings) {
      const key = `${f.file}:${f.line}`;
      if (!byLocation.has(key)) byLocation.set(key, []);
      byLocation.get(key).push({ category: c.category, finding: f });
    }
  }
  for (const group of byLocation.values()) {
    if (group.length < 2) continue;
    for (const { category, finding } of group) {
      finding.alsoIn = group.filter((g) => g.category !== category).map((g) => g.category);
    }
  }

  const report = {
    scannedRoot: root,
    generatedAt: new Date().toISOString(),
    note: 'Candidates only — every entry must be triaged against references/vulnerability-catalog.md before it counts as a vulnerability.',
    totals: {
      filesScanned,
      findings: total,
      byCategory: Object.fromEntries(categories.map((c) => [c.category, c.count])),
      bySeverity,
    },
    categories,
  };

  mkdirSync(dirname(outPath), { recursive: true });
  writeFileSync(outPath, JSON.stringify(report, null, 2));

  // The dump quotes vulnerable lines (and any found secrets) verbatim — never let it slip
  // into VCS silently. `git check-ignore` honors every .gitignore in the repo: exit 0 =
  // ignored (fine), 1 = inside a repo and NOT ignored (warn), 128/error = not a repo (fine).
  const ignoreProbe = spawnSync('git', ['check-ignore', '-q', outPath], {
    cwd: dirname(outPath),
    encoding: 'utf8',
  });
  if (!ignoreProbe.error && ignoreProbe.status === 1) {
    console.error(
      `[warn] findings were written inside a git repo and "${basename(dirname(outPath))}/" is not gitignored — ` +
        'the dump quotes vulnerable lines verbatim. Point --out outside the repo (e.g. a temp dir) or gitignore it.',
    );
  }

  // One file per non-empty category, so triage (and helper fan-out) can read a
  // small slice instead of the full findings.json on large result sets.
  const catDir = join(dirname(outPath), 'categories');
  rmSync(catDir, { recursive: true, force: true });
  mkdirSync(catDir, { recursive: true });
  for (const c of categories) {
    if (c.count > 0) writeFileSync(join(catDir, `${c.category}.json`), JSON.stringify(c, null, 2));
  }

  if (!opts.quiet) {
    const order = { critical: 0, high: 1, medium: 2, low: 3 };
    const sorted = [...categories].sort(
      (a, b) => order[a.severity] - order[b.severity] || b.count - a.count,
    );
    console.log(`\nFrontend security scan — ${root}`);
    console.log(`Candidates: ${total} in ${filesScanned ?? '?'} scanned files  (critical ${bySeverity.critical}, high ${bySeverity.high}, medium ${bySeverity.medium}, low ${bySeverity.low})`);
    console.log('—'.repeat(64));
    for (const c of sorted) {
      if (c.count === 0) continue;
      let tags = c.serverHits ? `  [${c.serverHits} in server paths]` : '';
      if (c.argKinds) {
        tags += `  [${c.argKinds.dynamic} dynamic, ${c.argKinds.template} template, ${c.argKinds.literal} literal]`;
      }
      if (c.likelyFalsePositives) {
        tags += `  [${c.likelyFalsePositives} likely-FP: low-entropy]`;
      }
      if (c.likelySanitized) {
        tags += `  [${c.likelySanitized} likely-sanitized]`;
      }
      if (c.category === 'cspt') {
        tags += `  [${c.files} files, ${c.likelyEncoded} likely-encoded]`;
      }
      if (c.envGated) {
        tags += `  [${c.envGated} env-gated]`;
      }
      if (c.likelyHandled) {
        tags += `  [${c.likelyHandled} likely-handled]`;
      }
      console.log(`  ${c.severity.toUpperCase().padEnd(8)} ${c.category.padEnd(22)} ${String(c.count).padStart(5)}${tags}`);
    }
    console.log('—'.repeat(64));
    console.log(`Full findings written to: ${outPath}`);
    console.log(`Per-category slices:      ${catDir}/<category>.json`);
    console.log('Next: triage each category against the vulnerability catalog. Candidates ≠ vulnerabilities.\n');
  }
}

main();
