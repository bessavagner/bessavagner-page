// web/src/lib/cta-core.ts
// Pure resolver: a per-post CTA goal -> the single call-to-action copy + link.
// The closed vocabulary mirrors the `cta` enum in content.config.ts. No
// `astro:content` / `import.meta`, so it runs under `node --test`. EndCta.astro
// is a thin render over resolveCta(); clicks fire via data-track (Epic A path).

export type CtaGoal = 'lets-talk' | 'cv' | 'follow-build' | 'subscribe';
export type Collection = 'blog' | 'buildlog';

export interface ResolvedCta {
  goal: CtaGoal;
  lead: string;   // soft-lead sentence
  action: string; // the one hard action (button label)
  href: string;   // where the action points ('' = component supplies it)
}

/** Per-collection default when a post sets no `cta`. */
export const DEFAULT_CTA: Record<Collection, CtaGoal> = {
  blog: 'lets-talk',
  buildlog: 'follow-build',
};

const COPY: Record<CtaGoal, Omit<ResolvedCta, 'goal'>> = {
  'lets-talk': {
    lead: 'Working on something in this space, or hiring for it?',
    action: "Let's talk",
    href: '/#section-contact',
  },
  cv: {
    lead: 'Want the full background behind work like this?',
    action: 'Download my CV',
    href: '', // EndCta substitutes portfolio.profile.links.cv
  },
  'follow-build': {
    lead: "I'm building this in the open, one update at a time.",
    action: 'Follow the build',
    href: '/building/', // EndCta may override with the current project hub
  },
  subscribe: {
    lead: 'Want the next post in your inbox?',
    action: 'Subscribe',
    href: '#subscribe',
  },
};

/** Resolve a post's goal (or the collection default) into concrete CTA copy. */
export function resolveCta(goal: CtaGoal | undefined, collection: Collection): ResolvedCta {
  const g = goal ?? DEFAULT_CTA[collection];
  return { goal: g, ...COPY[g] };
}
