// web/scripts/digest.test.ts
// Covers a review finding against scripts/digest.ts: dedupeAgainstSent stands
// between "announce" and both failure directions — silently skipping a real
// post, or double-announcing one already sent — and had no test at all.
//
// Importing scripts/digest.ts for its exported functions must not trigger a
// real run: main() is guarded behind an entry-point check (`isMain`), the
// same pattern scripts/post.ts uses, so importing this module here is
// side-effect-free — no network call, no `main()` output.
import { describe, it, expect } from 'vitest';
import { dedupeAgainstSent } from './digest.ts';
import type { AnnounceCandidate } from '../src/lib/digest-core.ts';

function candidate(path: string): AnnounceCandidate {
  return {
    kind: 'blog',
    title: `Post at ${path}`,
    description: 'test fixture',
    path,
    pubDate: new Date('2026-07-01T00:00:00Z'),
    state: 'published',
  };
}

describe('dedupeAgainstSent', () => {
  it('drops an item whose path is an exact match in a sent body', () => {
    const items = [candidate('/blog/foo/')];
    const sentBodies = ['Check out this post: https://bessavagner.com/blog/foo/ — enjoy!'];
    expect(dedupeAgainstSent(items, sentBodies)).toEqual([]);
  });

  it('does NOT drop /blog/foo/ on a body that only contains /blog/foo-bar/ (no false match on a hyphenated-suffix path)', () => {
    const items = [candidate('/blog/foo/')];
    const sentBodies = ['See https://bessavagner.com/blog/foo-bar/ for details.'];
    expect(dedupeAgainstSent(items, sentBodies)).toEqual(items);
  });

  it('drops nothing when sentBodies is empty', () => {
    const items = [candidate('/blog/foo/'), candidate('/building/regwatch/01-foo/')];
    expect(dedupeAgainstSent(items, [])).toEqual(items);
  });

  it('drops the matching item out of several sent bodies, keeping the rest', () => {
    const items = [candidate('/blog/foo/'), candidate('/blog/bar/'), candidate('/building/regwatch/01-foo/')];
    const sentBodies = [
      'Old newsletter about something else entirely.',
      'Announcing https://bessavagner.com/blog/bar/ today!',
      'Yet another unrelated email body.',
    ];
    expect(dedupeAgainstSent(items, sentBodies)).toEqual([candidate('/blog/foo/'), candidate('/building/regwatch/01-foo/')]);
  });
});
