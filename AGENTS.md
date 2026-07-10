# bessavagner-page

Personal site + dev blog. The web app is an **Astro** project under `web/` — run
all `astro` / `npm` commands from there (`cd web` first).

## Development

When starting the dev server, use background mode:

```
cd web
astro dev --background
```

Manage the background server with `astro dev stop`, `astro dev status`, and `astro dev logs`.

## Code intelligence (codegraph)

This repo is indexed by **codegraph** — a live SQLite knowledge graph of every
symbol, edge, and file, served through the `codegraph` MCP tools and kept fresh
by a background daemon (the `.codegraph/` dir is machine-local and gitignored;
never commit it). Reads are sub-millisecond and the index auto-syncs ~1s behind
edits.

**Use it BEFORE reading or editing code, not during** — it is the pre-built
search index, so a `codegraph_explore` call is Read-equivalent and beats a
manual grep-then-read loop:

- "How does X work" / "where is X" / architecture / tracing a flow →
  `codegraph_explore` (one call; pass a natural-language question or a bag of
  symbol/file names — it returns the verbatim source grouped by file, and is
  usually the only call you need).
- "What calls this?" / "what does this call?" / "what breaks if I change this?"
  → `codegraph_callers` / `codegraph_callees` / `codegraph_impact`.
- Just a symbol's location → `codegraph_search`.

It indexes **code** (`.ts`/`.astro`/etc.), not MDX content — reach for the file
tools directly when working on `src/content/`.

## Writing content (blog + build log)

Follow the writing guide at `web/src/content/writing-style.md` before drafting any
build-log update or blog post — first person, honest, concrete, **never fabricate**.

- Build-log updates: `web/src/content/buildlog/<project>/NN-slug.mdx` (keep the
  `NN-slug` ordering). Frontmatter needs `title`, `description`, `project`,
  `update`, `pubDate`, `tags`, `status` (see `web/src/content.config.ts`).
- Blog posts: `web/src/content/blog/<slug>.mdx`.
- Post visibility: frontmatter `status` controls publication. Use `status: draft`
  (or omit it; defaults to `draft`), `status: review`, or `status: approved`. Only
  `approved` posts that have a current `pubDate` and whose content hash matches the
  stored `reviewHash` are visible in production; run `pnpm post:approve <path>` to
  stamp a post as approved (it computes and stores `reviewHash` and `reviewedAt`
  automatically—never hand-edit these fields). Check post status with `pnpm post:status`
  and validate frontmatter with `pnpm post:lint`.
- Scheduling: a future `pubDate` keeps a post hidden until that moment, so it's safe to
  merge/push ahead of go-live. Use a full ISO timestamp (e.g. `2026-06-28T08:00:00-03:00`)
  to pin the hour; a bare date is UTC midnight. `astro dev` shows everything.

## Documentation

Full documentation: https://docs.astro.build

Consult these guides before working on related tasks:

- [Adding pages, dynamic routes, or middleware](https://docs.astro.build/en/guides/routing/)
- [Working with Astro components](https://docs.astro.build/en/basics/astro-components/)
- [Using React, Vue, Svelte, or other framework components](https://docs.astro.build/en/guides/framework-components/)
- [Adding or managing content](https://docs.astro.build/en/guides/content-collections/)
- [Adding styles or using Tailwind](https://docs.astro.build/en/guides/styling/)
- [Supporting multiple languages](https://docs.astro.build/en/guides/internationalization/)
