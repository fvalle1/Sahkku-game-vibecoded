"""Shared helpers for replaying the TypeScript-derived parity fixtures."""

from __future__ import annotations

import json
import re
from dataclasses import replace
from pathlib import Path
from typing import Any

from sahkku.engine import (
    Action,
    Die,
    GameState,
    MoveAction,
    Piece,
    Rethrow,
    RethrowAll,
    Throw,
    candidates_for,
    legal_actions,
    new_game,
    pt_of,
)
from sahkku.rules import RuleOptions

FIXTURES = Path(__file__).parent / "fixtures"


def load(name: str) -> Any:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def snake(name: str) -> str:
    return re.sub(r"([A-Z])", lambda m: "_" + m.group(1).lower(), name)


def options_from_ts(d: dict[str, Any]) -> RuleOptions:
    return RuleOptions.from_mapping({snake(k): v for k, v in d.items()})


def canon(x: Any) -> str:
    return json.dumps(x, sort_keys=True, separators=(",", ":"))


def snapshot(s: GameState) -> dict[str, Any]:
    return {
        "current": s.current,
        "phase": s.phase,
        "winner": s.winner,
        "winReason": s.win_reason,
        "dice": [[d.face, int(d.used)] for d in s.dice],
        "pieces": [
            [p.id, p.kind, p.side, int(p.active), p.pt, p.pi]
            for p in sorted(s.pieces, key=lambda p: p.id)
        ],
    }


def action_key(a: Action) -> list[Any]:
    if isinstance(a, MoveAction):
        return ["move", a.die, a.piece_id, a.to, a.fate]
    if isinstance(a, Rethrow):
        return ["rethrow", a.die, None, None, None]
    if isinstance(a, RethrowAll):
        return ["rethrowAll", None, None, None, None]
    assert isinstance(a, Throw)
    return ["throw", None, None, None, None]


def action_from_key(k: list[Any]) -> Action:
    if k[0] == "move":
        return MoveAction(k[1], k[2], k[3], k[4])
    if k[0] == "rethrow":
        return Rethrow(k[1])
    if k[0] == "rethrowAll":
        return RethrowAll()
    return Throw()


def legal_keys(s: GameState) -> list[str]:
    return sorted(canon(action_key(a)) for a in legal_actions(s))


def cand_rows(s: GameState) -> dict[str, list[str]]:
    faces = list(dict.fromkeys(d.face for d in s.dice))
    rows: dict[str, list[str]] = {}
    for p in s.pieces:
        if p.side != s.current:
            continue
        for f in faces:
            cs = []
            for c in candidates_for(s, p.id, f):
                king = c.out.king
                cs.append(
                    canon(
                        [
                            c.to,
                            int(c.ok),
                            c.reason,
                            c.fate,
                            c.new_pi,
                            sorted(c.out.captures),
                            [king.side, king.pt, king.kind] if king else None,
                        ]
                    )
                )
            rows[f"{p.id}/{f}"] = sorted(cs)
    return rows


def fixture_cands(rows: list[Any]) -> dict[str, list[str]]:
    return {f"{pid}/{f}": sorted(canon(c) for c in cs) for pid, f, cs in rows}


def _index(seq: tuple[int, ...], x: int) -> int:
    """JavaScript ``indexOf`` semantics (-1 when absent), as the fixtures were generated with it."""
    return seq.index(x) if x in seq else -1


def build(
    options: RuleOptions,
    specs: list[dict[str, Any]] | None,
    current: int,
    starter: int,
    miedut: bool,
    equal_odds: bool,
) -> GameState:
    g = new_game(options, starter=starter, miedut=miedut, equal_odds=equal_odds)
    if specs is None:
        return replace(g, current=current, phase="throw", dice=(), events=())
    n = options.cols
    pieces: list[Piece] = []
    for pid, sp in enumerate(specs):
        pt = pt_of(n, sp["at"][0], sp["at"][1])
        pi = -1
        if sp["kind"] == "soldier":
            if sp.get("active", True) is False:
                pi = _index(g.home_slots[sp["side"]], pt)
            else:
                pi = _index(g.tracks[sp["side"]].points, pt)
        pieces.append(Piece(pid, sp["kind"], sp["side"], sp.get("active", True), pt, pi))
    return replace(g, pieces=tuple(pieces), current=current, phase="throw", dice=(), events=())


def hold_dice(s: GameState, faces: list[str]) -> GameState:
    o = s.options
    dice = tuple(Die(f, f == "blank" and o.blank_value == 0) for f in faces)  # type: ignore[arg-type]
    return replace(s, phase="move", dice=dice)
