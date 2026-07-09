// web/src/lib/og.test.ts
import { test } from 'vitest';
import assert from 'node:assert/strict';
import { loadFonts } from './og.ts';

test('loadFonts returns 5 non-empty font entries', () => {
  const fonts = loadFonts();
  assert.equal(fonts.length, 5);
  for (const f of fonts) {
    assert.ok(f.data.length > 1000, `${f.name} ${f.weight} buffer too small`);
    assert.equal(f.style, 'normal');
  }
  const names = new Set(fonts.map((f) => `${f.name}:${f.weight}`));
  assert.ok(names.has('Space Grotesk:700'));
  assert.ok(names.has('Plus Jakarta Sans:400'));
  assert.ok(names.has('JetBrains Mono:400'));
});

import { buildOgMarkup } from './og.ts';

test('buildOgMarkup tags building cards with a BUILDING IN PUBLIC eyebrow', () => {
  const markup = buildOgMarkup({ title: 't', description: 'd', tags: [], minutes: 3, kind: 'building' });
  assert.ok(JSON.stringify(markup).includes('BUILDING IN PUBLIC'));
});

test('buildOgMarkup leaves blog cards without the building eyebrow', () => {
  const markup = buildOgMarkup({ title: 't', description: 'd', tags: [], minutes: 3 });
  assert.ok(!JSON.stringify(markup).includes('BUILDING IN PUBLIC'));
});

import { renderOgPng } from './og.ts';

test('renderOgPng returns a 1200x630 PNG', async () => {
  const png = await renderOgPng({
    title: 'Running LLM-Generated Code — Without Getting Burned',
    description: 'A practical look at sandboxing the code a language model writes — the threat model.',
    tags: ['llm-agents', 'docker', 'security'],
    minutes: 7,
  });
  // PNG signature
  assert.deepEqual([...png.subarray(0, 8)], [137, 80, 78, 71, 13, 10, 26, 10]);
  // IHDR width/height (big-endian uint32 at byte 16 and 20)
  assert.equal(png.readUInt32BE(16), 1200);
  assert.equal(png.readUInt32BE(20), 630);
});
