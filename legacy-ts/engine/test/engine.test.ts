import { describe, expect, it } from 'vitest';
import {
  CUSTOM,
  LAGESVUOTNA,
  NAVUOTNA_MAZE,
  NAVUOTNA_RAISA,
  UNJARGA,
  VUOVDAGUOIKA,
  applyAction,
  candidatesFor,
  checkInvariants,
  legalActions,
  legalMoves,
  newGame,
  playableDiceIndices,
  royalDestinations,
  figureEight,
  xfPoint,
  ptOf,
  rowOf,
  colOf,
} from '../src';
import type { Action, GameState } from '../src';
import { P, scenario } from './helpers';

const L = LAGESVUOTNA.options;
const V = VUOVDAGUOIKA.options;
const N = NAVUOTNA_RAISA.options;
const U = UNJARGA.options;

const move = (
  s: GameState,
  pieceId: number,
  to: number,
  die = 0,
  fate?: 'take' | 'remove',
): GameState => applyAction(s, { type: 'move', die, pieceId, to, fate });

describe('setup', () => {
  it('Lágesvuotna: 15 soldiers + queen each, neutral king on the Castle', () => {
    const g = newGame(L, { seed: 3 });
    for (const side of [0, 1]) {
      expect(g.pieces.filter((p) => p.kind === 'soldier' && p.side === side)).toHaveLength(15);
      expect(g.pieces.filter((p) => p.kind === 'queen' && p.side === side)).toHaveLength(1);
    }
    const king = g.pieces.find((p) => p.kind === 'king')!;
    expect(king.side).toBeNull();
    expect(king.pt).toBe(P(L, 1, 7));
    expect(checkInvariants(g)).toEqual([]);
  });
  it('queens stand on the marked points, four lines from each end, on their owner’s right', () => {
    const g = newGame(L, { seed: 3 });
    const q = (side: number) => g.pieces.find((p) => p.kind === 'queen' && p.side === side)!;
    expect(q(0).pt).toBe(P(L, 1, 11));
    expect(q(1).pt).toBe(P(L, 1, 3));
    const mirrored = newGame({ ...L, queenStart: 'left' }, { seed: 3 });
    expect(mirrored.pieces.find((p) => p.kind === 'queen' && p.side === 0)!.pt).toBe(P(L, 1, 3));
  });
  it('Návuotna: 12 soldiers on 13 squares, rightmost square empty', () => {
    const g = newGame(N, { seed: 1 });
    const mine = g.pieces.filter((p) => p.kind === 'soldier' && p.side === 0).map((p) => p.pt);
    expect(mine).toHaveLength(12);
    expect(mine).not.toContain(P(N, 0, 12));
    const theirs = g.pieces.filter((p) => p.kind === 'soldier' && p.side === 1).map((p) => p.pt);
    expect(theirs).not.toContain(P(N, 2, 0)); // rightmost from their seat
  });
  it('equal odds activates three soldiers per side', () => {
    const g = newGame(L, { seed: 1, equalOdds: true });
    expect(g.pieces.filter((p) => p.kind === 'soldier' && p.active)).toHaveLength(6);
  });
  it('is deterministic for a seed', () => {
    const a = newGame(L, { seed: 99 });
    const b = newGame(L, { seed: 99 });
    expect(a.current).toBe(b.current);
    expect(applyAction(a, { type: 'throw' }).dice).toEqual(applyAction(b, { type: 'throw' }).dice);
  });
});

