// web/src/lib/og-pages.ts
// Pure registry mapping each hub/index page's card key to its OgProps. No
// `astro:content` / `import.meta` here, so this module runs under vitest —
// same convention as related-core.ts. Task 3's Astro route owns computing
// the counts and reading the registries; this module only turns already-
// computed plain data into card copy.
import type { OgProps } from './og.ts';

/** Minimal shape `pageCardKeys` needs from a portfolio registry project. */
export interface RegistryProjectLike {
  id: string;
  ogImage?: string;
}

/** Minimal shape `pageCardKeys` needs from a build-project registry entry. */
export interface RegistryBuildProjectLike {
  slug: string;
}

/** Copy + counts for one `building/<slug>` card. */
export interface BuildProjectCardData {
  slug: string;
  title: string;
  blurb: string;
  stack: string[];
  updateCount: number;
}

/** Copy + counts for one `projects/<id>` card. */
export interface PortfolioProjectCardData {
  id: string;
  name: string;
  summary: string;
  tagline: string;
  stack: string[];
  year?: number;
}

/** Everything `buildPageCard` may need across all 9 keys, already computed
 *  by the caller (no filesystem/content-collection reads happen in here). */
export interface PageCardData {
  postCount: number;
  updateCount: number;
  buildProjects: BuildProjectCardData[];
  projects: PortfolioProjectCardData[];
}

const BUILDING_PREFIX = 'building/';
const PROJECTS_PREFIX = 'projects/';

/** `N post`/`N posts`, `N update`/`N updates`, etc. */
function pluralize(count: number, noun: string): string {
  return `${count} ${noun}${count === 1 ? '' : 's'}`;
}

/** The card key for every hub/index page that needs one: the two fixed
 *  keys (`blog`, `building`), one `building/<slug>` per registered build
 *  project, and one `projects/<id>` per portfolio project that has no
 *  `ogImage` of its own. Order is stable given stable input order, and the
 *  count is always derived from the registries — never hardcoded — so a
 *  6th build project yields a 10th key without touching this function. */
export function pageCardKeys(
  projects: RegistryProjectLike[],
  buildProjects: RegistryBuildProjectLike[],
): string[] {
  return [
    'blog',
    'building',
    ...buildProjects.map((p) => `${BUILDING_PREFIX}${p.slug}`),
    ...projects.filter((p) => !p.ogImage).map((p) => `${PROJECTS_PREFIX}${p.id}`),
  ];
}

/** Turn one card key into its `OgProps`. Copy is lifted verbatim from the
 *  real `<Base title>`/`<Base description>` of the page it represents (see
 *  the plan's task-2 brief for the source lines). Throws on an unknown key,
 *  or on a `building/<slug>` / `projects/<id>` key whose registry entry is
 *  missing from `data` — never falls back to a blank card. */
export function buildPageCard(key: string, data: PageCardData): OgProps {
  if (key === 'blog') {
    return {
      title: 'Blog',
      description:
        'Articles on AI engineering, LLM agents, and building production software in Python and TypeScript.',
      tags: [],
      footerNote: pluralize(data.postCount, 'post'),
    };
  }

  if (key === 'building') {
    return {
      title: 'Building Publicly',
      description: 'Updates from the projects I am building in public, grouped by project.',
      tags: [],
      footerNote: pluralize(data.updateCount, 'update'),
      kind: 'building',
    };
  }

  if (key.startsWith(BUILDING_PREFIX)) {
    const slug = key.slice(BUILDING_PREFIX.length);
    const project = data.buildProjects.find((p) => p.slug === slug);
    if (!project) throw new Error(`buildPageCard: no build project registered for key "${key}"`);
    return {
      title: `${project.title} — Building Publicly`,
      description: project.blurb,
      tags: project.stack.slice(0, 2),
      footerNote: pluralize(project.updateCount, 'update'),
      kind: 'building',
    };
  }

  if (key.startsWith(PROJECTS_PREFIX)) {
    const id = key.slice(PROJECTS_PREFIX.length);
    const project = data.projects.find((p) => p.id === id);
    if (!project) throw new Error(`buildPageCard: no portfolio project registered for key "${key}"`);
    return {
      title: project.name,
      description: project.summary || project.tagline,
      tags: project.stack.slice(0, 2),
      footerNote: project.year !== undefined ? String(project.year) : project.stack.slice(0, 3).join(' · '),
    };
  }

  throw new Error(`buildPageCard: unknown page card key "${key}"`);
}
