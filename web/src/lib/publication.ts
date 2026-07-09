// web/src/lib/publication.ts
// The single source of truth for whether a post is visible.
//
// Pure by construction: no fs, no network, no astro:content, no Date.now(), no
// import.meta. `now` and `prod` arrive as arguments. Four previous copies of this
// rule — in blog.ts, buildlog-core.ts, content-core.ts and check-publish.ts —
// drifted apart and caused every publishing incident to date. There is one now.

export const PUBLICATION_STATUSES = ['draft', 'review', 'approved'] as const;
export type PublicationStatus = (typeof PUBLICATION_STATUSES)[number];

/**
 * Where a post sits on the road to being live.
 *
 * `stale-approval` is the interesting one: the post was approved, then its content
 * changed, so the approval no longer refers to what would be published. It is
 * hidden and reported, never silently shipped.
 */
export type PublicationState = 'draft' | 'review' | 'stale-approval' | 'scheduled' | 'published';

export interface PublicationFacts {
  status: PublicationStatus;
  pubDate: Date;
  /** Whether the post's stored reviewHash still matches its content. See review-hash.ts. */
  hashMatches: boolean;
}

export interface Clock {
  now: number;
  prod: boolean;
}

export function publicationState(f: PublicationFacts, ctx: Clock): PublicationState {
  if (f.status === 'draft') return 'draft';
  if (f.status === 'review') return 'review';
  if (!f.hashMatches) return 'stale-approval';
  return f.pubDate.getTime() <= ctx.now ? 'published' : 'scheduled';
}

/** In dev everything is visible, so drafts and future posts stay previewable. */
export function isVisible(f: PublicationFacts, ctx: Clock): boolean {
  if (!ctx.prod) return true;
  return publicationState(f, ctx) === 'published';
}
