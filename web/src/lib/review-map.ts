// web/src/lib/review-map.ts
// The build-time bridge between an Astro collection entry and the fs-bound review
// hash. `blog.ts`/`buildlog.ts` cannot compute the hash themselves: `content.config.ts`
// declares `heroImage` with Astro's `image()` helper, so on a `CollectionEntry` it is
// an `ImageMetadata` object, not the `../../assets/...` string `reviewHashOf` needs.
//
// So this module — the ONLY fs-bound one on the render path, by design — walks the
// content tree ONCE at import time, reads each post's RAW frontmatter off disk, and
// computes the hash its current bytes would produce. `hashMatches(entry)` then asks
// whether the entry's stored `reviewHash` still equals that. It runs at build time
// only (Astro SSG); the walk is memoized, not repeated per entry.
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { resolve } from 'node:path';
import { parse as parseYaml } from 'yaml';
import { splitFrontmatter } from './content-core.ts';
import { reviewHashOf, UnresolvedAssetError, type PostFrontmatter } from './review-verify.ts';

// The Astro project root (web/). This module is bundled into dist/ during the
// build, so `import.meta.url` no longer points at src/lib/ — but `astro build`
// and `astro dev` both run with cwd at the project root, and `entry.filePath` is
// reported relative to that same root, so both sides resolve consistently.
const SITE_ROOT = process.cwd();
const CONTENT_DIR = resolve(SITE_ROOT, 'src/content');

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
 * Absolute post path -> the reviewHash its content on disk currently produces, or
 * null when an asset it references cannot be resolved (a stale approval that must
 * never match). Computed once at module load.
 */
function buildDiskHashes(): Map<string, string | null> {
  const map = new Map<string, string | null>();
  for (const root of ['blog', 'buildlog']) {
    const dir = resolve(CONTENT_DIR, root);
    for (const absPath of listMdx(dir)) {
      const split = splitFrontmatter(readFileSync(absPath, 'utf8'));
      if (!split) continue;
      const raw = (parseYaml(split.yaml) ?? {}) as Record<string, unknown>;
      const data: PostFrontmatter = {
        title: (raw.title as string | undefined) ?? '',
        description: (raw.description as string | undefined) ?? '',
        tags: raw.tags as string[] | undefined,
        heroImage: raw.heroImage as string | undefined,
        heroImageDark: raw.heroImageDark as string | undefined,
      };
      try {
        map.set(absPath, reviewHashOf(absPath, { body: split.body, data }));
      } catch (err) {
        if (err instanceof UnresolvedAssetError) map.set(absPath, null);
        else throw err;
      }
    }
  }
  return map;
}

const diskHashes = buildDiskHashes();

/** The shape both collections' entries share for this check. */
interface ReviewableEntry {
  /** Relative to the site root (web/); Astro 7's `DataEntry.filePath`. */
  filePath?: string;
  data: { reviewHash?: string };
}

/**
 * Does this entry's stored `reviewHash` still match its content on disk? False when
 * the entry has no stored hash, no resolvable file, or its assets can no longer be
 * resolved — in every uncertain case it fails closed, so `publicationState` treats
 * a broken approval as `stale-approval` rather than shipping it.
 */
export function hashMatches(entry: ReviewableEntry): boolean {
  const stored = entry.data.reviewHash;
  if (!stored || !entry.filePath) return false;
  const disk = diskHashes.get(resolve(SITE_ROOT, entry.filePath));
  return disk != null && disk === stored;
}
