// web/src/lib/digest-core.test.ts
import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  utcDateStamp,
  selectDue,
  renderDigest,
  type DigestItem,
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

test('selectDue keeps only items dated today', () => {
  const items = [
    item({ title: 'today-blog', pubDate: new Date('2026-06-27') }),
    item({ title: 'yesterday', pubDate: new Date('2026-06-26') }),
    item({ title: 'future', pubDate: new Date('2026-06-29') }),
  ];
  const due = selectDue(items, '2026-06-27');
  assert.deepEqual(due.map((i) => i.title), ['today-blog']);
});

test('selectDue orders Building before Blog', () => {
  const items = [
    item({ kind: 'blog', title: 'b', pubDate: new Date('2026-06-27') }),
    item({ kind: 'building', title: 'a', pubDate: new Date('2026-06-27'), path: '/building/x/a/' }),
  ];
  const due = selectDue(items, '2026-06-27');
  assert.deepEqual(due.map((i) => i.kind), ['building', 'blog']);
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
