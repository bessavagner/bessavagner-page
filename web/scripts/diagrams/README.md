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

## Light + dark variants (theme-aware figures)

A single baked PNG can't read on both page themes (dark text vanishes on the dark
base). So a diagram ships as two files: `<name>.mmd` (light) and a sibling
`<name>-dark.mmd`. The renderer bakes each onto its theme's `base-100` surface —
light on `#f7fafc`, dark rendered with mermaid's `dark` theme on `#121621` — so
the figure sits seamlessly inside its bordered card. Keep the two sources
structurally identical; they differ only in the `classDef` palette.

Then in the post, render both through `ThemedFigure`, which shows the one that
matches `[data-theme]` (same swap pattern as `blog/PostCard.astro`):

```mdx
import ThemedFigure from '../../../components/ThemedFigure.astro';
import archSeam from '../../../assets/buildlog/stealthbench/architecture-seam.png';
import archSeamDark from '../../../assets/buildlog/stealthbench/architecture-seam-dark.png';

<ThemedFigure light={archSeam} dark={archSeamDark} alt="…describe the diagram…" />
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
