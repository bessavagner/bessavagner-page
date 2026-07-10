import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { mkdtempSync, mkdirSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { UnresolvedAssetError, hashAssets, reviewHashOf } from './review-verify';

let root = '';
const post = () => join(root, 'content', 'blog', 'a-post.mdx');

beforeEach(() => {
  root = mkdtempSync(join(tmpdir(), 'review-verify-'));
  mkdirSync(join(root, 'content', 'blog'), { recursive: true });
  mkdirSync(join(root, 'assets', 'blog'), { recursive: true });
  writeFileSync(join(root, 'assets', 'blog', 'chart.svg'), '<svg>one</svg>');
  writeFileSync(join(root, 'assets', 'blog', 'hero.png'), 'PNGBYTES');
  writeFileSync(post(), 'unused');
});

afterEach(() => rmSync(root, { recursive: true, force: true }));

describe('hashAssets', () => {
  it('resolves specifiers relative to the post and digests their bytes', () => {
    const got = hashAssets(post(), ['../../assets/blog/chart.svg']);
    expect(got).toHaveLength(1);
    expect(got[0].specifier).toBe('../../assets/blog/chart.svg');
    expect(got[0].sha256).toMatch(/^[0-9a-f]{64}$/);
  });

  it('gives different digests for different bytes', () => {
    const before = hashAssets(post(), ['../../assets/blog/chart.svg'])[0].sha256;
    writeFileSync(join(root, 'assets', 'blog', 'chart.svg'), '<svg>two</svg>');
    const after = hashAssets(post(), ['../../assets/blog/chart.svg'])[0].sha256;
    expect(after).not.toBe(before);
  });

  it('throws UnresolvedAssetError rather than hashing around a missing file', () => {
    expect(() => hashAssets(post(), ['../../assets/blog/gone.svg'])).toThrow(UnresolvedAssetError);
    try {
      hashAssets(post(), ['../../assets/blog/gone.svg']);
    } catch (err) {
      expect((err as UnresolvedAssetError).specifier).toBe('../../assets/blog/gone.svg');
    }
  });
});

describe('reviewHashOf', () => {
  const data = { title: 'T', description: 'D', tags: ['a'] };

  it('changes when a referenced chart is regenerated', () => {
    const body = "import c from '../../assets/blog/chart.svg';\n\nText.\n";
    const before = reviewHashOf(post(), { body, data });
    writeFileSync(join(root, 'assets', 'blog', 'chart.svg'), '<svg>regenerated</svg>');
    expect(reviewHashOf(post(), { body, data })).not.toBe(before);
  });

  it('changes when heroImage bytes change', () => {
    const withHero = { ...data, heroImage: '../../assets/blog/hero.png' };
    const before = reviewHashOf(post(), { body: 'Text.\n', data: withHero });
    writeFileSync(join(root, 'assets', 'blog', 'hero.png'), 'DIFFERENT');
    expect(reviewHashOf(post(), { body: 'Text.\n', data: withHero })).not.toBe(before);
  });

  it('is unchanged by an unrelated file in the tree', () => {
    const before = reviewHashOf(post(), { body: 'Text.\n', data });
    writeFileSync(join(root, 'assets', 'blog', 'unrelated.svg'), '<svg/>');
    expect(reviewHashOf(post(), { body: 'Text.\n', data })).toBe(before);
  });
});
