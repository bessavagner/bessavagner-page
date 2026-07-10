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
 * Blank out fenced code regions (``` or ~~~, up to 3 spaces of indent, optional
 * info string, closing fence at least as long as the opening one — per
 * CommonMark) so a documentation example like `import chart from './example.svg'`
 * shown inside a fence isn't mistaken for a real top-level import. MDX requires
 * real imports at the top level of the document, never inside a fence, so
 * nothing legitimate is lost.
 *
 * Fenced lines are replaced with empty lines rather than deleted to preserve
 * line numbers and line boundaries, and blank lines double as the block
 * separators `extractAssetSpecifiers` splits on below.
 *
 * The import regex's `[^'"]*` negated character class spans newlines freely,
 * so scanning the whole body would let a line beginning with `import` in the
 * middle of a paragraph bridge forward into an unrelated later `from '...'`
 * line and fabricate a specifier. `extractAssetSpecifiers` guards against that
 * by only scanning blocks whose first line begins with `import` — the same
 * rule MDX itself uses to decide whether a line is an ESM statement. A
 * mid-paragraph `import` is prose to MDX, and is now prose to us too.
 */
function stripFencedCode(body: string): string {
  const lines = body.split('\n');
  const openRe = /^ {0,3}(`{3,}|~{3,})/;
  const out: string[] = [];
  let i = 0;
  while (i < lines.length) {
    const open = lines[i].match(openRe);
    if (!open) {
      out.push(lines[i]);
      i++;
      continue;
    }
    const fenceChar = open[1][0];
    const fenceLen = open[1].length;
    const closeRe = new RegExp(`^ {0,3}[${fenceChar}]{${fenceLen},}\\s*$`);
    out.push(''); // opening fence line
    i++;
    while (i < lines.length && !closeRe.test(lines[i])) {
      out.push('');
      i++;
    }
    if (i < lines.length) {
      out.push(''); // closing fence line
      i++;
    }
  }
  return out.join('\n');
}

/**
 * Strip JS comments from an import-led block before the import regex runs, so
 * a comment sitting between `import` and the specifier (valid whitespace in an
 * import declaration) can't have its own quoted text mistaken for the real
 * specifier, and so a commented-out `from '...'` can't hide the real one.
 *
 * Block comments are removed outright — `/*` is not a legal substring of a
 * file path. Line comments are removed only where `//` is preceded by
 * start-of-line or whitespace, and only that whitespace is kept in place of
 * the match: a specifier's own `//` (a path segment boundary, e.g.
 * `./a//b.svg`, or a URL scheme, e.g. `https://cdn/x.js`) is always preceded
 * by a non-whitespace character and is left untouched.
 *
 * This is regex-based, not a real JS tokenizer, so it does not understand
 * string literals: a `//` or `/*` that happens to sit inside some other part
 * of the statement (outside the specifier itself) could still be misread.
 */
function stripComments(block: string): string {
  return block.replace(/\/\*[\s\S]*?\*\//g, '').replace(/(^|\s)\/\/[^\n]*/g, '$1');
}

/**
 * Every local asset the post depends on, deduplicated and sorted — import order is
 * not content. Sources: the body's `import x from '<spec>'` statements outside
 * fenced code blocks, and the heroImage / heroImageDark frontmatter fields.
 */
export function extractAssetSpecifiers(
  body: string,
  frontmatter: { heroImage?: string; heroImageDark?: string },
): string[] {
  const found = new Set<string>();
  const importRe = /^\s*import\s+[^'"]*from\s*['"]([^'"]+)['"]/gm;
  // Normalize CRLF to LF first, same as normalizeBody: the block-splitting
  // regex below only recognizes \n-bounded blank lines, and a CRLF blank line
  // is \r\n\r\n (\n \r \n) — the stray \r blocks the split, so an
  // un-normalized CRLF body never splits into blocks at all and no import
  // anywhere in it is found.
  const normalized = body.replace(/\r\n/g, '\n');
  // MDX only treats a line beginning with `import` as ESM when that line
  // begins a block (document start, or right after a blank line) — so only
  // scan blocks whose first line begins with `import`. A mid-paragraph line
  // starting with the word "import" is prose and must not be scanned.
  for (const rawBlock of stripFencedCode(normalized).split(/\n(?:[ \t]*\n)+/)) {
    // A leading blank line (e.g. right after frontmatter) survives the split
    // as part of the first block instead of being consumed as a separator,
    // since there's no preceding block for it to separate from. Trim it so
    // the block-start check below looks at the block's first real line.
    const block = rawBlock.replace(/^(?:[ \t]*\n)+/, '');
    if (!/^[ \t]{0,3}import\b/.test(block)) continue;
    for (const m of stripComments(block).matchAll(importRe)) {
      if (isLocal(m[1])) found.add(m[1]);
    }
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
 * Locale-independent string comparator: plain UTF-16 code-unit order, the same
 * order the default `.sort()` used on `tags` below produces for strings.
 * `String.prototype.localeCompare()` with no arguments depends on the engine's
 * default locale and bundled ICU/CLDR collation tables (ECMA-402), so it is not
 * guaranteed to agree between machines or Node versions. This digest is stamped
 * on one machine and re-verified on another (CI), so any comparator it uses must
 * be a pure function of the bytes, not of where it happens to run.
 */
const byCodeUnit = (a: string, b: string): number => (a < b ? -1 : a > b ? 1 : 0);

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
    ['assets', [...p.assets].sort((a, b) => byCodeUnit(a.specifier, b.specifier)).map((a) => [a.specifier, a.sha256])],
  ]);
}

export function computeReviewHash(p: ReviewPayload): string {
  return 'sha256:' + createHash('sha256').update(canonicalize(p), 'utf8').digest('hex');
}
