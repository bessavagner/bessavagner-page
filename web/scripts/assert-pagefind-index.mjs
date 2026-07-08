// Fails (exit 1) if the Pagefind index is missing or has zero fragments.
// Run after `astro build`. Keeps a broken/empty search from shipping silently.
import { existsSync, readdirSync } from 'node:fs';

const runtime = 'dist/pagefind/pagefind.js';
const fragmentsDir = 'dist/pagefind/fragment';

if (!existsSync(runtime)) {
  console.error(`✗ pagefind runtime missing: ${runtime} (did the build run the integration?)`);
  process.exit(1);
}
const count = existsSync(fragmentsDir) ? readdirSync(fragmentsDir).length : 0;
if (count === 0) {
  console.error('✗ pagefind index has 0 fragments — no content was indexed (check data-pagefind-body regions).');
  process.exit(1);
}
console.log(`✓ pagefind index OK — ${count} fragments.`);
