// web/src/lib/analytics.ts
// Browser entry: ONE document-level delegated click listener fires every
// [data-track] element through the dual-track core. Imported once from
// Base.astro so a single handler covers the whole site. (Navigation-safe
// delivery for same-tab links is added in Task 6 / story A4.)
import { track, trackParams } from './analytics-core.ts';

function onClick(e: MouseEvent): void {
  const el = (e.target as HTMLElement | null)?.closest<HTMLElement>('[data-track]');
  if (!el) return;
  const name = el.getAttribute('data-track');
  if (!name) return;
  track(name, trackParams(el.attributes));
}

document.addEventListener('click', onClick);
