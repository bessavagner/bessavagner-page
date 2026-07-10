// web/scripts/post.test.ts
// Covers two review findings against scripts/post.ts:
//   1. `post approve` must not corrupt a CRLF file's line endings.
//   2. `post lint` must also report posts with an unparsable pubDate, not
//      just posts missing `status`.
// The CLI dispatch at the bottom of post.ts is guarded behind an
// entry-point check (`isMain`) so importing this module for its exported
// functions is side-effect-free.
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { approvePost, cmdLint, cmdPreview, rewriteKeys, detectEol } from './post.ts';
import { readPosts } from './read-posts.ts';

let root = '';
let contentDir = '';

beforeEach(() => {
  root = mkdtempSync(join(tmpdir(), 'post-cli-'));
  contentDir = join(root, 'content');
  mkdirSync(join(contentDir, 'blog'), { recursive: true });
  mkdirSync(join(contentDir, 'buildlog'), { recursive: true });
});

afterEach(() => rmSync(root, { recursive: true, force: true }));

describe('detectEol', () => {
  it('detects CRLF when present', () => {
    expect(detectEol('a\r\nb\r\n')).toBe('\r\n');
  });

  it('defaults to LF otherwise', () => {
    expect(detectEol('a\nb\n')).toBe('\n');
  });
});

describe('rewriteKeys', () => {
  it('rejoins with the given eol and does not leave stray \\r on untouched lines', () => {
    const yaml = 'title: T\r\ndescription: D\r\nstatus: review';
    const out = rewriteKeys(yaml, { status: 'approved', reviewHash: 'sha256:x' }, ['status', 'reviewHash'], '\r\n');
    expect(out.split('\r\n')).toEqual(['title: T', 'description: D', 'status: approved', 'reviewHash: sha256:x']);
    expect(out).not.toContain('\r\r');
    // No lone \r left glued onto a line before the eol.
    for (const line of out.split('\r\n')) expect(line.endsWith('\r')).toBe(false);
  });
});

describe('approvePost — CRLF safety', () => {
  it('keeps a CRLF file entirely CRLF after stamping the three approval keys', () => {
    const abs = join(contentDir, 'blog', 'crlf-post.mdx');
    const raw = ['---', 'title: CRLF post', 'description: A post with CRLF endings', 'pubDate: 2020-01-01', 'status: review', '---', '', 'Body line one.', 'Body line two.', ''].join(
      '\r\n',
    );
    writeFileSync(abs, raw);

    const hash = approvePost(abs);
    expect(hash).toMatch(/^sha256:[0-9a-f]{64}$/);

    const after = readFileSync(abs, 'utf8');

    // Every line ending in the rewritten file is CRLF; there is no bare LF
    // anywhere (a bare LF would only occur if \r\n and \n got mixed).
    expect(after.includes('\r\n')).toBe(true);
    expect(after.replace(/\r\n/g, '')).not.toContain('\n');

    // The three approval keys were stamped.
    expect(after).toMatch(/status: approved\r\n/);
    expect(after).toMatch(/reviewedAt: \S+\r\n/);
    expect(after).toContain(`reviewHash: ${hash}\r\n`);

    // Untouched content survived.
    expect(after).toContain('title: CRLF post\r\n');
    expect(after).toContain('Body line one.\r\n');
  });

  it('keeps an LF file entirely LF (control case)', () => {
    const abs = join(contentDir, 'blog', 'lf-post.mdx');
    const raw = ['---', 'title: LF post', 'description: d', 'pubDate: 2020-01-01', 'status: review', '---', '', 'Body.', ''].join('\n');
    writeFileSync(abs, raw);

    approvePost(abs);
    const after = readFileSync(abs, 'utf8');
    expect(after).not.toContain('\r');
  });
});

