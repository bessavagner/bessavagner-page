import { describe, it, expect } from 'vitest';
import {
  normalizeBody,
  extractAssetSpecifiers,
  computeReviewHash,
  type ReviewPayload,
} from './review-hash';

const payload = (over: Partial<ReviewPayload> = {}): ReviewPayload => ({
  body: 'Hello.\n',
  title: 'T',
  description: 'D',
  tags: ['b', 'a'],
  assets: [],
  ...over,
});

describe('normalizeBody', () => {
  it('converts CRLF to LF', () => {
    expect(normalizeBody('a\r\nb\r\n')).toBe('a\nb\n');
  });
  it('strips trailing whitespace from each line', () => {
    expect(normalizeBody('a   \nb\t\n')).toBe('a\nb\n');
  });
  it('collapses trailing newlines to exactly one', () => {
    expect(normalizeBody('a\n\n\n')).toBe('a\n');
  });
  it('adds a trailing newline when missing', () => {
    expect(normalizeBody('a')).toBe('a\n');
  });
});

describe('extractAssetSpecifiers', () => {
  it('finds relative imports of assets', () => {
    const body = [
      "import chart from '../../assets/blog/x/pass-rate.svg';",
      'import Foo from "../../assets/blog/x/other.png"',
      'text',
    ].join('\n');
    expect(extractAssetSpecifiers(body, {})).toEqual([
      '../../assets/blog/x/other.png',
      '../../assets/blog/x/pass-rate.svg',
    ]);
  });

  it('includes heroImage and heroImageDark', () => {
    const got = extractAssetSpecifiers('', { heroImage: './a.png', heroImageDark: './b.png' });
    expect(got).toEqual(['./a.png', './b.png']);
  });

  it('ignores bare package imports', () => {
    expect(extractAssetSpecifiers("import { Chart } from 'chart.js';", {})).toEqual([]);
  });

  it('deduplicates and sorts, so import order is not content', () => {
    const body = "import a from './x.svg';\nimport b from './x.svg';";
    expect(extractAssetSpecifiers(body, {})).toEqual(['./x.svg']);
  });
});

describe('computeReviewHash', () => {
  it('is a sha256: prefixed 64-char hex digest', () => {
    expect(computeReviewHash(payload())).toMatch(/^sha256:[0-9a-f]{64}$/);
  });

  it('is stable across runs', () => {
    expect(computeReviewHash(payload())).toBe(computeReviewHash(payload()));
  });

  it('ignores tag order', () => {
    expect(computeReviewHash(payload({ tags: ['a', 'b'] }))).toBe(
      computeReviewHash(payload({ tags: ['b', 'a'] })),
    );
  });

  it('ignores line endings and trailing whitespace', () => {
    expect(computeReviewHash(payload({ body: 'Hello.  \r\n' }))).toBe(computeReviewHash(payload()));
  });

  it('changes when the body changes', () => {
    expect(computeReviewHash(payload({ body: 'Goodbye.\n' }))).not.toBe(computeReviewHash(payload()));
  });

  it('changes when the title or description changes', () => {
    expect(computeReviewHash(payload({ title: 'U' }))).not.toBe(computeReviewHash(payload()));
    expect(computeReviewHash(payload({ description: 'E' }))).not.toBe(computeReviewHash(payload()));
  });

  it('changes when a tag is added', () => {
    expect(computeReviewHash(payload({ tags: ['a', 'b', 'c'] }))).not.toBe(computeReviewHash(payload()));
  });

  it('changes when a referenced asset changes', () => {
    const withAsset = (sha: string) => payload({ assets: [{ specifier: './x.svg', sha256: sha }] });
    expect(computeReviewHash(withAsset('aa'))).not.toBe(computeReviewHash(withAsset('bb')));
  });

  it('changes when an asset is added — the chart-swap hole', () => {
    expect(computeReviewHash(payload({ assets: [{ specifier: './x.svg', sha256: 'aa' }] }))).not.toBe(
      computeReviewHash(payload()),
    );
  });
});
