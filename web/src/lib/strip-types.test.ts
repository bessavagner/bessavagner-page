// web/src/lib/strip-types.test.ts
// Regression guard: vitest transpiles TypeScript with esbuild, which accepts
// TypeScript-only syntax (e.g. constructor parameter properties) that Node's
// `--experimental-strip-types` rejects in strip-only mode. Production runs these
// modules under that exact runtime — `ops/systemd/run-check.sh` and
// `.github/workflows/scheduled-publish.yml` both invoke scripts with
// `node --experimental-strip-types` — so a module that only "works" under esbuild
// crashes the nightly check and the CI digest at import time. This test spawns
// real `node --experimental-strip-types` subprocesses to import each covered
// module and fails loudly, naming the module, if any of them can't load.
//
// Coverage is limited to modules that are side-effect-free on import (no git
// commands, no network, no filesystem work at module scope):
//   - src/lib/publication.ts
//   - src/lib/review-hash.ts
//   - src/lib/review-verify.ts
//   - src/lib/content-core.ts
//   - src/lib/digest-core.ts
//
// Deliberately NOT covered: scripts/check-publish.ts and scripts/digest.ts —
// both execute real work (git commands, network calls) as soon as they're
// imported, so spawning them here would make this test slow and non-hermetic.
// When Task 5 rewrites scripts/read-posts.ts into a pure module, add it to the
// list below.
import { describe, it, expect } from 'vitest';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const modules = [
  'publication.ts',
  'review-hash.ts',
  'review-verify.ts',
  'content-core.ts',
  'digest-core.ts',
];

describe('modules load under node --experimental-strip-types', () => {
  for (const moduleName of modules) {
    it(`${moduleName} imports cleanly under strip-only mode`, () => {
      const absPath = fileURLToPath(new URL(moduleName, import.meta.url));

      try {
        execFileSync(
          process.execPath,
          ['--experimental-strip-types', '--input-type=module', '-e', `await import(${JSON.stringify(`file://${absPath}`)})`],
          { stdio: 'pipe' },
        );
      } catch (err) {
        const stderr = (err as { stderr?: Buffer }).stderr?.toString() ?? String(err);
        throw new Error(
          `${moduleName} failed to load under node --experimental-strip-types:\n${stderr}`,
        );
      }
    });
  }
});
