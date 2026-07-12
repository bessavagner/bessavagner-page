// web/src/layouts/base-ga4.test.ts
// Regression test for the GA4 bootstrap inline script in Base.astro.
//
// Astro wraps a `define:vars` inline script in an IIFE at build time. If the
// snippet declares `function gtag(){...}` instead of assigning it onto
// `window`, the function is scoped to that IIFE and `window.gtag` is never
// defined — silently dropping every custom `track()` call in
// analytics-core.ts (which reads `globalThis.gtag`), while GA4's automatic
// events still fire because `gtag('js'/'config')` run fine *inside* the IIFE.
//
// This test extracts the real snippet body from Base.astro, wraps it in the
// same IIFE shape Astro emits for `define:vars`, executes it against a fake
// `window`, and asserts `window.gtag` is a real, callable global.

import { test } from 'vitest';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import vm from 'node:vm';

const here = path.dirname(fileURLToPath(import.meta.url));
const baseAstroSource = readFileSync(path.join(here, 'Base.astro'), 'utf-8');

function extractGa4ScriptBody(source: string): string {
  const match = source.match(
    /<script is:inline define:vars=\{\{ ga4Id \}\}>([\s\S]*?)<\/script>/,
  );
  if (!match) {
    throw new Error('Could not find the GA4 define:vars inline script in Base.astro');
  }
  return match[1];
}

test('the GA4 bootstrap snippet, run the way Astro actually emits it, defines window.gtag', () => {
  const body = extractGa4ScriptBody(baseAstroSource);

  // Reproduce Astro's define:vars wrapping verbatim: it hoists the declared
  // vars into `const` bindings at the top of an IIFE around the script body.
  const emitted = `(function(){ const ga4Id = "G-TEST"; ${body} })()`;

  // Run inside a real vm context, not a plain `new Function` sandbox: in a
  // browser, `window` IS the global object, so `window.gtag = ...` and a
  // later bare `gtag(...)` reference the SAME binding via global-object
  // identifier resolution. A vm context reproduces that; a bag of function
  // parameters would not (a bare `gtag()` call would just throw
  // ReferenceError there, masking the real bug this test exists to catch).
  const sandbox: Record<string, unknown> = {};
  sandbox.window = sandbox;
  const context = vm.createContext(sandbox);
  vm.runInContext(emitted, context);

  const win = sandbox.window as Record<string, unknown>;
  assert.equal(typeof win.gtag, 'function', 'window.gtag must be defined by the snippet');

  const dataLayer = win.dataLayer as unknown[];
  const before = dataLayer.length;
  (win.gtag as (...args: unknown[]) => void)('event', 'x');
  assert.equal(dataLayer.length, before + 1, 'calling window.gtag must push onto dataLayer');
});
