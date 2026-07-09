// web/src/lib/analytics-core.ts
// Framework-free analytics core (mirrors the *-core.ts convention). No DOM here
// beyond the injectable `scope` — the browser glue lives in analytics.ts. Each
// tracker call is isolated in its own try/catch so a blocked/absent global can
// never break the other.

export type TrackParams = Record<string, string | number | boolean>;

export interface AnalyticsGlobals {
  umami?: { track: (name: string, data?: TrackParams) => void };
  gtag?: (command: 'event', name: string, params?: Record<string, unknown>) => void;
}

function fireUmami(scope: AnalyticsGlobals, name: string, params: TrackParams): void {
  try { scope.umami?.track(name, params); } catch { /* tracker blocked/absent */ }
}

function fireGtag(scope: AnalyticsGlobals, name: string, params: Record<string, unknown>): void {
  try { scope.gtag?.('event', name, params); } catch { /* gtag blocked/absent */ }
}

/** Fire one canonical event to BOTH Umami and GA4 from a single call site. */
export function track(
  name: string,
  params: TrackParams = {},
  scope: AnalyticsGlobals = globalThis as AnalyticsGlobals,
): void {
  fireUmami(scope, name, params);
  fireGtag(scope, name, params);
}

/** Collect `data-track-*` attributes into a flat params object (the marker
 *  `data-track` itself is excluded — it lacks the trailing dash). e.g.
 *  data-track-location="hero" -> { location: 'hero' }. */
export function trackParams(
  attributes: Iterable<{ name: string; value: string }>,
): Record<string, string> {
  const PREFIX = 'data-track-';
  const out: Record<string, string> = {};
  for (const attr of attributes) {
    if (attr.name.startsWith(PREFIX)) out[attr.name.slice(PREFIX.length)] = attr.value;
  }
  return out;
}
