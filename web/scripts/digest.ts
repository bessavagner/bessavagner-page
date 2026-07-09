// web/scripts/digest.ts
// Composes and sends the daily content digest via Buttondown. Post discovery and
// frontmatter parsing live in scripts/read-posts.ts + src/lib/content-core.ts.
import { selectDue, renderDigest, utcDateStamp } from '../src/lib/digest-core.ts';
import { readPosts } from './read-posts.ts';

const SITE_URL = 'https://bessavagner.com';
const API = 'https://api.buttondown.com/v1';

const argv = process.argv.slice(2);
const DRY_RUN = argv.includes('--dry-run');
const dateArg = argv.find((a) => a.startsWith('--date='))?.split('=')[1];
const TODAY = dateArg ?? utcDateStamp(new Date());

async function alreadySent(subject: string, key: string): Promise<boolean> {
  let url: string | null = `${API}/emails`;
  while (url) {
    const res = await fetch(url, { headers: { Authorization: `Token ${key}` } });
    if (!res.ok) throw new Error(`list emails failed: ${res.status} ${await res.text()}`);
    const data = (await res.json()) as { results?: { subject?: string }[]; next?: string | null };
    if ((data.results ?? []).some((e) => e.subject === subject)) return true;
    url = data.next ?? null;
  }
  return false;
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
  const { posts, invalid } = readPosts();
  for (const bad of invalid) {
    console.warn(`WARN  ${bad.repoPath} — unparsable pubDate "${bad.rawPubDate}"; skipped`);
  }
  const due = selectDue(posts.map((p) => p.item), TODAY);
  if (due.length === 0) {
    console.log(`Nothing dated ${TODAY}; not sending.`);
    return;
  }
  const { subject, body } = renderDigest(due, { siteUrl: SITE_URL, today: TODAY });

  if (DRY_RUN) {
    console.log(`--- DRY RUN (${due.length} item(s) for ${TODAY}) ---`);
    console.log(`Subject: ${subject}\n`);
    console.log(body);
    return;
  }

  const key = process.env.BUTTONDOWN_KEY;
  if (!key) throw new Error('BUTTONDOWN_KEY is not set');

  if (await alreadySent(subject, key)) {
    console.log(`Digest "${subject}" already exists; skipping (idempotent).`);
    return;
  }
  await send(subject, body, key);
  console.log(`Sent digest "${subject}" (${due.length} item(s)).`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
