import { describe, it, expect } from 'vitest';
import { resolvePublishAt } from './clock';

describe('resolvePublishAt', () => {
  it('falls back to the supplied instant when PUBLISH_AT is absent', () => {
    expect(resolvePublishAt({}, 1234)).toBe(1234);
  });

  it('parses an ISO instant', () => {
    expect(resolvePublishAt({ PUBLISH_AT: '2026-07-14T12:05:00Z' }, 0)).toBe(
      Date.parse('2026-07-14T12:05:00Z'),
    );
  });

  it('throws on an unparsable value rather than silently using now', () => {
    expect(() => resolvePublishAt({ PUBLISH_AT: 'next tuesday' }, 0)).toThrow(/PUBLISH_AT/);
  });

  it('treats an empty string as absent, since CI passes "" for unset inputs', () => {
    expect(resolvePublishAt({ PUBLISH_AT: '' }, 99)).toBe(99);
  });
});
