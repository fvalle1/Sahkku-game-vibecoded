import type { RuleOptions, Track, Transform } from './types';

export const ROWS = 3;

export const rowOf = (n: number, pt: number) => Math.floor(pt / n);
export const colOf = (n: number, pt: number) => pt % n;
export const ptOf = (n: number, row: number, col: number) => row * n + col;

export function xfPoint(n: number, xf: Transform, pt: number): number {
  const r = rowOf(n, pt);
  const c = colOf(n, pt);
  switch (xf) {
    case 'id':
      return pt;
    case 'rot':
      return ptOf(n, ROWS - 1 - r, n - 1 - c);
    case 'rowflip':
      return ptOf(n, ROWS - 1 - r, c);
    case 'colflip':
      return ptOf(n, r, n - 1 - c);
  }
}

const seq = (a: number, b: number): number[] => {
  const out: number[] = [];
  if (a <= b) for (let i = a; i <= b; i++) out.push(i);
  else for (let i = a; i >= b; i--) out.push(i);
  return out;
};

/** Track for side 0 in its own frame (home row 0, moving right = increasing column first). */
export function baseTrack(kind: RuleOptions['track'], n: number): Track {
  const home = seq(0, n - 1).map((c) => ptOf(n, 0, c));
  const mid = seq(n - 1, 0).map((c) => ptOf(n, 1, c));
  const far = seq(0, n - 1).map((c) => ptOf(n, 2, c));
  switch (kind) {
    case 'loop':
      return { points: [...home, ...mid, ...far], loopStart: n };
    case 'loop-from-middle':
      return { points: [...mid, ...far], loopStart: 0 };
    case 'figure-eight':
      return { points: [...home, ...mid, ...far, ...mid], loopStart: 0 };
  }
}

/** The closed figure-eight used by king/queen movement, in side 0's frame. */
export function figureEight(n: number): number[] {
  return baseTrack('figure-eight', n).points;
}

export function transformTrack(n: number, t: Track, xf: Transform): Track {
  return { points: t.points.map((p) => xfPoint(n, xf, p)), loopStart: t.loopStart };
}

export function baseHomeSlots(n: number, count: number): number[] {
  return seq(0, count - 1).map((c) => ptOf(n, 0, c));
}

export function nextIndex(t: Track, i: number): number {
  return i + 1 < t.points.length ? i + 1 : t.loopStart;
}

export function indicesOf(t: Track, pt: number): number[] {
  const out: number[] = [];
  t.points.forEach((p, i) => {
    if (p === pt) out.push(i);
  });
  return out;
}

/** Points reachable by a king/queen with a die worth `v`, ignoring occupancy. */
export function royalDestinations(
  n: number,
  fig: number[],
  movement: RuleOptions['kingMovement'],
  ownTrack: Track | null,
  pt: number,
  v: number,
  vertical = true,
): number[] {
  const out = new Set<number>();
  if (movement === 'figure-eight') {
    const len = fig.length;
    fig.forEach((p, i) => {
      if (p !== pt) return;
      out.add(fig[(i + v) % len]);
      out.add(fig[(((i - v) % len) + len) % len]);
    });
    const r = rowOf(n, pt);
    const c = colOf(n, pt);
    if (!vertical) {
      // bends only
    } else if (v === 1) {
      if (r > 0) out.add(ptOf(n, r - 1, c));
      if (r < ROWS - 1) out.add(ptOf(n, r + 1, c));
    } else if (v === 2) {
      if (r === 0) out.add(ptOf(n, 2, c));
      if (r === 2) out.add(ptOf(n, 0, c));
    }
  } else if (ownTrack) {
    for (const i of indicesOf(ownTrack, pt)) {
      let j = i;
      for (let k = 0; k < v; k++) j = nextIndex(ownTrack, j);
      out.add(ownTrack.points[j]);
    }
  }
  out.delete(pt);
  return [...out];
}
