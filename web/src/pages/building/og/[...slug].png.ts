import type { APIRoute } from 'astro';
import { getCollection } from 'astro:content';
import { readingTime } from '../../../lib/blog';
import { isVisible } from '../../../lib/buildlog';
import { renderOgPng, type OgProps } from '../../../lib/og';

export async function getStaticPaths() {
  const updates = await getCollection('buildlog', isVisible);
  return updates.map((u) => ({
    params: { slug: u.id },
    props: {
      title: u.data.title,
      description: u.data.description,
      tags: u.data.tags,
      minutes: readingTime(u.body ?? ''),
      kind: 'building',
    } satisfies OgProps,
  }));
}

export const GET: APIRoute = async ({ props }) => {
  const png = await renderOgPng(props as OgProps);
  return new Response(new Uint8Array(png), {
    headers: { 'Content-Type': 'image/png', 'Cache-Control': 'public, max-age=31536000, immutable' },
  });
};
