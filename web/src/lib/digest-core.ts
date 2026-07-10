// web/src/lib/digest-core.ts
// Pure logic for the email digest: selecting announceable items and rendering
// the Markdown email. No I/O and no `astro:content`, so it is unit-testable
// under `node --test`.

import type { PublicationState } from './publication.ts';

export interface DigestItem {
  kind: 'building' | 'blog';
  title: string;
  description: string;
  path: string; // site-relative, e.g. "/blog/foo/" or "/building/regwatch/01-foo/"
  pubDate: Date;
  project?: string;
}

/** A candidate for the digest, carrying the PublicationState that decides whether
 *  it is safe to announce at all. */
export interface AnnounceCandidate extends DigestItem {
  state: PublicationState;
}

export interface Digest {
  subject: string;
  body: string;
}

/** UTC calendar date of a Date, as YYYY-MM-DD. */
export function utcDateStamp(d: Date): string {
  return d.toISOString().slice(0, 10);
}

/** Posts that are actually live (`state === 'published'`, never `scheduled` — a
 *  post can be scheduled for later in its own UTC day than the deploy cron, so
 *  matching on state instead of calendar date is what keeps the digest from
 *  linking to a page the build hasn't shipped yet) and landed within the last
 *  `windowDays` — the back-catalogue guard, so a long-idle digest run doesn't
 *  re-announce everything ever published. Building first, then Blog,
 *  newest-first within each group. */
export function selectAnnounceable(
  posts: AnnounceCandidate[],
  opts: { now: number; windowDays: number },
): AnnounceCandidate[] {
  const rank = { building: 0, blog: 1 } as const;
  const cutoff = opts.now - opts.windowDays * 86_400_000;
  return posts
    .filter((p) => p.state === 'published' && p.pubDate.getTime() > cutoff)
    .sort((a, b) => rank[a.kind] - rank[b.kind] || b.pubDate.getTime() - a.pubDate.getTime());
}

/** Compose the digest email (Markdown). The subject is date-stamped; that stamp is the
 *  idempotency key the sender uses to avoid double-sends. */
export function renderDigest(items: DigestItem[], opts: { siteUrl: string; today: string }): Digest {
  const subject = `New on bessavagner.com — ${opts.today}`;
  const lines: string[] = [
    `Here's what just went live on [bessavagner.com](${opts.siteUrl}/).`,
    '',
  ];

  const section = (heading: string, list: DigestItem[]) => {
    if (list.length === 0) return;
    lines.push(`## ${heading}`, '');
    for (const i of list) {
      lines.push(`**[${i.title}](${opts.siteUrl}${i.path})**`, '', i.description, '');
    }
  };

  section('Building', items.filter((i) => i.kind === 'building'));
  section('Writing', items.filter((i) => i.kind === 'blog'));

  lines.push('—', '', `You're getting this because you subscribed at bessavagner.com.`);
  return { subject, body: lines.join('\n').trim() + '\n' };
}
