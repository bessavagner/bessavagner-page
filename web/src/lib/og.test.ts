// web/src/lib/og.test.ts
import { test } from 'node:test';
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
