/* One-off generator for the Python parity fixtures (run with bun; Node is not needed):
   bun run engine/tools/gen-parity-fixtures.ts <output-dir>
   Dice are scripted, never seeded, so the fixtures do not depend on any RNG. */
import { mkdirSync, writeFileSync } from 'node:fs';
import {
  VARIANTS,
  applyAction,
  candidatesFor,
  getVariant,
  legalActions,
  legalMoves,
  newGame,
  ptOf,
  throwWith,
} from '../src';
import type { Action, Face, GameState, Piece, PieceKind, RuleOptions, Side } from '../src';

const out = process.argv[2] ?? 'tests/parity/fixtures';
mkdirSync(out, { recursive: true });

// ---------------------------------------------------------------- canonical forms
const snapshot = (s: GameState) => ({
  current: s.current,
  phase: s.phase,
  winner: s.winner,
  winReason: s.winReason,
  dice: s.dice.map((d) => [d.face, d.used ? 1 : 0]),
  pieces: [...s.pieces]
    .sort((a, b) => a.id - b.id)
    .map((p) => [p.id, p.kind, p.side, p.active ? 1 : 0, p.pt, p.pi]),
});
const actionKey = (a: Action) =>
  a.type === 'move'
    ? ['move', a.die, a.pieceId, a.to, a.fate ?? null]
    : a.type === 'rethrow'
      ? ['rethrow', a.die, null, null, null]
      : [a.type, null, null, null, null];
const sortKeys = (xs: unknown[][]) => xs.sort((a, b) => JSON.stringify(a).localeCompare(JSON.stringify(b)));
const legalList = (s: GameState) => sortKeys(legalActions(s).map(actionKey));
const candList = (s: GameState) => {
  const faces = [...new Set(s.dice.map((d) => d.face))];
  const rows: unknown[][] = [];
  for (const p of s.pieces) {
    if (p.side !== s.current) continue;
    for (const f of faces) {
      const cs = candidatesFor(s, p.id, f).map((c) => [
        c.to,
        c.ok ? 1 : 0,
        c.reason ?? null,
        c.fate ?? null,
        c.newPi,
        [...c.out.captures].sort((a, b) => a - b),
        c.out.king ? [c.out.king.side, c.out.king.pt, c.out.king.kind] : null,
      ]);
      cs.sort((a, b) => JSON.stringify(a).localeCompare(JSON.stringify(b)));
      rows.push([p.id, f, cs]);
    }
  }
  return rows;
};

// ---------------------------------------------------------------- scripted state helpers
interface Spec {
  kind: PieceKind;
  side: Side | null;
  at: [number, number];
  active?: boolean;
}
type Opt = Partial<RuleOptions>;

function setup(options: RuleOptions, starter: Side, miedut: boolean, equalOdds: boolean): GameState {
  for (let seed = 1; seed < 5000; seed++) {
    const g = newGame(options, { seed, miedut, equalOdds });
    if (g.current === starter) return g;
  }
  throw new Error('no seed gives the wanted starter');
}

function build(options: RuleOptions, specs: Spec[] | null, current: Side, starter: Side, miedut: boolean, equalOdds: boolean): GameState {
  const g = setup(options, starter, miedut, equalOdds);
  if (!specs) return { ...g, current, phase: 'throw', dice: [], events: [] };
  const n = options.cols;
  const pieces: Piece[] = specs.map((sp, id) => {
    const pt = ptOf(n, sp.at[0], sp.at[1]);
    let pi = -1;
    if (sp.kind === 'soldier') {
      pi = sp.active === false ? g.homeSlots[sp.side as Side].indexOf(pt) : g.tracks[sp.side as Side].points.indexOf(pt);
    }
    return { id, kind: sp.kind, side: sp.side, active: sp.active ?? true, pt, pi };
  });
  return { ...g, pieces, current, phase: 'throw', dice: [], events: [] };
}

function withDice(s: GameState, faces: Face[], settle: boolean): GameState {
  if (settle) return throwWith(s, faces);
  return { ...s, phase: 'move', dice: faces.map((face) => ({ face, used: face === 'blank' && s.options.blankValue === 0 })) };
}

/** Force a re-throw outcome by searching for an rng value that produces it (TS uses an internal rng). */
function forceRethrow(s: GameState, a: Action, wanted: Face[]): GameState {
  for (let r = 1; r < 3_000_000; r++) {
    const t = applyAction({ ...s, rng: r }, a);
    const ev = t.events.find((e) => e.type === 'rethrow');
    const got = ev && ev.type === 'rethrow' ? ev.faces : [];
    if (JSON.stringify(got) === JSON.stringify(wanted)) return t;
  }
  throw new Error('cannot force rethrow ' + JSON.stringify(wanted));
}

