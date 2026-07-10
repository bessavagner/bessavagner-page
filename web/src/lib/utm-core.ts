// web/src/lib/utm-core.ts
// Assembles LinkedIn campaign URLs from one closed UTM vocabulary, so every
// outbound link is generated — never hand-typed — and GA4 + Umami collapse
// LinkedIn into a single Organic Social (or Paid Social) / linkedin row with
// per-post attribution. Convention + GA4 channel rules:
//   docs/.ai/playbooks/utm-convention.md
//   docs/.ai/sprints/backlog-2026-07/contexts/03-utm-conventions-and-ga4-attribution.md
//
// Casing is the whole point: GA4's channel regexes are anchored + lowercase, so
// a capitalized source/medium silently lands in Unassigned. The closed
// vocabulary below makes a wrong value a throw at generation time, not a dead
// tag on a live link.

/** Canonical site origin. Mirror of astro.config.mjs `site`. */
export const SITE_ORIGIN = 'https://bessavagner.com';

/** The only valid utm_source. Never linkedin.com / lnkd.in / LinkedIn. */
export const UTM_SOURCES = ['linkedin'] as const;

/** social = organic share; paid-social = boosted / sponsored. The channel switch. */
export const UTM_MEDIUMS = ['social', 'paid-social'] as const;

export type UtmSource = (typeof UTM_SOURCES)[number];
export type UtmMedium = (typeof UTM_MEDIUMS)[number];

/** Lowercase, hyphen-joined slug: a-z / 0-9, single interior hyphens only. */
export const SLUG_RE = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

export interface UtmInput {
  /** Destination path (`/blog/foo`) or a full canonical URL on the site origin. */
  destination: string;
  /** Defaults to 'linkedin'. */
  source?: string;
  /** Defaults to 'social'. */
  medium?: string;
  /** Asset slug being promoted, e.g. 'polymorphic-vaults'. */
  campaign: string;
  /** Per-post id, e.g. '2026-07-09-am'. */
  content: string;
}

export interface RegistryRow {
  destinationUrl: string;
  source: UtmSource;
  medium: UtmMedium;
  campaign: string;
  content: string;
  taggedUrl: string;
  datePosted: string;
}

const isSource = (v: string): v is UtmSource => (UTM_SOURCES as readonly string[]).includes(v);
const isMedium = (v: string): v is UtmMedium => (UTM_MEDIUMS as readonly string[]).includes(v);

/**
 * Resolve a destination to an absolute URL on SITE_ORIGIN. UTMs are inbound-only,
 * so the destination must be a canonical page on this site with no query string.
 * Rejects off-site hosts (external tagging), pre-existing queries (would fragment
 * or collide), and non-absolute paths.
 */
export function resolveDestination(destination: string): string {
  let url: URL;
  if (/^https?:\/\//i.test(destination)) {
    url = new URL(destination);
    if (url.origin !== SITE_ORIGIN) {
      throw new Error(`destination must be on ${SITE_ORIGIN}, got ${url.origin}`);
    }
  } else {
    if (!destination.startsWith('/')) {
      throw new Error(`destination path must start with "/" (got "${destination}")`);
    }
    url = new URL(destination, SITE_ORIGIN);
  }
  if (url.search) {
    throw new Error(`destination must be canonical with no query string (got "${url.search}")`);
  }
  return url.toString();
}

/** Build the one canonical tagged URL. Throws on any out-of-vocab / non-slug value. */
export function buildTaggedUrl(input: UtmInput): string {
  const source = input.source ?? 'linkedin';
  const medium = input.medium ?? 'social';
  if (!isSource(source)) {
    throw new Error(`utm_source "${source}" is out of vocabulary; allowed: ${UTM_SOURCES.join(', ')}`);
  }
  if (!isMedium(medium)) {
    throw new Error(`utm_medium "${medium}" is out of vocabulary; allowed: ${UTM_MEDIUMS.join(', ')}`);
  }
  if (!SLUG_RE.test(input.campaign)) {
    throw new Error(`utm_campaign "${input.campaign}" must be a lowercase hyphenated slug (${SLUG_RE})`);
  }
  if (!SLUG_RE.test(input.content)) {
    throw new Error(`utm_content "${input.content}" must be a lowercase hyphenated slug (${SLUG_RE})`);
  }
  const url = new URL(resolveDestination(input.destination));
  // Insertion order is preserved and mirrors the convention doc's column order.
  // .set() percent-encodes each value, so the assembled query is always well-formed.
  url.searchParams.set('utm_source', source);
  url.searchParams.set('utm_medium', medium);
  url.searchParams.set('utm_campaign', input.campaign);
  url.searchParams.set('utm_content', input.content);
  return url.toString();
}

/**
 * Link-placement A/B variants (E3) — the dimension GA4 will decide. Encoded as a
 * suffix on utm_content so the one field carries both the date-slot and the
 * placement (there is no spare UTM field). Closed vocab: a typo throws, same as
 * UTM_SOURCES / UTM_MEDIUMS.
 */
export const UTM_PLACEMENTS = ['post-body', 'first-comment', 'profile-featured'] as const;
export type UtmPlacement = (typeof UTM_PLACEMENTS)[number];

const isPlacement = (v: string): v is UtmPlacement =>
  (UTM_PLACEMENTS as readonly string[]).includes(v);

/**
 * Compose the compound utm_content that carries both the date-slot and the A/B
 * placement, e.g. ('2026-07-09-am','first-comment') → '2026-07-09-am-first-comment'.
 * Throws on a non-slug date-slot or an out-of-vocab placement, so the result is
 * guaranteed to still match SLUG_RE and pass buildTaggedUrl.
 */
export function composePlacementContent(dateSlot: string, placement: string): string {
  if (!SLUG_RE.test(dateSlot)) {
    throw new Error(`date-slot "${dateSlot}" must be a lowercase hyphenated slug (${SLUG_RE})`);
  }
  if (!isPlacement(placement)) {
    throw new Error(`utm placement "${placement}" is out of vocabulary; allowed: ${UTM_PLACEMENTS.join(', ')}`);
  }
  return `${dateSlot}-${placement}`;
}

/** Column order for registry.csv — asserted against formatRegistryRow in the test. */
export const REGISTRY_HEADER = 'destination_url,source,medium,campaign,content,tagged_url,date_posted';

/**
 * One CSV line for the registry log. All fields are comma-free by construction
 * (closed-vocab tokens, lowercase slugs, and query-less URLs whose only encoded
 * chars are the UTM separators), so no CSV quoting is needed.
 */
export function formatRegistryRow(row: RegistryRow): string {
  return [
    row.destinationUrl,
    row.source,
    row.medium,
    row.campaign,
    row.content,
    row.taggedUrl,
    row.datePosted,
  ].join(',');
}
