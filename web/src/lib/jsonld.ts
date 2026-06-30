// web/src/lib/jsonld.ts
/**
 * Serialize a value for safe injection into an inline
 * `<script type="application/ld+json">` element via `set:html`.
 *
 * `JSON.stringify` does not escape `<`, `>`, or `&`, so a string value
 * containing `</script>` (or an HTML comment opener) could terminate the
 * script element early and inject arbitrary markup. Escaping those three
 * characters to their `\uXXXX` forms keeps the output valid JSON while making
 * such a break-out impossible. Use this anywhere structured data is emitted
 * with `set:html`, even when the source is author-controlled today.
 */
export function jsonLd(data: unknown): string {
  return JSON.stringify(data)
    .replace(/</g, '\\u003c')
    .replace(/>/g, '\\u003e')
    .replace(/&/g, '\\u0026');
}