// ---------------------------------------------------------------- 1. setup fixtures
const setups: unknown[] = [];
for (const rs of VARIANTS) {
  for (const starter of [0, 1] as Side[]) {
    for (const miedut of [false, true]) {
      for (const equalOdds of [false, true]) {
        const g = setup(rs.options, starter, miedut, equalOdds);
        setups.push({
          variant: rs.id,
          options: rs.options,
          starter,
          miedutRequested: miedut,
          equalOdds,
          miedut: g.miedut,
          transforms: g.transforms,
          tracks: g.tracks,
          homeSlots: g.homeSlots,
          snapshot: snapshot({ ...g, phase: 'throw', dice: [] }),
        });
      }
    }
  }
}
writeFileSync(`${out}/setup.json`, JSON.stringify(setups));

// ---------------------------------------------------------------- 2. hand-built scenarios
const S = (kind: PieceKind, side: Side | null, r: number, c: number, active = true): Spec => ({ kind, side, at: [r, c], active });
const sold = (side: Side, r: number, c: number, active = true) => S('soldier', side, r, c, active);
const queens = (a = [1, 11], b = [1, 3]): Spec[] => [S('queen', 0, a[0], a[1], false), S('queen', 1, b[0], b[1], false)];

interface Scn {
  name: string;
  variant: string;
  opts?: Opt;
  specs: Spec[] | null;
  current?: Side;
  starter?: Side;
  miedut?: boolean;
  equalOdds?: boolean;
  dice: Face[];
  settle?: boolean;
  /** extra scripted continuation applied after the first legal-move sweep */
  walk?: number;
}
const L = 'lagesvuotna', V = 'vuovdaguoika', R = 'navuotna-raisa', M = 'navuotna-maze', U = 'unjarga';
const full = (variant: string, o?: Opt) => ({ ...getVariant(variant).options, ...(o ?? {}) }) as RuleOptions;

