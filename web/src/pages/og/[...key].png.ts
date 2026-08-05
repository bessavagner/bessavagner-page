import type { APIRoute } from 'astro';
import { getCollection } from 'astro:content';
import { isPublic } from '../../lib/blog';
import { getBuildProjects, getVisibleUpdates, splitUpdateId } from '../../lib/buildlog';
import { portfolio } from '../../lib/portfolio';
import {
  pageCardKeys,
  buildPageCard,
  type BuildProjectCardData,
  type PageCardData,
} from '../../lib/og-pages';
import { renderOgPng, type OgProps } from '../../lib/og';

export async function getStaticPaths() {
  const posts = await getCollection('blog', isPublic);
  const allUpdates = await getVisibleUpdates();
  const buildProjectsRegistry = getBuildProjects();
  const registryProjects = [...portfolio.featured, ...portfolio.cards];

  const updateCountByProject = new Map<string, number>();
  for (const u of allUpdates) {
    const { project } = splitUpdateId(u.id);
    updateCountByProject.set(project, (updateCountByProject.get(project) ?? 0) + 1);
  }

  const buildProjects: BuildProjectCardData[] = buildProjectsRegistry.map((p) => ({
    slug: p.slug,
    title: p.title,
    blurb: p.blurb,
    stack: p.stack,
    updateCount: updateCountByProject.get(p.slug) ?? 0,
  }));

  const data: PageCardData = {
    postCount: posts.length,
    updateCount: allUpdates.length,
    buildProjects,
    projects: registryProjects,
  };

  const keys = pageCardKeys(registryProjects, buildProjectsRegistry);
  return keys.map((key) => ({
    params: { key },
    props: buildPageCard(key, data) satisfies OgProps,
  }));
}

export const GET: APIRoute = async ({ props }) => {
  const png = await renderOgPng(props as OgProps);
  return new Response(new Uint8Array(png), {
    headers: { 'Content-Type': 'image/png', 'Cache-Control': 'public, max-age=31536000, immutable' },
  });
};
