// web/src/lib/review-verify.ts
// The fs half of the review hash: resolve a post's assets from disk, digest their
// bytes, and hand a complete payload to the pure hasher in review-hash.ts.
//
// An asset that cannot be resolved is a hard error. Hashing around it would let an
// approval survive a file that no longer exists — the opposite of the guarantee.
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { computeReviewHash, extractAssetSpecifiers, type AssetDigest } from './review-hash.ts';

/**
 * Raw frontmatter as read from an .mdx file's YAML header.
 *
 * The fields `heroImage` and `heroImageDark` are strings as they appear in the
 * file — paths to image assets. Do NOT pass an Astro `CollectionEntry`'s `data`
 * directly to `hashAssets()`, as Astro's `image()` schema helper in
 * `web/src/content.config.ts` resolves those strings to `ImageMetadata` objects
 * at parse time, which would produce incorrect specifiers or a crash.
 */
export interface PostFrontmatter {
  title: string;
  description: string;
  tags?: string[];
  heroImage?: string;
  heroImageDark?: string;
}

export class UnresolvedAssetError extends Error {
  readonly specifier: string;
  readonly from: string;

  constructor(specifier: string, from: string, options?: ErrorOptions) {
    super(`cannot resolve asset "${specifier}" referenced by ${from}`, options);
    this.name = 'UnresolvedAssetError';
    this.specifier = specifier;
    this.from = from;
  }
}

/** Digest each specifier's bytes, resolved relative to the post that references it. */
export function hashAssets(postAbsPath: string, specifiers: string[]): AssetDigest[] {
  const base = dirname(postAbsPath);
  return specifiers.map((specifier) => {
    let bytes: Buffer;
    try {
      const abs = resolve(base, specifier);
      bytes = readFileSync(abs);
    } catch (err) {
      throw new UnresolvedAssetError(specifier, postAbsPath, { cause: err });
    }
    return { specifier, sha256: createHash('sha256').update(bytes).digest('hex') };
  });
}

/** The reviewHash a post's current content on disk would produce. */
export function reviewHashOf(
  postAbsPath: string,
  parsed: { body: string; data: PostFrontmatter },
): string {
  const specifiers = extractAssetSpecifiers(parsed.body, {
    heroImage: parsed.data.heroImage,
    heroImageDark: parsed.data.heroImageDark,
  });
  return computeReviewHash({
    body: parsed.body,
    title: parsed.data.title,
    description: parsed.data.description,
    tags: parsed.data.tags ?? [],
    assets: hashAssets(postAbsPath, specifiers),
  });
}
