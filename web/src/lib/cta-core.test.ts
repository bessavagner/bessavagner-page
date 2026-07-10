import { test } from 'vitest';
import assert from 'node:assert/strict';
import { resolveCta, DEFAULT_CTA } from './cta-core.ts';

test('resolveCta applies the per-collection default when goal is undefined', () => {
  assert.equal(DEFAULT_CTA.blog, 'lets-talk');
  assert.equal(DEFAULT_CTA.buildlog, 'follow-build');
  assert.equal(resolveCta(undefined, 'blog').goal, 'lets-talk');
  assert.equal(resolveCta(undefined, 'buildlog').goal, 'follow-build');
});

test('resolveCta honours an explicit goal over the default', () => {
  const cta = resolveCta('cv', 'buildlog');
  assert.equal(cta.goal, 'cv');
  assert.equal(cta.action, 'Download my CV');
  assert.equal(cta.href, ''); // component fills from portfolio.links.cv
});

test('resolveCta returns concrete copy + href for every goal', () => {
  assert.equal(resolveCta('lets-talk', 'blog').href, '/#section-contact');
  assert.equal(resolveCta('follow-build', 'buildlog').href, '/building/');
  assert.equal(resolveCta('subscribe', 'blog').href, '#subscribe');
  for (const g of ['lets-talk', 'cv', 'follow-build', 'subscribe'] as const) {
    const cta = resolveCta(g, 'blog');
    assert.ok(cta.lead.length > 0, `${g} has a lead sentence`);
    assert.ok(cta.action.length > 0, `${g} has an action label`);
  }
});
