import { newGame, ptOf, throwWith } from '../src';
import type { Face, GameState, Piece, PieceKind, RuleOptions, Side } from '../src';

export interface Spec {
  kind: PieceKind;
  side: Side | null;
  /** point as [row, col] */
  at?: [number, number];
  /** index on the owner's track (active soldiers) */
  ti?: number;
  active?: boolean;
}

/** Fresh game with a custom, hand-built position. Side `current` is to throw/play. */
export function scenario(
  opts: RuleOptions,
  specs: Spec[],
  cfg: { current?: Side; dice?: Face[]; miedut?: boolean; hold?: boolean } = {},
): GameState {
  const g = newGame(opts, { seed: 7, miedut: cfg.miedut });
  const n = opts.cols;
  const current = cfg.current ?? 0;
  const pieces: Piece[] = specs.map((sp, id) => {
    let pt: number;
    let pi = -1;
    if (sp.at) pt = ptOf(n, sp.at[0], sp.at[1]);
    else {
      const tr = g.tracks[sp.side as Side];
      pt = tr.points[sp.ti!];
      pi = sp.ti!;
    }
    if (sp.kind === 'soldier' && sp.at) {
      if (sp.active !== false) pi = g.tracks[sp.side as Side].points.indexOf(pt);
      else pi = g.homeSlots[sp.side as Side].indexOf(pt);
    }
    return { id, kind: sp.kind, side: sp.side, active: sp.active ?? true, pt, pi };
  });
  let s: GameState = { ...g, pieces, current, phase: 'throw', dice: [], events: [] };
  if (cfg.dice && cfg.hold) {
    s = { ...s, phase: 'move', dice: cfg.dice.map((face) => ({ face, used: false })) };
  } else if (cfg.dice) s = throwWith(s, cfg.dice);
  return s;
}

export const P = (opts: RuleOptions, row: number, col: number) => ptOf(opts.cols, row, col);