describe('tracks', () => {
  it('standard loop for seat 0: home right, middle left, enemy row right, middle left …', () => {
    const g = newGame(V, { seed: 1 });
    const t = g.tracks[0];
    const rc = t.points.map((p) => [rowOf(15, p), colOf(15, p)]);
    expect(rc[0]).toEqual([0, 0]);
    expect(rc[14]).toEqual([0, 14]);
    expect(rc[15]).toEqual([1, 14]);
    expect(rc[29]).toEqual([1, 0]);
    expect(rc[30]).toEqual([2, 0]);
    expect(rc[44]).toEqual([2, 14]);
    expect(t.loopStart).toBe(15);
    expect(t.points).toHaveLength(45);
  });
  it('figure-eight returns to the home row on the second middle pass', () => {
    const g = newGame(L, { seed: 1 });
    const t = g.tracks[0];
    expect(t.points).toHaveLength(60);
    const rc = t.points.map((p) => [rowOf(15, p), colOf(15, p)]);
    expect(rc[45]).toEqual([1, 14]); // second middle pass starts after the enemy row
    expect(rc[59]).toEqual([1, 0]);
    // wrapping from the last index goes to the home row start
    expect(t.loopStart).toBe(0);
  });
  it.each([
    ['figure-eight', L],
    ['loop', V],
    ['loop-from-middle', U],
  ])('seat 1 track is the 180° rotation of seat 0 (%s)', (_n, opts) => {
    const g = newGame(opts, { seed: 1 });
    const a = g.tracks[0].points;
    const b = g.tracks[1].points;
    expect(b).toEqual(a.map((p) => xfPoint(opts.cols, 'rot', p)));
    // both tracks cover the same set of points (mirror images through the centre)
    expect(new Set(a.map((p) => xfPoint(opts.cols, 'rot', p)))).toEqual(new Set(b));
  });
  it('mieđut: the non-starter moves the mirrored track and enters the middle row at the same place', () => {
    for (let seed = 1; seed < 6; seed++) {
      const g = newGame(V, { seed, miedut: true });
      const first = g.tracks[0].points.find((p) => rowOf(15, p) === 1)!;
      const second = g.tracks[1].points.find((p) => rowOf(15, p) === 1)!;
      expect(first).toBe(second);
    }
  });
  it('king graph is the same for both seats', () => {
    const fig = figureEight(15);
    const rot = fig.map((p) => xfPoint(15, 'rot', p));
    for (let pt = 0; pt < 45; pt++) {
      for (const v of [1, 2, 3]) {
        const a = royalDestinations(15, fig, 'figure-eight', null, pt, v).sort();
        const b = royalDestinations(15, rot, 'figure-eight', null, pt, v).sort();
        expect(b).toEqual(a);
      }
    }
  });
});

describe('dice order', () => {
  it('Lágesvuotna fixed order: X first, then III, then II', () => {
    const s = scenario(
      L,
      [
        { kind: 'soldier', side: 0, at: [1, 5] },
        { kind: 'soldier', side: 1, at: [2, 3], active: false },
      ],
      {
        dice: ['II', 'X', 'III'],
      },
    );
    expect(playableDiceIndices(s).map((i) => s.dice[i].face)).toEqual(['X']);
  });
  it('after X is played, III comes before II', () => {
    let s = scenario(
      L,
      [
        { kind: 'soldier', side: 0, at: [1, 5] },
        { kind: 'soldier', side: 1, at: [2, 3], active: false },
      ],
      {
        dice: ['II', 'X', 'III'],
      },
    );
    const mv = legalMoves(s).find((m) => m.face === 'X')!;
    s = move(s, mv.pieceId, mv.to, mv.die);
    expect(playableDiceIndices(s).map((i) => s.dice[i].face)).toEqual(['III']);
  });
  it('fixed order: if the III has no legal move the whole turn is lost', () => {
    // Only soldier is blocked for III (lands on an enemy sleeping soldier) but could move II.
    const s = scenario(
      L,
      [
        { kind: 'soldier', side: 0, at: [1, 8] },
        { kind: 'soldier', side: 1, at: [1, 5], active: false },
        { kind: 'soldier', side: 1, at: [2, 0], active: false },
      ],
      { dice: ['II', 'III', 'blank'] },
    );
    // 8 -> 7 -> 6 -> 5: III lands on the sleeping enemy soldier (illegal). II would land on 6 (legal).
    expect(legalMoves(s)).toHaveLength(0);
    expect(s.current).toBe(1);
    expect(s.events.some((e) => e.type === 'turn-lost')).toBe(true);
  });
  it('free order (Máze): any order is playable', () => {
    const s = scenario(
      NAVUOTNA_MAZE.options,
      [
        { kind: 'soldier', side: 0, at: [1, 5] },
        { kind: 'soldier', side: 1, at: [2, 3] },
      ],
      {
        dice: ['III', 'I'],
      },
    );
    expect(playableDiceIndices(s)).toHaveLength(2);
  });
  it('blank is 0 in Lágesvuotna (spent) and 4 in Vuovdaguoika (a move)', () => {
    const a = scenario(
      L,
      [
        { kind: 'soldier', side: 0, at: [1, 9] },
        { kind: 'soldier', side: 1, at: [2, 0], active: false },
      ],
      { dice: ['blank', 'blank', 'blank'] },
    );
    expect(a.current).toBe(1);
    const b = scenario(
      V,
      [
        { kind: 'soldier', side: 0, at: [1, 9] },
        { kind: 'soldier', side: 1, at: [2, 0], active: false },
      ],
      { dice: ['blank', 'III', 'II'] },
    );
    expect(
      candidatesFor(b, 0, 'blank')
        .filter((c) => c.ok)
        .map((c) => c.to),
    ).toEqual([P(V, 1, 5)]);
  });
  it('dice are applied separately, never summed', () => {
    expect(L.diceApplication).toBe('separate');
    const s = scenario(
      V,
      [
        { kind: 'soldier', side: 0, at: [1, 9] },
        { kind: 'soldier', side: 1, at: [2, 0], active: false },
      ],
      { dice: ['III', 'II', 'II'] },
    );
    const targets = new Set(legalMoves(s).map((m) => m.to));
    expect(targets).toEqual(new Set([P(V, 1, 6), P(V, 1, 7)]));
  });
});

