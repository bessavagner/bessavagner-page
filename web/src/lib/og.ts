// web/src/lib/og.ts
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import satori from 'satori';
import { Resvg } from '@resvg/resvg-js';
import { sanitizeDashes, clampText } from './og-text.ts';

const require = createRequire(import.meta.url);

export interface FontEntry {
  name: string;
  data: Buffer;
  weight: 400 | 500 | 600 | 700;
  style: 'normal';
}

const FONT_FILES: { name: string; weight: FontEntry['weight']; pkgPath: string }[] = [
  { name: 'Space Grotesk', weight: 600, pkgPath: '@fontsource/space-grotesk/files/space-grotesk-latin-600-normal.woff' },
  { name: 'Space Grotesk', weight: 700, pkgPath: '@fontsource/space-grotesk/files/space-grotesk-latin-700-normal.woff' },
  { name: 'Plus Jakarta Sans', weight: 400, pkgPath: '@fontsource/plus-jakarta-sans/files/plus-jakarta-sans-latin-400-normal.woff' },
  { name: 'Plus Jakarta Sans', weight: 500, pkgPath: '@fontsource/plus-jakarta-sans/files/plus-jakarta-sans-latin-500-normal.woff' },
  { name: 'JetBrains Mono', weight: 400, pkgPath: '@fontsource/jetbrains-mono/files/jetbrains-mono-latin-400-normal.woff' },
];

let cached: FontEntry[] | null = null;

/** Load the 5 Satori font buffers from the @fontsource packages (cached). */
export function loadFonts(): FontEntry[] {
  if (cached) return cached;
  cached = FONT_FILES.map(({ name, weight, pkgPath }) => ({
    name,
    weight,
    style: 'normal' as const,
    data: readFileSync(require.resolve(pkgPath)),
  }));
  return cached;
}

export interface OgProps {
  title: string;
  description: string;
  tags: string[];
  minutes: number;
  kind?: 'blog' | 'building';
}

const ACCENT = '#787de0';
const BASE = '#121621';
const TEXT_MUTED = '#cdd2e6';
const FOOTER_MUTED = '#8b90a8';

const div = (style: Record<string, unknown>, children: unknown): object => ({
  type: 'div',
  props: { style, children },
});

/** Build the Satori element tree for one post's card. Pure given props. */
export function buildOgMarkup(props: OgProps): object {
  const title = clampText(sanitizeDashes(props.title), 84);
  const description = clampText(sanitizeDashes(props.description), 168);
  const chips = props.tags.slice(0, 2).map((t) =>
    div(
      {
        display: 'flex',
        fontFamily: 'Plus Jakarta Sans',
        fontWeight: 500,
        fontSize: 22,
        color: ACCENT,
        border: `1px solid ${ACCENT}59`,
        backgroundColor: `${ACCENT}26`,
        borderRadius: 8,
        padding: '6px 16px',
        marginLeft: 12,
      },
      `#${t}`,
    ),
  );

  return div(
    {
      position: 'relative',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'space-between',
      width: '100%',
      height: '100%',
      backgroundColor: BASE,
      color: '#ffffff',
      padding: '64px',
      paddingLeft: '76px',
      fontFamily: 'Plus Jakarta Sans',
    },
    [
      div({ position: 'absolute', left: 0, top: 0, bottom: 0, width: 12, backgroundColor: ACCENT }, ''),
      // top row: wordmark + chips
      div({ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }, [
        div(
          { display: 'flex', fontFamily: 'Space Grotesk', fontWeight: 600, fontSize: 22, letterSpacing: 3, color: TEXT_MUTED },
          'VAGNER BESSA',
        ),
        div({ display: 'flex' }, chips),
      ]),
      // middle: optional building eyebrow + title + description
      div({ display: 'flex', flexDirection: 'column' }, [
        ...(props.kind === 'building'
          ? [div(
              { display: 'flex', fontFamily: 'Space Grotesk', fontWeight: 600, fontSize: 22, letterSpacing: 3, color: ACCENT, marginBottom: 16 },
              'BUILDING IN PUBLIC',
            )]
          : []),
        div(
          { display: 'flex', fontFamily: 'Space Grotesk', fontWeight: 700, fontSize: 60, lineHeight: 1.1, color: '#ffffff' },
          title,
        ),
        div(
          { display: 'flex', fontFamily: 'Plus Jakarta Sans', fontWeight: 400, fontSize: 28, lineHeight: 1.4, color: TEXT_MUTED, marginTop: 24, maxWidth: 960 },
          description,
        ),
      ]),
      // footer: dot + domain · reading time
      div({ display: 'flex', alignItems: 'center' }, [
        div({ display: 'flex', width: 12, height: 12, borderRadius: 9999, backgroundColor: ACCENT, marginRight: 16 }, ''),
        div(
          { display: 'flex', fontFamily: 'JetBrains Mono', fontWeight: 400, fontSize: 24, color: FOOTER_MUTED },
          `bessavagner.com · ${props.minutes} min`,
        ),
      ]),
    ],
  );
}

/** Render a post's OG card to a 1200x630 PNG buffer. */
export async function renderOgPng(props: OgProps): Promise<Buffer> {
  const svg = await satori(buildOgMarkup(props) as never, {
    width: 1200,
    height: 630,
    fonts: loadFonts(),
  });
  const resvg = new Resvg(svg, { fitTo: { mode: 'width', value: 1200 } });
  return resvg.render().asPng();
}
