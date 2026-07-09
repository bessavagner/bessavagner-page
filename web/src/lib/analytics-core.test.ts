// web/src/lib/analytics-core.test.ts
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { track, trackParams, trackAndGo, type AnalyticsGlobals } from './analytics-core.ts';

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

test('trackAndGo navigates once via the gtag event_callback', () => {
  let navigated = 0;
  const scope: AnalyticsGlobals = {
    gtag: (_cmd, _name, params) => (params as { event_callback: () => void }).event_callback(),
  };
  // setTimeoutFn is a no-op here so only the callback path can navigate.
  trackAndGo('email_click', {}, { navigate: () => navigated++, scope, setTimeoutFn: () => {} });
  assert.equal(navigated, 1);
});

test('trackAndGo passes beacon transport + a timeout to gtag', () => {
  let seen: Record<string, unknown> = {};
  const scope: AnalyticsGlobals = { gtag: (_c, _n, params) => { seen = params as Record<string, unknown>; } };
  trackAndGo('email_click', { location: 'hero' }, { navigate: () => {}, scope, timeoutMs: 800, setTimeoutFn: () => {} });
  assert.equal(seen.transport_type, 'beacon');
  assert.equal(seen.event_timeout, 800);
  assert.equal(seen.location, 'hero');
  assert.equal(typeof seen.event_callback, 'function');
});

test('trackAndGo navigates via the fallback timer when gtag never calls back', async () => {
  let navigated = 0;
  const scope: AnalyticsGlobals = { gtag: () => { /* never invokes the callback */ } };
  trackAndGo('email_click', {}, { navigate: () => navigated++, scope, timeoutMs: 10 });
  assert.equal(navigated, 0);
  await new Promise((r) => setTimeout(r, 120));
  assert.equal(navigated, 1);
});

test('trackAndGo navigates even when gtag is absent (blocked)', async () => {
  let navigated = 0;
  trackAndGo('email_click', {}, { navigate: () => navigated++, scope: {}, timeoutMs: 10 });
  await new Promise((r) => setTimeout(r, 120));
  assert.equal(navigated, 1);
});

test('trackAndGo never navigates twice when callback AND fallback both fire', async () => {
  let navigated = 0;
  const scope: AnalyticsGlobals = {
    gtag: (_c, _n, params) => (params as { event_callback: () => void }).event_callback(),
  };
  trackAndGo('email_click', {}, { navigate: () => navigated++, scope, timeoutMs: 10 });
  await new Promise((r) => setTimeout(r, 120));
  assert.equal(navigated, 1);
});

test('trackAndGo also fires umami', () => {
  let umami = 0;
  const scope: AnalyticsGlobals = {
    umami: { track: () => umami++ },
    gtag: (_c, _n, params) => (params as { event_callback: () => void }).event_callback(),
  };
  trackAndGo('email_click', {}, { navigate: () => {}, scope, setTimeoutFn: () => {} });
  assert.equal(umami, 1);
});
