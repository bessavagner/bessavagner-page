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

/** Navigation-coupled variant: fire the event, then run `navigate` only after
 *  GA4 confirms the hit (event_callback) OR a timeout elapses — whichever first,
 *  never twice. An independent timer guarantees navigation even if gtag is
 *  entirely blocked/absent (the callback would never fire). Umami fires
 *  immediately; its own transport survives unload. See context 01 §2. */
export function trackAndGo(
  name: string,
  params: TrackParams,
  opts: {
    navigate: () => void;
    timeoutMs?: number;
    scope?: AnalyticsGlobals;
    setTimeoutFn?: (fn: () => void, ms: number) => void;
  },
): void {
  const scope = opts.scope ?? (globalThis as AnalyticsGlobals);
  const timeoutMs = opts.timeoutMs ?? 800;
  const schedule = opts.setTimeoutFn ?? ((fn, ms) => { setTimeout(fn, ms); });

  let navigated = false;
  const go = () => { if (!navigated) { navigated = true; opts.navigate(); } };

  fireUmami(scope, name, params);
  try {
    scope.gtag?.('event', name, {
      ...params,
      transport_type: 'beacon',
      event_callback: go,
      event_timeout: timeoutMs,
    });
  } catch { /* gtag blocked — the fallback timer below still navigates */ }

  // Independent safety net: fires slightly after event_timeout, so a blocked or
  // absent gtag (callback never runs) can't trap the user on the page.
  schedule(go, timeoutMs + 50);
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
