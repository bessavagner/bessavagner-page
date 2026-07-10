import { test } from 'node:test';
import assert from 'node:assert/strict';
import { relatedPosts, type RelatableLike } from './related-core.ts';

const post = (id: string, tags: string[], date: string): RelatableLike =>
  ({ id, data: { tags, pubDate: new Date(date) } });

const TARGET = post('a', ['llm', 'python'], '2026-01-10');
const ALL = [
  TARGET,
  post('b', ['llm', 'python', 'django'], '2026-01-01'), // 2 shared
  post('c', ['llm'], '2026-01-05'),                      // 1 shared
  post('d', ['rust'], '2026-01-20'),                     // 0 shared, newest
  post('e', ['python'], '2026-01-02'),                   // 1 shared, older than c
];

test('relatedPosts ranks by shared-tag count then recency, excluding self', () => {
  const out = relatedPosts(TARGET, ALL, 3);
  assert.deepEqual(out.map((p) => p.id), ['b', 'c', 'e']);
});

test('relatedPosts caps the result at n', () => {
  assert.equal(relatedPosts(TARGET, ALL, 2).length, 2);
});

test('relatedPosts falls back to most-recent when the target has no tags', () => {
  const untagged = post('z', [], '2026-01-15');
  const out = relatedPosts(untagged, [untagged, ...ALL], 3);
  // all overlaps are 0 -> pure recency: d (01-20), a (01-10), c (01-05)
  assert.deepEqual(out.map((p) => p.id), ['d', 'a', 'c']);
});

test('relatedPosts returns [] for n <= 0', () => {
  assert.deepEqual(relatedPosts(TARGET, ALL, 0), []);
});
