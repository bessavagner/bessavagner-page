// web/src/lib/analytics-events.test.ts
import { test } from 'vitest';
import assert from 'node:assert/strict';
import { EVENTS, type EventName } from './analytics-events.ts';

test('every event name is snake_case and starts with a letter (GA4 rule)', () => {
  for (const name of Object.values(EVENTS)) {
    assert.match(name, /^[a-z][a-z0-9_]*$/, `${name} is not a valid GA4 event name`);
  }
});

test('the live GA4 key events keep their exact names (never rename)', () => {
  assert.equal(EVENTS.WHATSAPP_CLICK, 'whatsapp_click');
  assert.equal(EVENTS.GENERATE_LEAD, 'generate_lead');
  assert.equal(EVENTS.NEWSLETTER_SIGNUP, 'newsletter_signup');
});

test('taxonomy covers all seven wired actions with unique names', () => {
  const values = Object.values(EVENTS);
  assert.equal(values.length, 7);
  assert.equal(new Set(values).size, 7, 'event names must be unique');
  assert.deepEqual(
    [...values].sort(),
    ['cv_download', 'email_click', 'generate_lead', 'hero_cta_contact',
     'hero_cta_work', 'newsletter_signup', 'whatsapp_click'],
  );
});

test('EventName is the union of the values', () => {
  const n: EventName = EVENTS.CV_DOWNLOAD;
  assert.equal(n, 'cv_download');
});
