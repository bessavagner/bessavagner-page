import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    // vitest owns the schema builder and content-core tests; node:test owns the rest.
    // Named explicitly, not globbed: the node:test files fail under the vitest runner.
    include: ['src/**/schema.test.ts', 'src/**/content-core.test.ts'],
    environment: 'node',
  },
});
