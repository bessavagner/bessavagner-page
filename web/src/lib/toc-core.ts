// web/src/lib/toc-core.ts
// Pure heading logic for the table of contents. `import type` is stripped at
// runtime, so this file runs under `node --test` with no `astro` dependency.
import type { MarkdownHeading } from 'astro';

/** The h2/h3 headings the TOC renders (deeper levels are noise). */
export function tocEntries(headings: MarkdownHeading[]): MarkdownHeading[] {
  return headings.filter((h) => h.depth === 2 || h.depth === 3);
}

/** Show the TOC only on genuinely long posts: at least `min` h2/h3 headings
 *  (default 3), so a post with one subhead no longer shows a 1-item TOC. */
export function shouldRenderToc(headings: MarkdownHeading[], min = 3): boolean {
  return tocEntries(headings).length >= min;
}
