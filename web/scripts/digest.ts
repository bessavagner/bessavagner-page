// web/scripts/digest.ts
// Composes and sends the digest of newly-live content via Buttondown. Post
// discovery and frontmatter parsing live in scripts/read-posts.ts +
// src/lib/content-core.ts. Selection is pure (digest-core.ts); everything below
// that touches the network — the liveness check, the Buttondown dedupe lookup,
// and the send itself — lives here.
import { selectAnnounceable, renderDigest, utcDateStamp, type AnnounceCandidate } from '../src/lib/digest-core.ts';
import { resolvePublishAt } from '../src/lib/clock.ts';
import { readPosts } from './read-posts.ts';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';

const SITE_URL = 'https://bessavagner.com';
const API = 'https://api.buttondown.com/v1';
const WINDOW_DAYS = 30;
const CAP = 3;
const LIVENESS_TIMEOUT_MS = 10_000;
/** Buttondown's `/v1/emails` list is expected to be a handful of pages. A cap
 *  bounds a runaway `next` loop (e.g. the API looping a `next` link back on
 *  itself) so the nightly job can't hang forever. Hitting the cap throws
 *  rather than returning what was paged so far: a truncated sent-history
 *  would make an already-announced post look un-announced, and dedupe would
 *  re-announce it — the exact double-send this system exists to prevent. So
 *  the safe failure here is "the whole run aborts", not "silently proceed
 *  with partial data". */
const MAX_SENT_EMAIL_PAGES = 50;

/**
 * The instant this publication system went live. Posts published before it are never
 * announced: eight of them were missed by the old exact-UTC-day `selectDue` and, per the
 * project's standing rule, a missed digest is never sent retroactively. Buttondown's
 * dedupe covers the ones that DID go out; this covers the ones that never did.
 */
const ANNOUNCE_FROM = Date.parse('2026-07-10T00:00:00Z');

const argv = process.argv.slice(2);
const DRY_RUN = argv.includes('--dry-run');
const FORCE = argv.includes('--force');
const nowArg = argv.find((a) => a.startsWith('--now='))?.split('=')[1];
const NOW = resolvePublishAt({ PUBLISH_AT: nowArg ?? process.env.PUBLISH_AT }, Date.now());

/** Drop any item whose page does not respond 200 to a HEAD request. This is what
 *  makes a 404 in the newsletter structurally impossible: the deploy is what the
 *  digest job `needs:`, but proving the specific page is live is stronger than
 *  trusting the deploy job's overall exit code. */
async function filterLive(items: AnnounceCandidate[]): Promise<AnnounceCandidate[]> {
  const live: AnnounceCandidate[] = [];
  for (const item of items) {
    const url = `${SITE_URL}${item.path}`;
    let ok = false;
    try {
      const res = await fetch(url, { method: 'HEAD', signal: AbortSignal.timeout(LIVENESS_TIMEOUT_MS) });
      ok = res.status === 200;
    } catch (err) {
      // Covers both a network failure and a timeout (AbortSignal.timeout aborts with
      // a DOMException here) — either way the page's liveness is unproven, so fail
      // safe and drop it rather than block the rest of the sequential loop.
      console.warn(`DROP  ${item.path} — HEAD request failed: ${(err as Error).message}`);
      continue;
    }
    if (ok) {
      live.push(item);
    } else {
      console.warn(`DROP  ${item.path} — HEAD returned non-200; not announcing`);
    }
  }
  return live;
}

/** Every email body Buttondown has actually sent, paginated. GET only — this is
 *  read-only reconnaissance, never a send. */
async function sentEmailBodies(key: string): Promise<string[]> {
  const bodies: string[] = [];
  let url: string | null = `${API}/emails`;
  let pages = 0;
  while (url) {
    if (pages >= MAX_SENT_EMAIL_PAGES) {
      throw new Error(
        `sentEmailBodies: exceeded ${MAX_SENT_EMAIL_PAGES} pages of /v1/emails without reaching the end — ` +
          'refusing to proceed with a truncated sent-history (that would make an already-sent post look ' +
          'un-announced and get re-announced).',
      );
    }
    const res = await fetch(url, { headers: { Authorization: `Token ${key}` } });
    if (!res.ok) throw new Error(`list emails failed: ${res.status} ${await res.text()}`);
    const data = (await res.json()) as { results?: { body?: string }[]; next?: string | null };
    for (const e of data.results ?? []) if (e.body) bodies.push(e.body);
    url = data.next ?? null;
    pages++;
  }
  return bodies;
}

