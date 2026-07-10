import { getCollection, type CollectionEntry } from 'astro:content';
import { isVisible } from './publication.ts';
import { hashMatches } from './review-map.ts';
import { resolvePublishAt } from './clock.ts';

export type Post = CollectionEntry<'blog'>;

/**
 * Whether a post is publicly visible.
 *
 * Defers to the one publication rule in `publication.ts`: in dev everything shows,
 * and in a production build a post is visible only when it is `approved`, its
 * `reviewHash` still matches its content on disk, and its `pubDate` has arrived. A
 * scheduled rebuild on the post's date surfaces it automatically. This is the
 * blog's single entry point to that rule; the index, post pages, and OG routes
 * all use it.
 */
export function isPublic(p: Post): boolean {
  return isVisible(
    { status: p.data.status, pubDate: p.data.pubDate, hashMatches: hashMatches(p) },
    { now: resolvePublishAt(process.env, Date.now()), prod: import.meta.env.PROD },
  );
}

/** Published posts (drafts/future excluded in production), newest first. */
export async function getPublishedPosts(): Promise<Post[]> {
  const posts = await getCollection('blog', isPublic);
  return posts.sort((a, b) => b.data.pubDate.getTime() - a.data.pubDate.getTime());
}

/** Unique tags across published posts, alphabetical. */
export async function getAllTags(): Promise<string[]> {
  const posts = await getPublishedPosts();
  return [...new Set(posts.flatMap((p) => p.data.tags))].sort();
}

/** Whole-minute reading estimate at 200 wpm, minimum 1. */
export function readingTime(text: string): number {
  const words = text.trim().split(/\s+/).filter(Boolean).length;
  return Math.max(1, Math.round(words / 200));
}

export function formatDate(d: Date): string {
  return d.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
}
