import type { GameState } from './types';

/** Returns a list of violated invariants (empty = state is consistent). */
export function checkInvariants(s: GameState): string[] {
  const bad: string[] = [];
  const o = s.options;
  const ids = new Set<number>();
  const byPt = new Map<number, typeof s.pieces>();
  for (const p of s.pieces) {
    if (ids.has(p.id)) bad.push(`duplicate id ${p.id}`);
    ids.add(p.id);
    if (p.pt < 0 || p.pt >= o.cols * 3) bad.push(`piece ${p.id} off board`);
    byPt.set(p.pt, [...(byPt.get(p.pt) ?? []), p]);
  }
  for (const [pt, ps] of byPt) {
    const sides = new Set(ps.filter((p) => p.side !== null).map((p) => p.side));
    if (sides.size > 1) bad.push(`enemy pieces share point ${pt}`);
    const nonKing = ps.filter((p) => p.kind !== 'king');
    if (o.stacking === 'single' && nonKing.length > 1)
      bad.push(`stacked pieces at ${pt} in single mode`);
    if (!o.royalsShareWithOwn) {
      const royal = ps.filter((p) => p.kind !== 'soldier' && p.side !== null);
      for (const r of royal) {
        const mates = ps.filter(
          (p) => p.id !== r.id && p.side === r.side && p.kind !== 'king' && r.kind !== 'king',
        );
        if (r.kind === 'queen' && mates.length) bad.push(`queen shares with own piece at ${pt}`);
      }
    }
  }
  const kings = s.pieces.filter((p) => p.kind === 'king');
  if (kings.length > 1) bad.push('more than one king');
  for (const side of [0, 1] as const) {
    const sol = s.pieces.filter((p) => p.kind === 'soldier' && p.side === side).length;
    if (sol > o.soldiersPerSide) bad.push('too many soldiers');
    const q = s.pieces.filter((p) => p.kind === 'queen' && p.side === side).length;
    if (q > 1) bad.push('too many queens');
  }
  if (s.phase === 'move' && s.dice.length === 0) bad.push('move phase without dice');
  return bad;
}
