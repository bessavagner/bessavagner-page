// @ts-check
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';
import mdx from '@astrojs/mdx';
import tailwindcss from '@tailwindcss/vite';
import { readFileSync, readdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const fromHere = (/** @type {string} */ p) => fileURLToPath(new URL(p, import.meta.url));

/**
 * Build a `pathname -> lastmod (Date)` map for the sitemap from real content
 * dates, so `<lastmod>` values are stable across rebuilds (no misleading
 * build-time stamps) and only move when the underlying content actually changes:
 *
 *   /blog/<slug>/        frontmatter `updatedDate ?? pubDate`
 *   /blog/               newest published post
 *   /blog/tags/<tag>/    newest published post carrying that tag
 *   /projects/<id>/      portfolio.json `updated` (per-project override supported)
 *   /                    portfolio.json `updated`
 *
 * Dates are sourced from files inside the build context (frontmatter + the
 * portfolio JSON) rather than git, because the production Docker build copies
 * only `web/` and has no `.git` available. Any URL without a known date simply
 * gets no `<lastmod>`, which is preferable to a fabricated one.
 */
function buildLastmod() {
  /** @type {Map<string, Date>} */
  const byPath = new Map();
  const now = Date.now();

  // --- Blog: parse frontmatter straight off disk (no astro:content in config) ---
  const blogDir = fromHere('./src/content/blog');
  const posts = [];
  for (const file of readdirSync(blogDir)) {
    if (!file.endsWith('.mdx')) continue;
    const src = readFileSync(`${blogDir}/${file}`, 'utf8');
    const fm = src.match(/^---\r?\n([\s\S]*?)\r?\n---/);
    if (!fm) continue;
    const block = fm[1];
    if (/^draft:\s*true\b/m.test(block)) continue;
    const pubRaw = (block.match(/^pubDate:\s*["']?([\d:.+\-TZ]+)["']?/m) || [])[1];
    if (!pubRaw) continue;
    const pubDate = new Date(pubRaw);
    // Future-dated posts aren't published in a prod build, so they're absent
    // from the sitemap — skip them here to keep "newest" computations honest.
    if (pubDate.getTime() > now) continue;
    const updRaw = (block.match(/^updatedDate:\s*["']?([\d:.+\-TZ]+)["']?/m) || [])[1];
    const lastmod = updRaw ? new Date(updRaw) : pubDate;
    const tagsRaw = (block.match(/^tags:\s*\[([^\]]*)\]/m) || [])[1] || '';
    const tags = tagsRaw
      .split(',')
      .map((t) => t.trim().replace(/^["']|["']$/g, ''))
      .filter(Boolean);
    const slug = file.replace(/\.mdx$/, '');
    posts.push({ lastmod, tags });
    byPath.set(`/blog/${slug}/`, lastmod);
  }

  if (posts.length) {
    const newest = new Date(Math.max(...posts.map((p) => p.lastmod.getTime())));
    byPath.set('/blog/', newest);
    /** @type {Map<string, Date>} */
    const tagNewest = new Map();
    for (const p of posts) {
      for (const tag of p.tags) {
        const cur = tagNewest.get(tag);
        if (!cur || p.lastmod > cur) tagNewest.set(tag, p.lastmod);
      }
    }
    for (const [tag, d] of tagNewest) byPath.set(`/blog/tags/${tag}/`, d);
  }

  // --- Projects + home: single honest date from the portfolio data source ---
  try {
    const data = JSON.parse(readFileSync(fromHere('./src/data/portfolio.json'), 'utf8'));
    const fallback = data.updated ? new Date(data.updated) : undefined;
    if (fallback) byPath.set('/', fallback);
    for (const proj of data.projects ?? []) {
      const d = proj?.updated ? new Date(proj.updated) : fallback;
      if (proj?.id && d) byPath.set(`/projects/${proj.id}/`, d);
    }
  } catch {
    /* no portfolio data — leave those URLs without a lastmod */
  }

  return byPath;
}

const LASTMOD = buildLastmod();

// https://astro.build/config
export default defineConfig({
  site: 'https://bessavagner.com',
  integrations: [
    mdx(),
    sitemap({
      filter: (page) => !page.includes('/blog/og/'),
      serialize(item) {
        const { pathname } = new URL(item.url);
        const lastmod = LASTMOD.get(pathname);
        if (lastmod) item.lastmod = lastmod.toISOString();
        return item;
      },
    }),
  ],
  vite: {
    plugins: [tailwindcss()],
  },
});