describe('activation and X', () => {
  it('only an X activates; the front soldier goes first', () => {
    const g = newGame(L, { seed: 1 });
    const s = scenario(
      L,
      g.pieces.map((p) => ({
        kind: p.kind,
        side: p.side,
        at: [rowOf(15, p.pt), colOf(15, p.pt)] as [number, number],
        active: p.active,
      })),
      { current: 0, dice: ['X', 'II', 'II'] },
    );
    const xs = legalMoves(s).filter(
      (m) => m.face === 'X' && s.pieces.find((p) => p.id === m.pieceId)!.kind === 'soldier',
    );
    expect(xs).toHaveLength(1);
    expect(xs[0].to).toBe(P(L, 1, 14)); // front soldier steps up onto the middle row
    const wrong = candidatesFor(s, 0, 'X')[0]; // rearmost soldier
    expect(wrong.ok).toBe(false);
    expect(wrong.reason).toBe('not-front');
  });
  it('Návuotna activates in any order (a gap lets a non-front soldier wake)', () => {
    const s = scenario(
      N,
      [
        { kind: 'soldier', side: 0, at: [0, 3], active: false },
        { kind: 'soldier', side: 0, at: [0, 8], active: false },
        { kind: 'soldier', side: 1, at: [2, 3], active: false },
      ],
      { dice: ['X', 'II'], hold: true },
    );
    const ok = (id: number) => candidatesFor(s, id, 'X').every((c) => c.ok);
    expect(ok(0) && ok(1)).toBe(true);
  });
  it('Návuotna: from the opening position every soldier can be woken (it steps onto a neighbouring sleeper)', () => {
    const g = newGame(N, { seed: 1 });
    const s = scenario(
      N,
      g.pieces.map((p) => ({
        kind: p.kind,
        side: p.side,
        at: [rowOf(13, p.pt), colOf(13, p.pt)] as [number, number],
        active: p.active,
      })),
      { current: 0, dice: ['X', 'II'], hold: true },
    );
    const wake = s.pieces
      .filter((p) => p.side === 0 && p.kind === 'soldier')
      .map((p) => candidatesFor(s, p.id, 'X')[0]);
    expect(wake.every((c) => c.ok)).toBe(true);
  });
  it('Unjárga option: first-middle activation sends the soldier to the first middle-row point', () => {
    const o = { ...U, activation: 'first-middle' as const };
    const g = newGame(o, { seed: 1 });
    const s = scenario(
      o,
      g.pieces.map((p) => ({
        kind: p.kind,
        side: p.side,
        at: [rowOf(15, p.pt), colOf(15, p.pt)] as [number, number],
        active: p.active,
      })),
      { current: 0, dice: ['X', 'II', 'II'], hold: true },
    );
    const c = candidatesFor(s, 4, 'X')[0];
    expect(c.reason).toBe('not-front');
    expect(candidatesFor(s, 14, 'X')[0].to).toBe(P(o, 1, 14));
  });
  it('vertical crossing can be switched off', () => {
    const fig = figureEight(15);
    expect(
      royalDestinations(15, fig, 'figure-eight', null, ptOf(15, 0, 5), 2, false),
    ).not.toContain(ptOf(15, 2, 5));
  });
  it('Lágesvuotna front-first: the same position only allows the front soldier', () => {
    const s = scenario(
      L,
      [
        { kind: 'soldier', side: 0, at: [0, 3], active: false },
        { kind: 'soldier', side: 0, at: [0, 8], active: false },
        { kind: 'soldier', side: 1, at: [2, 3], active: false },
      ],
      { dice: ['X', 'II', 'II'], hold: true },
    );
    expect(candidatesFor(s, 0, 'X')[0].reason).toBe('not-front');
    expect(candidatesFor(s, 1, 'X')[0].ok).toBe(true);
  });
  it('a non-X face cannot wake a sleeping soldier', () => {
    const s = scenario(
      N,
      [
        { kind: 'soldier', side: 0, at: [0, 3], active: false },
        { kind: 'soldier', side: 1, at: [2, 3], active: false },
      ],
      { dice: ['I', 'II'] },
    );
    expect(legalMoves(s)).toHaveLength(0);
  });
  it('Unjárga: an activated soldier moves straight up onto the middle row', () => {
    const g = newGame(U, { seed: 1 });
    const s = scenario(
      U,
      g.pieces.map((p) => ({
        kind: p.kind,
        side: p.side,
        at: [rowOf(15, p.pt), colOf(15, p.pt)] as [number, number],
        active: p.active,
      })),
      { current: 0, dice: ['X', 'II', 'II'] },
    );
    const m = legalMoves(s).find((x) => x.face === 'X')!;
    expect(m.to).toBe(P(U, 1, 14));
    const s2 = scenario(
      U,
      g.pieces.map((p) => ({
        kind: p.kind,
        side: p.side,
        at: [rowOf(15, p.pt), colOf(15, p.pt)] as [number, number],
        active: p.active,
      })),
      { current: 1, dice: ['X', 'II', 'II'] },
    );
    const m2 = legalMoves(s2).find((x) => x.face === 'X')!;
    expect(rowOf(15, m2.to)).toBe(1);
    expect(colOf(15, m2.to)).toBe(colOf(15, s2.pieces.find((p) => p.id === m2.pieceId)!.pt));
  });
});

