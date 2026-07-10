// web/src/lib/analytics-events.ts
// Single source of truth for analytics event names. One canonical snake_case
// name per user action, fired identically to Umami and GA4 so the two tools can
// be joined by name. Names already registered as GA4 key events
// (generate_lead, whatsapp_click, newsletter_signup) are verbatim — renaming one
// orphans a live key event. Parity table:
// docs/.ai/sprints/backlog-2026-07/contexts/05-umami-ga4-dual-analytics.md §5.

export const EVENTS = {
  /** WhatsApp floating button. Live GA4 key event — do not rename. */
  WHATSAPP_CLICK: 'whatsapp_click',
  /** Contact form submit (lead). Live GA4 key event — do not rename. */
  GENERATE_LEAD: 'generate_lead',
  /** Newsletter subscribe. Live GA4 key event — do not rename. */
  NEWSLETTER_SIGNUP: 'newsletter_signup',
  /** CV / résumé download. New GA4 key event (A5). */
  CV_DOWNLOAD: 'cv_download',
  /** Hero "Let's talk" CTA. */
  HERO_CTA_CONTACT: 'hero_cta_contact',
  /** Hero "See my work" CTA. */
  HERO_CTA_WORK: 'hero_cta_work',
  /** Email address click (hero + contact). */
  EMAIL_CLICK: 'email_click',
  /** Buildlog series prev/next/hub nav. Param: direction = prev|next|hub. */
  SERIES_NAV: 'series_nav',
} as const;

export type EventName = (typeof EVENTS)[keyof typeof EVENTS];
