import { nextRandom } from './rng';
import {
  baseHomeSlots,
  baseTrack,
  colOf,
  figureEight,
  indicesOf,
  nextIndex,
  ptOf,
  rowOf,
  royalDestinations,
  transformTrack,
  xfPoint,
} from './tracks';
import type {
  Action,
  Die,
  Face,
  GameEvent,
  GameState,
  NewGameOptions,
  OrderKey,
  Piece,
  PieceKind,
  RuleOptions,
  Side,
  Transform,
} from './types';

export const other = (s: Side): Side => (s === 0 ? 1 : 0);

// ---------------------------------------------------------------- dice

export function faceValue(o: RuleOptions, f: Face): number {
  switch (f) {
    case 'X':
    case 'I':
      return 1;
    case 'II':
      return 2;
    case 'III':
      return 3;
    case 'blank':
      return o.blankValue;
  }
}

export const orderKey = (o: RuleOptions, f: Face): OrderKey => (f === 'X' ? 'X' : faceValue(o, f));

function rollFaces(o: RuleOptions, rng: number): [Face[], number] {
  const faces: Face[] = [];
  for (let i = 0; i < o.diceCount; i++) {
    const [r, n] = nextRandom(rng);
    rng = n;
    faces.push(o.faces[Math.floor(r * o.faces.length)]);
  }
  return [faces, rng];
}

function toDice(o: RuleOptions, faces: Face[]): Die[] {
  // A blank worth 0 is "no move": it is spent immediately.
  return faces.map((face) => ({ face, used: face === 'blank' && o.blankValue === 0 }));
}

// ---------------------------------------------------------------- setup

export function newGame(options: RuleOptions, g: NewGameOptions): GameState {
  const o = options;
  let rng = g.seed >>> 0;
  const startLog: { side: Side; faces: Face[] }[] = [];

  const [r0, n0] = nextRandom(rng);
  rng = n0;
  const first: Side = r0 < 0.5 ? 0 : 1;
  let starter: Side = first;
  for (let guard = 0; guard < 1000; guard++) {
    const order: Side[] = [first, other(first)];
    const counts: number[] = [0, 0];
    let decided = false;
    for (const side of order) {
      let faces: Face[];
      [faces, rng] = rollFaces(o, rng);
      startLog.push({ side, faces });
      counts[side] = faces.filter((f) => f === 'X').length;
      if (o.startRule === 'first-x' && counts[side] > 0) {
        starter = side;
        decided = true;
        break;
      }
    }
    if (decided) break;
    if (o.startRule === 'most-x' && counts[0] !== counts[1]) {
      starter = counts[0] > counts[1] ? 0 : 1;
      break;
    }
  }

  const miedut = !!g.miedut && o.allowMiedut && !o.queens;
  const transforms: [Transform, Transform] =
    starter === 0 ? ['id', miedut ? 'rowflip' : 'rot'] : [miedut ? 'colflip' : 'id', 'rot'];

  const n = o.cols;
  const bt = baseTrack(o.track, n);
  const tracks = [
    transformTrack(n, bt, transforms[0]),
    transformTrack(n, bt, transforms[1]),
  ] as GameState['tracks'];
  const bh = baseHomeSlots(n, o.soldiersPerSide);
  const homeSlots = [
    bh.map((p) => xfPoint(n, transforms[0], p)),
    bh.map((p) => xfPoint(n, transforms[1], p)),
  ] as GameState['homeSlots'];

  const pieces: Piece[] = [];
  let id = 0;
  for (const side of [0, 1] as Side[]) {
    for (let j = 0; j < o.soldiersPerSide; j++) {
      const frontThree = j >= o.soldiersPerSide - 3;
      const active = !!g.equalOdds && frontThree;
      let pt = homeSlots[side][j];
      let pi = j;
      if (active && o.activation !== 'step') {
        let col = colOf(n, pt);
        // With mieđut both sides would otherwise stand on the same middle-row points.
        if (pieces.some((q) => q.pt === ptOf(n, 1, col))) col = n - 1 - col;
        pt = ptOf(n, 1, col);
        pi = indicesOf(tracks[side], pt)[0];
      }
      pieces.push({ id: id++, kind: 'soldier', side, active, pt, pi });
    }
    if (o.queens) {
      const baseCol = o.queenStart === 'right' ? n - 1 - o.queenMarkIndex : o.queenMarkIndex;
      const pt = xfPoint(n, side === 0 ? 'id' : 'rot', ptOf(n, 1, baseCol));
      pieces.push({ id: id++, kind: 'queen', side, active: false, pt, pi: -1 });
    }
  }
  pieces.push({
    id,
    kind: 'king',
    side: null,
    active: true,
    pt: ptOf(n, 1, Math.floor(n / 2)),
    pi: -1,
  });

  return {
    options: o,
    tracks,
    homeSlots,
    transforms,
    pieces,
    current: starter,
    phase: 'throw',
    dice: [],
    winner: null,
    winReason: null,
    rng,
    turnNumber: 1,
    miedut,
    equalOdds: !!g.equalOdds,
    startLog,
    events: [{ type: 'start', starter, log: startLog }],
  };
}

