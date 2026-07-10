// web/src/lib/content-core.test.ts
import { describe, it, expect } from 'vitest';
import { splitFrontmatter, toDigestItem } from './content-core';

describe('toDigestItem', () => {
  it('maps blog/<slug>.mdx to /blog/<slug>/', () => {
    const item = toDigestItem('blog/running-llm-generated-code-safely.mdx', {
      title: 'Running LLM code',
      description: 'Sandboxes',
      pubDate: new Date('2026-06-23'),
    });
    expect(item).toMatchObject({
      kind: 'blog',
      title: 'Running LLM code',
      description: 'Sandboxes',
      path: '/blog/running-llm-generated-code-safely/',
    });
    expect(item?.project).toBeUndefined();
  });

  it('maps buildlog/<project>/<slug>.mdx to /building/<project>/<slug>/', () => {
    const item = toDigestItem('buildlog/replaygate/05-the-llm-judge.mdx', {
      title: 'The LLM judge',
      description: 'It cannot fail your build',
      pubDate: new Date('2026-07-08'),
    });
    expect(item).toMatchObject({
      kind: 'building',
      project: 'replaygate',
      path: '/building/replaygate/05-the-llm-judge/',
    });
  });

  it('keeps a nested buildlog slug intact', () => {
    const item = toDigestItem('buildlog/turmarium/deep/06-matricula.mdx', {
      title: 'Matricula',
      description: 'd',
      pubDate: new Date('2026-07-06'),
    });
    expect(item?.path).toBe('/building/turmarium/deep/06-matricula/');
    expect(item?.project).toBe('turmarium');
  });

  it('excludes a buildlog file that is not under a project folder', () => {
    expect(
      toDigestItem('buildlog/stray.mdx', { title: 'S', description: 'd', pubDate: new Date('2026-07-08') }),
    ).toBeNull();
  });

  it('excludes an unknown top-level content root', () => {
    expect(
      toDigestItem('notes/x.mdx', { title: 'X', description: 'd', pubDate: new Date('2026-07-08') }),
    ).toBeNull();
  });

  it('falls back to the slug when title is absent', () => {
    expect(toDigestItem('blog/my-slug.mdx', { description: 'd', pubDate: new Date('2026-07-08') })?.title).toBe(
      'my-slug',
    );
    expect(
      toDigestItem('buildlog/proj/01-update.mdx', { description: 'd', pubDate: new Date('2026-07-08') })?.title,
    ).toBe('01-update');
  });

  it('defaults an absent description to the empty string', () => {
    expect(toDigestItem('blog/x.mdx', { title: 'X', pubDate: new Date('2026-07-08') })?.description).toBe('');
  });

  it('passes pubDate through unchanged', () => {
    const pubDate = new Date('2026-07-08T08:00:00-03:00');
    const item = toDigestItem('blog/x.mdx', { title: 'X', description: 'd', pubDate });
    expect(item?.pubDate).toBe(pubDate);
  });
});

describe('splitFrontmatter', () => {
  it('separates the YAML block from the body', () => {
    const got = splitFrontmatter('---\ntitle: T\n---\n\nBody text.\n');
    expect(got).toEqual({ yaml: 'title: T', body: '\nBody text.\n' });
  });

  it('returns null when there is no frontmatter', () => {
    expect(splitFrontmatter('Body only.\n')).toBeNull();
  });

  it('does not treat a --- inside the body as a delimiter', () => {
    const got = splitFrontmatter('---\ntitle: T\n---\n\nA\n\n---\n\nB\n');
    expect(got?.yaml).toBe('title: T');
    expect(got?.body).toContain('---');
  });
});
