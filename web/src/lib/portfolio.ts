import data from '../data/portfolio.json';

export interface Metric { label: string; value: string; }
export interface ProjectLinks {
  repo?: string; live?: string; case_study?: string;
  repo_frontend?: string; repo_app?: string;
}
export interface Project {
  id: string;
  name: string;
  tagline: string;
  summary: string;
  /** Long-form narrative paragraph rendered on the project detail page. */
  body?: string;
  /** Optional case-study framing (rendered on featured project pages). */
  problem?: string;
  approach?: string;
  outcome?: string;
  kind?: string;
  role?: string;
  featured: boolean;
  order: number;
  year?: number;
  status?: string;
  private?: boolean;
  stack: string[];
  highlights?: string[];
  metrics?: Metric[];
  links: ProjectLinks;
  image?: string;
  ogImage?: string;
}
export interface Profile {
  name: string;
  headline: string;
  tagline: string;
  location?: string;
  availability?: string;
  languages?: string[];
  links: { github?: string; linkedin?: string; email?: string; cv?: string };
  stacks: Record<string, string[]>;
}

/** Public-asset path: "images/x.png" -> "/images/x.png"; strips a legacy "/static/" prefix. */
export function asset(path?: string): string {
  if (!path) return '';
  if (path.startsWith('/static/')) return path.replace('/static/', '/');
  if (path.startsWith('http') || path.startsWith('/')) return path;
  return '/' + path;
}

const profile = data.profile as Profile;
const projects = [...(data.projects as Project[])].sort((a, b) => a.order - b.order);

export const portfolio = {
  profile,
  featured: projects.filter((p) => p.featured),
  cards: projects.filter((p) => !p.featured),
};