// ---------------------------------------------------------------- movement generation

export interface KingChange {
  side: Side | null;
  pt: number;
  removed?: boolean;
  kind: 'taken' | 'pushed' | 'removed';
}
export interface Outcome {
  captures: number[];
  king?: KingChange;
}
export interface Cand {
  pieceId: number;
  to: number;
  ok: boolean;
  /** Reason code when !ok. */
  reason?: string;
  fate?: 'take' | 'remove';
  newPi: number;
  out: Outcome;
}
export interface Move extends Cand {
  die: number;
  face: Face;
}

const fail = (pieceId: number, to: number, reason: string): Cand => ({
  pieceId,
  to,
  ok: false,
  reason,
  newPi: -1,
  out: { captures: [] },
});

const getKing = (s: GameState) => s.pieces.find((p) => p.kind === 'king');
const isDormant = (s: GameState) => {
  const k = getKing(s);
  return !!k && k.side === null && s.options.kingAcquire !== 'landing';
};
const enemyHomeRow = (side: Side) => (side === 0 ? 2 : 0);

/** Evaluate a piece landing on `pt`. Returns one candidate per choice (two with king knock-out). */
function evalLanding(s: GameState, mover: Piece, pt: number, newPi: number): Cand[] {
  const o = s.options;
  const me = mover.side as Side;
  const occ = s.pieces.filter((p) => p.pt === pt && p.id !== mover.id);
  const king = occ.find((p) => p.kind === 'king');
  const others = occ.filter((p) => p.kind !== 'king');
  const own = others.filter((p) => p.side === me);
  const enemy = others.filter((p) => p.side !== me);
  const isRoyal = mover.kind !== 'soldier';

  // Where sleeping pieces are protected, nobody may land on them (not even their owner).
  if (own.some((p) => !p.active) && !o.capturesInactive)
    return [fail(mover.id, pt, 'own-sleeping')];
  if (enemy.some((p) => !p.active) && !o.capturesInactive)
    return [fail(mover.id, pt, 'enemy-sleeping')];
  if (own.length > 0) {
    if (o.stacking === 'single') return [fail(mover.id, pt, 'own-piece-here')];
    if (isRoyal && !o.royalsShareWithOwn) return [fail(mover.id, pt, 'royal-no-share')];
    if (own.some((p) => p.kind === 'queen') && !o.royalsShareWithOwn)
      return [fail(mover.id, pt, 'queen-no-share')];
  }
  if (king && isDormant(s)) return [fail(mover.id, pt, 'king-dormant')];
  if (king && king.side === me) {
    if (o.stacking === 'single') return [fail(mover.id, pt, 'own-piece-here')];
    if (!o.royalsShareWithOwn) return [fail(mover.id, pt, 'royal-no-share')];
  }

  const captures = enemy.map((p) => p.id);
  const base: Cand = { pieceId: mover.id, to: pt, ok: true, newPi, out: { captures } };

  if (king && king.side !== me && !isDormant(s)) {
    const track = s.tracks[me];
    if (o.kingMode === 'recruit') {
      const take: Cand = {
        ...base,
        fate: o.kingKnockOut ? 'take' : undefined,
        out: { captures, king: { side: me, pt: king.pt, kind: 'taken' } },
      };
      if (!o.kingKnockOut) return [take];
      const rem: Cand = {
        ...base,
        fate: 'remove',
        out: { captures, king: { side: null, pt: king.pt, removed: true, kind: 'removed' } },
      };
      return [take, rem];
    }
    // push: the king is driven one line forward along the lander's track
    if (newPi < 0) return [fail(mover.id, pt, 'cannot-push')];
    const dest = track.points[nextIndex(track, newPi)];
    const there = s.pieces.filter((p) => p.pt === dest && p.id !== mover.id && p.kind !== 'king');
    if (there.some((p) => p.side === me)) return [fail(mover.id, pt, 'cannot-push-onto-own')];
    if (there.some((p) => !p.active) && !o.capturesInactive)
      return [fail(mover.id, pt, 'enemy-sleeping')];
    const caps = [...captures, ...there.map((p) => p.id)];
    const push: Cand = {
      ...base,
      fate: o.kingKnockOut ? 'take' : undefined,
      out: { captures: caps, king: { side: me, pt: dest, kind: 'pushed' } },
    };
    if (!o.kingKnockOut) return [push];
    const rem: Cand = {
      ...base,
      fate: 'remove',
      out: { captures, king: { side: null, pt: king.pt, removed: true, kind: 'removed' } },
    };
    return [push, rem];
  }

  const theKing = getKing(s);
  if (
    theKing &&
    mover.kind === 'soldier' &&
    o.kingAcquire !== 'landing' &&
    rowOf(o.cols, pt) === enemyHomeRow(me)
  ) {
    if (isDormant(s) || (o.kingAcquire === 'unjarga-every' && theKing.side !== me)) {
      return [{ ...base, out: { captures, king: { side: me, pt: theKing.pt, kind: 'taken' } } }];
    }
  }
  return [base];
}

