import rss from '@astrojs/rss';
import type { APIContext } from 'astro';
import { getVisibleUpdates, splitUpdateId } from '../../lib/buildlog';

export async function GET(context: APIContext) {
  const updates = await getVisibleUpdates();
  return rss({
    title: 'Vagner Bessa — Building Publicly',
    description: 'Progress updates from the projects I am building in public.',
    site: context.site ?? 'https://bessavagner.com',
    items: updates.map((u) => {
      const { project, slug } = splitUpdateId(u.id);
      return {
        title: u.data.title,
        description: u.data.description,
        pubDate: u.data.pubDate,
        link: `/building/${project}/${slug}/`,
      };
    }),
  });
}
