// web/scripts/read-posts.test.ts
// Pins the behaviour that moved out of content-core.ts when Task 5 rewrote
// frontmatter parsing as real YAML: draft-exclusion, missing/unparsable
// pubDate handling, bare-date and timezone resolution, status defaulting,
// reviewHash verification (including the stale-approval and
// missing-asset paths), and buildlog route mapping. None of this was
// covered anywhere Vitest collected before this file existed.
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { mkdtempSync, mkdirSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { readPosts } from './read-posts.ts';
import { reviewHashOf } from '../src/lib/review-verify.ts';

let root = '';
let contentDir = '';

/** Write a fixture post under contentDir/<relPath>, creating parent dirs. */
function writePost(relPath: string, yaml: string, body = 'Body text.\n'): string {
  const abs = join(contentDir, relPath);
  mkdirSync(dirname(abs), { recursive: true });
  writeFileSync(abs, `---\n${yaml}\n---\n${body}`);
  return abs;
}

// Fixture posts, built fresh in beforeEach.
const APPROVED_TITLE = 'Approved Post';
const APPROVED_DESCRIPTION = 'A correctly reviewed post';
const APPROVED_TAGS = ['a', 'b'];
const APPROVED_HERO = '../../assets/blog/hero.png';
const APPROVED_BODY = 'Reviewed content.\n';
let approvedHash = '';

beforeEach(() => {
  root = mkdtempSync(join(tmpdir(), 'read-posts-'));
  contentDir = join(root, 'content');
  mkdirSync(join(contentDir, 'blog'), { recursive: true });
  mkdirSync(join(contentDir, 'buildlog'), { recursive: true });
  mkdirSync(join(root, 'assets', 'blog'), { recursive: true });
  writeFileSync(join(root, 'assets', 'blog', 'hero.png'), 'PNGBYTES');

  writePost(
    'blog/draft-post.mdx',
    ['title: Draft', 'description: d', 'pubDate: 2026-01-01', 'draft: true'].join('\n'),
  );

  writePost('blog/no-pubdate.mdx', ['title: No date', 'description: d'].join('\n'));

  writePost(
    'blog/invalid-pubdate.mdx',
    ['title: Bad date', 'description: d', 'pubDate: not-a-date'].join('\n'),
  );

  writePost('blog/bare-date.mdx', ['title: Bare', 'description: d', 'pubDate: 2026-06-23'].join('\n'));

  writePost(
    'blog/morning.mdx',
    ['title: Morning', 'description: d', 'pubDate: 2026-07-08T08:00:00-03:00'].join('\n'),
  );

  writePost(
    'blog/evening.mdx',
    ['title: Evening', 'description: d', 'pubDate: 2026-06-30T21:00:00-03:00'].join('\n'),
  );

  writePost(
    'blog/no-status.mdx',
    ['title: No status', 'description: d', 'pubDate: 2026-01-01'].join('\n'),
  );

  const approvedAbs = join(contentDir, 'blog', 'approved-correct.mdx');
  approvedHash = reviewHashOf(approvedAbs, {
    body: APPROVED_BODY,
    data: {
      title: APPROVED_TITLE,
      description: APPROVED_DESCRIPTION,
      tags: APPROVED_TAGS,
      heroImage: APPROVED_HERO,
    },
  });
  writePost(
    'blog/approved-correct.mdx',
    [
      `title: ${APPROVED_TITLE}`,
      `description: ${APPROVED_DESCRIPTION}`,
      'pubDate: 2026-06-01T00:00:00Z',
      'tags: [a, b]',
      'status: approved',
      `heroImage: ${APPROVED_HERO}`,
      `reviewHash: ${approvedHash}`,
    ].join('\n'),
    APPROVED_BODY,
  );

  writePost(
    'blog/approved-stale.mdx',
    [
      'title: Stale',
      'description: d',
      'pubDate: 2020-01-01',
      'status: approved',
      `reviewHash: sha256:${'0'.repeat(64)}`,
    ].join('\n'),
  );

  writePost(
    'blog/approved-missing-asset.mdx',
    [
      'title: Missing asset',
      'description: d',
      'pubDate: 2020-01-01',
      'status: approved',
      'heroImage: ../../assets/blog/gone.png',
      `reviewHash: sha256:${'1'.repeat(64)}`,
    ].join('\n'),
  );

  writePost(
    'buildlog/proj1/nested/route-post.mdx',
    ['title: Route', 'description: d', 'pubDate: 2026-01-01'].join('\n'),
  );
});

afterEach(() => rmSync(root, { recursive: true, force: true }));

const find = (posts: ReturnType<typeof readPosts>['posts'], repoPath: string) =>
  posts.find((p) => p.repoPath.endsWith(repoPath));

describe('readPosts — pubDate presence and validity', () => {
  it('excludes a post with no pubDate, without reporting it as invalid', () => {
    const { posts, invalid } = readPosts(Date.now(), contentDir);
    expect(find(posts, 'blog/no-pubdate.mdx')).toBeUndefined();
    expect(invalid.some((i) => i.repoPath.endsWith('blog/no-pubdate.mdx'))).toBe(false);
  });

  it('reports an unparsable pubDate as invalid with its raw value, excludes it from posts, and does not throw', () => {
    expect(() => readPosts(Date.now(), contentDir)).not.toThrow();
    const { posts, invalid } = readPosts(Date.now(), contentDir);
    expect(find(posts, 'blog/invalid-pubdate.mdx')).toBeUndefined();
    const bad = invalid.find((i) => i.repoPath.endsWith('blog/invalid-pubdate.mdx'));
    expect(bad?.rawPubDate).toBe('not-a-date');
  });
});

describe('readPosts — pubDate resolution', () => {
  it('resolves a bare date to UTC midnight', () => {
    const { posts } = readPosts(Date.now(), contentDir);
    const p = find(posts, 'blog/bare-date.mdx');
    expect(p?.data.pubDate.toISOString()).toBe('2026-06-23T00:00:00.000Z');
  });

  it('keeps a morning -03:00 timestamp on the same UTC day', () => {
    const { posts } = readPosts(Date.now(), contentDir);
    const p = find(posts, 'blog/morning.mdx');
    expect(p?.data.pubDate.toISOString()).toBe('2026-07-08T11:00:00.000Z');
  });

  it('rolls an evening -03:00 timestamp to the next UTC day', () => {
    const { posts } = readPosts(Date.now(), contentDir);
    const p = find(posts, 'blog/evening.mdx');
    expect(p?.data.pubDate.toISOString()).toBe('2026-07-01T00:00:00.000Z');
  });
});

describe('readPosts — status defaulting', () => {
  it('defaults an absent status to draft, both in data and state', () => {
    const { posts } = readPosts(Date.now(), contentDir);
    const p = find(posts, 'blog/no-status.mdx');
    expect(p?.data.status).toBe('draft');
    expect(p?.state).toBe('draft');
  });
});

describe('readPosts — reviewHash verification', () => {
  it('matches a correctly computed reviewHash and reports scheduled when pubDate is in the future', () => {
    const past = Date.parse('2026-01-01T00:00:00Z'); // before the fixture's 2026-06-01 pubDate
    const { posts } = readPosts(past, contentDir);
    const p = find(posts, 'blog/approved-correct.mdx');
    expect(p?.state).toBe('scheduled');
  });

  it('matches a correctly computed reviewHash and reports published when pubDate has passed', () => {
    const future = Date.parse('2026-07-01T00:00:00Z'); // after the fixture's 2026-06-01 pubDate
    const { posts } = readPosts(future, contentDir);
    const p = find(posts, 'blog/approved-correct.mdx');
    expect(p?.state).toBe('published');
  });

  it('reports stale-approval when the stored reviewHash does not match current content', () => {
    const { posts } = readPosts(Date.now(), contentDir);
    const p = find(posts, 'blog/approved-stale.mdx');
    expect(p?.state).toBe('stale-approval');
  });

  it('catches UnresolvedAssetError for a missing referenced asset, treats it as stale-approval, and does not throw', () => {
    expect(() => readPosts(Date.now(), contentDir)).not.toThrow();
    const { posts } = readPosts(Date.now(), contentDir);
    const p = find(posts, 'blog/approved-missing-asset.mdx');
    expect(p?.state).toBe('stale-approval');
  });
});

describe('readPosts — buildlog route mapping', () => {
  it('maps a nested buildlog slug to /building/<project>/<nested>/<slug>/', () => {
    const { posts } = readPosts(Date.now(), contentDir);
    const p = find(posts, 'buildlog/proj1/nested/route-post.mdx');
    expect(p?.item?.path).toBe('/building/proj1/nested/route-post/');
  });
});