function soldierCands(s: GameState, p: Piece, face: Face): Cand[] {
  const o = s.options;
  const side = p.side as Side;
  const track = s.tracks[side];
  const v = faceValue(o, face);
  if (!p.active) {
    if (face !== 'X') return [];
    if (o.activationOrder === 'front-first') {
      const frontSlot = Math.max(
        ...s.pieces
          .filter((q) => q.kind === 'soldier' && q.side === side && !q.active)
          .map((q) => q.pi),
      );
      if (p.pi !== frontSlot) {
        const dest = activationTarget(s, p);
        return [fail(p.id, dest.pt, 'not-front')];
      }
    }
    const dest = activationTarget(s, p);
    return evalLanding(s, p, dest.pt, dest.pi).map((c) => ({ ...c, newPi: dest.pi }));
  }
  if (v <= 0) return [];
  let idx = p.pi;
  let blocked = false;
  for (let k = 1; k <= v; k++) {
    idx = nextIndex(track, idx);
    if (
      k < v &&
      !o.jumpOwnSoldiers &&
      s.pieces.some((q) => q.pt === track.points[idx] && q.side === side && q.id !== p.id)
    ) {
      blocked = true;
    }
  }
  if (blocked) return [fail(p.id, track.points[idx], 'cannot-jump-own')];
  return evalLanding(s, p, track.points[idx], idx).map((c) => ({ ...c, newPi: idx }));
}

function activationTarget(s: GameState, p: Piece): { pt: number; pi: number } {
  const o = s.options;
  const side = p.side as Side;
  const track = s.tracks[side];
  if (o.activation === 'first-middle') {
    return { pt: track.points[0], pi: 0 };
  }
  if (o.activation === 'up') {
    const pt = ptOf(o.cols, 1, colOf(o.cols, p.pt));
    return { pt, pi: indicesOf(track, pt)[0] };
  }
  const pi = nextIndex(track, p.pi);
  return { pt: track.points[pi], pi };
}

function royalCands(s: GameState, p: Piece, face: Face): Cand[] {
  const o = s.options;
  const side = p.side;
  if (side === null) return [];
  const v = faceValue(o, face);
  if (v <= 0) return [];
  if (!p.active) {
    if (face !== 'X') return [];
  }
  const dests = royalDestinations(
    o.cols,
    figureEight(o.cols),
    o.kingMovement,
    s.tracks[side],
    p.pt,
    v,
    o.royalVerticalCrossing,
  );
  const res: Cand[] = [];
  for (const d of dests) res.push(...evalLanding(s, p, d, -1));
  return res;
}

export function candidatesFor(s: GameState, pieceId: number, face: Face): Cand[] {
  const p = s.pieces.find((q) => q.id === pieceId);
  if (!p || p.side !== s.current) return [];
  return p.kind === 'soldier' ? soldierCands(s, p, face) : royalCands(s, p, face);
}