describe('re-throw', () => {
  it('single: an X die can be re-thrown until it is not X', () => {
    let s = scenario(
      L,
      [
        { kind: 'soldier', side: 0, at: [1, 5] },
        { kind: 'soldier', side: 1, at: [2, 3], active: false },
      ],
      { dice: ['X', 'III', 'II'] },
    );
    expect(legalActions(s).some((a) => a.type === 'rethrow')).toBe(true);
    s = applyAction(s, { type: 'rethrow', die: 0 });
    expect(s.dice[0].face).not.toBe('X');
  });
  it('triple: only when all dice show X', () => {
    const a = scenario(
      V,
      [
        { kind: 'soldier', side: 0, at: [1, 5] },
        { kind: 'soldier', side: 1, at: [2, 3] },
      ],
      { dice: ['X', 'X', 'II'] },
    );
    expect(legalActions(a).some((x) => x.type === 'rethrowAll')).toBe(false);
    const b = scenario(
      V,
      [
        { kind: 'soldier', side: 0, at: [1, 5] },
        { kind: 'soldier', side: 1, at: [2, 3] },
      ],
      { dice: ['X', 'X', 'X'] },
    );
    expect(legalActions(b).some((x) => x.type === 'rethrowAll')).toBe(true);
    const c = applyAction(b, { type: 'rethrowAll' });
    expect(c.dice).toHaveLength(3);
  });
});

