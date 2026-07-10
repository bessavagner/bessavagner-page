# Diagram sources (`.mmd` → committed PNG)

Mermaid diagram sources for blog / build-log posts. The site can't render Mermaid
at request time (no `rehype-mermaid`, and a raw ` ```mermaid ` fence would show as
source text), so — exactly like the matplotlib figures under `../plots/` — the
diagram is the **source of truth in text**, rendered to a PNG that gets committed
and imported into a post via `<Image>`.

## Layout mirrors `src/assets/`

A source at `scripts/diagrams/<path>/<name>.mmd` renders to
`src/assets/<path>/<name>.png`:

```
scripts/diagrams/buildlog/stealthbench/architecture-seam.mmd
  -> src/assets/buildlog/stealthbench/architecture-seam.png
```

Then in the post:

```mdx
import archSeam from '../../../assets/buildlog/stealthbench/architecture-seam.png';

<Image src={archSeam} alt="…describe the diagram…"
  class="rounded-2xl border border-primary/20 my-8 w-full h-auto" />
```

## Rendering

```sh
pnpm diagram:build                 # render every .mmd
pnpm diagram:build scripts/diagrams/buildlog/stealthbench/architecture-seam.mmd
pnpm diagram:build scripts/diagrams/buildlog/stealthbench   # a subtree
```

Then commit the regenerated PNG alongside the `.mmd`.

## Why it's not part of `astro build`

Mermaid needs a DOM, so build-time rendering means a headless Chromium in the
deploy pipeline (`astro build` → Docker → Cloud Run), which currently has zero
browser dependency. Keeping this a local step preserves that: `mermaid-cli` is run
via `pnpm dlx @mermaid-js/mermaid-cli@<pinned>` and never enters the lockfile or
the CI install. If diagrams ever become frequent enough to want inline
` ```mermaid ` authoring, revisit a build-time integration then.
