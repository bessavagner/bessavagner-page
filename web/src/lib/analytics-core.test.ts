// web/src/lib/analytics-core.test.ts
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { track, trackParams, type AnalyticsGlobals } from './analytics-core.ts';

function recorder() {
  const calls: { tool: 'umami' | 'gtag'; name: string; params: unknown }[] = [];
  const scope: AnalyticsGlobals = {
    umami: { track: (name, params) => calls.push({ tool: 'umami', name, params }) },
    gtag: (_cmd, name, params) => calls.push({ tool: 'gtag', name, params }),
  };
  return { calls, scope };
}

test('track fires both umami and gtag from one call', () => {
  const { calls, scope } = recorder();
  track('cv_download', { location: 'hero' }, scope);
  assert.equal(calls.length, 2);
  assert.deepEqual(calls.map((c) => c.tool).sort(), ['gtag', 'umami']);
  assert.ok(calls.every((c) => c.name === 'cv_download'));
});

test('a thrown/blocked gtag does not stop umami', () => {
  const fired: string[] = [];
  const scope: AnalyticsGlobals = {
    umami: { track: () => fired.push('umami') },
    gtag: () => { throw new Error('blocked'); },
  };
  track('whatsapp_click', {}, scope);
  assert.deepEqual(fired, ['umami']);
});

test('a thrown/blocked umami does not stop gtag', () => {
  const fired: string[] = [];
  const scope: AnalyticsGlobals = {
    umami: { track: () => { throw new Error('blocked'); } },
    gtag: () => fired.push('gtag'),
  };
  track('whatsapp_click', {}, scope);
  assert.deepEqual(fired, ['gtag']);
});

test('track no-ops safely when both globals are absent', () => {
  assert.doesNotThrow(() => track('cv_download', {}, {}));
});

test('trackParams keeps only data-track-* attributes, minus the marker', () => {
  const attrs = [
    { name: 'href', value: '/cv.pdf' },
    { name: 'data-track', value: 'cv_download' },
    { name: 'data-track-location', value: 'hero' },
    { name: 'data-track-file_extension', value: 'pdf' },
    { name: 'class', value: 'btn' },
  ];
  assert.deepEqual(trackParams(attrs), { location: 'hero', file_extension: 'pdf' });
});
