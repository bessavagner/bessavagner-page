// web/src/lib/content-core.ts
// Pure content-file -> DigestItem mapping, lifted out of scripts/digest.ts so it
// can be unit-tested. No fs and no network: the caller (scripts/read-posts.ts)
// supplies each file's already-parsed frontmatter and its content-root-relative
// path. This is the only place that knows how a file path becomes a site URL.
import type { DigestItem } from './digest-core.ts';

/** Split the leading `---` block from the body. Null when a post has no frontmatter. */
export function splitFrontmatter(src: string): { yaml: string; body: string } | null {
  const m = src.match(/^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n)?/);
  if (!m) return null;
  return { yaml: m[1], body: src.slice(m[0].length) };
}

/** The subset of a post's parsed frontmatter that route-mapping needs. */
export interface DigestItemInput {
  title?: string;
  description?: string;
  pubDate: Date;
}

/**
 * Map one content file to a DigestItem, or null if its path is not publishable.
 *
 * `relPath` is relative to web/src/content and keeps its extension:
 *   blog/<slug>.mdx               -> /blog/<slug>/
 *   buildlog/<project>/<slug>.mdx -> /building/<project>/<slug>/
 *
 * Takes already-parsed frontmatter — whether a post is a draft, in review, or has
 * an unparsable pubDate is decided by the caller (read-posts.ts) before this is
 * called. Null is returned only for an unrecognised top-level root, and for
 * buildlog files that do not sit under a project folder.
 */
export function toDigestItem(relPath: string, data: DigestItemInput): DigestItem | null {
  const rel = relPath.replace(/\.mdx$/, '');
  const cut = rel.indexOf('/');
  if (cut === -1) return null;
  const root = rel.slice(0, cut);
  const rest = rel.slice(cut + 1);

  const description = data.description ?? '';

  if (root === 'blog') {
    return { kind: 'blog', title: data.title ?? rest, description, path: `/blog/${rest}/`, pubDate: data.pubDate };
  }
  if (root !== 'buildlog') return null;

  // URL parts come from the folder path — the same id the /building route splits
  // on — not from frontmatter, so nested slugs stay consistent with the route.
  const split = rest.indexOf('/');
  if (split === -1) return null; // updates always live under a project folder
  const project = rest.slice(0, split);
  const slug = rest.slice(split + 1);
  return {
    kind: 'building',
    title: data.title ?? slug,
    description,
    path: `/building/${project}/${slug}/`,
    pubDate: data.pubDate,
    project,
  };
}
