// web/src/lib/og-text.test.ts
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { sanitizeDashes, clampText } from './og-text.ts';

test('sanitizeDashes replaces em/en dashes with a spaced hyphen', () => {
  assert.equal(sanitizeDashes('writes — the threat'), 'writes - the threat');
  assert.equal(sanitizeDashes('a–b'), 'a - b');
  assert.equal(sanitizeDashes('no dashes here'), 'no dashes here');
});

test('clampText leaves short strings untouched', () => {
  assert.equal(clampText('short title', 80), 'short title');
});

test('clampText truncates on a word boundary with an ellipsis', () => {
  const out = clampText('one two three four five six', 12);
  assert.ok(out.length <= 13, `got "${out}" len ${out.length}`);
  assert.ok(out.endsWith('…'));
  assert.ok(!out.includes('  '));
});
