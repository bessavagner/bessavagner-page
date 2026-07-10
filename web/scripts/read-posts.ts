// web/scripts/read-posts.ts
// The single reader for scheduled content. Walks web/src/content/{blog,buildlog}
// for .mdx files, splits frontmatter, parses it as real YAML (the same parser
// Astro uses), and hands each post its PublicationState. Consumers: digest.ts,
// check-publish.ts, scripts/post.ts.
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { parse as parseYaml } from 'yaml';
import { splitFrontmatter, toDigestItem } from '../src/lib/content-core.ts';
import type { DigestItem } from '../src/lib/digest-core.ts';
import { publicationState, type PublicationStatus } from '../src/lib/publication.ts';
import { reviewHashOf, UnresolvedAssetError } from '../src/lib/review-verify.ts';

export interface PostData {
  title: string;
  description: string;
  pubDate: Date;
  tags: string[];
  status: PublicationStatus;
  reviewHash?: string;
  heroImage?: string;
  heroImageDark?: string;
}

export interface PostFile {
  absPath: string;
  /** Repo-root-relative, forward slashes — the form git prints paths in. */
  repoPath: string;
  body: string;
  data: PostData;
  state: ReturnType<typeof publicationState>;
  item: ReturnType<typeof toDigestItem>;
  /**
   * Mirrors the pre-migration `draft: boolean` frontmatter key, which every post in
   * the content tree still carries — `status` does not exist on disk yet, so every
   * post's `state` above is 'draft' regardless of this flag (see publication.ts).
   * Not part of the new publication model; it exists only so digest.ts and
   * check-publish.ts, whose selection logic Tasks 6/8 own, can keep excluding the
   * same posts they exclude today until Task 6 migrates the schema and this field
   * goes away. post:status/post:lint/post:preview ignore it — they report every post.
   */
  legacyDraft: boolean;
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

/** yaml's core schema returns YYYY-MM-DD scalars as plain strings, not Dates
 *  (unlike js-yaml's default schema). Accept either shape defensively. */
function toDate(raw: unknown): Date | null {
  if (raw instanceof Date) return raw;
  if (typeof raw === 'string') {
    const d = new Date(raw);
    return Number.isNaN(d.getTime()) ? null : d;
  }
  return null;
}

/**
 * Every post under both content roots, with its parsed frontmatter and
 * PublicationState, plus any post whose pubDate could not be parsed at all
 * (surfaced as `invalid`, never silently dropped).
 */
export function readPosts(now: number = Date.now()): PostScan {
  const posts: PostFile[] = [];
  const invalid: InvalidPost[] = [];
  for (const root of ROOTS) {
    const dir = `${CONTENT_DIR}/${root}`;
    for (const file of listMdx(dir)) {
      const relPath = `${root}/${file.slice(dir.length + 1)}`;
      const repoPath = `web/src/content/${relPath}`;
      const src = readFileSync(file, 'utf8');
      const split = splitFrontmatter(src);
      if (!split) continue; // no frontmatter at all: not a post

      const raw = (parseYaml(split.yaml) ?? {}) as Record<string, unknown>;
      const pubDate = toDate(raw.pubDate);
      if (raw.pubDate !== undefined && pubDate === null) {
        invalid.push({ repoPath, rawPubDate: String(raw.pubDate) });
        continue;
      }
      if (!pubDate) continue; // no pubDate: not scheduled, not a post

      const status: PublicationStatus = (raw.status as PublicationStatus | undefined) ?? 'draft';
      const data: PostData = {
        title: (raw.title as string | undefined) ?? '',
        description: (raw.description as string | undefined) ?? '',
        pubDate,
        tags: (raw.tags as string[] | undefined) ?? [],
        status,
        reviewHash: raw.reviewHash as string | undefined,
        heroImage: raw.heroImage as string | undefined,
        heroImageDark: raw.heroImageDark as string | undefined,
      };

      let hashMatches = false;
      if (status === 'approved' && data.reviewHash) {
        try {
          hashMatches = reviewHashOf(file, { body: split.body, data }) === data.reviewHash;
        } catch (err) {
          if (err instanceof UnresolvedAssetError) hashMatches = false;
          else throw err;
        }
      }

      const state = publicationState({ status, pubDate, hashMatches }, { now, prod: true });
      const item = toDigestItem(relPath, { title: data.title, description: data.description, pubDate });
      const legacyDraft = raw.draft === true;

      posts.push({ absPath: file, repoPath, body: split.body, data, state, item, legacyDraft });
    }
  }
  return { posts, invalid };
}