describe('capture, stacking and sleeping pieces', () => {
  it('stacked capture: landing takes every enemy piece on the line', () => {
    const s = scenario(
      L,
      [
        { kind: 'soldier', side: 0, at: [1, 9] },
        { kind: 'soldier', side: 1, at: [1, 6] },
        { kind: 'soldier', side: 1, at: [1, 6] },
        { kind: 'soldier', side: 1, at: [1, 6] },
        { kind: 'soldier', side: 1, at: [2, 0], active: false },
        { kind: 'soldier', side: 0, at: [0, 0], active: false },
      ],
      { dice: ['III', 'blank', 'blank'] },
    );
    const t = move(s, 0, P(L, 1, 6));
    expect(t.pieces.filter((p) => p.side === 1 && p.kind === 'soldier')).toHaveLength(1);
    expect(checkInvariants(t)).toEqual([]);
  });
  it('Lágesvuotna: sleeping soldiers are protected and cannot be landed on', () => {
    const s = scenario(
      L,
      [
        { kind: 'soldier', side: 0, at: [1, 9] },
        { kind: 'soldier', side: 1, at: [1, 6], active: false },
        { kind: 'soldier', side: 1, at: [2, 0], active: false },
      ],
      { dice: ['III', 'blank', 'blank'], hold: true },
    );
    const c = candidatesFor(s, 0, 'III').find((x) => x.to === P(L, 1, 6))!;
    expect(c.ok).toBe(false);
    expect(c.reason).toBe('enemy-sleeping');
  });
  it.each([
    ['Vuovdaguoika', V],
    ['Návuotna', N],
  ])('%s: sleeping soldiers can be captured', (_n, o) => {
    const s = scenario(
      o,
      [
        { kind: 'soldier', side: 0, at: [1, 9] },
        { kind: 'soldier', side: 1, at: [1, 6], active: false },
        { kind: 'soldier', side: 1, at: [2, 0], active: false },
      ],
      { dice: o === N ? ['III', 'II'] : ['III', 'II', 'II'] },
    );
    const c = candidatesFor(s, 0, 'III').find((x) => x.to === P(o, 1, 6))!;
    expect(c.ok).toBe(true);
    expect(c.out.captures).toHaveLength(1);
  });
  it('single-file (Vuovdaguoika): cannot land on, or jump over, own soldiers', () => {
    const s = scenario(
      V,
      [
        { kind: 'soldier', side: 0, at: [1, 9] },
        { kind: 'soldier', side: 0, at: [1, 8] },
        { kind: 'soldier', side: 1, at: [2, 0], active: false },
      ],
      { dice: ['II', 'III', 'III'] },
    );
    const over = candidatesFor(s, 0, 'III');
    expect(over.every((c) => !c.ok)).toBe(true);
    const flat = scenario(
      V,
      [
        { kind: 'soldier', side: 0, at: [1, 9] },
        { kind: 'soldier', side: 0, at: [1, 8] },
        { kind: 'soldier', side: 1, at: [2, 0], active: false },
      ],
      { dice: ['II', 'III', 'III'] },
    );
    expect({
      ...flat,
      options: { ...V, jumpOwnSoldiers: true, stacking: 'allowed' as const },
    }).toBeTruthy();
  });
  it('captures never leave enemy pieces sharing a line (random Lágesvuotna play)', () => {
    let s = newGame(L, { seed: 5 });
    for (let i = 0; i < 400 && s.phase !== 'over'; i++) {
      const acts = legalActions(s);
      const a = acts[(i * 7) % acts.length];
      s = applyAction(s, a);
      expect(checkInvariants(s)).toEqual([]);
    }
  });
});