// ---------------------------------------------------------------- legal actions

/** Indices of dice that may be played now (one representative per distinct face). */
export function playableDiceIndices(s: GameState): number[] {
  const o = s.options;
  const unused = s.dice.map((d, i) => ({ d, i })).filter((x) => !x.d.used);
  let pool = unused;
  if (o.diceOrder === 'fixed' && unused.length) {
    const rank = (f: Face) => {
      const k = orderKey(o, f);
      const idx = o.fixedOrder.indexOf(k);
      return idx < 0 ? 999 : idx;
    };
    const best = Math.min(...unused.map((x) => rank(x.d.face)));
    pool = unused.filter((x) => rank(x.d.face) === best);
  }
  const seen = new Set<Face>();
  const out: number[] = [];
  for (const x of pool) {
    if (!seen.has(x.d.face)) {
      seen.add(x.d.face);
      out.push(x.i);
    }
  }
  return out;
}

export function legalMoves(s: GameState): Move[] {
  if (s.phase !== 'move') return [];
  const moves: Move[] = [];
  for (const di of playableDiceIndices(s)) {
    const face = s.dice[di].face;
    for (const p of s.pieces) {
      if (p.side !== s.current) continue;
      for (const c of candidatesFor(s, p.id, face)) if (c.ok) moves.push({ ...c, die: di, face });
    }
  }
  return moves;
}

export function legalActions(s: GameState): Action[] {
  if (s.phase === 'over') return [];
  if (s.phase === 'throw') return [{ type: 'throw' }];
  const acts: Action[] = legalMoves(s).map((m) => ({
    type: 'move',
    die: m.die,
    pieceId: m.pieceId,
    to: m.to,
    fate: m.fate,
  }));
  const o = s.options;
  for (const di of playableDiceIndices(s)) {
    if (o.rethrow === 'single' && s.dice[di].face === 'X') acts.push({ type: 'rethrow', die: di });
  }
  if (
    o.rethrow === 'triple' &&
    s.dice.length > 1 &&
    s.dice.every((d) => !d.used && d.face === 'X')
  ) {
    acts.push({ type: 'rethrowAll' });
  }
  return acts;
}

/** Why a die cannot be played right now (for the UI). */
export function dieStatus(s: GameState, di: number): 'ready' | 'used' | 'out-of-order' | 'no-move' {
  const d = s.dice[di];
  if (!d || d.used) return 'used';
  const playable = playableDiceIndices(s);
  const sameFace = playable.some((i) => s.dice[i].face === d.face);
  if (!sameFace) return 'out-of-order';
  const has =
    legalMoves(s).some((m) => s.dice[m.die].face === d.face) ||
    (s.options.rethrow === 'single' && d.face === 'X');
  return has ? 'ready' : 'no-move';
}

// ---------------------------------------------------------------- apply

function checkWin(s: GameState): { winner: Side; reason: 'no-soldiers' | 'queen-captured' } | null {
  const o = s.options;
  const king = getKing(s);
  for (const side of [other(s.current), s.current] as Side[]) {
    if (o.queens && !s.pieces.some((p) => p.kind === 'queen' && p.side === side)) {
      return { winner: other(side), reason: 'queen-captured' };
    }
    const soldiers = s.pieces.some((p) => p.kind === 'soldier' && p.side === side);
    if (!soldiers && (o.kingAloneLoses || !king || king.side !== side)) {
      return { winner: other(side), reason: 'no-soldiers' };
    }
  }
  return null;
}

function endTurn(s: GameState, events: GameEvent[]): GameState {
  events.push({ type: 'turn-end', side: s.current });
  return {
    ...s,
    current: other(s.current),
    phase: 'throw',
    dice: [],
    turnNumber: s.turnNumber + 1,
  };
}

/** After any action: end the turn if nothing more can be played. */
function settle(s: GameState, events: GameEvent[]): GameState {
  if (s.phase !== 'move') return s;
  if (s.dice.every((d) => d.used)) return endTurn(s, events);
  if (legalActions(s).length === 0) {
    const fixedBlocked = s.options.diceOrder === 'fixed' && s.dice.some((d) => !d.used);
    events.push({
      type: 'turn-lost',
      side: s.current,
      reason: fixedBlocked ? 'fixed-order-blocked' : 'no-legal-move',
    });
    return endTurn(s, events);
  }
  return s;
}

