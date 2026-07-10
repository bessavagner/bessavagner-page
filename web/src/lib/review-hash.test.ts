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

  it('does not fabricate a specifier from a mid-paragraph line beginning with "import"', () => {
    // A line beginning with "import" only starts an ESM statement to MDX when
    // it begins a block (document start, or after a blank line). Mid-paragraph,
    // it's prose — and the old whole-body regex let [^'"]* bridge from that
    // prose line to an unrelated later `from '...'` line.
    const body = [
      'Here is some prose.',
      'import the logic works like this',
      '',
      "we source from './fab.svg' here",
    ].join('\n');
    expect(extractAssetSpecifiers(body, {})).toEqual([]);
  });

  it('does not fabricate a specifier from soft-wrapped prose starting with "import"', () => {
    const body = [
      'To use the helper you must',
      'import the module before you can',
      '',
      "read it from './fab.svg' at build time",
    ].join('\n');
    expect(extractAssetSpecifiers(body, {})).toEqual([]);
  });

  it('still finds a multi-line import whose specifier is on a later line', () => {
    const body = ["import {", '  Chart,', "} from '../../assets/x.svg';", '', 'Text.'].join('\n');
    expect(extractAssetSpecifiers(body, {})).toEqual(['../../assets/x.svg']);
  });

  it('finds two imports that share a single block', () => {
    const body = ["import a from './a.svg';", "import b from './b.svg';", '', 'Text.'].join('\n');
    expect(extractAssetSpecifiers(body, {})).toEqual(['./a.svg', './b.svg']);
  });

  it('finds a real import in a CRLF body (a CRLF blank line must still split blocks)', () => {
    // A CRLF blank line is \r\n\r\n — i.e. \n \r \n — so a block-splitting
    // regex that only recognizes \n-bounded blank lines never splits a CRLF
    // body at all, and the whole document becomes one block gated on its
    // literal first line. Prose-opening posts (all of them) then fail the
    // gate and no import anywhere is found.
    const body = [
      'Some intro prose.',
      '',
      "import Chart from '../../assets/blog/x/chart.svg';",
      '',
      'Closing prose.',
    ].join('\r\n');
    expect(extractAssetSpecifiers(body, {})).toEqual(['../../assets/blog/x/chart.svg']);
  });

  it('ignores a block comment inside an import statement and finds the real specifier', () => {
    const body = "import x /* from './fake.svg' nonsense */ from './real.svg';";
    expect(extractAssetSpecifiers(body, {})).toEqual(['./real.svg']);
  });

  it('ignores a line comment inside an import statement and finds the real specifier', () => {
    const body = ["import x // was './old.svg'", "  from './real.svg';"].join('\n');
    expect(extractAssetSpecifiers(body, {})).toEqual(['./real.svg']);
  });

  it('ignores a trailing line comment after a real import statement', () => {
    const body = "import x from './real.svg'; // see './other.svg'";
    expect(extractAssetSpecifiers(body, {})).toEqual(['./real.svg']);
  });

  it('does not mangle a specifier that legitimately contains //', () => {
    const body = "import x from './a//b.svg';";
    expect(extractAssetSpecifiers(body, {})).toEqual(['./a//b.svg']);
  });

  it('does not mangle a bare https:// specifier into a false local match', () => {
    const body = "import x from 'https://cdn.example/x.js';";
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
