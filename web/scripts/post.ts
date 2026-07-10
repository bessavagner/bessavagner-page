// web/scripts/post.ts
// CLI for the publication workflow: stamp an approval, list every post's
// PublicationState, catch posts missing `status`, and preview what ships soon.
// A thin layer over read-posts.ts + publication.ts + review-verify.ts — the
// only logic of its own is CLI formatting and approve's textual frontmatter
// rewrite.
import { readFileSync, writeFileSync } from 'node:fs';
import { isAbsolute, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { parse as parseYaml } from 'yaml';
import { splitFrontmatter } from '../src/lib/content-core.ts';
import type { PublicationStatus } from '../src/lib/publication.ts';
import { reviewHashOf, type PostFrontmatter } from '../src/lib/review-verify.ts';
import { readPosts } from './read-posts.ts';

/** Resolve a CLI-supplied path against the current working directory. Scripts that
 *  scan the content tree resolve from import.meta.url; this resolves a path the
 *  user typed, which is inherently relative to wherever they ran the command. */
function resolveTarget(arg: string): string {
  return isAbsolute(arg) ? arg : resolve(process.cwd(), arg);
}

/**
 * Replace/insert exactly the keys in `values` inside a frontmatter YAML block,
 * in the position order given by `order`. Every other line, and the position of
 * a key that already exists, is preserved untouched; a key with no existing
 * line is appended in `order`. Never round-trips through `stringify`, which
 * would reorder keys and strip comments.
 *
 * Splits on `\r?\n` (not a bare `\n`) so a CRLF source doesn't leave stray `\r`
 * characters glued to the end of untouched lines, and rejoins with `eol` — the
 * caller's job is to pass the file's own dominant line ending so a CRLF file
 * stays CRLF and an LF file stays LF.
 */
export function rewriteKeys(yaml: string, values: Record<string, string>, order: string[], eol: string): string {
  const remaining = new Set(order);
  const lines = yaml.split(/\r?\n/).map((line) => {
    const m = line.match(/^([A-Za-z_][A-Za-z0-9_]*):/);
    if (m && remaining.has(m[1])) {
      remaining.delete(m[1]);
      return `${m[1]}: ${values[m[1]]}`;
    }
    return line;
  });
  for (const key of order) {
    if (remaining.has(key)) lines.push(`${key}: ${values[key]}`);
  }
  return lines.join(eol);
}

/** A file's dominant line ending: CRLF if any `\r\n` is present, else LF. */
export function detectEol(src: string): string {
  return src.includes('\r\n') ? '\r\n' : '\n';
}

/** Thrown by approvePost for a condition the CLI reports and exits 1 on, rather
 *  than a bug — no frontmatter block, or an approval that's already current. */
export class ApproveError extends Error {}

/**
 * Stamp `status: approved`, `reviewedAt`, and `reviewHash` into a post's
 * frontmatter on disk, preserving whichever line ending (CRLF or LF) the file
 * already used throughout — the fence delimiters and the rewritten YAML lines
 * are joined with that same ending, so they never end up mismatched against
 * the untouched lines and the body. Returns the computed hash.
 */
export function approvePost(absPath: string): string {
  const src = readFileSync(absPath, 'utf8');
  const split = splitFrontmatter(src);
  if (!split) throw new ApproveError(`${absPath}: no frontmatter block`);

  const raw = (parseYaml(split.yaml) ?? {}) as Record<string, unknown>;
  const status: PublicationStatus = (raw.status as PublicationStatus | undefined) ?? 'draft';
  const data: PostFrontmatter = {
    title: (raw.title as string | undefined) ?? '',
    description: (raw.description as string | undefined) ?? '',
    tags: raw.tags as string[] | undefined,
    heroImage: raw.heroImage as string | undefined,
    heroImageDark: raw.heroImageDark as string | undefined,
  };
  const hash = reviewHashOf(absPath, { body: split.body, data });

  if (status === 'approved' && raw.reviewHash === hash) {
    throw new ApproveError(`${absPath}: already approved and unchanged since — nothing to do`);
  }

  const eol = detectEol(src);
  const reviewedAt = new Date().toISOString();
  const newYaml = rewriteKeys(
    split.yaml,
    { status: 'approved', reviewedAt, reviewHash: hash },
    ['status', 'reviewedAt', 'reviewHash'],
    eol,
  );
  writeFileSync(absPath, `---${eol}${newYaml}${eol}---${eol}${split.body}`);
  return hash;
}

function cmdApprove(argv: string[]): void {
  const arg = argv[0];
  if (!arg) {
    console.error('usage: post approve <path>');
    process.exit(1);
  }
  const absPath = resolveTarget(arg);
  try {
    const hash = approvePost(absPath);
    console.log(`${arg}: approved (${hash})`);
  } catch (err) {
    console.error(err instanceof ApproveError ? err.message : String(err));
    process.exit(1);
  }
}

function cmdStatus(): void {
  const { posts } = readPosts();
  const sorted = [...posts].sort((a, b) => a.data.pubDate.getTime() - b.data.pubDate.getTime());
  for (const p of sorted) {
    console.log(`${p.state}  ${p.repoPath}  ${p.data.pubDate.toISOString()}`);
  }
}

/** `contentDir` is exposed only so tests can point this at a fixture tree; the
 *  CLI always calls this with no argument, which resolves the real content dir. */
export function cmdLint(contentDir?: string): void {
  const { posts, invalid } = readPosts(Date.now(), contentDir);
  const missing = posts.filter((p) => {
    const split = splitFrontmatter(readFileSync(p.absPath, 'utf8'));
    return !split || !/^status:/m.test(split.yaml);
  });

  if (missing.length === 0 && invalid.length === 0) {
    console.log('OK — every post declares status.');
    return;
  }

  if (missing.length > 0) {
    for (const p of missing) console.log(p.repoPath);
    console.error(`\n${missing.length} post${missing.length === 1 ? '' : 's'} missing status.`);
  }

  if (invalid.length > 0) {
    for (const p of invalid) console.log(`${p.repoPath}  pubDate: ${p.rawPubDate}`);
    console.error(`\n${invalid.length} post${invalid.length === 1 ? '' : 's'} with an unparsable pubDate.`);
  }

  process.exit(1);
}

function parseDays(argv: string[]): number {
  const eq = argv.find((a) => a.startsWith('--days='));
  if (eq) return Number(eq.split('=')[1]);
  const i = argv.indexOf('--days');
  if (i !== -1 && argv[i + 1]) return Number(argv[i + 1]);
  return 7;
}

/** `contentDir` is exposed only so tests can point this at a fixture tree; the
 *  CLI always calls this with no argument, which resolves the real content dir. */
export function cmdPreview(argv: string[], contentDir?: string): void {
  const days = parseDays(argv);
  const now = Date.now();
  const windowEnd = now + days * 24 * 60 * 60 * 1000;

  const { posts } = readPosts(now, contentDir);
  const upcoming = posts.filter((p) => {
    const due = p.data.pubDate.getTime();
    return p.state === 'stale-approval' || (due >= now && due <= windowEnd);
  });
  const sorted = [...upcoming].sort((a, b) => a.data.pubDate.getTime() - b.data.pubDate.getTime());

  const lines: string[] = [`# Shipping in the next ${days} day${days === 1 ? '' : 's'}`, ''];
  if (sorted.length === 0) {
    lines.push('Nothing scheduled.');
  } else {
    for (const p of sorted) {
      const title = p.data.title || p.repoPath;
      lines.push(`- **${title}** — ${p.state} — ${p.data.pubDate.toISOString()} — \`${p.repoPath}\``);
    }
  }
  console.log(lines.join('\n'));
}

// Only run the CLI dispatch when this file is the process entry point (`node
// scripts/post.ts ...`), not when it's imported for its functions — e.g. by
// scripts/post.test.ts, which unit-tests rewriteKeys/detectEol directly and
// must not trigger a real command on import.
const isMain = process.argv[1] !== undefined && fileURLToPath(import.meta.url) === resolve(process.argv[1]);

if (isMain) {
  const [, , cmd, ...rest] = process.argv;

  switch (cmd) {
    case 'approve':
      cmdApprove(rest);
      break;
    case 'status':
      cmdStatus();
      break;
    case 'lint':
      cmdLint();
      break;
    case 'preview':
      cmdPreview(rest);
      break;
    default:
      console.error('usage: post <approve <path>|status|lint|preview [--days N]>');
      process.exit(1);
  }
}
