import { expect, test } from '@playwright/test';
import { dismissNotice, playToTheEnd, startGame } from './flows';

test('first-run notice and About page', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('alertdialog')).toContainText(
    'unofficial implementation of a traditional Sámi game',
  );
  await page.getByRole('link', { name: 'About & credits' }).first().click();
  await expect(page.getByRole('heading', { name: 'About & credits' })).toBeVisible();
  await expect(page.getByText('who is not Sámi')).toBeVisible();
});

test('rules panel shows the active variant and uncertainty badges', async ({ page }) => {
  await page.goto('/');
  await dismissNotice(page);
  await expect(page.getByTestId('variant-badge')).toHaveText('Lágesvuotna');
  await page.getByRole('button', { name: /Rules in this game/ }).click();
  await expect(page.getByText('Uncertain').first()).toBeVisible();
});

test('tutorial walks through every step', async ({ page }) => {
  await page.goto('/#/tutorial');
  await dismissNotice(page);
  for (let i = 0; i < 12; i++) {
    const next = page.getByRole('button', { name: 'Next' });
    if (!(await next.isVisible())) break;
    await next.click();
  }
  await expect(page.getByRole('button', { name: /Done: start a game/ })).toBeVisible();
});

for (const [variant, opponent] of [
  ['Lágesvuotna', 'Computer: easy'],
  ['Vuovdaguoika / Gávkevuotna', 'Computer: medium'],
  ['Návuotna – Máze', 'Computer: easy'],
  ['Unjárga (experimental)', 'Computer: easy'],
] as const) {
  test(`full game: ${variant} vs ${opponent}`, async ({ page }) => {
    await startGame(page, variant, opponent);
    await playToTheEnd(page);
    await expect(page.locator('.statusbar')).toContainText('won');
  });
}
