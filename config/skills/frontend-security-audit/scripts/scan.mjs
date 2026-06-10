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
//   node scan.mjs [root] [--out findings.json] [--exclude <glob>]... [--only <cat>] [--quiet]
//
// Defaults: root = "." , out = "<root>/.security-audit/findings.json"
// Requires: ripgrep (`rg`) on PATH. Install: `brew install ripgrep` / `apt install ripgrep`.

import { spawnSync } from 'node:child_process';
import { mkdirSync, rmSync, writeFileSync } from 'node:fs';
import { dirname, resolve, join } from 'node:path';

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
    ],
  },
  {
    id: 'open-redirect',
    severity: 'high',
    why: 'Navigation sinks. If the destination is user-controlled without an allow-list, this is an open redirect.',
    patterns: [
      'window\\.location\\s*=',
      'window\\.location\\.href\\s*=',
      'location\\.href\\s*=',
      'location\\.(assign|replace)\\s*\\(',
      'router\\.(push|replace)\\s*\\(',
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
    /(?:router\.(?:push|replace)|location\.(?:assign|replace)|window\.location\.href|window\.location|location\.href|\bredirect)\s*[=(]\s*/,
  );
  if (!m) return null;
  const rest = line.slice(m.index + m[0].length);
  const c = rest[0];
  if (c === undefined) return null;
  if (c === "'" || c === '"') return 'literal';
  if (c === '`') return rest.includes('${') ? 'template' : 'literal';
  return 'dynamic';
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
const INCLUDE_GLOBS = [
  '*.{ts,tsx,js,jsx,mjs,cjs,vue,svelte,astro,html,htm,json,yml,yaml}',
  '.env*',
];

function parseArgs(argv) {
  const opts = { root: '.', out: null, excludes: [], only: null, quiet: false };
  const positional = [];
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--out') opts.out = argv[++i];
    else if (a === '--exclude') opts.excludes.push(argv[++i]);
    else if (a === '--only') opts.only = argv[++i];
    else if (a === '--quiet') opts.quiet = true;
    else if (a === '--help' || a === '-h') opts.help = true;
    else positional.push(a);
  }
  if (positional[0]) opts.root = positional[0];
  return opts;
}

// Files carrying a 'use server' directive are server actions regardless of their path.
function collectUseServerFiles(root, excludes) {
  const args = ['--files-with-matches', '--hidden', '--no-ignore-vcs', '--no-messages'];
  for (const g of INCLUDE_GLOBS) args.push('-g', g);
  for (const g of [...DEFAULT_EXCLUDES, ...excludes]) args.push('-g', `!${g}`);
  args.push('-e', '^\\s*[\'"`]use server[\'"`]', '--', root);
  const res = spawnSync('rg', args, { encoding: 'utf8', maxBuffer: 1024 * 1024 * 64 });
  if (res.status === 2 || !res.stdout) return new Set();
  return new Set(res.stdout.split('\n').filter(Boolean));
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

function runCategory(cat, root, excludes, useServerFiles) {
  // --no-ignore-vcs pins the semantics across ripgrep versions: since rg 14 a positive
  // -g glob already overrides .gitignore, older versions skip ignored files. We always
  // want gitignored files scanned — a gitignored .env still feeds NEXT_PUBLIC_* into the
  // bundle and gitignored generated code still ships. Build dirs are excluded explicitly.
  const args = ['--json', '--hidden', '--no-ignore-vcs', '--no-messages'];
  for (const g of INCLUDE_GLOBS) args.push('-g', g);
  for (const g of [...DEFAULT_EXCLUDES, ...excludes]) args.push('-g', `!${g}`);
  for (const p of cat.patterns) args.push('-e', p);
  args.push('--', root);

  const res = spawnSync('rg', args, { encoding: 'utf8', maxBuffer: 1024 * 1024 * 512 });
  // rg exit codes: 0 = matches, 1 = no matches, 2 = error.
  if (res.status === 2) {
    console.error(`[warn] category "${cat.id}" produced an rg error and was skipped:\n${res.stderr}`);
    return [];
  }
  if (!res.stdout) return [];

  const seen = new Set();
  const findings = [];
  for (const line of res.stdout.split('\n')) {
    if (!line) continue;
    let obj;
    try {
      obj = JSON.parse(line);
    } catch {
      continue;
    }
    if (obj.type !== 'match') continue;
    const file = obj.data.path?.text;
    const lineNo = obj.data.line_number;
    if (!file || !lineNo) continue;
    const key = `${file}:${lineNo}`;
    if (seen.has(key)) continue;
    seen.add(key);
    const raw = (obj.data.lines?.text ?? '').replace(/\s+/g, ' ').trim();
    const matched = (obj.data.submatches?.[0]?.match?.text ?? '').replace(/\s+/g, ' ').trim();
    const finding = {
      file,
      line: lineNo,
      text: raw.length > 240 ? `${raw.slice(0, 240)}…` : raw,
      // Which pattern hit, to speed up triage of multi-pattern categories.
      match: matched.length > 80 ? `${matched.slice(0, 80)}…` : matched,
      serverHint: SERVER_HINT.test(file.replace(/\\/g, '/')) || useServerFiles.has(file),
    };
    // open-redirect is the noisiest category — tag the destination kind so triage can jump
    // straight to the `dynamic` entries (constant/template internal routes are ~always safe).
    if (cat.id === 'open-redirect') {
      const argKind = classifyNavArg(raw);
      if (argKind) finding.argKind = argKind;
    }
    findings.push(finding);
  }
  return findings;
}

function main() {
  const opts = parseArgs(process.argv.slice(2));
  if (opts.help) {
    console.log(
      'Usage: node scan.mjs [root] [--out file] [--exclude glob]... [--only category] [--quiet]',
    );
    process.exit(0);
  }
  ensureRg();

  const root = resolve(opts.root);
  const outPath = opts.out ? resolve(opts.out) : join(root, '.security-audit', 'findings.json');

  const selected = opts.only ? CATEGORIES.filter((c) => c.id === opts.only) : CATEGORIES;
  if (selected.length === 0) {
    console.error(`Unknown category "${opts.only}". Known: ${CATEGORIES.map((c) => c.id).join(', ')}`);
    process.exit(2);
  }

  const useServerFiles = collectUseServerFiles(root, opts.excludes);

  const categories = [];
  const bySeverity = { critical: 0, high: 0, medium: 0, low: 0 };
  let total = 0;

  for (const cat of selected) {
    const findings = runCategory(cat, root, opts.excludes, useServerFiles);
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
    // Surface the destination breakdown so a 150-candidate open-redirect category reads as
    // "N dynamic worth reviewing" instead of an undifferentiated wall.
    if (cat.id === 'open-redirect') {
      entry.argKinds = {
        dynamic: findings.filter((f) => f.argKind === 'dynamic').length,
        template: findings.filter((f) => f.argKind === 'template').length,
        literal: findings.filter((f) => f.argKind === 'literal').length,
      };
    }
    categories.push(entry);
  }

  const report = {
    scannedRoot: root,
    generatedAt: new Date().toISOString(),
    note: 'Candidates only — every entry must be triaged against references/vulnerability-catalog.md before it counts as a vulnerability.',
    totals: {
      findings: total,
      byCategory: Object.fromEntries(categories.map((c) => [c.category, c.count])),
      bySeverity,
    },
    categories,
  };

  mkdirSync(dirname(outPath), { recursive: true });
  writeFileSync(outPath, JSON.stringify(report, null, 2));

  // One file per non-empty category, so triage (and Explore fan-out) can read a
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
    console.log(`Candidates: ${total}  (critical ${bySeverity.critical}, high ${bySeverity.high}, medium ${bySeverity.medium})`);
    console.log('—'.repeat(64));
    for (const c of sorted) {
      if (c.count === 0) continue;
      let tags = c.serverHits ? `  [${c.serverHits} in server paths]` : '';
      if (c.argKinds) {
        tags += `  [${c.argKinds.dynamic} dynamic, ${c.argKinds.template} template, ${c.argKinds.literal} literal]`;
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
