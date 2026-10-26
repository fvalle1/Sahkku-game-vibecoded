"""Small builders for hand-made positions."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from sahkku.engine import Die, GameState, Piece, new_game, pt_of, throw_with
from sahkku.rules import Face, RuleOptions


def S(kind: str, side: int | None, row: int, col: int, active: bool = True) -> tuple[Any, ...]:
    return (kind, side, row, col, active)


def sold(side: int, row: int, col: int, active: bool = True) -> tuple[Any, ...]:
    return S("soldier", side, row, col, active)


def scenario(
    options: RuleOptions,
    specs: list[tuple[Any, ...]] | None,
    *,
    current: int = 0,
    dice: list[Face] | None = None,
    hold: bool = False,
    starter: int = 0,
    miedut: bool = False,
    equal_odds: bool = False,
) -> GameState:
    """A game with a hand-built position. ``hold`` keeps the dice without ending a stuck turn."""
    g = new_game(options, starter=starter, miedut=miedut, equal_odds=equal_odds)
    n = options.cols
    if specs is not None:
        pieces: list[Piece] = []
        for pid, (kind, side, r, c, active) in enumerate(specs):
            pt = pt_of(n, r, c)
            pi = -1
            if kind == "soldier":
                if active:
                    pts = g.tracks[side].points
                    pi = pts.index(pt) if pt in pts else -1
                else:
                    slots = g.home_slots[side]
                    pi = slots.index(pt) if pt in slots else -1
            pieces.append(Piece(pid, kind, side, active, pt, pi))
        g = replace(g, pieces=tuple(pieces))
    g = replace(g, current=current, phase="throw", dice=(), events=())
    if dice is None:
        return g
    if hold:
        return replace(
            g,
            phase="move",
            dice=tuple(Die(f, f == "blank" and options.blank_value == 0) for f in dice),
        )
    return throw_with(g, dice)


def P(o: RuleOptions, row: int, col: int) -> int:
    return pt_of(o.cols, row, col)
