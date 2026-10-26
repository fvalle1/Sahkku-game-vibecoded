import { chooseAction, mulberry } from '@ai';
import type { Level } from '@ai';
import type { Action, GameState } from '@engine';

let worker: Worker | null = null;
let nextId = 1;
const pending = new Map<number, (a: Action) => void>();

function getWorker(): Worker | null {
  if (worker) return worker;
  try {
    worker = new Worker(new URL('./ai.worker.ts', import.meta.url), { type: 'module' });
    worker.onmessage = (e: MessageEvent<{ id: number; action: Action }>) => {
      pending.get(e.data.id)?.(e.data.action);
      pending.delete(e.data.id);
    };
    worker.onerror = () => {
      worker = null; // fall back to the main thread
    };
  } catch {
    worker = null;
  }
  return worker;
}

/** Ask the AI for the next action. Runs in a Web Worker so the UI stays responsive. */
export function askAI(state: GameState, level: Level, seed: number): Promise<Action> {
  const budget = level === 'hard' ? 1200 : 100;
  const w = getWorker();
  if (!w) return Promise.resolve(chooseAction(state, level, mulberry(seed), budget));
  return new Promise((resolve) => {
    const id = nextId++;
    pending.set(id, resolve);
    w.postMessage({ id, state, level, seed, budget });
  });
}
