import { getCollection, type CollectionEntry } from 'astro:content';
import bpData from '../data/buildProjects.json';
import {
  splitUpdateId,
  seriesNeighbors,
  sortUpdatesByDateDesc,
  type BuildProject,
} from './buildlog-core.ts';
import { isVisible as isPublicationVisible } from './publication.ts';
import { hashMatches } from './review-map.ts';
import { resolvePublishAt } from './clock.ts';

export type BuildUpdate = CollectionEntry<'buildlog'>;
export { splitUpdateId, seriesNeighbors };
export type { BuildProject };

/** Visibility for a single update, via the one publication rule in publication.ts. */
export function isVisible(u: BuildUpdate): boolean {
  return isPublicationVisible(
    { status: u.data.status, pubDate: u.data.pubDate, hashMatches: hashMatches(u) },
    { now: resolvePublishAt(process.env, Date.now()), prod: import.meta.env.PROD },
  );
}

/** All registry projects, active first then shipped, preserving file order within each. */
export function getBuildProjects(): BuildProject[] {
  const all = bpData.projects as BuildProject[];
  return [...all].sort((a, b) => Number(a.status === 'shipped') - Number(b.status === 'shipped'));
}

export function getBuildProject(slug: string): BuildProject | undefined {
  return (bpData.projects as BuildProject[]).find((p) => p.slug === slug);
}

/** Visible updates (optionally for one project), newest first. */
export async function getVisibleUpdates(project?: string): Promise<BuildUpdate[]> {
  const all = await getCollection('buildlog', isVisible);
  const filtered = project ? all.filter((u) => splitUpdateId(u.id).project === project) : all;
  return sortUpdatesByDateDesc(filtered);
}

export async function latestUpdateFor(slug: string): Promise<BuildUpdate | undefined> {
  return (await getVisibleUpdates(slug))[0];
}

/** Group visible updates by project folder. */
async function groupByProject(): Promise<Map<string, BuildUpdate[]>> {
  const updates = await getVisibleUpdates();
  const byProject = new Map<string, BuildUpdate[]>();
  for (const u of updates) {
    const { project } = splitUpdateId(u.id);
    const list = byProject.get(project);
    if (list) list.push(u);
    else byProject.set(project, [u]);
  }
  return byProject; // each list already newest-first
}

/** Data for /building: active projects (with their latest update) + shipped projects. */
export async function getIndexData() {
  const byProject = await groupByProject();
  const projects = getBuildProjects();
  const active = projects
    .filter((p) => p.status === 'active' && byProject.has(p.slug))
    .map((p) => ({ project: p, latest: byProject.get(p.slug)![0], count: byProject.get(p.slug)!.length }));
  const shipped = projects
    .filter((p) => p.status === 'shipped')
    .map((p) => ({ project: p, count: byProject.get(p.slug)?.length ?? 0 }));
  return { active, shipped };
}

/** Registry projects that have at least one visible update (get a hub page). */
export async function getHubProjects(): Promise<BuildProject[]> {
  const byProject = await groupByProject();
  return getBuildProjects().filter((p) => byProject.has(p.slug));
}
