// web/src/lib/digest-core.test.ts
import { test } from 'vitest';
import assert from 'node:assert/strict';
import {
  utcDateStamp,
  selectAnnounceable,
  renderDigest,
  type DigestItem,
  type AnnounceCandidate,
} from './digest-core.ts';

const item = (over: Partial<DigestItem>): DigestItem => ({
  kind: 'blog',
  title: 'T',
  description: 'D',
  path: '/blog/t/',
  pubDate: new Date('2026-06-27'),
  ...over,
});

test('utcDateStamp formats a Date as UTC YYYY-MM-DD', () => {
  assert.equal(utcDateStamp(new Date('2026-06-27T00:00:00Z')), '2026-06-27');
  assert.equal(utcDateStamp(new Date('2026-06-27T23:59:59Z')), '2026-06-27');
});

const NOW = Date.parse('2026-07-09T12:00:00Z');
const at = (iso: string): AnnounceCandidate => ({
  ...item({}),
  pubDate: new Date(iso),
  state: 'published',
});

// No launch cutoff in effect — used by tests that predate the `notBefore` guard.
const NO_CUTOFF = Number.NEGATIVE_INFINITY;

test('includes a post published inside the window', () => {
  assert.equal(
    selectAnnounceable([at('2026-07-09T11:00:00Z')], { now: NOW, windowDays: 30, notBefore: NO_CUTOFF }).length,
    1,
  );
});

test('excludes a post older than the window — the back-catalogue guard', () => {
  assert.equal(
    selectAnnounceable([at('2026-01-01T00:00:00Z')], { now: NOW, windowDays: 30, notBefore: NO_CUTOFF }).length,
    0,
  );
});

test('excludes a post that is not in the published state', () => {
  const scheduled = { ...at('2026-07-09T11:00:00Z'), state: 'scheduled' as const };
  assert.equal(
    selectAnnounceable([scheduled], { now: NOW, windowDays: 30, notBefore: NO_CUTOFF }).length,
    0,
  );
});

test('announces a post that was due yesterday but missed — late is fine', () => {
  assert.equal(
    selectAnnounceable([at('2026-07-08T11:00:00Z')], { now: NOW, windowDays: 30, notBefore: NO_CUTOFF }).length,
    1,
  );
});

test('selectAnnounceable orders Building before Blog', () => {
  const items: AnnounceCandidate[] = [
    { ...at('2026-07-09T11:00:00Z'), kind: 'blog', title: 'b' },
    { ...at('2026-07-09T11:00:00Z'), kind: 'building', title: 'a', path: '/building/x/a/' },
  ];
  const due = selectAnnounceable(items, { now: NOW, windowDays: 30, notBefore: NO_CUTOFF });
  assert.deepEqual(due.map((i) => i.kind), ['building', 'blog']);
});

// The launch cutoff: posts from before this publication system went live are never
// announced, even though they are otherwise `published` and inside the window — a
// missed digest is never sent retroactively.
const NOT_BEFORE = Date.parse('2026-07-10T00:00:00Z');

test('excludes a published, in-window post dated before the launch cutoff', () => {
  assert.equal(
    selectAnnounceable([at('2026-07-08T11:00:00Z')], { now: NOW, windowDays: 30, notBefore: NOT_BEFORE }).length,
    0,
  );
});

test('includes a published post dated exactly at the launch cutoff — boundary is inclusive', () => {
  assert.equal(
    selectAnnounceable([at('2026-07-10T00:00:00Z')], {
      now: Date.parse('2026-07-10T12:00:00Z'),
      windowDays: 30,
      notBefore: NOT_BEFORE,
    }).length,
    1,
  );
});

test('includes a published, in-window post dated after the launch cutoff', () => {
  assert.equal(
    selectAnnounceable([at('2026-07-10T12:00:00Z')], {
      now: Date.parse('2026-07-10T12:30:00Z'),
      windowDays: 30,
      notBefore: NOT_BEFORE,
    }).length,
    1,
  );
});

test('renderDigest produces a date-stamped subject', () => {
  const { subject } = renderDigest([item({})], { siteUrl: 'https://bessavagner.com', today: '2026-06-27' });
  assert.ok(subject.includes('2026-06-27'), subject);
});

test('renderDigest lists each item with an absolute URL and groups Building before Writing', () => {
  const items: DigestItem[] = [
    item({ kind: 'building', title: 'Build A', description: 'da', path: '/building/x/a/' }),
    item({ kind: 'blog', title: 'Post B', description: 'db', path: '/blog/b/' }),
  ];
  const { body } = renderDigest(items, { siteUrl: 'https://bessavagner.com', today: '2026-06-27' });
  assert.ok(body.includes('https://bessavagner.com/building/x/a/'), body);
  assert.ok(body.includes('https://bessavagner.com/blog/b/'), body);
  assert.ok(body.includes('## Building'));
  assert.ok(body.includes('## Writing'));
  assert.ok(body.indexOf('## Building') < body.indexOf('## Writing'));
  assert.ok(body.includes('Build A') && body.includes('Post B'));
});

test('renderDigest omits an empty section', () => {
  const { body } = renderDigest([item({ kind: 'blog', title: 'Only Post' })], {
    siteUrl: 'https://bessavagner.com', today: '2026-06-27',
  });
  assert.ok(!body.includes('## Building'));
  assert.ok(body.includes('## Writing'));
});
