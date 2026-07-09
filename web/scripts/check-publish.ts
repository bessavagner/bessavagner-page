// web/scripts/check-publish.ts
// Fails when a post whose pubDate has passed is not on origin/main — because it
// was never committed, or committed and never pushed. Run locally (see the
// systemd timer in ops/systemd/); CI structurally cannot catch this, since an
// Action checks out the remote, which by definition lacks the missing file.
//
// Offline is a warning, never a silent pass: if origin cannot be reached the
// script says so, and still reports every untracked post it can see.
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { utcDateStamp } from '../src/lib/digest-core.ts';
import { readPosts } from './read-posts.ts';

const REPO_ROOT = fileURLToPath(new URL('../..', import.meta.url));
const CONTENT_DIR = 'web/src/content';
const DAY_MS = 24 * 60 * 60 * 1000;

/** Run git at the repo root and return stdout. Throws on a non-zero exit. */
function git(...args: string[]): string {
  return execFileSync('git', args, {
    cwd: REPO_ROOT,
    encoding: 'utf8',
    stdio: ['ignore', 'pipe', 'pipe'],
  });
}

const lines = (s: string): string[] => s.split('\n').filter(Boolean);
const reason = (err: unknown): string => (err instanceof Error ? err.message.split('\n')[0] : String(err));

const warnings: string[] = [];
const failures: string[] = [];

// 1. Refresh origin/main so the comparison is not against a stale ref.
//    A fetch failure (offline, no remote) is a warning, not a crash.
try {
  git('fetch', 'origin', 'main', '--quiet');
} catch (err) {
  warnings.push(`could not fetch origin — origin/main may be stale (${reason(err)})`);
}

// 2. What content files exist on origin/main? Null when the ref is unresolvable,
//    in which case only the untracked check below can run.
let onOrigin: Set<string> | null = null;
try {
  git('rev-parse', '--verify', '--quiet', 'origin/main');
  onOrigin = new Set(lines(git('ls-tree', '-r', '--name-only', 'origin/main', '--', CONTENT_DIR)));
} catch {
  warnings.push('origin/main could not be resolved — only untracked files were checked');
}

// 3. What content files does git not know about at all? This works offline.
const untracked = new Set(lines(git('ls-files', '--others', '--exclude-standard', '--', CONTENT_DIR)));

type State = 'ok' | 'untracked' | 'unpushed' | 'unknown';

function stateOf(repoPath: string): State {
  if (untracked.has(repoPath)) return 'untracked';
  if (onOrigin === null) return 'unknown'; // tracked, but we cannot see the remote
  return onOrigin.has(repoPath) ? 'ok' : 'unpushed';
}

const EXPLAIN: Record<'untracked' | 'unpushed', string> = {
  untracked: 'untracked — never committed',
  unpushed: 'committed but not on origin/main — never pushed',
};

const now = Date.now();

for (const { item, repoPath } of readPosts()) {
  const state = stateOf(repoPath);
  if (state === 'ok' || state === 'unknown') continue;

  const due = item.pubDate.getTime();
  const line = `${repoPath}\n      due ${utcDateStamp(item.pubDate)} — ${EXPLAIN[state]}`;

  if (due <= now) failures.push(line);
  else if (due <= now + DAY_MS) warnings.push(`${line} (due within 24h)`);
}

for (const w of warnings) console.warn(`WARN  ${w}`);
for (const f of failures) console.error(`FAIL  ${f}`);

if (failures.length > 0) {
  const n = failures.length;
  console.error(`\n${n} post${n === 1 ? ' is' : 's are'} due but not on origin/main. Commit and push.`);
  process.exit(1);
}

console.log(`OK — every due post is on origin/main.${warnings.length > 0 ? ' (with warnings)' : ''}`);
