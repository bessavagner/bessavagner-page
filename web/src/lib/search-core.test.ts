// web/src/lib/search-core.test.ts
import { test } from 'vitest';
import assert from 'node:assert/strict';
import { toRow, debounce, formatDate, type PagefindResultData } from './search-core.ts';

test('toRow maps a blog result to a labelled row', () => {
  const data: PagefindResultData = {
    url: '/blog/hello/',
    meta: { title: 'Hello World', type: 'blog', date: '2026-01-02T00:00:00.000Z' },
    excerpt: 'a <mark>hello</mark> excerpt',
  };
  const row = toRow(data);
  assert.equal(row.url, '/blog/hello/');
  assert.equal(row.title, 'Hello World');
  assert.equal(row.type, 'blog');
  assert.equal(row.typeLabel, 'Blog');
  assert.equal(row.date, '2026-01-02T00:00:00.000Z');
  assert.equal(row.dateLabel, 'Jan 2, 2026');
  assert.equal(row.excerptHtml, 'a <mark>hello</mark> excerpt');
});

test('toRow labels build-log results and tolerates missing meta', () => {
  const row = toRow({ url: '/building/x/1/', meta: { type: 'buildlog' }, excerpt: '' });
  assert.equal(row.typeLabel, 'Build log');
  assert.equal(row.type, 'buildlog');
  assert.equal(row.title, 'Untitled');
  assert.equal(row.date, '');
  assert.equal(row.dateLabel, '');
});

test('toRow falls back to "other" for unknown types', () => {
  const row = toRow({ url: '/x/', meta: { type: 'project' }, excerpt: '' });
  assert.equal(row.type, 'other');
  assert.equal(row.typeLabel, 'Page');
});

test('formatDate renders a short human date and is safe on bad input', () => {
  assert.equal(formatDate('2026-01-02T00:00:00.000Z'), 'Jan 2, 2026');
  assert.equal(formatDate(''), '');
  assert.equal(formatDate('not-a-date'), '');
});

test('debounce calls the function once after the window with the latest args', async () => {
  let calls: number[] = [];
  const d = debounce((n: number) => calls.push(n), 20);
  d(1); d(2); d(3);
  assert.deepEqual(calls, []);
  await new Promise((r) => setTimeout(r, 40));
  assert.deepEqual(calls, [3]);
});
