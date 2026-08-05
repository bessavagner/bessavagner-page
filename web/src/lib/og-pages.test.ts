// web/src/lib/og-pages.test.ts
import { test } from 'vitest';
import assert from 'node:assert/strict';
import { pageCardKeys, buildPageCard } from './og-pages.ts';

// Small synthetic registry shapes — mirror the real JSON files' fields but
// stay independent of live data so a 6th build project doesn't break these.
const buildProjects = [
  { slug: 'regwatch', title: 'RegWatch', blurb: 'Watches the DOU.', stack: ['Django', 'PostgreSQL'], updateCount: 7 },
  { slug: 'replaygate', title: 'ReplayGate', blurb: 'Cross-turn regression testing.', stack: ['Python', 'Pydantic v2'], updateCount: 1 },
];
const projects = [
  { id: 'replaygate', name: 'ReplayGate', summary: 'A regression harness.', tagline: 'Cross-turn testing', stack: ['Python'], year: 2026 },
  { id: 'regwatch', name: 'RegWatch', summary: '', tagline: 'Google Alerts for the DOU', stack: ['Django'], year: 2026 },
  { id: 'weberist', name: 'Weberist', summary: 'Stealth automation.', tagline: 'Stealth framework', stack: ['Python'], year: 2024, ogImage: 'images/og/weberist.png' },
];

test('pageCardKeys derives one key per build project, plus the two fixed keys, plus one per project lacking ogImage', () => {
  const keys = pageCardKeys(projects, buildProjects);
  assert.deepEqual(keys, [
    'blog',
    'building',
    'building-regwatch',
    'building-replaygate',
    'projects-replaygate',
    'projects-regwatch',
  ]);
});

test('pageCardKeys grows when the registry grows, without any hardcoded count', () => {
  const grownBuildProjects = [...buildProjects, { slug: 'supskill', title: 'supskill', blurb: 'A sprint conductor.', stack: ['Python'], updateCount: 2 }];
  const keys = pageCardKeys(projects, grownBuildProjects);
  assert.equal(keys.length, 2 + grownBuildProjects.length + projects.filter((p) => !p.ogImage).length);
  assert.ok(keys.includes('building-supskill'));
});

test('pageCardKeys excludes registry projects that already have an ogImage', () => {
  const keys = pageCardKeys(projects, buildProjects);
  assert.ok(!keys.includes('projects-weberist'));
});

test('buildPageCard blog: title is the blog index title, footerNote pluralises the post count', () => {
  const card = buildPageCard('blog', { postCount: 1, updateCount: 0, buildProjects, projects });
  assert.equal(card.title, 'Blog');
  assert.equal(card.footerNote, '1 post');
  assert.equal(card.kind, undefined);

  const many = buildPageCard('blog', { postCount: 19, updateCount: 0, buildProjects, projects });
  assert.equal(many.footerNote, '19 posts');
});

test('buildPageCard blog: description is the real Base description, lifted verbatim', () => {
  const card = buildPageCard('blog', { postCount: 3, updateCount: 0, buildProjects, projects });
  assert.equal(
    card.description,
    'Articles on AI engineering, LLM agents, and building production software in Python and TypeScript.',
  );
});

test('buildPageCard building: title, description, kind, and pluralised update count', () => {
  const card = buildPageCard('building', { postCount: 0, updateCount: 1, buildProjects, projects });
  assert.equal(card.title, 'Building Publicly');
  assert.equal(
    card.description,
    'Updates from the projects I am building in public, grouped by project.',
  );
  assert.equal(card.footerNote, '1 update');
  assert.equal(card.kind, 'building');

  const many = buildPageCard('building', { postCount: 0, updateCount: 19, buildProjects, projects });
  assert.equal(many.footerNote, '19 updates');
});

test('buildPageCard building-<slug>: lifts the project title, blurb, and per-project update count', () => {
  const card = buildPageCard('building-regwatch', { postCount: 0, updateCount: 0, buildProjects, projects });
  assert.equal(card.title, 'RegWatch — Building Publicly');
  assert.equal(card.description, 'Watches the DOU.');
  assert.equal(card.footerNote, '7 updates');
  assert.equal(card.kind, 'building');
  assert.equal(card.minutes, undefined);
});

test('buildPageCard building-<slug>: singular update count pluralises correctly', () => {
  const card = buildPageCard('building-replaygate', { postCount: 0, updateCount: 0, buildProjects, projects });
  assert.equal(card.footerNote, '1 update');
});

test('buildPageCard projects-<id>: lifts the project name and summary, no building eyebrow', () => {
  const card = buildPageCard('projects-replaygate', { postCount: 0, updateCount: 0, buildProjects, projects });
  assert.equal(card.title, 'ReplayGate');
  assert.equal(card.description, 'A regression harness.');
  assert.equal(card.footerNote, '2026');
  assert.equal(card.kind, undefined);
});

test('buildPageCard projects-<id>: falls back to tagline when summary is empty, matching the real page', () => {
  const card = buildPageCard('projects-regwatch', { postCount: 0, updateCount: 0, buildProjects, projects });
  assert.equal(card.description, 'Google Alerts for the DOU');
});

test('buildPageCard throws on an unknown key rather than returning a blank card', () => {
  assert.throws(() => buildPageCard('nope', { postCount: 0, updateCount: 0, buildProjects, projects }));
});

test('buildPageCard throws when a building-<slug> key has no matching registry project', () => {
  assert.throws(() => buildPageCard('building-ghost', { postCount: 0, updateCount: 0, buildProjects, projects }));
});

test('buildPageCard throws when a projects-<id> key has no matching registry project', () => {
  assert.throws(() => buildPageCard('projects-ghost', { postCount: 0, updateCount: 0, buildProjects, projects }));
});
