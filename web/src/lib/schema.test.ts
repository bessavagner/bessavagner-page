import { describe, it, expect } from 'vitest';
import { personNode } from './schema';
import type { Profile } from './portfolio';

const SITE = 'https://bessavagner.com';

const profile: Profile = {
  name: 'Vagner Bessa',
  headline: 'Senior Developer & AI Engineer',
  tagline: 'Building production AI.',
  location: 'Crateús, Brazil',
  languages: ['pt-BR', 'en', 'es'],
  links: { github: 'https://github.com/bessavagner' },
  stacks: { core: ['Python'] },
  sameAs: [
    'https://github.com/bessavagner',
    'https://orcid.org/0000-0002-7584-262X',
    'https://dev.to/bessavagner',
  ],
  occupation: { name: 'Software Developer', category: '15-1252.00' },
};

describe('personNode', () => {
  const node = personNode(SITE, profile);

  it('is a Person with the canonical @id', () => {
    expect(node['@type']).toBe('Person');
    expect(node['@id']).toBe('https://bessavagner.com/#vagner-bessa');
  });

  it('carries every sameAs URL from the profile', () => {
    expect(node.sameAs).toEqual(profile.sameAs);
  });

  it('emits hasOccupation with an occupationalCategory', () => {
    expect(node.hasOccupation).toMatchObject({
      '@type': 'Occupation',
      name: 'Software Developer',
      occupationalCategory: '15-1252.00',
    });
  });

  it('emits image as an ImageObject with real dimensions', () => {
    expect(node.image).toMatchObject({
      '@type': 'ImageObject',
      url: 'https://bessavagner.com/images/avatar.png',
      width: 1220,
      height: 1220,
    });
  });

  it('omits hasOccupation and sameAs when the profile lacks them', () => {
    const bare = personNode(SITE, { ...profile, sameAs: undefined, occupation: undefined });
    expect(bare).not.toHaveProperty('hasOccupation');
    expect(bare).not.toHaveProperty('sameAs');
  });
});
