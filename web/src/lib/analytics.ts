// web/src/lib/analytics.ts
// Browser entry: ONE document-level delegated click listener fires every
// [data-track] element through the dual-track core. Same-tab navigations that
// unload the page are routed through trackAndGo (beacon + callback guard) so the
// hit isn't dropped mid-navigation; everything else fires the plain track().
// Imported once from Base.astro.
import { track, trackAndGo, trackParams } from './analytics-core.ts';

/** True when following this click will unload the current document — i.e. a
 *  same-tab navigation to another URL. New-tab links (target=_blank), in-page
 *  hashes (#section), and modified/middle clicks do NOT unload. */
function unloadsPage(anchor: HTMLAnchorElement | null, e: MouseEvent): anchor is HTMLAnchorElement {
  if (!anchor) return false;
  if (anchor.target.toLowerCase() === '_blank') return false;
  if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return false;
  const href = anchor.getAttribute('href') ?? '';
  if (!href || href.startsWith('#')) return false; // in-page anchor: no unload
  return true;
}

function onClick(e: MouseEvent): void {
  const el = (e.target as HTMLElement | null)?.closest<HTMLElement>('[data-track]');
  if (!el) return;
  const name = el.getAttribute('data-track');
  if (!name) return;
  const params = trackParams(el.attributes);

  const anchor = el.closest('a');
  if (unloadsPage(anchor, e)) {
    const url = anchor.href;
    e.preventDefault();
    trackAndGo(name, params, { navigate: () => { window.location.href = url; } });
  } else {
    track(name, params);
  }
}

document.addEventListener('click', onClick);
