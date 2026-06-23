# bessavagner.com — Astro site

Static personal site (Astro + Tailwind 4 + DaisyUI 5). Replaces the legacy aiohttp app
at the repo root (kept until deploy cutover).

## Develop
```bash
corepack enable        # activates pnpm@10.15.1 (pinned in package.json)
pnpm install
pnpm dev               # http://localhost:4321
```

## Content
Edit `src/data/portfolio.json` (profile + projects). Components render everything from it —
adding a project = one JSON entry. Schema mirrors `../content/projects.schema.json`.

## Contact form
Uses [Web3Forms](https://web3forms.com) (no backend). Copy `.env.example` to `.env` and set
`PUBLIC_WEB3FORMS_KEY` (free — enter your email at web3forms.com to get a key).

## Build & preview
```bash
pnpm build         # -> dist/ (static)
pnpm preview
```

## Deploy (Cloud Run, static via nginx)
```bash
# from web/
docker build --build-arg PUBLIC_WEB3FORMS_KEY=xxxx -t <region>-docker.pkg.dev/bessavagner-page/web/site .
# push, then deploy to Cloud Run (container listens on :8080)
```
See `Dockerfile` + `nginx.conf`.
