/** Browser flows shared by the @playwright/test spec (CI, Node) and run-with-bun.ts (local, no Node). */
import type { Page } from '@playwright/test';

export async function dismissNotice(page: Page) {
  await page.getByRole('button', { name: 'I understand' }).click();
}

export async function startGame(page: Page, variant: string, opponent: string) {
  await page.goto('/?fast');
  await dismissNotice(page);
  await page.getByRole('button', { name: 'New game' }).click();
  await page.getByLabel('Rule set').selectOption({ label: variant });
  await page.getByLabel('Opponent').selectOption({ label: opponent });
  await page.getByRole('button', { name: 'Start', exact: true }).click();
}

/** Plays the human side by clicking: first enabled die, first glowing piece, first legal destination. */
export async function playToTheEnd(page: Page): Promise<string> {
  const status = page.locator('.statusbar strong');
  for (let i = 0; i < 6000; i++) {
    const text = (await status.textContent()) ?? '';
    if (/won/.test(text)) return text;
    const throwBtn = page.getByRole('button', { name: /Throw dice/ });
    if (await throwBtn.isVisible()) {
      await throwBtn.click();
      continue;
    }
    const dice = page.locator('button.die:not([disabled])');
    const nDice = await dice.count();
    let moved = false;
    for (let d = 0; d < nDice && !moved; d++) {
      await dice.nth(d).click();
      const glowing = page.locator('g.pt:has(.piece.glow)');
      const nPieces = await glowing.count();
      for (let p = 0; p < nPieces && !moved; p++) {
        await glowing.nth(p).click();
        const dest = page.locator('g.pt.dest').first();
        if (await dest.count()) {
          await dest.click();
          moved = true;
        }
      }
    }
    if (!moved) await page.waitForTimeout(20);
  }
  throw new Error('game did not finish');
}
