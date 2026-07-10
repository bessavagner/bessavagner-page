import { test } from 'vitest';
import assert from 'node:assert/strict';
import type { MarkdownHeading } from 'astro';
import { tocEntries, shouldRenderToc } from './toc-core.ts';

const h = (depth: number, i: number): MarkdownHeading => ({ depth, slug: `s${i}`, text: `H${i}` });

test('tocEntries keeps only h2 and h3', () => {
  const headings = [h(1, 0), h(2, 1), h(3, 2), h(4, 3)];
  assert.deepEqual(tocEntries(headings).map((x) => x.depth), [2, 3]);
});

test('shouldRenderToc is true only at or above the threshold (default 3)', () => {
  assert.equal(shouldRenderToc([h(2, 1), h(2, 2)]), false);              // 2 entries
  assert.equal(shouldRenderToc([h(2, 1), h(2, 2), h(3, 3)]), true);      // 3 entries
  assert.equal(shouldRenderToc([h(1, 0), h(4, 9)]), false);             // no h2/h3
  assert.equal(shouldRenderToc([h(2, 1), h(2, 2)], 2), true);           // custom min
});
