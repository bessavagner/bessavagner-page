import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';
import { PUBLICATION_STATUSES } from './lib/publication.ts';

const publicationFields = {
  title: z.string(),
  description: z.string(),
  pubDate: z.coerce.date(),
  updatedDate: z.coerce.date().optional(),
  tags: z.array(z.string()).default([]),
  // Absent means draft: the post fails closed without failing the build. Presence
  // is enforced by `pnpm post:lint` in CI, not by Zod — a missing key must never
  // break the deploy of every other post.
  status: z.enum(PUBLICATION_STATUSES).default('draft'),
  reviewedAt: z.coerce.date().optional(),
  reviewHash: z.string().optional(),
};

const blog = defineCollection({
  loader: glob({ pattern: '**/*.mdx', base: './src/content/blog' }),
  schema: ({ image }) =>
    z.object({
      ...publicationFields,
      cta: z.enum(['lets-talk', 'cv', 'follow-build', 'subscribe']).optional(),
      heroImage: image().optional(),
      heroImageDark: image().optional(),
    }),
});

const buildlog = defineCollection({
  loader: glob({ pattern: '**/*.mdx', base: './src/content/buildlog' }),
  schema: ({ image }) =>
    z.object({
      ...publicationFields,
      project: z.string(),
      update: z.number(),
      cta: z.enum(['lets-talk', 'cv', 'follow-build', 'subscribe']).optional(),
      heroImage: image().optional(),
    }),
});

export const collections = { blog, buildlog };
