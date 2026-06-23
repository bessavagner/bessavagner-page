// web/src/lib/og-text.ts
/** Replace em/en dashes (and surrounding whitespace) with a spaced hyphen. */
export function sanitizeDashes(s: string): string {
  return s.replace(/\s*[—–]\s*/g, ' - ');
}

/** Trim to <= max characters on a word boundary, appending an ellipsis when cut. */
export function clampText(s: string, max: number): string {
  if (s.length <= max) return s;
  const slice = s.slice(0, max);
  const lastSpace = slice.lastIndexOf(' ');
  const base = lastSpace > 0 ? slice.slice(0, lastSpace) : slice;
  return base.replace(/[\s.,;:]+$/, '') + '…';
}