const scn: Scn[] = [
  { name: 'L opening X', variant: L, specs: null, current: 0, dice: ['X', 'II', 'II'] },
  { name: 'L opening X seat 1', variant: L, specs: null, current: 1, dice: ['X', 'III', 'II'] },
  { name: 'L fixed order II X III', variant: L, specs: null, current: 0, dice: ['II', 'X', 'III'] },
  { name: 'L equal odds III II II', variant: L, specs: null, current: 0, equalOdds: true, dice: ['III', 'II', 'II'] },
  { name: 'L blank blank blank settles', variant: L, specs: [sold(0, 1, 9), sold(1, 2, 0, false)], dice: ['blank', 'blank', 'blank'], settle: true },
  { name: 'L fixed-order lost turn', variant: L, specs: [sold(0, 1, 8), sold(1, 1, 5, false), sold(1, 2, 0, false)], dice: ['II', 'III', 'blank'], settle: true },
  { name: 'L stacked capture', variant: L, specs: [sold(0, 1, 9), sold(1, 1, 6), sold(1, 1, 6), sold(1, 1, 6), sold(1, 2, 0, false), sold(0, 0, 0, false)], dice: ['III', 'blank', 'blank'] },
  { name: 'L sleeping protected', variant: L, specs: [sold(0, 1, 9), sold(1, 1, 6, false), sold(1, 2, 0, false)], dice: ['III', 'II', 'blank'] },
  { name: 'L king neutral recruit', variant: L, specs: [sold(0, 1, 10), sold(1, 1, 3), ...queens(), S('king', null, 1, 7)], dice: ['III', 'II', 'X'] },
  { name: 'L king recruit back', variant: L, specs: [sold(0, 1, 7), sold(1, 1, 4), ...queens([1, 12]), S('king', 0, 1, 7)], current: 1, dice: ['III', 'II', 'X'] },
  { name: 'L king at home row', variant: L, specs: [sold(0, 1, 11), sold(1, 2, 14, false), ...queens(), S('king', 0, 0, 5)], dice: ['X', 'II', 'III'] },
  { name: 'L king at mid row', variant: L, specs: [sold(0, 0, 3), sold(1, 2, 14, false), ...queens(), S('king', 0, 1, 5)], dice: ['X', 'II', 'III'] },
  { name: 'L king at bend', variant: L, specs: [sold(0, 0, 3), sold(1, 2, 14, false), ...queens(), S('king', 0, 0, 13)], dice: ['X', 'II', 'III'] },
  { name: 'L king at far bend', variant: L, specs: [sold(0, 0, 3, false), sold(1, 2, 14, false), ...queens(), S('king', 0, 1, 0)], dice: ['X', 'II', 'III'] },
  { name: 'L king blocked by own', variant: L, specs: [sold(0, 1, 6), sold(1, 2, 0, false), ...queens([1, 12]), S('king', 0, 1, 7)], dice: ['X', 'II', 'blank'] },
  { name: 'L king takes enemy', variant: L, specs: [sold(0, 0, 3), sold(1, 1, 5), ...queens(), S('king', 0, 1, 7)], dice: ['II', 'X', 'blank'] },
  { name: 'L soldier joins own king', variant: L, specs: [sold(0, 1, 10), sold(0, 1, 9), sold(1, 1, 3), ...queens(), S('king', null, 1, 7)], dice: ['III', 'II', 'blank'] },
  { name: 'L queen frees', variant: L, specs: [sold(0, 1, 9), sold(1, 2, 0, false), ...queens(), S('king', null, 1, 7)], dice: ['X', 'blank', 'blank'] },
  { name: 'L queen asleep landed', variant: L, specs: [sold(0, 1, 14), sold(1, 2, 5, false), S('queen', 0, 1, 12, false), S('queen', 1, 1, 11, false), S('king', null, 1, 7)], dice: ['II', 'blank', 'blank'] },
  { name: 'L queen captured', variant: L, specs: [sold(0, 1, 9), sold(1, 2, 0, false), S('queen', 0, 1, 11, false), S('queen', 1, 1, 6), S('king', null, 1, 7)], dice: ['III', 'blank', 'blank'] },
  { name: 'L queen active moves', variant: L, specs: [sold(0, 1, 9), sold(1, 2, 0, false), S('queen', 0, 1, 11), S('queen', 1, 1, 3, false), S('king', null, 1, 7)], dice: ['III', 'II', 'X'] },
  { name: 'L lone king loses', variant: L, specs: [sold(0, 1, 9), sold(1, 1, 6), ...queens(), S('king', 1, 1, 2)], dice: ['III', 'blank', 'blank'] },
  { name: 'L lone king no-lose option', variant: L, opts: { kingAloneLoses: false, queens: false }, specs: [sold(0, 1, 9), sold(1, 1, 6), S('king', 1, 1, 2)], dice: ['III', 'blank', 'blank'] },
  { name: 'L vertical off', variant: L, opts: { royalVerticalCrossing: false }, specs: [sold(0, 1, 11), sold(1, 2, 14, false), ...queens(), S('king', 0, 0, 5)], dice: ['X', 'II', 'III'] },
  { name: 'L figure-eight soldier wrap', variant: L, specs: [sold(0, 1, 1), sold(1, 2, 0, false), ...queens(), S('king', null, 1, 7)], dice: ['III', 'II', 'X'] },
  { name: 'L mid soldier second pass', variant: L, specs: [sold(0, 2, 13), sold(1, 2, 0, false), ...queens(), S('king', null, 1, 7)], dice: ['III', 'II', 'X'] },
  { name: 'V opening', variant: V, specs: null, current: 0, dice: ['X', 'II', 'blank'] },
  { name: 'V opening seat 1 miedut', variant: V, specs: null, current: 1, starter: 0, miedut: true, dice: ['X', 'III', 'blank'] },
  { name: 'V triple X', variant: V, specs: null, current: 0, dice: ['X', 'X', 'X'] },
  { name: 'V two X not triple', variant: V, specs: null, current: 0, dice: ['X', 'X', 'II'] },
  { name: 'V blank four', variant: V, specs: [sold(0, 1, 9), sold(1, 2, 0, false)], dice: ['blank', 'III', 'II'] },
  { name: 'V push king', variant: V, specs: [sold(0, 1, 10), sold(1, 2, 0, false), S('king', null, 1, 7)], dice: ['III', 'II', 'II'] },
  { name: 'V ram', variant: V, specs: [sold(0, 1, 10), sold(1, 1, 6), sold(1, 2, 0, false), S('king', null, 1, 7)], dice: ['III', 'II', 'II'] },
  { name: 'V push onto own', variant: V, specs: [sold(0, 1, 10), sold(0, 1, 6), sold(1, 2, 0, false), S('king', null, 1, 7)], dice: ['III', 'II', 'II'] },
  { name: 'V knock-out', variant: V, opts: { kingKnockOut: true }, specs: [sold(0, 1, 10), sold(1, 2, 0, false), S('king', null, 1, 7)], dice: ['III', 'II', 'II'] },
  { name: 'V king jumps own', variant: V, specs: [sold(0, 1, 6), sold(0, 1, 5), sold(1, 2, 0, false), S('king', 0, 1, 7)], dice: ['X', 'II', 'III'] },
  { name: 'V single file', variant: V, specs: [sold(0, 1, 9), sold(0, 1, 8), sold(1, 2, 0, false)], dice: ['II', 'III', 'III'] },
  { name: 'V free soldiers jump', variant: V, opts: { jumpOwnSoldiers: true }, specs: [sold(0, 1, 9), sold(0, 1, 8), sold(1, 2, 0, false)], dice: ['II', 'III', 'III'] },
  { name: 'V sleeping capturable', variant: V, specs: [sold(0, 1, 9), sold(1, 1, 6, false), sold(1, 2, 0, false)], dice: ['III', 'II', 'II'] },
  { name: 'V king alone no pieces', variant: V, specs: [sold(0, 1, 9), sold(1, 1, 6), S('king', 1, 1, 2)], dice: ['III', 'II', 'II'] },
  { name: 'R opening', variant: R, specs: null, current: 0, dice: ['X', 'I'] },
  { name: 'R order III II', variant: R, specs: null, current: 0, dice: ['III', 'II'] },
  { name: 'R sleeping capturable', variant: R, specs: [sold(0, 1, 9), sold(1, 1, 6, false), sold(1, 2, 0, false)], dice: ['III', 'II'] },
  { name: 'R stack and king', variant: R, specs: [sold(0, 1, 9), sold(0, 1, 9), sold(1, 2, 0, false), S('king', null, 1, 6)], dice: ['III', 'III'] },
  { name: 'M opening', variant: M, specs: null, current: 0, dice: ['X', 'X'] },
  { name: 'M order free', variant: M, specs: null, current: 0, dice: ['III', 'I'] },
  { name: 'M gap activation', variant: M, specs: [sold(0, 0, 3, false), sold(0, 0, 8, false), sold(1, 2, 3, false)], dice: ['X', 'II'] },
  { name: 'U opening seat 0', variant: U, specs: null, current: 0, dice: ['X', 'II', 'III'] },
  { name: 'U opening seat 1', variant: U, specs: null, current: 1, dice: ['X', 'II', 'III'] },
  { name: 'U blank four', variant: U, opts: { blankValue: 4 }, specs: [sold(0, 1, 9), sold(1, 0, 5, false)], dice: ['blank', 'III', 'II'] },
  { name: 'U wake king', variant: U, specs: [sold(0, 1, 1), sold(1, 2, 3, false), S('king', null, 1, 7)], dice: ['II', 'II', 'II'] },
  { name: 'U dormant landing', variant: U, specs: [sold(0, 1, 9), sold(1, 2, 3, false), S('king', null, 1, 7)], dice: ['II', 'II', 'II'] },
  { name: 'U retake', variant: U, specs: [sold(0, 1, 9), sold(1, 1, 10), S('king', 0, 1, 7)], current: 1, dice: ['III', 'II', 'II'] },
  { name: 'U every time', variant: U, opts: { kingAcquire: 'unjarga-every' }, specs: [sold(0, 1, 1), sold(1, 2, 3, false), S('king', 1, 1, 7)], dice: ['II', 'II', 'II'] },
  { name: 'U knockout', variant: U, opts: { kingKnockOut: true }, specs: [sold(0, 1, 9), sold(1, 2, 3, false), S('king', 1, 1, 7)], dice: ['II', 'III', 'II'] },
  { name: 'U first-middle', variant: U, opts: { activation: 'first-middle' }, specs: null, current: 0, dice: ['X', 'II', 'III'] },
  { name: 'U figure-eight track', variant: U, opts: { track: 'figure-eight' }, specs: null, current: 0, equalOdds: true, dice: ['X', 'II', 'III'] },
  { name: 'U miedut equal odds', variant: U, specs: null, current: 0, miedut: true, equalOdds: true, dice: ['X', 'II', 'III'] },
  { name: 'U fixed order', variant: U, opts: { diceOrder: 'fixed', blankValue: 4 }, specs: null, current: 0, equalOdds: true, dice: ['II', 'blank', 'III'] },
  { name: 'U triple rethrow', variant: U, opts: { rethrow: 'triple' }, specs: null, current: 0, dice: ['X', 'X', 'X'] },
];

