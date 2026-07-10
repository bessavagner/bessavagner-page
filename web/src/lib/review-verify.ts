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

  constructor(specifier: string, from: string) {
    super(`cannot resolve asset "${specifier}" referenced by ${from}`);
    this.name = 'UnresolvedAssetError';
    this.specifier = specifier;
    this.from = from;
  }
}

/** Digest each specifier's bytes, resolved relative to the post that references it. */
export function hashAssets(postAbsPath: string, specifiers: string[]): AssetDigest[] {
  const base = dirname(postAbsPath);
  return specifiers.map((specifier) => {
    const abs = resolve(base, specifier);
    let bytes: Buffer;
    try {
      bytes = readFileSync(abs);
    } catch {
      throw new UnresolvedAssetError(specifier, postAbsPath);
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