describe('cmdLint — reports posts with an unparsable pubDate', () => {
  it('reports both missing-status and invalid-pubDate posts, and exits 1', () => {
    writeFileSync(
      join(contentDir, 'blog', 'missing-status.mdx'),
      ['---', 'title: No status field', 'description: d', 'pubDate: 2026-01-01', '---', '', 'Body.', ''].join('\n'),
    );
    writeFileSync(
      join(contentDir, 'blog', 'bad-pubdate.mdx'),
      ['---', 'title: Bad date', 'description: d', 'pubDate: not-a-date', 'status: review', '---', '', 'Body.', ''].join('\n'),
    );
    writeFileSync(
      join(contentDir, 'blog', 'fine.mdx'),
      ['---', 'title: Fine', 'description: d', 'pubDate: 2026-01-01', 'status: review', '---', '', 'Body.', ''].join('\n'),
    );

    const logs: string[] = [];
    const errors: string[] = [];
    const logSpy = vi.spyOn(console, 'log').mockImplementation((msg: string) => {
      logs.push(msg);
    });
    const errorSpy = vi.spyOn(console, 'error').mockImplementation((msg: string) => {
      errors.push(msg);
    });
    const exitSpy = vi.spyOn(process, 'exit').mockImplementation(((code?: number) => {
      throw new Error(`process.exit(${code})`);
    }) as never);

    expect(() => cmdLint(contentDir)).toThrow('process.exit(1)');

    logSpy.mockRestore();
    errorSpy.mockRestore();
    exitSpy.mockRestore();

    const out = logs.join('\n');
    const err = errors.join('\n');

    expect(out).toContain('missing-status.mdx');
    expect(out).toContain('bad-pubdate.mdx');
    expect(out).toContain('pubDate: not-a-date');
    expect(out).not.toContain('fine.mdx');
    expect(err).toContain('missing status');
    expect(err).toContain('unparsable pubDate');
  });

  it('reports OK and does not exit when every post is clean', () => {
    writeFileSync(
      join(contentDir, 'blog', 'fine.mdx'),
      ['---', 'title: Fine', 'description: d', 'pubDate: 2026-01-01', 'status: review', '---', '', 'Body.', ''].join('\n'),
    );

    const logs: string[] = [];
    const logSpy = vi.spyOn(console, 'log').mockImplementation((msg: string) => {
      logs.push(msg);
    });
    const exitSpy = vi.spyOn(process, 'exit').mockImplementation(((code?: number) => {
      throw new Error(`process.exit(${code})`);
    }) as never);

    expect(() => cmdLint(contentDir)).not.toThrow();
    expect(logs.join('\n')).toContain('OK — every post declares status.');

    logSpy.mockRestore();
    exitSpy.mockRestore();
  });
});

// Sanity: cmdLint(contentDir) and readPosts(now, contentDir) agree on what's invalid,
// so the fixture above is exercising the real invalid-pubDate path, not a fluke.
describe('cmdLint fixture sanity', () => {
  it('the bad-pubdate fixture actually lands in readPosts().invalid', () => {
    writeFileSync(
      join(contentDir, 'blog', 'bad-pubdate.mdx'),
      ['---', 'title: Bad date', 'description: d', 'pubDate: not-a-date', 'status: review', '---', '', 'Body.', ''].join('\n'),
    );
    const { invalid } = readPosts(Date.now(), contentDir);
    expect(invalid.some((i) => i.rawPubDate === 'not-a-date')).toBe(true);
  });
});

describe('cmdPreview — includes stale-approval posts regardless of date', () => {
  it('includes a stale-approval post outside the 7-day window in the preview', () => {
    const now = Date.now();

    // Create an approved post with an invalid hash (stale-approval state)
    // and a pubDate 30 days in the future (well outside the 7-day window)
    const pubDate = new Date(now + 30 * 24 * 60 * 60 * 1000).toISOString();
    writeFileSync(
      join(contentDir, 'blog', 'stale-post.mdx'),
      ['---', 'title: Stale Approval Post', 'description: A post with stale approval', `pubDate: ${pubDate}`, 'status: approved', 'reviewHash: invalid-hash-that-wont-match', '---', '', 'Body content.', ''].join('\n'),
    );

    // Create a normal scheduled post within 7 days for comparison
    const scheduledPubDate = new Date(now + 3 * 24 * 60 * 60 * 1000).toISOString();
    writeFileSync(
      join(contentDir, 'blog', 'scheduled-post.mdx'),
      ['---', 'title: Scheduled Post', 'description: A scheduled post', `pubDate: ${scheduledPubDate}`, 'status: approved', 'reviewHash: sha256:0000000000000000000000000000000000000000000000000000000000000000', '---', '', 'Different body.', ''].join('\n'),
    );

    const logs: string[] = [];
    const logSpy = vi.spyOn(console, 'log').mockImplementation((msg: string) => {
      logs.push(msg);
    });

    cmdPreview(['--days', '7'], contentDir);

    logSpy.mockRestore();

    const out = logs.join('\n');

    // Stale approval post should appear even though it's 30 days in the future
    expect(out).toContain('Stale Approval Post');
    expect(out).toContain('stale-approval');

    // Scheduled post should also appear (sanity check that preview works)
    expect(out).toContain('Scheduled Post');
    expect(out).toContain('scheduled');
  });
});