/** Deterministically set the dice for the player to move (used by tests, tutorials and AI search). */
export function throwWith(s: GameState, faces: Face[]): GameState {
  if (s.phase !== 'throw') throw new Error('Not in throw phase');
  const events: GameEvent[] = [{ type: 'throw', side: s.current, faces }];
  const next: GameState = { ...s, phase: 'move', dice: toDice(s.options, faces) };
  const settled = settle(next, events);
  return { ...settled, events };
}

export function applyAction(s: GameState, a: Action): GameState {
  if (s.phase === 'over') throw new Error('Game is over');
  const o = s.options;
  const events: GameEvent[] = [];

  if (a.type === 'throw') {
    if (s.phase !== 'throw') throw new Error('Cannot throw now');
    const [faces, rng] = rollFaces(o, s.rng);
    const r = throwWith({ ...s, rng }, faces);
    return r;
  }
  if (s.phase !== 'move') throw new Error('Throw the dice first');

  if (a.type === 'rethrow') {
    const d = s.dice[a.die];
    if (o.rethrow !== 'single' || !d || d.used || d.face !== 'X')
      throw new Error('Illegal re-throw');
    if (!playableDiceIndices(s).includes(a.die)) throw new Error('Illegal re-throw (order)');
    let rng = s.rng;
    let face: Face = 'X';
    for (let g = 0; g < 1000 && face === 'X'; g++) {
      const [r, n] = nextRandom(rng);
      rng = n;
      face = o.faces[Math.floor(r * o.faces.length)];
    }
    const dice = s.dice.map((x, i) => (i === a.die ? toDice(o, [face])[0] : x));
    events.push({ type: 'rethrow', side: s.current, faces: [face], all: false });
    return finish(settle({ ...s, rng, dice }, events), events);
  }
  if (a.type === 'rethrowAll') {
    if (!legalActions(s).some((x) => x.type === 'rethrowAll'))
      throw new Error('Illegal re-throw of all dice');
    const [faces, rng] = rollFaces(o, s.rng);
    events.push({ type: 'rethrow', side: s.current, faces, all: true });
    return finish(settle({ ...s, rng, dice: toDice(o, faces) }, events), events);
  }

  const faceOf = s.dice[a.die]?.face;
  const mv = legalMoves(s).find(
    (m) => m.face === faceOf && m.pieceId === a.pieceId && m.to === a.to && m.fate === a.fate,
  );
  if (!mv) throw new Error('Illegal move');

  const mover = s.pieces.find((p) => p.id === mv.pieceId)!;
  const removed = new Set(mv.out.captures);
  const captured: PieceKind[] = s.pieces.filter((p) => removed.has(p.id)).map((p) => p.kind);
  let pieces = s.pieces
    .filter((p) => !removed.has(p.id))
    .map((p) =>
      p.id === mover.id
        ? { ...p, pt: mv.to, active: true, pi: mover.kind === 'soldier' ? mv.newPi : -1 }
        : p,
    );
  const kc = mv.out.king;
  if (kc) {
    pieces = kc.removed
      ? pieces.filter((p) => p.kind !== 'king')
      : pieces.map((p) => (p.kind === 'king' ? { ...p, side: kc.side, pt: kc.pt } : p));
  }
  const dice = s.dice.map((d, i) => (i === mv.die ? { ...d, used: true } : d));
  events.push({
    type: 'move',
    side: s.current,
    piece: mover.kind,
    pieceId: mover.id,
    from: mover.pt,
    to: mv.to,
    face: mv.face,
    activated: !mover.active,
    captured,
    king: kc?.kind,
  });
  let next: GameState = { ...s, pieces, dice };
  const win = checkWin(next);
  if (win) {
    events.push({ type: 'win', winner: win.winner, reason: win.reason });
    next = { ...next, phase: 'over', winner: win.winner, winReason: win.reason };
    return { ...next, events };
  }
  return finish(settle(next, events), events);
}

function finish(s: GameState, events: GameEvent[]): GameState {
  return { ...s, events };
}

export function stateKey(s: GameState): string {
  return (
    `${s.current}${s.phase[0]}|` +
    s.dice.map((d) => d.face[0] + (d.used ? 'u' : '')).join('') +
    '|' +
    s.pieces.map((p) => `${p.id}:${p.pt}:${p.side}:${p.active ? 1 : 0}:${p.pi}`).join(',')
  );
}
