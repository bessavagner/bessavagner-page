// web/src/lib/schema.ts
// Pure builders for the site's schema.org JSON-LD. No Astro imports here, so the
// logic is unit-testable and reused across Base.astro / index.astro / API routes.
import type { Profile } from './portfolio';

/** The canonical Person entity, driven entirely by portfolio data. */
export function personNode(siteUrl: string, profile: Profile): Record<string, unknown> {
  const node: Record<string, unknown> = {
    '@type': 'Person',
    '@id': `${siteUrl}/#vagner-bessa`,
    name: 'Vagner Bessa',
    url: `${siteUrl}/`,
    image: {
      '@type': 'ImageObject',
      url: `${siteUrl}/images/avatar.png`,
      width: 1220,
      height: 1220,
      caption: 'Vagner Bessa',
    },
    jobTitle: 'Senior Developer & AI Engineer',
    description:
      'Senior full-stack and AI engineer building production-grade AI products and web platforms in Python and TypeScript. Works remotely with US and European teams across overlapping business hours.',
    email: 'bessavagner.dev@gmail.com',
    address: { '@type': 'PostalAddress', addressLocality: 'Crateús', addressRegion: 'CE', addressCountry: 'BR' },
    alumniOf: {
      '@type': 'CollegeOrUniversity',
      name: 'Instituto Federal de Educação, Ciência e Tecnologia do Ceará',
      alternateName: 'IFCE',
      url: 'https://ifce.edu.br',
    },
    knowsLanguage: ['pt-BR', 'en', 'es'],
    knowsAbout: [
      'Python', 'TypeScript', 'Artificial Intelligence', 'LLM agents',
      'RAG (Retrieval-Augmented Generation)', 'FastAPI', 'Django', 'React',
      'Full-stack web development', 'Machine learning', 'Google Cloud', 'Software engineering',
    ],
    workLocation: { '@type': 'VirtualLocation', name: 'Remote — US & Europe' },
    contactPoint: {
      '@type': 'ContactPoint',
      contactType: 'Hiring & project inquiries',
      email: 'bessavagner.dev@gmail.com',
      availableLanguage: ['en', 'pt', 'es'],
      areaServed: ['US', 'Europe'],
    },
  };
  if (profile.sameAs?.length) node.sameAs = profile.sameAs;
  if (profile.occupation) {
    node.hasOccupation = {
      '@type': 'Occupation',
      name: profile.occupation.name,
      occupationalCategory: profile.occupation.category,
    };
  }
  return node;
}
