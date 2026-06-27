// web/scripts/digest.ts
// Composes and sends the daily content digest via Buttondown. Reads blog + buildlog
// frontmatter straight off disk (no astro:content runtime needed), mirroring the
// frontmatter parsing already used in astro.config.mjs.
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { selectDue, renderDigest, utcDateStamp, type DigestItem } from '../src/lib/digest-core.ts';

const SITE_URL = 'https://bessavagner.com';
const API = 'https://api.buttondown.com/v1';

const fromHere = (p: string) => fileURLToPath(new URL(p, import.meta.url));

const argv = process.argv.slice(2);
const DRY_RUN = argv.includes('--dry-run');
const dateArg = argv.find((a) => a.startsWith('--date='))?.split('=')[1];
const TODAY = dateArg ?? utcDateStamp(new Date());

interface Frontmatter { [k: string]: string }

/** Minimal frontmatter parse: the leading --- block, one `key: value` per line. */
function parseFrontmatter(src: string): Frontmatter | null {
  const m = src.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!m) return null;
  const fm: Frontmatter = {};
  for (const line of m[1].split(/\r?\n/)) {
    const kv = line.match(/^([A-Za-z_]+):\s*(.*)$/);
    if (!kv) continue;
    fm[kv[1]] = kv[2].trim().replace(/^["']|["']$/g, '');
  }
  return fm;
}

/** Recursively list *.mdx under a directory. */
function listMdx(dir: string): string[] {
  const out: string[] = [];
  for (const name of readdirSync(dir)) {
    const full = `${dir}/${name}`;
    if (statSync(full).isDirectory()) out.push(...listMdx(full));
    else if (name.endsWith('.mdx')) out.push(full);
  }
  return out;
}

function readItems(): DigestItem[] {
  const items: DigestItem[] = [];

  // Blog: web/src/content/blog/<slug>.mdx -> /blog/<slug>/
  const blogDir = fromHere('../src/content/blog');
  for (const file of listMdx(blogDir)) {
    const fm = parseFrontmatter(readFileSync(file, 'utf8'));
    if (!fm || fm.draft === 'true' || !fm.pubDate) continue;
    const slug = file.slice(blogDir.length + 1).replace(/\.mdx$/, '');
    items.push({
      kind: 'blog',
      title: fm.title ?? slug,
      description: fm.description ?? '',
      path: `/blog/${slug}/`,
      pubDate: new Date(fm.pubDate),
    });
  }

  // Buildlog: web/src/content/buildlog/<project>/<slug>.mdx -> /building/<project>/<slug>/
  // URL parts come from the folder path (the same id the building route splits on),
  // not from frontmatter, so nested slugs stay consistent with the route.
  const buildDir = fromHere('../src/content/buildlog');
  for (const file of listMdx(buildDir)) {
    const fm = parseFrontmatter(readFileSync(file, 'utf8'));
    if (!fm || fm.draft === 'true' || !fm.pubDate) continue;
    const rel = file.slice(buildDir.length + 1).replace(/\.mdx$/, ''); // "regwatch/01-foo"
    const cut = rel.indexOf('/');
    if (cut === -1) continue; // updates always live under a project folder
    const project = rel.slice(0, cut);
    const slug = rel.slice(cut + 1);
    items.push({
      kind: 'building',
      title: fm.title ?? slug,
      description: fm.description ?? '',
      path: `/building/${project}/${slug}/`,
      pubDate: new Date(fm.pubDate),
      project,
    });
  }

  return items;
}

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
  const due = selectDue(readItems(), TODAY);
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