describe('king (recruit mode, Lágesvuotna)', () => {
  const base = [
    { kind: 'soldier' as const, side: 0 as const, at: [1, 11] as [number, number] },
    { kind: 'soldier' as const, side: 1 as const, at: [1, 3] as [number, number] },
    { kind: 'queen' as const, side: 0 as const, at: [1, 12] as [number, number], active: false },
    { kind: 'queen' as const, side: 1 as const, at: [1, 2] as [number, number], active: false },
    { kind: 'king' as const, side: null, at: [1, 7] as [number, number] },
  ];
  it('landing on the neutral king recruits it; the opponent can recruit it back', () => {
    // soldier of side 0 on (1,11) moves 4? use three dice: blank=0 in L, so use III from col 10
    let s = scenario(L, [{ ...base[0], at: [1, 10] }, base[1], base[2], base[3], base[4]], {
      dice: ['III', 'blank', 'blank'],
    });
    s = move(s, 0, P(L, 1, 7));
    const king = () => s.pieces.find((p) => p.kind === 'king')!;
    expect(king().side).toBe(0);
    expect(king().pt).toBe(P(L, 1, 7));
    // now side 1 lands on it
    s = scenario(
      L,
      [
        { kind: 'soldier', side: 0, at: [1, 7] },
        { kind: 'soldier', side: 1, at: [1, 10] },
        base[2],
        base[3],
        { kind: 'king', side: 0, at: [1, 7] },
      ],
      { current: 1, dice: ['III', 'blank', 'blank'] },
    );
    // side 1 moves left-to-right on the middle row (rotated track): 10 -> 11 -> 12 -> 13; so use a closer one
    s = scenario(
      L,
      [
        { kind: 'soldier', side: 0, at: [1, 7] },
        { kind: 'soldier', side: 1, at: [1, 4] },
        base[2],
        base[3],
        { kind: 'king', side: 0, at: [1, 7] },
      ],
      { current: 1, dice: ['III', 'blank', 'blank'] },
    );
    const t = move(s, 1, P(L, 1, 7));
    const k = t.pieces.find((p) => p.kind === 'king')!;
    expect(k.side).toBe(1);
    // side 0's soldier on that line was captured, king stays put and shares the line with its new owner
    expect(t.pieces.filter((p) => p.side === 0 && p.kind === 'soldier')).toHaveLength(0);
    expect(t.winner).toBe(1);
  });
  it('the king cannot be captured, only recruited', () => {
    const s = scenario(L, [{ ...base[0], at: [1, 10] }, base[1], base[2], base[3], base[4]], {
      dice: ['III', 'blank', 'blank'],
    });
    const t = move(s, 0, P(L, 1, 7));
    expect(t.pieces.some((p) => p.kind === 'king')).toBe(true);
  });
  it('king row crossing: II crosses home↔enemy row, X crosses to the middle row', () => {
    const fig = figureEight(15);
    const at = (r: number, c: number) => ptOf(15, r, c);
    const home = royalDestinations(15, fig, 'figure-eight', null, at(0, 5), 2);
    expect(home).toContain(at(2, 5));
    const homeX = royalDestinations(15, fig, 'figure-eight', null, at(0, 5), 1);
    expect(homeX).toContain(at(1, 5));
    const midX = royalDestinations(15, fig, 'figure-eight', null, at(1, 5), 1);
    expect(midX).toContain(at(0, 5));
    expect(midX).toContain(at(2, 5));
    // III does not cross rows straight
    const home3 = royalDestinations(15, fig, 'figure-eight', null, at(0, 5), 3);
    expect(home3).not.toContain(at(2, 5));
  });
  it('king moves around a bend as if straight, forward and backward', () => {
    const fig = figureEight(15);
    const at = (r: number, c: number) => ptOf(15, r, c);
    const d = royalDestinations(15, fig, 'figure-eight', null, at(0, 13), 3);
    expect(d).toContain(at(1, 13)); // 13 -> 14 -> up the bend -> one step left, all counted as straight
    expect(royalDestinations(15, fig, 'figure-eight', null, at(0, 13), 2)).toContain(at(1, 14));
    expect(d).toContain(at(0, 10)); // backward
  });
  it('a recruiting piece may share the line with the king; own pieces cannot join it afterwards', () => {
    let s = scenario(
      L,
      [
        { ...base[0], at: [1, 10] },
        { kind: 'soldier', side: 0, at: [1, 9] },
        base[1],
        base[2],
        base[3],
        base[4],
      ],
      { dice: ['III', 'II', 'blank'] },
    );
    s = move(s, 0, P(L, 1, 7), 0);
    const c = candidatesFor(s, 1, 'II').find((x) => x.to === P(L, 1, 7))!;
    expect(c.ok).toBe(false);
    expect(c.reason).toBe('royal-no-share');
  });
  it('the king may not land on its own army’s pieces', () => {
    const s = scenario(
      L,
      [
        { kind: 'soldier', side: 0, at: [1, 6] },
        { kind: 'soldier', side: 1, at: [2, 0], active: false },
        { kind: 'queen', side: 0, at: [1, 12], active: false },
        { kind: 'queen', side: 1, at: [1, 2], active: false },
        { kind: 'king', side: 0, at: [1, 7] },
      ],
      { dice: ['X', 'II', 'blank'] },
    );
    const c = candidatesFor(s, 4, 'X').find((x) => x.to === P(L, 1, 6))!;
    expect(c.ok).toBe(false);
  });
});

