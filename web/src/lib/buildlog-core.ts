// web/src/lib/buildlog-core.ts
// Pure, framework-free logic for the Building-Publicly section. No `astro:content`
// or `import.meta` here, so this module is unit-testable under `node --test`.
import type { Project, Metric } from './portfolio.ts';

export interface BuildWork {
  summary?: string;
  body?: string;
  problem?: string;
  approach?: string;
  outcome?: string;
  highlights?: string[];
  metrics?: Metric[];
  year?: number;
  kind?: string;
  role?: string;
  image?: string;
  ogImage?: string;
  links?: Partial<Project['links']>;
  featured?: boolean;
  order?: number;
}

export interface BuildProject {
  slug: string;
  title: string;
  tagline: string;
  blurb: string;
  repo: string;
  startDate: string;
  status: 'active' | 'shipped';
  stack: string[];
  work?: BuildWork;
}

/** Split a collection id ("regwatch/01-foo") into its project folder + update slug. */
export function splitUpdateId(id: string): { project: string; slug: string } {
  const i = id.indexOf('/');
  if (i === -1) return { project: id, slug: id };
  return { project: id.slice(0, i), slug: id.slice(i + 1) };
}

/** Newest-first by pubDate. Returns a new array; input is not mutated. */
export function sortUpdatesByDateDesc<T extends { data: { pubDate: Date } }>(updates: T[]): T[] {
  return [...updates].sort((a, b) => b.data.pubDate.getTime() - a.data.pubDate.getTime());
}

/** The single newest update, or undefined for an empty list. */
export function latestUpdate<T extends { data: { pubDate: Date } }>(updates: T[]): T | undefined {
  return sortUpdatesByDateDesc(updates)[0];
}

/** Prev/next siblings of an update within its project, by ascending `update`
 *  number. `prev` = the closest earlier update (lower number), `next` = the
 *  closest later one. Robust to unsorted input and gaps in numbering; returns
 *  `{}` when `current` is not in `projectUpdates`, and an undefined side when it
 *  is first (no prev) or last (no next). Pure — unit-tested under `node --test`. */
export function seriesNeighbors<T extends UpdateLike>(
  current: T,
  projectUpdates: T[],
): { prev?: T; next?: T } {
  const ordered = [...projectUpdates].sort((a, b) => a.data.update - b.data.update);
  const i = ordered.findIndex((u) => u.id === current.id);
  if (i === -1) return {};
  return { prev: ordered[i - 1], next: ordered[i + 1] };
}

/** Map a shipped registry entry into a synthetic portfolio Project (graduation). */
export function buildProjectToProject(bp: BuildProject): Project {
  const w = bp.work ?? {};
  return {
    id: bp.slug,
    name: bp.title,
    tagline: bp.tagline,
    summary: w.summary ?? bp.blurb,
    body: w.body,
    problem: w.problem,
    approach: w.approach,
    outcome: w.outcome,
    kind: w.kind,
    role: w.role,
    featured: w.featured ?? false,
    order: w.order ?? 999,
    year: w.year,
    status: 'shipped',
    private: false,
    stack: bp.stack,
    highlights: w.highlights,
    metrics: w.metrics,
    links: { repo: bp.repo, buildlog: `/building/${bp.slug}/`, ...(w.links ?? {}) },
    image: w.image,
    ogImage: w.ogImage,
  };
}
