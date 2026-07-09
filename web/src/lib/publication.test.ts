import { describe, it, expect } from 'vitest';
import { publicationState, isVisible, type PublicationFacts } from './publication';

const NOW = Date.parse('2026-07-09T12:00:00Z');
const PAST = new Date('2026-07-01T00:00:00Z');
const FUTURE = new Date('2026-08-01T00:00:00Z');

const facts = (over: Partial<PublicationFacts> = {}): PublicationFacts => ({
  status: 'approved',
  pubDate: PAST,
  hashMatches: true,
  ...over,
});

describe('publicationState', () => {
  const cases: [string, Partial<PublicationFacts>, string][] = [
    ['a draft is a draft, even when due', { status: 'draft' }, 'draft'],
    ['a draft is a draft, even with a bad hash', { status: 'draft', hashMatches: false }, 'draft'],
    ['a post in review is in review, even when due', { status: 'review' }, 'review'],
    ['approved but edited since is stale-approval', { hashMatches: false }, 'stale-approval'],
    ['stale-approval beats scheduled', { hashMatches: false, pubDate: FUTURE }, 'stale-approval'],
    ['approved, clean, future-dated is scheduled', { pubDate: FUTURE }, 'scheduled'],
    ['approved, clean, due is published', {}, 'published'],
  ];

  for (const [name, over, expected] of cases) {
    it(name, () => {
      expect(publicationState(facts(over), { now: NOW, prod: true })).toBe(expected);
    });
  }

  it('treats a pubDate exactly equal to now as due', () => {
    const pubDate = new Date(NOW);
    expect(publicationState(facts({ pubDate }), { now: NOW, prod: true })).toBe('published');
  });

  it('ignores prod — all states are independent of the build environment', () => {
    // publicationState's state is a fact about the post, not about the build.
    // This test pins that invariant: changing prod must not change the output.
    for (const [, over] of cases) {
      const withProd = publicationState(facts(over), { now: NOW, prod: true });
      const withoutProd = publicationState(facts(over), { now: NOW, prod: false });
      expect(withoutProd).toBe(withProd);
    }
  });
});

describe('isVisible', () => {
  it('shows only published posts in prod', () => {
    expect(isVisible(facts(), { now: NOW, prod: true })).toBe(true);
    expect(isVisible(facts({ status: 'review' }), { now: NOW, prod: true })).toBe(false);
    expect(isVisible(facts({ hashMatches: false }), { now: NOW, prod: true })).toBe(false);
    expect(isVisible(facts({ pubDate: FUTURE }), { now: NOW, prod: true })).toBe(false);
  });

  it('shows everything in dev, including a stale approval', () => {
    for (const over of [{ status: 'draft' as const }, { hashMatches: false }, { pubDate: FUTURE }]) {
      expect(isVisible(facts(over), { now: NOW, prod: false })).toBe(true);
    }
  });
});
