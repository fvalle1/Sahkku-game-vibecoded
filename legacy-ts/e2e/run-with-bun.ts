/* Runs the same flows without the Playwright test runner (which needs Node):
   bun run e2e/run-with-bun.ts   (with `bun run preview -- --port 4173` serving the build) */
import { chromium } from 'playwright-core';
import type { Page } from '@playwright/test';
import { dismissNotice, playToTheEnd, startGame } from './flows';

const base = process.env.BASE_URL ?? 'http://localhost:4173';
const b = await chromium.launch();
let failures = 0;

async function check(name: string, fn: (p: Page) => Promise<void>) {
  const ctx = await b.newContext({ baseURL: base, viewport: { width: 1280, height: 900 } });
  const page = (await ctx.newPage()) as unknown as Page;
  page.on('pageerror', (e) => console.log('  pageerror:', e.message));
  const t0 = Date.now();
  try {
    await fn(page);
    console.log(`ok   ${name} (${((Date.now() - t0) / 1000).toFixed(1)}s)`);
  } catch (e) {
    failures++;
    console.log(`FAIL ${name}: ${(e as Error).message.split('\n')[0]}`);
    await page.screenshot({ path: `e2e-fail-${failures}.png` });
  }
  await ctx.close();
}
const must = (c: unknown, m: string) => {
  if (!c) throw new Error(m);
};

await check('first-run notice and About', async (p) => {
  await p.goto('/');
  must(
    (await p.getByRole('alertdialog').textContent())?.includes('unofficial implementation'),
    'notice text',
  );
  await dismissNotice(p);
  await p.getByRole('link', { name: 'About & credits' }).first().click();
  await p.getByRole('heading', { name: 'About & credits' }).waitFor();
  must(await p.getByText('who is not Sámi').isVisible(), 'About credit text');
});
await check('rules panel and variant badge', async (p) => {
  await p.goto('/');
  await dismissNotice(p);
  must((await p.getByTestId('variant-badge').textContent()) === 'Lágesvuotna', 'badge');
  await p.getByRole('button', { name: /Rules in this game/ }).click();
  must(await p.getByText('Uncertain').first().isVisible(), 'uncertain badge');
});
await check('tutorial', async (p) => {
  await p.goto('/#/tutorial');
  await dismissNotice(p);
  for (let i = 0; i < 12 && (await p.getByRole('button', { name: 'Next' }).isVisible()); i++)
    await p.getByRole('button', { name: 'Next' }).click();
  must(await p.getByRole('button', { name: /Done: start a game/ }).isVisible(), 'last step');
});
const only = process.argv[2];
for (const [v, o] of [
  ['Lágesvuotna', 'Computer: easy'],
  ['Vuovdaguoika / Gávkevuotna', 'Computer: medium'],
  ['Návuotna – Máze', 'Computer: easy'],
  ['Návuotna – Ráisa', 'Computer: easy'],
  ['Unjárga (experimental)', 'Computer: easy'],
] as const) {
  if (only && !v.includes(only)) continue;
  await check(`full game ${v} vs ${o}`, async (p) => {
    await startGame(p, v, o);
    const r = await playToTheEnd(p);
    must(/won/.test(r), 'no winner');
  });
}
await b.close();
process.exit(failures ? 1 : 0);
