import { faceValue, nextIndex } from '@engine';
import type { GameState, Side } from '@engine';

const WIN = 1e6;

/** How many of `side`'s pieces an enemy soldier could hit with a single die. */
function threats(s: GameState, side: Side): number {
  const o = s.options;
  const enemy = (side === 0 ? 1 : 0) as Side;
  const track = s.tracks[enemy];
  const values = [...new Set(o.faces.map((f) => faceValue(o, f)).filter((v) => v > 0))];
  const mine = new Map<number, number>();
  for (const p of s.pieces) {
    if (p.side !== side || p.kind === 'king') continue;
    if (!p.active && !o.capturesInactive) continue;
    mine.set(p.pt, (mine.get(p.pt) ?? 0) + (p.kind === 'queen' ? 6 : 1));
  }
  let t = 0;
  for (const p of s.pieces) {
    if (p.side !== enemy || p.kind !== 'soldier' || !p.active) continue;
    for (const v of values) {
      let i = p.pi;
      for (let k = 0; k < v; k++) i = nextIndex(track, i);
      t += mine.get(track.points[i]) ?? 0;
    }
  }
  return t;
}

/** Static evaluation from `side`'s point of view (higher is better). */
export function evaluate(s: GameState, side: Side): number {
  if (s.phase === 'over') return s.winner === side ? WIN : -WIN;
  const o = s.options;
  const n = o.cols;
  let score = 0;
  for (const p of s.pieces) {
    if (p.kind === 'king') {
      if (p.side === side) score += 8;
      else if (p.side !== null) score -= 8;
      continue;
    }
    const sign = p.side === side ? 1 : -1;
    if (p.kind === 'queen') {
      score += sign * 40;
      continue;
    }
    let v = 10 + (p.active ? 3 : 0);
    if (p.active && Math.floor(p.pt / n) === 1) v += 0.6; // middle-row control
    score += sign * v;
  }
  const enemy = (side === 0 ? 1 : 0) as Side;
  score -= threats(s, side) * 1.5;
  score += threats(s, enemy) * 1.0;
  return score;
}
