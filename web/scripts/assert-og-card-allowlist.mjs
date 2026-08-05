// Fails (exit 1) if any built page outside the known allowlist falls back to
// og-default.png. The 9 hub/index pages in og-pages.ts each get a generated
// card; every other page is expected to fall back — except a scheduled or
// misconfigured post can silently widen that set (e.g. a page that should
// have gotten a card, or a stray page under /blog/tags/ with the wrong
// shape). Run after `astro build`, same pattern as assert-pagefind-index.mjs.
import { execFileSync } from 'node:child_process';

const DIST = 'dist';

// Allowlist: the 63 tag pages plus the 3 fixed pages that intentionally have
// no card of their own (/, /search/, /404). Keep in sync with Task 5's
// verified composition — a page matching none of these is the failure mode
// this script exists to catch.
const ALLOW_PATTERNS = [/^\/blog\/tags\/[^/]+\/index\.html$/, /^\/index\.html$/, /^\/search\/index\.html$/, /^\/404\.html$/];

function isAllowed(path) {
  return ALLOW_PATTERNS.some((re) => re.test(path));
}

let output;
try {
  output = execFileSync('grep', ['-rl', 'og-default.png', DIST, '--include=*.html'], { encoding: 'utf8' });
} catch (err) {
  // grep exits 1 with no output when nothing matches — that's a real failure
  // here (every one of the 9 cards would then be unreachable via fallback
  // detection), not a clean pass.
  if (err.status === 1 && !err.stdout) {
    console.error('✗ no page references og-default.png — expected the 66-page fallback set, found none');
    process.exit(1);
  }
  throw err;
}

const paths = output
  .split('\n')
  .filter(Boolean)
  .map((p) => p.slice(DIST.length));

const unexpected = paths.filter((p) => !isAllowed(p));

if (unexpected.length > 0) {
  console.error(`✗ ${unexpected.length} page(s) fall back to og-default.png outside the known allowlist:`);
  for (const p of unexpected) console.error(`    ${p}`);
  console.error('Either the page should reference a generated card, or the allowlist in this script is stale.');
  process.exit(1);
}

console.log(`✓ og card allowlist OK — ${paths.length} pages on the default card, all within the known allowlist.`);
