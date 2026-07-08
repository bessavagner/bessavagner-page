import type { APIRoute } from 'astro';
import { asset, portfolio } from '../lib/portfolio';

// Served at /llms.txt — a clean, prose summary for AI engines (llmstxt.org format).
// Generated from the same portfolio data as the rest of the site, so it stays in sync.
export const GET: APIRoute = ({ site }) => {
  const base = (site?.href ?? 'https://bessavagner.com/').replace(/\/$/, '');
  const p = portfolio.profile;
  const projects = [...portfolio.featured, ...portfolio.cards];

  const lines: string[] = [
    `# ${p.name} — ${p.headline}`,
    '',
    `> ${p.tagline} Based in ${p.location}. ${p.availability}.`,
    '',
    '## About',
    `- Role: ${p.headline}`,
    `- Location: ${p.location}`,
  ];
  if (p.languages?.length) lines.push(`- Languages: ${p.languages.join(', ')}`);
  lines.push('- Affiliation: IFCE Innovation Hub · EMBRAPII');
  lines.push(`- Core skills: ${Object.values(p.stacks).flat().join(', ')}`);

  lines.push('', '## Links', `- Website: ${base}/`);
  if (p.links.github) lines.push(`- GitHub: ${p.links.github}`);
  if (p.links.linkedin) lines.push(`- LinkedIn: ${p.links.linkedin}`);
  if (p.links.email) lines.push(`- Email: ${p.links.email}`);
  if (p.links.cv) lines.push(`- CV: ${base}${asset(p.links.cv)}`);

  if (p.sameAs?.length) {
    lines.push('', '## Profiles');
    for (const url of p.sameAs) lines.push(`- ${url}`);
  }

  lines.push('', '## Projects');
  for (const pr of projects) {
    lines.push(`- [${pr.name}](${base}/projects/${pr.id}/): ${pr.tagline}. ${pr.summary}`);
  }
  lines.push('');

  return new Response(lines.join('\n'), {
    headers: { 'Content-Type': 'text/plain; charset=utf-8' },
  });
};