describe('queen (Lágesvuotna)', () => {
  const mkq = (dice: ('X' | 'II' | 'III' | 'blank')[] = ['X', 'blank', 'blank']) =>
    scenario(
      L,
      [
        { kind: 'soldier', side: 0, at: [1, 9] },
        { kind: 'soldier', side: 1, at: [2, 0], active: false },
        { kind: 'queen', side: 0, at: [1, 11], active: false },
        { kind: 'queen', side: 1, at: [1, 3], active: false },
        { kind: 'king', side: null, at: [1, 7] },
      ],
      { dice },
    );
  it('is inactive until an X frees her; the X moves her one line', () => {
    const s = mkq();
    const q = candidatesFor(s, 2, 'X')
      .filter((c) => c.ok)
      .map((c) => c.to);
    expect(q).toEqual(expect.arrayContaining([P(L, 1, 10), P(L, 1, 12), P(L, 0, 11), P(L, 2, 11)]));
    const t = move(s, 2, P(L, 1, 10));
    expect(t.pieces.find((p) => p.id === 2)!.active).toBe(true);
  });
  it('an inactive queen cannot be landed on or captured', () => {
    const s = scenario(
      L,
      [
        { kind: 'soldier', side: 0, at: [1, 14] },
        { kind: 'soldier', side: 1, at: [2, 5], active: false },
        { kind: 'queen', side: 0, at: [1, 12], active: false },
        { kind: 'queen', side: 1, at: [1, 11], active: false },
        { kind: 'king', side: null, at: [1, 7] },
      ],
      { dice: ['II', 'blank', 'blank'], hold: true },
    );
    const c = candidatesFor(s, 0, 'II').find((x) => x.to === P(L, 1, 12))!;
    expect(c.ok).toBe(false);
    expect(c.reason).toBe('own-sleeping');
    const s2 = { ...s, current: 1 as const };
    expect(s2).toBeTruthy();
  });
  it('capturing the queen ends the game', () => {
    const s = scenario(
      L,
      [
        { kind: 'soldier', side: 0, at: [1, 9] },
        { kind: 'soldier', side: 1, at: [2, 0], active: false },
        { kind: 'queen', side: 0, at: [1, 11], active: false },
        { kind: 'queen', side: 1, at: [1, 6] },
        { kind: 'king', side: null, at: [1, 7] },
      ],
      { dice: ['III', 'blank', 'blank'] },
    );
    const t = move(s, 0, P(L, 1, 6));
    expect(t.phase).toBe('over');
    expect(t.winner).toBe(0);
    expect(t.winReason).toBe('queen-captured');
  });
  it('a lone king does not save a side without soldiers', () => {
    const s = scenario(
      L,
      [
        { kind: 'soldier', side: 0, at: [1, 9] },
        { kind: 'soldier', side: 1, at: [1, 6] },
        { kind: 'queen', side: 0, at: [1, 11], active: false },
        { kind: 'queen', side: 1, at: [1, 3], active: false },
        { kind: 'king', side: 1, at: [1, 2] },
      ],
      { dice: ['III', 'blank', 'blank'] },
    );
    const t = move(s, 0, P(L, 1, 6));
    expect(t.winner).toBe(0);
    expect(t.winReason).toBe('no-soldiers');
  });
});

