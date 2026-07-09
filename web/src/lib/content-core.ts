// web/src/lib/content-core.ts
// Pure frontmatter parsing and content-file -> DigestItem mapping, lifted out of
// scripts/digest.ts so it can be unit-tested. No fs and no network: the caller
// (scripts/read-posts.ts) supplies each file's text and its content-root-relative
// path. This is the only place that knows how a file path becomes a site URL.
import type { DigestItem } from './digest-core.ts';

export interface Frontmatter {
  [k: string]: string;
}

/** Minimal frontmatter parse: the leading --- block, one `key: value` per line. */
export function parseFrontmatter(src: string): Frontmatter | null {
  const m = src.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!m) return null;
  const fm: Frontmatter = {};
  for (const line of m[1].split(/\r?\n/)) {
    const kv = line.match(/^([A-Za-z_]+):\s*(.*)$/);
    if (!kv) continue;
    fm[kv[1]] = kv[2].trim().replace(/^["']|["']$/g, '');
  }
  return fm;
}

/**
 * Map one content file to a DigestItem, or null if it is not publishable.
 *
 * `relPath` is relative to web/src/content and keeps its extension:
 *   blog/<slug>.mdx               -> /blog/<slug>/
 *   buildlog/<project>/<slug>.mdx -> /building/<project>/<slug>/
 *
 * Null is returned for drafts, files without frontmatter or without a pubDate,
 * a pubDate that cannot be parsed into a valid Date, an unrecognised top-level
 * root, and buildlog files that do not sit under a project folder.
 */
export function toDigestItem(relPath: string, src: string): DigestItem | null {
  const fm = parseFrontmatter(src);
  if (!fm || fm.draft === 'true' || !fm.pubDate) return null;

  const rel = relPath.replace(/\.mdx$/, '');
  const cut = rel.indexOf('/');
  if (cut === -1) return null;
  const root = rel.slice(0, cut);
  const rest = rel.slice(cut + 1);

  const pubDate = new Date(fm.pubDate);
  if (Number.isNaN(pubDate.getTime())) return null;
  const description = fm.description ?? '';

  if (root === 'blog') {
    return { kind: 'blog', title: fm.title ?? rest, description, path: `/blog/${rest}/`, pubDate };
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
    title: fm.title ?? slug,
    description,
    path: `/building/${project}/${slug}/`,
    pubDate,
    project,
  };
}

/**
 * The raw `pubDate` of a would-be-publishable file whose date cannot be parsed, or null.
 *
 * Mirrors toDigestItem's publishability gate: drafts and files without frontmatter or a
 * pubDate are not flagged, because they are not scheduled to publish. Astro's z.coerce.date()
 * rejects the same value at build time; this exists so the local tooling can say what it
 * could not read instead of dropping the file silently.
 */
export function malformedPubDate(src: string): string | null {
  const fm = parseFrontmatter(src);
  if (!fm || fm.draft === 'true' || !fm.pubDate) return null;
  return Number.isNaN(new Date(fm.pubDate).getTime()) ? fm.pubDate : null;
}
