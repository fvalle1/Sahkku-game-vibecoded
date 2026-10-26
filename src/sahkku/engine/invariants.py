"""Consistency checks used by property tests and the self-play harness."""

from __future__ import annotations

from collections import defaultdict

from .types import GameState, Piece


def check_invariants(s: GameState) -> list[str]:
    """Return a list of violated invariants (empty = the state is consistent)."""
    bad: list[str] = []
    o = s.options
    ids: set[int] = set()
    by_pt: dict[int, list[Piece]] = defaultdict(list)
    for p in s.pieces:
        if p.id in ids:
            bad.append(f"duplicate id {p.id}")
        ids.add(p.id)
        if not 0 <= p.pt < o.cols * 3:
            bad.append(f"piece {p.id} off board")
        by_pt[p.pt].append(p)
    for pt, ps in by_pt.items():
        sides = {p.side for p in ps if p.side is not None}
        if len(sides) > 1:
            bad.append(f"enemy pieces share point {pt}")
        non_king = [p for p in ps if p.kind != "king"]
        if o.stacking == "single" and len(non_king) > 1:
            bad.append(f"stacked pieces at {pt} in single mode")
        if not o.royals_share_with_own:
            for r in ps:
                if r.kind == "queen" and any(
                    m.id != r.id and m.side == r.side and m.kind != "king" for m in ps
                ):
                    bad.append(f"queen shares with own piece at {pt}")
    if sum(1 for p in s.pieces if p.kind == "king") > 1:
        bad.append("more than one king")
    for side in (0, 1):
        if sum(1 for p in s.pieces if p.kind == "soldier" and p.side == side) > o.soldiers_per_side:
            bad.append("too many soldiers")
        if sum(1 for p in s.pieces if p.kind == "queen" and p.side == side) > 1:
            bad.append("too many queens")
    if s.phase == "move" and not s.dice:
        bad.append("move phase without dice")
    return bad
