import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import { fileURLToPath } from 'node:url';

const r = (p: string) => fileURLToPath(new URL(p, import.meta.url));

export default defineConfig({
  root: r('./app'),
  base: './',
  plugins: [react()],
  resolve: {
    alias: {
      '@engine': r('./engine/src/index.ts'),
      '@ai': r('./ai/src/index.ts'),
    },
  },
  build: { outDir: r('./dist'), emptyOutDir: true, target: 'es2022' },
  worker: { format: 'es' },
  test: {
    root: r('./'),
    include: ['engine/test/**/*.test.ts', 'ai/test/**/*.test.ts', 'app/src/**/*.test.ts'],
    testTimeout: 60000,
  },
});