const scenarios: unknown[] = [];
for (const sc of scn) {
  const options = full(sc.variant, sc.opts);
  const starter = sc.starter ?? 0;
  const s0 = build(options, sc.specs, sc.current ?? 0, starter, !!sc.miedut, !!sc.equalOdds);
  const s = withDice(s0, sc.dice, !!sc.settle);
  const entry: Record<string, unknown> = {
    name: sc.name,
    variant: sc.variant,
    options,
    specs: sc.specs,
    current: sc.current ?? 0,
    starter,
    miedutRequested: !!sc.miedut,
    equalOdds: !!sc.equalOdds,
    dice: sc.dice,
    settle: !!sc.settle,
    start: snapshot(s),
    legal: s.phase === 'move' ? legalList(s) : [],
    candidates: s.phase === 'move' ? candList(s) : [],
  };
  // apply every legal move (non-rethrow) and record the result
  const results: unknown[] = [];
  if (s.phase === 'move') {
    for (const a of legalActions(s)) {
      if (a.type === 'rethrow' || a.type === 'rethrowAll') continue;
      const t = applyAction(s, a);
      results.push({ action: actionKey(a), after: snapshot(t), legalAfter: t.phase === 'over' ? [] : legalList(t) });
    }
  }
  entry.results = sortKeys(results.map((r) => [JSON.stringify((r as { action: unknown[] }).action), r])).map((x) => x[1]);
  scenarios.push(entry);
}
writeFileSync(`${out}/scenarios.json`, JSON.stringify(scenarios));

