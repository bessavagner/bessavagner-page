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

import { webSiteNode, profilePageNode, projectItemList } from './schema';

describe('webSiteNode', () => {
  const node = webSiteNode(SITE);
  it('is a WebSite published by the person entity', () => {
    expect(node['@type']).toBe('WebSite');
    expect(node['@id']).toBe('https://bessavagner.com/#website');
    expect(node.publisher).toEqual({ '@id': 'https://bessavagner.com/#vagner-bessa' });
  });
});

describe('profilePageNode', () => {
  it('links to the person and website entities', () => {
    const node = profilePageNode(SITE);
    expect(node['@type']).toBe('ProfilePage');
    expect(node['@id']).toBe('https://bessavagner.com/#profile');
    expect(node.mainEntity).toEqual({ '@id': 'https://bessavagner.com/#vagner-bessa' });
    expect(node.isPartOf).toEqual({ '@id': 'https://bessavagner.com/#website' });
  });
  it('adds dateModified when a date is given, omits it otherwise', () => {
    expect(profilePageNode(SITE, '2026-06-25').dateModified).toBe('2026-06-25');
    expect(profilePageNode(SITE)).not.toHaveProperty('dateModified');
  });
});

describe('projectItemList', () => {
  const node = projectItemList(SITE, [
    { id: 'regwatch', name: 'RegWatch' },
    { id: 'replaygate', name: 'ReplayGate' },
  ]);
  it('lists each project as a positioned ListItem URL', () => {
    expect(node['@type']).toBe('ItemList');
    expect(node.itemListElement).toEqual([
      { '@type': 'ListItem', position: 1, name: 'RegWatch', url: 'https://bessavagner.com/projects/regwatch/' },
      { '@type': 'ListItem', position: 2, name: 'ReplayGate', url: 'https://bessavagner.com/projects/replaygate/' },
    ]);
  });
});
