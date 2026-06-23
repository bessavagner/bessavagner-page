import { OGImageRoute } from 'astro-og-canvas';
import { getCollection } from 'astro:content';

const posts = await getCollection('blog', (p) =>
  import.meta.env.PROD ? p.data.draft !== true : true,
);
const pages = Object.fromEntries(posts.map((p) => [p.id, p.data]));

export const { getStaticPaths, GET } = await OGImageRoute({
  param: 'route',
  pages,
  getImageOptions: (_path, page: { title: string; description: string }) => ({
    title: page.title,
    description: page.description,
    bgGradient: [[18, 22, 33], [58, 61, 152]],
    border: { color: [120, 125, 224], width: 8, side: 'inline-start' },
    padding: 60,
    font: {
      title: { color: [255, 255, 255], weight: 'Bold', size: 64 },
      description: { color: [205, 210, 230], weight: 'Normal', size: 30 },
    },
  }),
});
