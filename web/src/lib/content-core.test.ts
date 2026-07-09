// web/src/lib/content-core.test.ts
import { describe, it, expect } from 'vitest';
import { parseFrontmatter, toDigestItem } from './content-core';

/** A minimal .mdx document with the given frontmatter lines. */
const doc = (fm: string) => `---\n${fm}\n---\n\nSome body text.\n`;

describe('parseFrontmatter', () => {
  it('reads the leading --- block into key/value pairs', () => {
    const fm = parseFrontmatter(doc('title: Hello\ndescription: A post'));
    expect(fm).toEqual({ title: 'Hello', description: 'A post' });
  });

  it('strips surrounding quotes from values', () => {
    const fm = parseFrontmatter(doc(`title: "Quoted"\ndescription: 'Single'`));
    expect(fm).toEqual({ title: 'Quoted', description: 'Single' });
  });

  it('returns null when there is no frontmatter block', () => {
    expect(parseFrontmatter('# Just a heading\n')).toBeNull();
  });
});

describe('toDigestItem', () => {
  it('maps blog/<slug>.mdx to /blog/<slug>/', () => {
    const item = toDigestItem(
      'blog/running-llm-generated-code-safely.mdx',
      doc('title: Running LLM code\ndescription: Sandboxes\npubDate: 2026-06-23'),
    );
    expect(item).toMatchObject({
      kind: 'blog',
      title: 'Running LLM code',
      description: 'Sandboxes',
      path: '/blog/running-llm-generated-code-safely/',
    });
    expect(item?.project).toBeUndefined();
  });

  it('maps buildlog/<project>/<slug>.mdx to /building/<project>/<slug>/', () => {
    const item = toDigestItem(
      'buildlog/replaygate/05-the-llm-judge.mdx',
      doc('title: The LLM judge\ndescription: It cannot fail your build\npubDate: 2026-07-08'),
    );
    expect(item).toMatchObject({
      kind: 'building',
      project: 'replaygate',
      path: '/building/replaygate/05-the-llm-judge/',
    });
  });

  it('keeps a nested buildlog slug intact', () => {
    const item = toDigestItem(
      'buildlog/turmarium/deep/06-matricula.mdx',
      doc('title: Matricula\ndescription: d\npubDate: 2026-07-06'),
    );
    expect(item?.path).toBe('/building/turmarium/deep/06-matricula/');
    expect(item?.project).toBe('turmarium');
  });

  it('excludes drafts', () => {
    expect(
      toDigestItem('blog/x.mdx', doc('title: X\ndescription: d\npubDate: 2026-07-08\ndraft: true')),
    ).toBeNull();
  });

  it('excludes files with no pubDate', () => {
    expect(toDigestItem('blog/x.mdx', doc('title: X\ndescription: d'))).toBeNull();
  });

  it('excludes a buildlog file that is not under a project folder', () => {
    expect(toDigestItem('buildlog/stray.mdx', doc('title: S\ndescription: d\npubDate: 2026-07-08'))).toBeNull();
  });

  it('excludes an unknown top-level content root', () => {
    expect(toDigestItem('notes/x.mdx', doc('title: X\ndescription: d\npubDate: 2026-07-08'))).toBeNull();
  });

  it('treats a bare-date pubDate as UTC midnight', () => {
    const item = toDigestItem('blog/x.mdx', doc('title: X\ndescription: d\npubDate: 2026-07-08'));
    expect(item?.pubDate.toISOString()).toBe('2026-07-08T00:00:00.000Z');
  });

  // The actual bug: ReplayGate #5 was dated 2026-07-08T08:00:00-03:00 and is due
  // on the UTC date 2026-07-08, not 2026-07-07.
  it('places a morning -03:00 timestamp on the same UTC day', () => {
    const item = toDigestItem(
      'buildlog/replaygate/05-the-llm-judge.mdx',
      doc('title: T\ndescription: d\npubDate: 2026-07-08T08:00:00-03:00'),
    );
    expect(item?.pubDate.toISOString().slice(0, 10)).toBe('2026-07-08');
  });

  // Timezone regression: an evening -03:00 timestamp rolls into the NEXT UTC day.
  it('places an evening -03:00 timestamp on the next UTC day', () => {
    const item = toDigestItem(
      'blog/x.mdx',
      doc('title: T\ndescription: d\npubDate: 2026-07-08T21:00:00-03:00'),
    );
    expect(item?.pubDate.toISOString().slice(0, 10)).toBe('2026-07-09');
  });

  it('falls back to the slug when title is absent', () => {
    expect(toDigestItem('blog/my-slug.mdx', doc('description: d\npubDate: 2026-07-08'))?.title).toBe('my-slug');
    expect(
      toDigestItem('buildlog/proj/01-update.mdx', doc('description: d\npubDate: 2026-07-08'))?.title,
    ).toBe('01-update');
  });

  it('defaults an absent description to the empty string', () => {
    expect(toDigestItem('blog/x.mdx', doc('title: X\npubDate: 2026-07-08'))?.description).toBe('');
  });
});
