"""Tracks, the king graph and board geometry, all as data."""

from __future__ import annotations

from ..rules import RuleOptions
from .types import Track, Transform

ROWS = 3


def row_of(n: int, pt: int) -> int:
    return pt // n


def col_of(n: int, pt: int) -> int:
    return pt % n


def pt_of(n: int, row: int, col: int) -> int:
    return row * n + col


def xf_point(n: int, xf: Transform, pt: int) -> int:
    r, c = row_of(n, pt), col_of(n, pt)
    if xf == "id":
        return pt
    if xf == "rot":
        return pt_of(n, ROWS - 1 - r, n - 1 - c)
    if xf == "rowflip":
        return pt_of(n, ROWS - 1 - r, c)
    return pt_of(n, r, n - 1 - c)  # colflip


def _seq(a: int, b: int) -> list[int]:
    return list(range(a, b + 1)) if a <= b else list(range(a, b - 1, -1))


def base_track(kind: str, n: int) -> Track:
    """The track for seat 0 in its own frame (home row 0, moving to increasing columns first)."""
    home = [pt_of(n, 0, c) for c in _seq(0, n - 1)]
    mid = [pt_of(n, 1, c) for c in _seq(n - 1, 0)]
    far = [pt_of(n, 2, c) for c in _seq(0, n - 1)]
    if kind == "loop":
        return Track(tuple(home + mid + far), n)
    if kind == "loop-from-middle":
        return Track(tuple(mid + far), 0)
    if kind == "figure-eight":
        return Track(tuple(home + mid + far + mid), 0)
    raise ValueError(f"unknown track kind {kind!r}")


def figure_eight(n: int) -> tuple[int, ...]:
    """The closed figure-eight used by king and queen movement."""
    return base_track("figure-eight", n).points


def transform_track(n: int, t: Track, xf: Transform) -> Track:
    return Track(tuple(xf_point(n, xf, p) for p in t.points), t.loop_start)


def base_home_slots(n: int, count: int) -> tuple[int, ...]:
    return tuple(pt_of(n, 0, c) for c in range(count))


def next_index(t: Track, i: int) -> int:
    return i + 1 if i + 1 < len(t.points) else t.loop_start


def indices_of(t: Track, pt: int) -> list[int]:
    return [i for i, p in enumerate(t.points) if p == pt]


def royal_destinations(
    n: int,
    fig: tuple[int, ...],
    movement: str,
    own_track: Track | None,
    pt: int,
    v: int,
    vertical: bool = True,
) -> list[int]:
    """Points reachable by a king or queen with a die worth ``v``, ignoring occupancy."""
    out: set[int] = set()
    if movement == "figure-eight":
        ln = len(fig)
        for i, p in enumerate(fig):
            if p != pt:
                continue
            out.add(fig[(i + v) % ln])
            out.add(fig[(i - v) % ln])
        r, c = row_of(n, pt), col_of(n, pt)
        if not vertical:
            pass  # only bends
        elif v == 1:
            if r > 0:
                out.add(pt_of(n, r - 1, c))
            if r < ROWS - 1:
                out.add(pt_of(n, r + 1, c))
        elif v == 2:
            if r == 0:
                out.add(pt_of(n, 2, c))
            if r == 2:
                out.add(pt_of(n, 0, c))
    elif own_track is not None:
        for i in indices_of(own_track, pt):
            j = i
            for _ in range(v):
                j = next_index(own_track, j)
            out.add(own_track.points[j])
    out.discard(pt)
    return sorted(out)


def track_for(options: RuleOptions, n: int | None = None) -> Track:
    return base_track(options.track, n if n is not None else options.cols)
