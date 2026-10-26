import { indicesOf, newGame, ptOf, throwWith } from '@engine';
import type { Face, GameState, Piece, PieceKind, RuleOptions, Side } from '@engine';

export interface PieceSpec {
  kind: PieceKind;
  side: Side | null;
  row: number;
  col: number;
  active?: boolean;
}

/** Hand-built teaching positions. Side 0 is to play with the given dice already thrown. */
export function scenario(
  options: RuleOptions,
  specs: PieceSpec[] | null,
  faces: Face[],
  equalOdds = false,
): GameState {
  const g = newGame(options, { seed: 11, equalOdds });
  let s: GameState = { ...g, current: 0, phase: 'throw', dice: [], events: [], startLog: [] };
  if (specs) {
    const n = options.cols;
    const pieces: Piece[] = specs.map((sp, id) => {
      const pt = ptOf(n, sp.row, sp.col);
      let pi = -1;
      if (sp.kind === 'soldier') {
        pi =
          sp.active === false
            ? s.homeSlots[sp.side as Side].indexOf(pt)
            : indicesOf(s.tracks[sp.side as Side], pt)[0];
      }
      return { id, kind: sp.kind, side: sp.side, active: sp.active ?? true, pt, pi };
    });
    s = { ...s, pieces };
  }
  return throwWith(s, faces.slice(0, options.diceCount));
}

export const dice = (o: RuleOptions, ...f: Face[]): Face[] => {
  const out = [...f];
  while (out.length < o.diceCount) out.push(f[f.length - 1]);
  return out;
};

/** Sleeping guards so that nobody has lost in the middle of an exercise, plus queens if in play. */
export function guards(s: GameState): PieceSpec[] {
  const n = s.options.cols;
  const out: PieceSpec[] = [];
  for (const side of [0, 1] as Side[]) {
    const pt = s.homeSlots[side][0];
    out.push({ kind: 'soldier', side, row: Math.floor(pt / n), col: pt % n, active: false });
    if (s.options.queens) {
      const q = s.pieces.find((p) => p.kind === 'queen' && p.side === side)!;
      out.push({ kind: 'queen', side, row: Math.floor(q.pt / n), col: q.pt % n, active: false });
    }
  }
  return out;
}
