# Vagner Bessa — Personal Site & Portfolio

Personal website and portfolio for Vagner Bessa, full-stack & AI engineer.
Live at **[bessavagner.com](https://bessavagner.com)**.

The site is a **static Astro app** (Astro + Tailwind CSS 4 + DaisyUI 5), built into an
nginx image and deployed to **Google Cloud Run** (`us-central1`). It is data-driven from a
single content source.

> The previous aiohttp/Python app was retired after the cutover to the Astro static site.
> Its history remains in git.

## Repository layout

| Path | What it is |
|------|------------|
| `web/` | The Astro site (pnpm). All site code, components, styles, and assets live here. |
| `content/projects.json` | Canonical portfolio content (source of truth). |
| `content/projects.schema.json` | JSON Schema for the content model. |
| `tools/cv/` | Résumé/CV (HTML + generated PDF). |
| `tools/og/` | Open Graph image generator (`generate.py`). |
| `docs/.ai/` | Planning docs, reports, and audit evidence. |
| `.github/workflows/deploy-web-cloudrun.yml` | CI: build + deploy `web/` to Cloud Run. |

> **Content sync:** `content/projects.json` is the source of truth; `web/src/data/portfolio.json`
> is its working copy consumed by the build. Keep the two identical.

## Develop

The site lives in `web/` and uses **pnpm** (via corepack).

```bash
cd web
corepack pnpm@10.15.1 install
pnpm dev        # local dev server
pnpm build      # static build into web/dist
pnpm preview    # serve the build (port 4322)
pnpm astro check  # type/diagnostics check
```

See [`web/README.md`](web/README.md) for more.

## Deploy

Pushes to `main` that touch `web/**` trigger
[`deploy-web-cloudrun.yml`](.github/workflows/deploy-web-cloudrun.yml), which builds the
nginx image and deploys it to the Cloud Run service `bessavagner-page` (auth via Workload
Identity Federation). See [`docs/.ai/plans/003-cloud-run-deploy.md`](docs/.ai/plans/003-cloud-run-deploy.md).

## License

Source code is licensed under the [MIT License](LICENSE).

Editorial content — blog posts, images, and branding (`web/src/content/**`,
`web/src/assets/**`, `web/public/images/**`) — is **All Rights Reserved** and
not covered by the MIT grant. See [`LICENSE`](LICENSE) for details.
