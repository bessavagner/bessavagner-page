import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    // Every test file, no exceptions. A test that CI does not run is not a test.
    include: ['src/**/*.test.ts', 'scripts/**/*.test.ts'],
    environment: 'node',
  },
});
