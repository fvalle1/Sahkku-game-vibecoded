"""Static position evaluation used by every AI level."""

from __future__ import annotations

from ..engine import GameState, Side, next_index
from ..engine.game import face_value

WIN = 1_000_000.0


def _threats(s: GameState, side: Side) -> float:
    """How much of ``side``'s material an enemy soldier could hit with a single die."""
    o = s.options
    enemy: Side = 1 if side == 0 else 0
    track = s.tracks[enemy]
    values = sorted({face_value(o, f) for f in o.faces if face_value(o, f) > 0})
    mine: dict[int, int] = {}
    for p in s.pieces:
        if p.side != side or p.kind == "king":
            continue
        if not p.active and not o.captures_inactive:
            continue
        mine[p.pt] = mine.get(p.pt, 0) + (6 if p.kind == "queen" else 1)
    total = 0.0
    for p in s.pieces:
        if p.side != enemy or p.kind != "soldier" or not p.active:
            continue
        for v in values:
            i = p.pi
            for _ in range(v):
                i = next_index(track, i)
            total += mine.get(track.points[i], 0)
    return total


def evaluate(s: GameState, side: Side) -> float:
    """Evaluation from ``side``'s point of view (higher is better).

    Heuristics from the reconstructors' strategy notes: keep material, wake soldiers, hold the
    middle row, protect the queen (losing her loses the game), and own the king.
    """
    if s.phase == "over":
        return WIN if s.winner == side else -WIN
    n = s.options.cols
    score = 0.0
    for p in s.pieces:
        if p.kind == "king":
            if p.side == side:
                score += 8
            elif p.side is not None:
                score -= 8
            continue
        sign = 1 if p.side == side else -1
        if p.kind == "queen":
            score += sign * 40
            continue
        v = 10.0 + (3.0 if p.active else 0.0)
        if p.active and p.pt // n == 1:
            v += 0.6  # middle-row control
        score += sign * v
    enemy: Side = 1 if side == 0 else 0
    score -= _threats(s, side) * 1.5
    score += _threats(s, enemy) * 1.0
    return score
