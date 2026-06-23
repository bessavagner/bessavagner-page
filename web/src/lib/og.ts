// web/src/lib/og.ts
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';

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
