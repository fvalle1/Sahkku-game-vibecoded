"""Hand-built teaching positions for the tutorial. Side 0 is to play with the dice already set."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from ..engine import Die, GameState, Piece, SeededDice, indices_of, new_game, pt_of, start_game
from ..rules import Face, RuleOptions

Spec = tuple[str, int | None, int, int, bool]  # kind, side, row, col, active


def scenario(
    o: RuleOptions, specs: list[Spec] | None, faces: list[Face], equal_odds: bool = False
) -> GameState:
    g = new_game(o, starter=0, equal_odds=equal_odds)
    s = replace(g, current=0, phase="throw", dice=(), events=(), start_log=())
    if specs is not None:
        n = o.cols
        pieces: list[Piece] = []
        for pid, (kind, side, row, col, active) in enumerate(specs):
            pt = pt_of(n, row, col)
            pi = -1
            if kind == "soldier":
                assert side is not None
                if active:
                    idx = indices_of(s.tracks[side], pt)
                    pi = idx[0] if idx else -1
                else:
                    slots = s.home_slots[side]
                    pi = slots.index(pt) if pt in slots else -1
            pieces.append(Piece(pid, kind, side, active, pt, pi))  # type: ignore[arg-type]
        s = replace(s, pieces=tuple(pieces))
    fs = tuple((faces + [faces[-1]] * o.dice_count)[: o.dice_count])
    # Hold the dice without ending a stuck turn: these are exercises, not real turns.
    return replace(
        s, phase="move", dice=tuple(Die(f, f == "blank" and o.blank_value == 0) for f in fs)
    )


def guards(s: GameState) -> list[Spec]:
    """Sleeping guards so nobody has lost mid-exercise, plus queens when in play."""
    n = s.options.cols
    out: list[Spec] = []
    for side in (0, 1):
        pt = s.home_slots[side][0]
        out.append(("soldier", side, pt // n, pt % n, False))
        if s.options.queens:
            q = next(p for p in s.pieces if p.kind == "queen" and p.side == side)
            out.append(("queen", side, q.pt // n, q.pt % n, False))
    return out


def opening(o: RuleOptions) -> GameState:
    return start_game(o, SeededDice(5))


__all__: list[Any] = ["Spec", "guards", "opening", "scenario"]
