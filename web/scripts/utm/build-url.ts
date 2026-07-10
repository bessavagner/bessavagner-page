// web/scripts/utm/build-url.ts
// One-step LinkedIn UTM link generator. Turns a destination + asset campaign +
// date-slot into the single canonical tagged URL (per the closed vocabulary in
// src/lib/utm-core.ts) and appends it to registry.csv as the source-of-truth log.
// A typo in source/medium or a non-lowercase slug is refused before anything is
// printed or logged. See docs/.ai/playbooks/utm-convention.md.
//
// Usage (from web/):
//   pnpm utm --path /blog/polymorphic-vaults-in-drf --campaign polymorphic-vaults --content 2026-07-09-am
//   pnpm utm --path /blog/x --campaign x --content boost-2026-07-09 --paid
//   pnpm utm --path /blog/x --campaign x --content 2026-07-09-am --dry-run
import { appendFileSync, existsSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import {
  buildTaggedUrl,
  resolveDestination,
  formatRegistryRow,
  composePlacementContent,
  REGISTRY_HEADER,
  type RegistryRow,
} from '../../src/lib/utm-core.ts';

const REGISTRY_PATH = fileURLToPath(new URL('./registry.csv', import.meta.url));

const argv = process.argv.slice(2);
const flag = (name: string): string | undefined => {
  const i = argv.indexOf(name);
  return i >= 0 ? argv[i + 1] : undefined;
};
const has = (name: string): boolean => argv.includes(name);

const destination = flag('--path') ?? flag('--url');
const campaign = flag('--campaign');
const content = flag('--content');
const placement = flag('--placement');
const source = flag('--source') ?? 'linkedin';
const medium = has('--paid') ? 'paid-social' : (flag('--medium') ?? 'social');
const datePosted = flag('--date') ?? new Date().toISOString().slice(0, 10);
const dryRun = has('--dry-run');

const USAGE =
  'usage: pnpm utm --path </blog/slug> --campaign <asset-slug> --content <date-slot> ' +
  '[--placement <post-body|first-comment|profile-featured>] ' +
  '[--paid | --medium <social|paid-social>] [--source linkedin] [--date YYYY-MM-DD] [--dry-run]';

if (!destination || !campaign || !content) {
  console.error(USAGE);
  process.exit(1);
}

let taggedUrl: string;
let destinationUrl: string;
let resolvedContent: string;
try {
  // Optional A/B placement: fold it into utm_content as <date-slot>-<placement>.
  // composePlacementContent throws (caught below) on an out-of-vocab placement.
  resolvedContent = placement ? composePlacementContent(content, placement) : content;
  taggedUrl = buildTaggedUrl({ destination, source, medium, campaign, content: resolvedContent });
  destinationUrl = resolveDestination(destination);
} catch (err) {
  console.error(`refused: ${err instanceof Error ? err.message : String(err)}`);
  process.exit(1);
}

// The tagged URL is the primary output — print it alone so it is pipe/copy-clean.
console.log(taggedUrl);

if (dryRun) process.exit(0);

// Registry is inbound-only bookkeeping; recreate the header if the file is missing.
if (!existsSync(REGISTRY_PATH)) writeFileSync(REGISTRY_PATH, `${REGISTRY_HEADER}\n`);
const row: RegistryRow = {
  destinationUrl,
  source: 'linkedin',
  medium: medium as RegistryRow['medium'],
  campaign,
  content: resolvedContent,
  taggedUrl,
  datePosted,
};
appendFileSync(REGISTRY_PATH, `${formatRegistryRow(row)}\n`);
console.error(`logged to ${REGISTRY_PATH}`);
