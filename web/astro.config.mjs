// @ts-check
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';
import mdx from '@astrojs/mdx';
import tailwindcss from '@tailwindcss/vite';

// https://astro.build/config
export default defineConfig({
  site: 'https://bessavagner.com',
  integrations: [
    mdx(),
    sitemap({ filter: (page) => !page.includes('/blog/og/') }),
  ],
  vite: {
    plugins: [tailwindcss()],
  },
});
