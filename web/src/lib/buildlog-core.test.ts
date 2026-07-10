// web/src/lib/buildlog-core.test.ts
import { test } from 'vitest';
import assert from 'node:assert/strict';
import {
  splitUpdateId,
  sortUpdatesByDateDesc,
  latestUpdate,
  seriesNeighbors,
  buildProjectToProject,
  type BuildProject,
  type UpdateLike,
} from './buildlog-core.ts';

test('splitUpdateId separates the project folder from the update slug', () => {
  assert.deepEqual(splitUpdateId('regwatch/01-postgres-fts'), { project: 'regwatch', slug: '01-postgres-fts' });
  assert.deepEqual(splitUpdateId('regwatch/sub/02-foo'), { project: 'regwatch', slug: 'sub/02-foo' });
  assert.deepEqual(splitUpdateId('loose'), { project: 'loose', slug: 'loose' });
});

test('sortUpdatesByDateDesc orders newest first and does not mutate input', () => {
  const a = { data: { pubDate: new Date('2026-06-25') } };
  const b = { data: { pubDate: new Date('2026-06-29') } };
  const input = [a, b];
  const out = sortUpdatesByDateDesc(input);
  assert.deepEqual(out.map((u) => u.data.pubDate.getTime()), [b.data.pubDate.getTime(), a.data.pubDate.getTime()]);
  assert.equal(input[0], a); // original array untouched
});

test('latestUpdate returns the newest entry, or undefined when empty', () => {
  const a = { data: { pubDate: new Date('2026-06-25') } };
  const b = { data: { pubDate: new Date('2026-06-29') } };
  assert.equal(latestUpdate([a, b]), b);
  assert.equal(latestUpdate([]), undefined);
});

const SHIPPED: BuildProject = {
  slug: 'regwatch',
  title: 'RegWatch',
  tagline: 'Google Alerts for the Diário Oficial da União',
  blurb: 'A DOU monitoring service for professional-services firms.',
  repo: 'https://github.com/bessavagner/regwatch',
  startDate: '2026-06-20',
  status: 'shipped',
  stack: ['Django', 'PostgreSQL'],
  work: {
    summary: 'Full summary.',
    highlights: ['h1'],
    metrics: [{ label: 'Tests', value: '19 passing' }],
    year: 2026,
    featured: false,
    order: 5,
    links: { live: 'https://example.com' },
  },
};

test('buildProjectToProject maps a shipped registry entry into a Project', () => {
  const p = buildProjectToProject(SHIPPED);
  assert.equal(p.id, 'regwatch');
  assert.equal(p.name, 'RegWatch');
  assert.equal(p.summary, 'Full summary.');
  assert.equal(p.featured, false);
  assert.equal(p.order, 5);
  assert.equal(p.status, 'shipped');
  assert.equal(p.private, false);
  assert.deepEqual(p.stack, ['Django', 'PostgreSQL']);
  assert.equal(p.links.repo, 'https://github.com/bessavagner/regwatch');
  assert.equal(p.links.buildlog, '/building/regwatch/');
  assert.equal(p.links.live, 'https://example.com');
});

test('buildProjectToProject falls back to blurb and defaults when work is sparse', () => {
  const p = buildProjectToProject({ ...SHIPPED, work: {} });
  assert.equal(p.summary, SHIPPED.blurb);
  assert.equal(p.featured, false);
  assert.equal(p.order, 999);
  assert.equal(p.links.buildlog, '/building/regwatch/');
});

const upd = (id: string, update: number): UpdateLike => ({
  id,
  data: { project: 'p', update, pubDate: new Date('2026-01-01'), draft: false },
});

test('seriesNeighbors returns the lower-numbered prev and higher-numbered next', () => {
  const list = [upd('p/01', 1), upd('p/02', 2), upd('p/03', 3)];
  const { prev, next } = seriesNeighbors(list[1], list);
  assert.equal(prev?.id, 'p/01');
  assert.equal(next?.id, 'p/03');
});

test('seriesNeighbors gives the first update no prev and the last no next', () => {
  const list = [upd('p/01', 1), upd('p/02', 2), upd('p/03', 3)];
  assert.equal(seriesNeighbors(list[0], list).prev, undefined);
  assert.equal(seriesNeighbors(list[0], list).next?.id, 'p/02');
  assert.equal(seriesNeighbors(list[2], list).next, undefined);
  assert.equal(seriesNeighbors(list[2], list).prev?.id, 'p/02');
});

test('seriesNeighbors is order-independent (sorts by update number, not array order)', () => {
  const shuffled = [upd('p/03', 3), upd('p/01', 1), upd('p/02', 2)];
  const { prev, next } = seriesNeighbors(shuffled[0], shuffled); // the update=3 entry
  assert.equal(prev?.id, 'p/02');
  assert.equal(next, undefined);
});

test('seriesNeighbors returns empty neighbors when the update is absent or alone', () => {
  const list = [upd('p/01', 1)];
  assert.deepEqual(seriesNeighbors(list[0], list), { prev: undefined, next: undefined });
  assert.deepEqual(seriesNeighbors(upd('p/99', 99), list), {});
});