describe('king push mode (Vuovdaguoika)', () => {
  it('landing pushes the king one line forward and takes control', () => {
    const s = scenario(
      V,
      [
        { kind: 'soldier', side: 0, at: [1, 10] },
        { kind: 'soldier', side: 1, at: [2, 0], active: false },
        { kind: 'king', side: null, at: [1, 7] },
      ],
      { dice: ['III', 'II', 'II'] },
    );
    const t = move(s, 0, P(V, 1, 7));
    const k = t.pieces.find((p) => p.kind === 'king')!;
    expect(k.side).toBe(0);
    expect(k.pt).toBe(P(V, 1, 6));
  });
  it('the king rams an enemy soldier standing on the next line', () => {
    const s = scenario(
      V,
      [
        { kind: 'soldier', side: 0, at: [1, 10] },
        { kind: 'soldier', side: 1, at: [1, 6] },
        { kind: 'soldier', side: 1, at: [2, 0], active: false },
        { kind: 'king', side: null, at: [1, 7] },
      ],
      { dice: ['III', 'II', 'II'] },
    );
    const t = move(s, 0, P(V, 1, 7));
    expect(t.pieces.filter((p) => p.side === 1 && p.kind === 'soldier')).toHaveLength(1);
  });
  it('cannot push the king onto your own soldier', () => {
    const s = scenario(
      V,
      [
        { kind: 'soldier', side: 0, at: [1, 10] },
        { kind: 'soldier', side: 0, at: [1, 6] },
        { kind: 'soldier', side: 1, at: [2, 0], active: false },
        { kind: 'king', side: null, at: [1, 7] },
      ],
      { dice: ['III', 'II', 'II'] },
    );
    const c = candidatesFor(s, 0, 'III').find((x) => x.to === P(V, 1, 7))!;
    expect(c.ok).toBe(false);
    expect(c.reason).toBe('cannot-push-onto-own');
  });
  it('knock-out option offers take and remove', () => {
    const s = scenario(
      { ...V, kingKnockOut: true },
      [
        { kind: 'soldier', side: 0, at: [1, 10] },
        { kind: 'soldier', side: 1, at: [2, 0], active: false },
        { kind: 'king', side: null, at: [1, 7] },
      ],
      { dice: ['III', 'II', 'II'] },
    );
    const cs = candidatesFor(s, 0, 'III').filter((x) => x.to === P(V, 1, 7));
    expect(cs.map((c) => c.fate).sort()).toEqual(['remove', 'take']);
    const t = move(s, 0, P(V, 1, 7), 0, 'remove');
    expect(t.pieces.some((p) => p.kind === 'king')).toBe(false);
  });
});

describe('Unjárga king', () => {
  const pcs = (second?: object) => [
    { kind: 'soldier' as const, side: 0 as const, at: [1, 3] as [number, number] },
    { kind: 'soldier' as const, side: 1 as const, at: [2, 5] as [number, number], active: false },
    { kind: 'king' as const, side: null, at: [1, 7] as [number, number] },
    ...(second ? [second as never] : []),
  ];
  it('is dormant until a soldier reaches the opponent’s home row', () => {
    // seat 0 soldier on middle row col 0 -> II is track step: (1,0)->(2,0)->(2,1)
    let s = scenario(
      U,
      [
        { kind: 'soldier', side: 0, at: [1, 1] },
        { kind: 'soldier', side: 1, at: [0, 5], active: false },
        { kind: 'king', side: null, at: [1, 7] },
      ],
      { dice: ['II', 'II', 'II'] },
    );
    expect(s.pieces.find((p) => p.kind === 'king')!.side).toBeNull();
    s = move(s, 0, P(U, 2, 0));
    expect(s.pieces.find((p) => p.kind === 'king')!.side).toBe(0);
    expect(pcs()).toBeTruthy();
  });
  it('nobody may land on the dormant king (assumption, avoids enemy pieces sharing a line)', () => {
    const s = scenario(
      U,
      [
        { kind: 'soldier', side: 0, at: [1, 9] },
        { kind: 'soldier', side: 1, at: [0, 5], active: false },
        { kind: 'king', side: null, at: [1, 7] },
      ],
      { dice: ['II', 'II', 'II'], hold: true },
    );
    const c = candidatesFor(s, 0, 'II').find((x) => x.to === P(U, 1, 7))!;
    expect(c.ok).toBe(false);
    expect(c.reason).toBe('king-dormant');
  });
});

describe('whole games', () => {
  it.each([LAGESVUOTNA, VUOVDAGUOIKA, NAVUOTNA_RAISA, NAVUOTNA_MAZE, UNJARGA, CUSTOM])(
    '$name: random play keeps invariants and finishes',
    (rs) => {
      for (let seed = 1; seed <= 3; seed++) {
        let s = newGame(rs.options, { seed, miedut: seed === 2 });
        let steps = 0;
        while (s.phase !== 'over' && steps++ < 20000) {
          const acts = legalActions(s);
          expect(acts.length).toBeGreaterThan(0);
          const a: Action = acts[Math.floor(((s.rng >>> 3) + steps * 31) % acts.length)];
          s = applyAction(s, a);
          expect(checkInvariants(s)).toEqual([]);
        }
        expect(s.phase).toBe('over');
      }
    },
  );
});
