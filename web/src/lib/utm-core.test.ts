// web/src/lib/utm-core.test.ts
import { test } from 'vitest';
import assert from 'node:assert/strict';
import {
  buildTaggedUrl,
  resolveDestination,
  formatRegistryRow,
  REGISTRY_HEADER,
  UTM_SOURCES,
  UTM_MEDIUMS,
  UTM_PLACEMENTS,
  composePlacementContent,
} from './utm-core.ts';

test('closed vocabulary is exactly {linkedin} / {social, paid-social}', () => {
  assert.deepEqual([...UTM_SOURCES], ['linkedin']);
  assert.deepEqual([...UTM_MEDIUMS], ['social', 'paid-social']);
});

test('rejects an out-of-vocabulary medium (a typo cannot reach a live link)', () => {
  assert.throws(
    () => buildTaggedUrl({ destination: '/blog/x', campaign: 'x', content: '2026-07-09-am', medium: 'Social' }),
    /utm_medium "Social" is out of vocabulary/,
  );
  assert.throws(
    () => buildTaggedUrl({ destination: '/blog/x', campaign: 'x', content: '2026-07-09-am', medium: 'linkedin' }),
    /out of vocabulary/,
  );
});

test('rejects an out-of-vocabulary source (never linkedin.com / lnkd.in)', () => {
  assert.throws(
    () => buildTaggedUrl({ destination: '/blog/x', campaign: 'x', content: 'y', source: 'linkedin.com' }),
    /utm_source "linkedin.com" is out of vocabulary/,
  );
});

test('rejects a non-lowercase / non-slug campaign or content (casing breaks GA4)', () => {
  assert.throws(
    () => buildTaggedUrl({ destination: '/blog/x', campaign: 'Polymorphic_Vaults', content: 'am' }),
    /utm_campaign/,
  );
  assert.throws(
    () => buildTaggedUrl({ destination: '/blog/x', campaign: 'ok', content: '2026-07-09 am' }),
    /utm_content/,
  );
});

test('resolveDestination refuses off-site hosts, pre-existing queries, and bare paths', () => {
  assert.throws(() => resolveDestination('https://evil.com/x'), /must be on https:\/\/bessavagner\.com/);
  assert.throws(() => resolveDestination('/blog/x?ref=1'), /no query string/);
  assert.throws(() => resolveDestination('blog/x'), /must start with "\/"/);
  assert.equal(resolveDestination('/blog/x'), 'https://bessavagner.com/blog/x');
});

test('assembles the canonical organic URL from the convention doc verbatim', () => {
  const url = buildTaggedUrl({
    destination: '/blog/polymorphic-vaults-in-drf',
    campaign: 'polymorphic-vaults',
    content: '2026-07-09-am',
  });
  assert.equal(
    url,
    'https://bessavagner.com/blog/polymorphic-vaults-in-drf?utm_source=linkedin&utm_medium=social&utm_campaign=polymorphic-vaults&utm_content=2026-07-09-am',
  );
});

test('paid-social medium produces the boosted variant verbatim', () => {
  const url = buildTaggedUrl({
    destination: '/blog/polymorphic-vaults-in-drf',
    campaign: 'polymorphic-vaults',
    content: 'boost-2026-07-09',
    medium: 'paid-social',
  });
  assert.equal(
    url,
    'https://bessavagner.com/blog/polymorphic-vaults-in-drf?utm_source=linkedin&utm_medium=paid-social&utm_campaign=polymorphic-vaults&utm_content=boost-2026-07-09',
  );
});

test('a full on-site destination URL is accepted and tagged', () => {
  const url = buildTaggedUrl({
    destination: 'https://bessavagner.com/buildlog/regwatch',
    campaign: 'regwatch-deploy',
    content: '2026-07-09-am',
  });
  assert.equal(
    url,
    'https://bessavagner.com/buildlog/regwatch?utm_source=linkedin&utm_medium=social&utm_campaign=regwatch-deploy&utm_content=2026-07-09-am',
  );
});

test('output query is lowercase, space-free, and round-trips (encoding guarantee)', () => {
  const url = buildTaggedUrl({ destination: '/buildlog/regwatch', campaign: 'regwatch-deploy', content: '2026-07-09-am' });
  const query = new URL(url).search;
  assert.equal(query, query.toLowerCase(), 'query must be lowercase');
  assert.ok(!query.includes(' '), 'query must not contain raw spaces');
  const p = new URL(url).searchParams;
  assert.equal(p.get('utm_source'), 'linkedin');
  assert.equal(p.get('utm_medium'), 'social');
  assert.equal(p.get('utm_campaign'), 'regwatch-deploy');
  assert.equal(p.get('utm_content'), '2026-07-09-am');
});

test('registry header and row share one column order', () => {
  const header = REGISTRY_HEADER.split(',');
  assert.deepEqual(header, [
    'destination_url', 'source', 'medium', 'campaign', 'content', 'tagged_url', 'date_posted',
  ]);
  const row = formatRegistryRow({
    destinationUrl: 'https://bessavagner.com/blog/polymorphic-vaults-in-drf',
    source: 'linkedin',
    medium: 'social',
    campaign: 'polymorphic-vaults',
    content: '2026-07-09-am',
    taggedUrl: 'https://bessavagner.com/blog/polymorphic-vaults-in-drf?utm_source=linkedin&utm_medium=social&utm_campaign=polymorphic-vaults&utm_content=2026-07-09-am',
    datePosted: '2026-07-09',
  });
  assert.equal(row.split(',').length, header.length);
  assert.ok(row.startsWith('https://bessavagner.com/blog/polymorphic-vaults-in-drf,linkedin,social,'));
});

test('placement vocabulary is exactly {post-body, first-comment, profile-featured}', () => {
  assert.deepEqual([...UTM_PLACEMENTS], ['post-body', 'first-comment', 'profile-featured']);
});

test('composePlacementContent joins date-slot + placement into one valid slug', () => {
  const content = composePlacementContent('2026-07-09-am', 'first-comment');
  assert.equal(content, '2026-07-09-am-first-comment');
  // the compound value must still pass the generator unchanged
  const url = buildTaggedUrl({ destination: '/buildlog/regwatch', campaign: 'regwatch-deploy', content });
  assert.ok(url.endsWith('utm_content=2026-07-09-am-first-comment'));
});

test('composePlacementContent rejects an out-of-vocab placement or a non-slug date-slot', () => {
  assert.throws(() => composePlacementContent('2026-07-09-am', 'sidebar'), /out of vocabulary/);
  assert.throws(() => composePlacementContent('2026-07-09 am', 'post-body'), /lowercase hyphenated slug/);
});
