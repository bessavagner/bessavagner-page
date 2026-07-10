// web/scripts/check-publish.ts
// Guards against the one failure CI structurally cannot see: a post that should be
// live is not on origin/main — because it was never committed, or committed and
// never pushed. An Action checks out the remote, which by definition lacks the
// missing file, so only a local run can catch it. See the systemd timer in
// ops/systemd/.
//
// Its severity model encodes the spec's "better late than wrong": lateness is not
// an incident. A due post still in `review`, or one whose approval went stale, is
// the system working as designed — WARN, exit 0. The FAILs (exit 1) are the two
// states that mean work exists nowhere but this laptop and is at risk of being
// *lost*: a due, live-eligible post that is untracked or unpushed.
//
// Offline is a warning, never a silent pass: if origin cannot be reached the script
// says so, and still reports every untracked post it can see.
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { utcDateStamp } from '../src/lib/digest-core.ts';
import { readPosts } from './read-posts.ts';

const REPO_ROOT = fileURLToPath(new URL('../..', import.meta.url));
const CONTENT_DIR = 'web/src/content';

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

type GitState = 'ok' | 'untracked' | 'unpushed' | 'unknown';

function gitStateOf(repoPath: string): GitState {
  if (untracked.has(repoPath)) return 'untracked';
  if (onOrigin === null) return 'unknown'; // tracked, but we cannot see the remote
  return onOrigin.has(repoPath) ? 'ok' : 'unpushed';
}

const GIT_EXPLAIN: Record<'untracked' | 'unpushed', string> = {
  untracked: 'untracked — never committed',
  unpushed: 'committed but not on origin/main — never pushed',
};

const now = Date.now();

const { posts, invalid } = readPosts();

for (const bad of invalid) {
  warnings.push(`${bad.repoPath} — unparsable pubDate "${bad.rawPubDate}"; cannot tell whether it is due`);
}

for (const { data, state, repoPath } of posts) {
  // Only posts whose date has already passed can be "late". A future post that
  // isn't yet on origin has time to be pushed before it is due.
  if (data.pubDate.getTime() > now) continue;
  if (state === 'published') {
    // Should be live now. Is it safe on origin, or only on this laptop?
    const g = gitStateOf(repoPath);
    if (g === 'untracked' || g === 'unpushed') {
      failures.push(`${repoPath}\n      due ${utcDateStamp(data.pubDate)} — ${GIT_EXPLAIN[g]}`);
    }
    continue;
  }
  // Due but not published: not an incident, just not live yet. Report the state.
  if (state === 'review') {
    warnings.push(`${repoPath}\n      due ${utcDateStamp(data.pubDate)} — in review, not approved`);
  } else if (state === 'stale-approval') {
    warnings.push(`${repoPath}\n      due ${utcDateStamp(data.pubDate)} — stale-approval, approved then edited`);
  }
  // state === 'draft': deliberately held, nothing to report.
}

for (const w of warnings) console.warn(`WARN  ${w}`);
for (const f of failures) console.error(`FAIL  ${f}`);

if (failures.length > 0) {
  const n = failures.length;
  console.error(`\n${n} due post${n === 1 ? ' is' : 's are'} not on origin/main. Commit and push.`);
  process.exit(1);
}

console.log(`OK — every due, published post is on origin/main.${warnings.length > 0 ? ' (with warnings)' : ''}`);
