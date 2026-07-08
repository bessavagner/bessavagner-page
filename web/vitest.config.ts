import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    // vitest owns only the schema builder tests; node:test owns the rest.
    include: ['src/**/schema.test.ts'],
    environment: 'node',
  },
});
