// web/scripts/read-posts.ts
// The single reader for scheduled content. Walks web/src/content/{blog,buildlog}
// for .mdx files and hands each one to content-core, which decides whether it is
// publishable and what its URL is. Consumers: digest.ts, check-publish.ts.
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { malformedPubDate, toDigestItem } from '../src/lib/content-core.ts';
import type { DigestItem } from '../src/lib/digest-core.ts';

export interface PostFile {
  item: DigestItem;
  /** Repo-root-relative, forward slashes — the form git prints paths in. */
  repoPath: string;
}

/** A publishable file whose pubDate could not be parsed. Surfaced, never silently dropped. */
export interface InvalidPost {
  repoPath: string;
  rawPubDate: string;
}

export interface PostScan {
  posts: PostFile[];
  invalid: InvalidPost[];
}

/** Absolute path to web/src/content, resolved from this file, not from cwd. */
const CONTENT_DIR = fileURLToPath(new URL('../src/content', import.meta.url));

/** The two content roots, in digest order. */
const ROOTS = ['blog', 'buildlog'] as const;

/** Recursively list *.mdx under a directory. */
function listMdx(dir: string): string[] {
  const out: string[] = [];
  for (const name of readdirSync(dir)) {
    const full = `${dir}/${name}`;
    if (statSync(full).isDirectory()) out.push(...listMdx(full));
    else if (name.endsWith('.mdx')) out.push(full);
  }
  return out;
}

/**
 * Every publishable post, plus any publishable file whose pubDate could not be
 * parsed. Drafts and pubDate-less files are dropped by content-core; they are
 * not scheduled to publish, so they are neither a post nor invalid.
 */
export function readPosts(): PostScan {
  const posts: PostFile[] = [];
  const invalid: InvalidPost[] = [];
  for (const root of ROOTS) {
    const dir = `${CONTENT_DIR}/${root}`;
    for (const file of listMdx(dir)) {
      const relPath = `${root}/${file.slice(dir.length + 1)}`;
      const repoPath = `web/src/content/${relPath}`;
      const src = readFileSync(file, 'utf8');
      const rawPubDate = malformedPubDate(src);
      if (rawPubDate) {
        invalid.push({ repoPath, rawPubDate });
        continue;
      }
      const item = toDigestItem(relPath, src);
      if (item) posts.push({ item, repoPath });
    }
  }
  return { posts, invalid };
}
