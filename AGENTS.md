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

## Writing content (blog + build log)

Follow the writing guide at `web/src/content/writing-style.md` before drafting any
build-log update or blog post — first person, honest, concrete, **never fabricate**.

- Build-log updates: `web/src/content/buildlog/<project>/NN-slug.mdx` (keep the
  `NN-slug` ordering). Frontmatter needs `title`, `description`, `project`,
  `update`, `pubDate`, `tags`, `draft` (see `web/src/content.config.ts`).
- Blog posts: `web/src/content/blog/<slug>.mdx`.
- Scheduling: a future `pubDate` keeps a post hidden in the production build until
  that moment, so it's safe to merge/push ahead of go-live. Use a full ISO
  timestamp (e.g. `2026-06-28T08:00:00-03:00`) to pin the hour; a bare date is UTC
  midnight. `draft: true` hides it unconditionally. `astro dev` shows everything.

## Documentation

Full documentation: https://docs.astro.build

Consult these guides before working on related tasks:

- [Adding pages, dynamic routes, or middleware](https://docs.astro.build/en/guides/routing/)
- [Working with Astro components](https://docs.astro.build/en/basics/astro-components/)
- [Using React, Vue, Svelte, or other framework components](https://docs.astro.build/en/guides/framework-components/)
- [Adding or managing content](https://docs.astro.build/en/guides/content-collections/)
- [Adding styles or using Tailwind](https://docs.astro.build/en/guides/styling/)
- [Supporting multiple languages](https://docs.astro.build/en/guides/internationalization/)
