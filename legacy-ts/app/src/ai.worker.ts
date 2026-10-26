import { chooseAction, mulberry } from '@ai';
import type { Level } from '@ai';
import type { GameState } from '@engine';

self.onmessage = (
  e: MessageEvent<{ id: number; state: GameState; level: Level; seed: number; budget: number }>,
) => {
  const { id, state, level, seed, budget } = e.data;
  const action = chooseAction(state, level, mulberry(seed), budget);
  (self as unknown as Worker).postMessage({ id, action });
};
