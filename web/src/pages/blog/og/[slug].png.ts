import type { APIRoute } from 'astro';
import { getCollection } from 'astro:content';
import { isPublic, readingTime } from '../../../lib/blog';
import { renderOgPng, type OgProps } from '../../../lib/og';

export async function getStaticPaths() {
  const posts = await getCollection('blog', isPublic);
  return posts.map((post) => ({
    params: { slug: post.id },
    props: {
      title: post.data.title,
      description: post.data.description,
      tags: post.data.tags,
      minutes: readingTime(post.body ?? ''),
    } satisfies OgProps,
  }));
}

export const GET: APIRoute = async ({ props }) => {
  const png = await renderOgPng(props as OgProps);
  return new Response(new Uint8Array(png), {
    headers: { 'Content-Type': 'image/png', 'Cache-Control': 'public, max-age=31536000, immutable' },
  });
};