// ---------------------------------------------------------------- 3. scripted walks
function lcg(seed: number) {
  let a = seed >>> 0;
  return () => {
    a = (Math.imul(a, 1664525) + 1013904223) >>> 0;
    return a / 4294967296;
  };
}
const walks: unknown[] = [];
const configs: [string, Opt | undefined, Side, boolean, boolean][] = [
  [L, undefined, 0, false, false],
  [L, undefined, 1, false, true],
  [V, undefined, 0, false, false],
  [V, undefined, 1, true, true],
  [R, undefined, 0, false, false],
  [M, undefined, 1, false, true],
  [U, undefined, 0, false, false],
  [U, undefined, 1, true, true],
  [U, { diceOrder: 'fixed', blankValue: 4, kingAcquire: 'unjarga-every', stacking: 'single', jumpOwnSoldiers: false }, 0, false, false],
  [V, { kingKnockOut: true, jumpOwnSoldiers: true }, 0, false, true],
  [L, { kingAloneLoses: false, royalVerticalCrossing: false }, 1, false, false],
];
let wi = 0;
for (const [variant, opts, starter, miedut, equalOdds] of configs) {
  for (const seed of [11, 12]) {
    const options = full(variant, opts);
    let s = setup(options, starter, miedut, equalOdds);
    const rnd = lcg(seed * 100 + wi++);
    const steps: unknown[] = [];
    const start = snapshot({ ...s, phase: 'throw', dice: [] });
    for (let i = 0; i < 260 && s.phase !== 'over'; i++) {
      if (s.phase === 'throw') {
        const faces: Face[] = [];
        for (let k = 0; k < options.diceCount; k++) faces.push(options.faces[Math.floor(rnd() * options.faces.length)]);
        s = throwWith(s, faces);
        steps.push({ op: 'throw', faces, after: snapshot(s) });
        continue;
      }
      const legal = legalActions(s);
      const lkey = sortKeys(legal.map(actionKey));
      const moves = legal.filter((a) => a.type === 'move');
      const rethrows = legal.filter((a) => a.type !== 'move');
      let chosen: Action;
      if (rethrows.length && (moves.length === 0 || rnd() < 0.2)) {
        chosen = rethrows[Math.floor(rnd() * rethrows.length)];
        const nonX = options.faces.filter((f) => f !== 'X');
        const wanted: Face[] =
          chosen.type === 'rethrow' ? [nonX[Math.floor(rnd() * nonX.length)]] : Array.from({ length: options.diceCount }, () => nonX[Math.floor(rnd() * nonX.length)]);
        s = forceRethrow(s, chosen, wanted);
        steps.push({ op: 'rethrow', action: actionKey(chosen), faces: wanted, legal: lkey, after: snapshot(s) });
        continue;
      }
      const sorted = moves.slice().sort((a, b) => JSON.stringify(actionKey(a)).localeCompare(JSON.stringify(actionKey(b))));
      chosen = sorted[Math.floor(rnd() * sorted.length)];
      s = applyAction(s, chosen);
      steps.push({ op: 'move', action: actionKey(chosen), legal: lkey, after: snapshot(s) });
    }
    walks.push({ variant, options, starter, miedutRequested: miedut, equalOdds, start, steps });
  }
}
writeFileSync(`${out}/walks.json`, JSON.stringify(walks));

const summary = { setups: setups.length, scenarios: scenarios.length, walks: walks.length, steps: walks.reduce((n: number, w) => n + (w as { steps: unknown[] }).steps.length, 0) };
console.log(summary);
void legalMoves;
