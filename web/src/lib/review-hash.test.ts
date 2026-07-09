import { describe, it, expect } from 'vitest';
import {
  normalizeBody,
  extractAssetSpecifiers,
  computeReviewHash,
  canonicalize,
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

  it('ignores a local import shown inside a fenced code block', () => {
    const body = [
      '```ts',
      "import chart from './example.svg';",
      '```',
      '',
      "import real from './real.svg';",
    ].join('\n');
    expect(extractAssetSpecifiers(body, {})).toEqual(['./real.svg']);
  });

  it('still finds a real top-level import in the same body as a fenced one', () => {
    const body = [
      "import before from './before.svg';",
      '```',
      "import fenced from './fenced.svg';",
      '```',
      "import after from './after.svg';",
    ].join('\n');
    expect(extractAssetSpecifiers(body, {})).toEqual(['./after.svg', './before.svg']);
  });

  it('handles a fence with a language info string', () => {
    const body = [
      '```typescript',
      "import fenced from './fenced.svg';",
      '```',
      "import real from './real.svg';",
    ].join('\n');
    expect(extractAssetSpecifiers(body, {})).toEqual(['./real.svg']);
  });

  it('handles a ~~~ fence', () => {
    const body = [
      '~~~',
      "import fenced from './fenced.svg';",
      '~~~',
      "import real from './real.svg';",
    ].join('\n');
    expect(extractAssetSpecifiers(body, {})).toEqual(['./real.svg']);
  });

  it('does not let fence-stripping join surrounding lines into a fabricated match', () => {
    // If the fence lines were deleted outright instead of blanked, the import
    // statement split across the fence boundary could be concatenated into
    // something that matches the import regex. Blanking must prevent that.
    const body = [
      'import broken',
      '```',
      "  from './should-not-match.svg';",
      '```',
    ].join('\n');
    expect(extractAssetSpecifiers(body, {})).toEqual([]);
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

  it('computes the same hash for assets in any input order — consistent and stable', () => {
    // Asset order must not affect the digest, since neither the MDX body nor
    // the frontmatter defines asset order. Supplying the two assets in either
    // order must hash identically, and that hash must not move across runs.
    const upperFirst = payload({
      assets: [
        { specifier: '../../assets/B.svg', sha256: 'aa' },
        { specifier: '../../assets/b.svg', sha256: 'bb' },
      ],
    });
    const lowerFirst = payload({
      assets: [
        { specifier: '../../assets/b.svg', sha256: 'bb' },
        { specifier: '../../assets/B.svg', sha256: 'aa' },
      ],
    });
    const h1 = computeReviewHash(upperFirst);
    const h2 = computeReviewHash(lowerFirst);
    expect(h1).toBe(h2);
    // Stable across repeated calls too, not just order-independent.
    expect(computeReviewHash(upperFirst)).toBe(h1);
  });

  it('canonicalizes assets in code-unit order, not locale collation order', () => {
    // Pins the actual ordering, not just that some consistent order is used:
    // under code-unit comparison 'B' (0x42) sorts before 'b' (0x62), while a
    // locale-aware comparator commonly reverses that on this machine's ICU data.
    const canonical = canonicalize(
      payload({
        assets: [
          { specifier: '../../assets/b.svg', sha256: 'bb' },
          { specifier: '../../assets/B.svg', sha256: 'aa' },
        ],
      }),
    );
    const upperIndex = canonical.indexOf('../../assets/B.svg');
    const lowerIndex = canonical.indexOf('../../assets/b.svg');
    expect(upperIndex).toBeGreaterThan(-1);
    expect(lowerIndex).toBeGreaterThan(-1);
    expect(upperIndex).toBeLessThan(lowerIndex);
  });
});
