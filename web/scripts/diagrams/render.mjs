// Render Mermaid (.mmd) diagram sources to committed PNGs under src/assets/.
//
// Convention: a source at  scripts/diagrams/<path>/<name>.mmd  renders to
//                          src/assets/<path>/<name>.png
// so the folder tree under scripts/diagrams/ mirrors the asset tree the posts
// import from (e.g. scripts/diagrams/buildlog/stealthbench/architecture-seam.mmd
// -> src/assets/buildlog/stealthbench/architecture-seam.png, imported via <Image>).
//
// This is a LOCAL authoring step, deliberately NOT part of the deploy build:
// the deploy pipeline (astro build -> Docker -> Cloud Run) stays browser-free.
// mermaid-cli is invoked via `pnpm dlx` so it never enters the lockfile / CI
// install. Run this when you add or edit a diagram, then commit the PNG, exactly
// like the matplotlib figures under scripts/plots/.
//
// Usage:
//   pnpm diagram:build                       # render every .mmd under scripts/diagrams/
//   pnpm diagram:build <file.mmd>            # render one source
//   pnpm diagram:build <dir>                 # render every .mmd under a subtree

import { readdirSync, statSync, mkdirSync, existsSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { join, dirname, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const scriptDir = dirname(fileURLToPath(import.meta.url)); // web/scripts/diagrams
const webRoot = resolve(scriptDir, '..', '..'); // web/
const SRC_ROOT = join(webRoot, 'scripts', 'diagrams');
const OUT_ROOT = join(webRoot, 'src', 'assets');
const PPTR_CONFIG = join(scriptDir, 'puppeteer-config.json');

// Pin the renderer to the version these diagrams were authored against, so a
// rerender is reproducible. Bump deliberately.
const MMDC = ['dlx', '@mermaid-js/mermaid-cli@11.16.0'];

// Tuned for crisp, white-background figure cards that match the site's <Image>
// convention (rounded border, shown on both light and dark page themes).
const RENDER_OPTS = ['-b', 'white', '-w', '1600', '-s', '2', '-p', PPTR_CONFIG];

/** Recursively collect *.mmd files, skipping dotdirs and node_modules. */
function findMmd(dir) {
  const out = [];
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    if (entry.name.startsWith('.') || entry.name === 'node_modules') continue;
    const full = join(dir, entry.name);
    if (entry.isDirectory()) out.push(...findMmd(full));
    else if (entry.name.endsWith('.mmd')) out.push(full);
  }
  return out;
}

function collectSources(argPath) {
  if (!argPath) return findMmd(SRC_ROOT);
  const abs = resolve(argPath);
  const st = statSync(abs);
  if (st.isDirectory()) return findMmd(abs);
  if (abs.endsWith('.mmd')) return [abs];
  throw new Error(`Not a .mmd file or directory: ${argPath}`);
}

/** scripts/diagrams/<rel>.mmd  ->  src/assets/<rel>.png */
function outputFor(mmd) {
  const rel = relative(SRC_ROOT, mmd);
  if (rel.startsWith('..')) {
    throw new Error(`Source must live under scripts/diagrams/: ${mmd}`);
  }
  return join(OUT_ROOT, rel.replace(/\.mmd$/, '.png'));
}

const sources = collectSources(process.argv[2]);
if (sources.length === 0) {
  console.error('No .mmd sources found under scripts/diagrams/.');
  process.exit(1);
}

let failed = 0;
for (const mmd of sources) {
  const out = outputFor(mmd);
  mkdirSync(dirname(out), { recursive: true });
  process.stdout.write(`${relative(webRoot, mmd)} -> ${relative(webRoot, out)} ... `);
  const res = spawnSync('pnpm', [...MMDC, '-i', mmd, '-o', out, ...RENDER_OPTS], {
    stdio: ['ignore', 'pipe', 'pipe'],
    encoding: 'utf8',
  });
  if (res.status === 0 && existsSync(out)) {
    console.log('ok');
  } else {
    failed++;
    console.log('FAILED');
    if (res.stderr) process.stderr.write(res.stderr);
    if (res.error) process.stderr.write(`${res.error}\n`);
  }
}

if (failed > 0) {
  console.error(`\n${failed} of ${sources.length} diagram(s) failed to render.`);
  process.exit(1);
}
console.log(`\nRendered ${sources.length} diagram(s).`);
