// web/src/lib/review-hash.ts
// The canonical form of "what was reviewed", and its digest.
//
// Pure: node:crypto only. No fs — asset bytes are hashed by the caller
// (review-verify.ts) and handed in already digested.
//
// The hash deliberately covers the post's referenced assets. Eight posts import
// chart SVGs and fourteen declare a heroImage; hashing only the .mdx text would
// let a chart be regenerated after approval and published unreviewed, which is
// precisely what this exists to prevent.
//
// It deliberately excludes pubDate and updatedDate: rescheduling a post is not
// un-reviewing it.
import { createHash } from 'node:crypto';

/** LF line endings, no trailing whitespace per line, exactly one trailing newline. */
export function normalizeBody(src: string): string {
  const lines = src.replace(/\r\n/g, '\n').split('\n').map((l) => l.replace(/[ \t]+$/, ''));
  while (lines.length > 0 && lines[lines.length - 1] === '') lines.pop();
  return lines.join('\n') + '\n';
}

/** A local file, not a package: starts with `.` or `/`. */
const isLocal = (spec: string): boolean => spec.startsWith('.') || spec.startsWith('/');

/**
 * Every local asset the post depends on, deduplicated and sorted — import order is
 * not content. Sources: the body's `import x from '<spec>'` statements, and the
 * heroImage / heroImageDark frontmatter fields.
 */
export function extractAssetSpecifiers(
  body: string,
  frontmatter: { heroImage?: string; heroImageDark?: string },
): string[] {
  const found = new Set<string>();
  const importRe = /^\s*import\s+[^'"]*from\s*['"]([^'"]+)['"]/gm;
  for (const m of body.matchAll(importRe)) {
    if (isLocal(m[1])) found.add(m[1]);
  }
  for (const hero of [frontmatter.heroImage, frontmatter.heroImageDark]) {
    if (hero) found.add(hero);
  }
  return [...found].sort();
}

export interface AssetDigest {
  specifier: string;
  sha256: string;
}

export interface ReviewPayload {
  body: string;
  title: string;
  description: string;
  tags: string[];
  assets: AssetDigest[];
}

/**
 * A deterministic string for a payload. Tags and assets are sorted, so reordering
 * them is not a content change. JSON.stringify over an explicit array — never over
 * an object — because object key order is not part of JSON's contract.
 */
export function canonicalize(p: ReviewPayload): string {
  return JSON.stringify([
    ['body', normalizeBody(p.body)],
    ['title', p.title.trim()],
    ['description', p.description.trim()],
    ['tags', [...p.tags].sort()],
    ['assets', [...p.assets].sort((a, b) => a.specifier.localeCompare(b.specifier)).map((a) => [a.specifier, a.sha256])],
  ]);
}

export function computeReviewHash(p: ReviewPayload): string {
  return 'sha256:' + createHash('sha256').update(canonicalize(p), 'utf8').digest('hex');
}