/** Drop any item whose path already appears in a previously-sent email body.
 *  Buttondown is the only system that knows what actually reached subscribers,
 *  so it is the source of truth for dedupe, not our own local state.
 *
 *  Assumption: this digest system is the only thing that ever puts one of these
 *  URLs into a Buttondown email body. If a post's URL were ever pasted into a
 *  manually-composed email (e.g. linked in prose), that post would match here
 *  and be silently skipped forever. The failure direction this assumption
 *  buys us is deliberate and one-way: a broken assumption causes a silent
 *  skip, never a double-send. */
export function dedupeAgainstSent(items: AnnounceCandidate[], sentBodies: string[]): AnnounceCandidate[] {
  return items.filter((item) => {
    const alreadySent = sentBodies.some((body) => body.includes(item.path));
    if (alreadySent) console.warn(`DROP  ${item.path} — already appears in a sent email`);
    return !alreadySent;
  });
}

async function send(subject: string, body: string, key: string): Promise<void> {
  const create = await fetch(`${API}/emails`, {
    method: 'POST',
    headers: { Authorization: `Token ${key}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ subject, body }),
  });
  if (!create.ok) throw new Error(`create email failed: ${create.status} ${await create.text()}`);
  const { id } = (await create.json()) as { id: string };

  const patch = await fetch(`${API}/emails/${id}`, {
    method: 'PATCH',
    headers: { Authorization: `Token ${key}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ status: 'about_to_send' }),
  });
  if (!patch.ok) throw new Error(`send email failed: ${patch.status} ${await patch.text()}`);
}

async function main() {
  const { posts, invalid } = readPosts(NOW);
  for (const bad of invalid) {
    console.warn(`WARN  ${bad.repoPath} — unparsable pubDate "${bad.rawPubDate}"; skipped`);
  }

  const candidates: AnnounceCandidate[] = posts
    .filter((p) => p.item !== null)
    .map((p) => ({ ...p.item!, state: p.state }));

  let items = selectAnnounceable(candidates, { now: NOW, windowDays: WINDOW_DAYS, notBefore: ANNOUNCE_FROM });
  if (items.length === 0) {
    console.log('Nothing to announce.');
    return;
  }

  // Guard 1: liveness. Never announce a page that doesn't actually 200.
  items = await filterLive(items);
  if (items.length === 0) {
    console.log('Nothing to announce.');
    return;
  }

  // Guard 2: dedupe against what Buttondown has actually sent.
  const key = process.env.BUTTONDOWN_KEY;
  if (!key) {
    console.warn('WARN  BUTTONDOWN_KEY is not set — cannot dedupe against sent emails; skipping dedupe');
  } else {
    const sentBodies = await sentEmailBodies(key);
    items = dedupeAgainstSent(items, sentBodies);
  }

  if (items.length === 0) {
    console.log('Nothing to announce.');
    return;
  }

  // Guard 3: cap. A digest that suddenly wants to announce a pile of posts is a bug.
  if (items.length > CAP && !FORCE) {
    console.error(`REFUSING to announce ${items.length} item(s) — exceeds the cap of ${CAP}:`);
    for (const item of items) console.error(`  ${item.path}`);
    console.error('Pass --force to override.');
    process.exit(1);
  }

  const today = utcDateStamp(new Date(NOW));
  const { subject, body } = renderDigest(items, { siteUrl: SITE_URL, today });

  if (DRY_RUN) {
    console.log(`--- DRY RUN (${items.length} item(s)) ---`);
    console.log(`Subject: ${subject}\n`);
    console.log(body);
    return;
  }

  if (!key) throw new Error('BUTTONDOWN_KEY is not set');
  await send(subject, body, key);
  console.log(`Sent digest "${subject}" (${items.length} item(s)).`);
}

// Only run the digest when this file is the process entry point (`node
// scripts/digest.ts ...`), not when it's imported for its functions — e.g. by
// scripts/digest.test.ts, which unit-tests dedupeAgainstSent directly and must
// not trigger a real (network-touching, potentially mail-sending) run on import.
const isMain = process.argv[1] !== undefined && fileURLToPath(import.meta.url) === resolve(process.argv[1]);

if (isMain) {
  main().catch((err) => {
    console.error(err);
    process.exit(1);
  });
}
