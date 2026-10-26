import { applyAction, faceValue, legalActions, legalMoves, stateKey, throwWith } from '@engine';
import type { Action, Face, GameState, Move, Side } from '@engine';
import { evaluate } from './eval';

export { evaluate } from './eval';

export type Level = 'easy' | 'medium' | 'hard';
export type Rand = () => number;

export function mulberry(seed: number): Rand {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function sameMove(a: Action, m: Move) {
  return (
    a.type === 'move' &&
    a.die === m.die &&
    a.pieceId === m.pieceId &&
    a.to === m.to &&
    a.fate === m.fate
  );
}

function easy(s: GameState, acts: Action[], rand: Rand): Action {
  const moves = legalMoves(s);
  const weights = acts.map((a) => {
    const m = moves.find((x) => sameMove(a, x));
    if (!m) return 0.4; // re-throws are rarely interesting
    return m.out.captures.length > 0 ? 4 : 1;
  });
  const total = weights.reduce((x, y) => x + y, 0);
  let r = rand() * total;
  for (let i = 0; i < acts.length; i++) {
    r -= weights[i];
    if (r <= 0) return acts[i];
  }
  return acts[acts.length - 1];
}

function medium(s: GameState, acts: Action[], rand: Rand): Action {
  const me = s.current;
  const base = evaluate(s, me);
  let best = acts[0];
  let bestV = -Infinity;
  for (const a of acts) {
    let v: number;
    if (a.type === 'rethrow') v = base + 1;
    else if (a.type === 'rethrowAll') v = base + 3;
    else v = evaluate(applyAction(s, a), me);
    v += rand() * 0.01;
    if (v > bestV) {
      bestV = v;
      best = a;
    }
  }
  return best;
}

// ------------------------------------------------------------ hard: expectimax

interface Outcome {
  faces: Face[];
  weight: number;
}

function diceOutcomes(s: GameState): Outcome[] {
  const o = s.options;
  const map = new Map<string, Outcome>();
  const total = Math.pow(o.faces.length, o.diceCount);
  const rec = (acc: Face[]) => {
    if (acc.length === o.diceCount) {
      const faces = [...acc].sort();
      const key = faces.join();
      const e = map.get(key);
      if (e) e.weight += 1 / total;
      else map.set(key, { faces, weight: 1 / total });
      return;
    }
    for (const f of o.faces) rec([...acc, f]);
  };
  rec([]);
  return [...map.values()];
}

function setDice(s: GameState, faces: Face[]): GameState {
  const o = s.options;
  return {
    ...s,
    dice: faces.map((face) => ({ face, used: face === 'blank' && o.blankValue === 0 })),
  };
}

class Search {
  deadline: number;
  nodes = 0;
  memo = new Map<string, number>();
  outcomes: Outcome[];
  constructor(
    public root: Side,
    budgetMs: number,
    s: GameState,
    public ownBeam: number,
    public oppBeam: number,
  ) {
    this.deadline = Date.now() + budgetMs;
    this.outcomes = diceOutcomes(s);
  }
  timeUp() {
    return (++this.nodes & 63) === 0 && Date.now() > this.deadline;
  }
  expectedAfterRethrow(s: GameState, die: number, depth: number): number {
    const o = s.options;
    const faces = o.faces.filter((f) => f !== 'X');
    let sum = 0;
    for (const f of faces) {
      const dice = s.dice.map((d, i) =>
        i === die ? { face: f, used: f === 'blank' && o.blankValue === 0 } : d,
      );
      sum += this.value({ ...s, dice }, depth);
    }
    return sum / faces.length;
  }
  /** Re-throwing all dice: condition on not getting all X again (the player could just repeat). */
  expectedAfterRethrowAll(s: GameState, depth: number): number {
    let sum = 0;
    let w = 0;
    for (const out of this.outcomes) {
      if (out.faces.every((f) => f === 'X')) continue;
      sum += out.weight * this.value(setDice(s, out.faces), depth);
      w += out.weight;
    }
    return w ? sum / w : evaluate(s, this.root);
  }
  value(s: GameState, depth: number): number {
    if (s.phase === 'over') return evaluate(s, this.root);
    if (this.timeUp()) return evaluate(s, this.root);
    const key = depth + '|' + stateKey(s);
    const hit = this.memo.get(key);
    if (hit !== undefined) return hit;
    let result: number;
    if (s.phase === 'throw') {
      if (depth <= 0) result = evaluate(s, this.root);
      else {
        result = 0;
        for (const out of this.outcomes) {
          result += out.weight * this.value(throwWith(s, out.faces), depth - 1);
        }
      }
    } else {
      const maximizing = s.current === this.root;
      const beam = maximizing ? this.ownBeam : this.oppBeam;
      const acts = legalActions(s);
      const scored: { a: Action; next: GameState | null; pre: number }[] = [];
      for (const a of acts) {
        if (a.type === 'rethrow' || a.type === 'rethrowAll') {
          scored.push({ a, next: null, pre: evaluate(s, this.root) + (maximizing ? 1 : -1) });
        } else {
          const next = applyAction(s, a);
          scored.push({ a, next, pre: evaluate(next, this.root) });
        }
      }
      scored.sort((x, y) => (maximizing ? y.pre - x.pre : x.pre - y.pre));
      let best = maximizing ? -Infinity : Infinity;
      for (const c of scored.slice(0, beam)) {
        let v: number;
        if (c.next) v = this.value(c.next, depth);
        else if (c.a.type === 'rethrow') v = this.expectedAfterRethrow(s, c.a.die, depth);
        else {
          v = this.expectedAfterRethrowAll(s, depth);
        }
        best = maximizing ? Math.max(best, v) : Math.min(best, v);
      }
      result = best;
    }
    this.memo.set(key, result);
    return result;
  }
}

function hard(s: GameState, acts: Action[], rand: Rand, budgetMs: number): Action {
  const me = s.current;
  const search = new Search(me, budgetMs, s, 4, 2);
  let best = medium(s, acts, rand); // fallback if the clock runs out
  let bestV = -Infinity;
  const fallbackKey = JSON.stringify(best);
  for (const a of acts) {
    let v: number;
    if (a.type === 'rethrow') v = search.expectedAfterRethrow(s, a.die, 1);
    else if (a.type === 'rethrowAll') {
      v = search.expectedAfterRethrowAll(s, 1);
    } else v = search.value(applyAction(s, a), 1);
    if (Date.now() > search.deadline) break;
    if (v > bestV || (v === bestV && JSON.stringify(a) === fallbackKey)) {
      bestV = v;
      best = a;
    }
  }
  return best;
}

/** Pick the next action for the player to move. Pure apart from `rand` and the clock (hard level). */
export function chooseAction(s: GameState, level: Level, rand: Rand, budgetMs = 900): Action {
  const acts = legalActions(s);
  if (acts.length === 0) throw new Error('No legal actions');
  if (acts.length === 1) return acts[0];
  if (s.phase === 'throw') return acts[0];
  switch (level) {
    case 'easy':
      return easy(s, acts, rand);
    case 'medium':
      return medium(s, acts, rand);
    case 'hard':
      return hard(s, acts, rand, budgetMs);
  }
}

export { faceValue };
