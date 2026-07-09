// web/scripts/read-posts.ts
// The single reader for scheduled content. Walks web/src/content/{blog,buildlog}
// for .mdx files and hands each one to content-core, which decides whether it is
// publishable and what its URL is. Consumers: digest.ts, check-publish.ts.
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { toDigestItem } from '../src/lib/content-core.ts';
import type { DigestItem } from '../src/lib/digest-core.ts';

export interface PostFile {
  item: DigestItem;
  /** Repo-root-relative, forward slashes — the form git prints paths in. */
  repoPath: string;
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

/** Every publishable post. Drafts and pubDate-less files are dropped by content-core. */
export function readPosts(): PostFile[] {
  const out: PostFile[] = [];
  for (const root of ROOTS) {
    const dir = `${CONTENT_DIR}/${root}`;
    for (const file of listMdx(dir)) {
      const relPath = `${root}/${file.slice(dir.length + 1)}`;
      const item = toDigestItem(relPath, readFileSync(file, 'utf8'));
      if (item) out.push({ item, repoPath: `web/src/content/${relPath}` });
    }
  }
  return out;
}
