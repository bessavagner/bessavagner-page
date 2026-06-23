import { getCollection, type CollectionEntry } from 'astro:content';

export type Post = CollectionEntry<'blog'>;

/**
 * Whether a post is publicly visible.
 *
 * In dev everything shows (so drafts and future posts stay previewable). In a
 * production build a post is visible only when it is not a draft *and* its
 * `pubDate` has arrived — so a scheduled rebuild on the post's date surfaces it
 * automatically, with no flag flip or commit. This is the single source of
 * truth for visibility; the blog index, post pages, and OG routes all use it.
 */
export function isPublic(p: Post): boolean {
  if (!import.meta.env.PROD) return true;
  if (p.data.draft === true) return false;
  return p.data.pubDate.getTime() <= Date.now();
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
