// web/scripts/utm/assert-no-internal-utm.mjs
// Fails if any internal link in site content/components/pages/layouts carries a
// utm_ param. UTMs are inbound-only (convention doc, hygiene rule 1): tagging an
// internal link starts a new session and overwrites attribution. The UTM
// *generator* (src/lib/utm-core.ts, scripts/utm/) legitimately contains "utm_"
// tokens, so those trees are out of scope here — only content the site renders
// as links is audited. Mirrors the assert-pagefind-index.mjs guard style.
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const ROOTS = ['src/content', 'src/components', 'src/pages', 'src/layouts'].map((p) =>
  fileURLToPath(new URL(`../../${p}`, import.meta.url)),
);

const AUDITED = /\.(astro|mdx|md|ts|js|jsx|tsx|html)$/;
const hits = [];

function walk(dir) {
  for (const name of readdirSync(dir)) {
    const full = `${dir}/${name}`;
    if (statSync(full).isDirectory()) {
      walk(full);
    } else if (AUDITED.test(name)) {
      const src = readFileSync(full, 'utf8');
      src.split('\n').forEach((line, i) => {
        if (line.includes('utm_')) hits.push(`${full}:${i + 1}: ${line.trim()}`);
      });
    }
  }
}

for (const root of ROOTS) walk(root);

if (hits.length > 0) {
  console.error('FAIL — internal links must not carry utm_ params (UTMs are inbound-only):');
  for (const h of hits) console.error(`  ${h}`);
  process.exit(1);
}
console.log('OK — no internal links carry utm_ params.');
