"""Turn engine events and positions into plain English text (via the i18n layer)."""

from __future__ import annotations

from ..engine import (
    GameState,
    MoveEvent,
    RethrowEvent,
    StartEvent,
    ThrowEvent,
    TurnEndEvent,
    TurnLostEvent,
    WinEvent,
    col_of,
    row_of,
)
from ..engine.types import Event
from ..i18n import t
from ..i18n.glossary import TERMS
from ..rules import Face, RuleOptions


def face_text(f: Face) -> str:
    return "–" if f == "blank" else f


def side_name(side: int | None) -> str:
    if side is None:
        return t("king.owner.none")
    return f"{t(f'side.{side}')} ({TERMS['men'] if side == 0 else TERMS['women']})"


def row_name(row: int) -> str:
    return t(("row.near", "row.middle", "row.far")[row])


def pt_name(o: RuleOptions, pt: int) -> str:
    r, c = row_of(o.cols, pt), col_of(o.cols, pt)
    unit = t("unit.squares" if o.board_style == "squares" else "unit.lines")
    return f"{row_name(r)} {unit} {c + 1}"


def describe_event(o: RuleOptions, e: Event) -> str | None:
    if isinstance(e, StartEvent):
        return t("log.start", side=side_name(e.starter))
    if isinstance(e, ThrowEvent):
        return t("log.throw", side=t(f"side.{e.side}"), faces=" ".join(map(face_text, e.faces)))
    if isinstance(e, RethrowEvent):
        return t("log.rethrow", side=t(f"side.{e.side}"), faces=" ".join(map(face_text, e.faces)))
    if isinstance(e, MoveEvent):
        base = t(
            "log.activate" if e.activated else "log.move",
            side=t(f"side.{e.side}"),
            piece=t(f"piece.{e.piece}"),
            **{"from": pt_name(o, e.from_pt)},
            to=pt_name(o, e.to_pt),
        )
        extra: list[str] = []
        if e.captured:
            what = ", ".join(dict.fromkeys(t(f"piece.{k}") for k in e.captured))
            extra.append(t("log.capture", n=len(e.captured), what=what))
        if e.king:
            extra.append(t(f"log.king.{e.king}"))
        return " · ".join([base, *extra])
    if isinstance(e, TurnLostEvent):
        return t(f"log.turnLost.{e.reason}", side=t(f"side.{e.side}"))
    if isinstance(e, WinEvent):
        return t("log.win", side=side_name(e.winner))
    if isinstance(e, TurnEndEvent):
        return None
    return None


def win_text(s: GameState) -> str:
    if s.winner is None or s.win_reason is None:
        return ""
    loser = 1 if s.winner == 0 else 0
    return (
        f"{t('game.over', side=side_name(s.winner))} "
        f"{t(f'game.overReason.{s.win_reason}', loser=t(f'side.{loser}'))}"
    )


def piece_text(kind: str, side: int | None, active: bool) -> str:
    if kind == "king":
        return t("piece.neutralKing") if side is None else f"{t(f'side.{side}')} {t('piece.king')}"
    who = f"{t(f'side.{side}')} {t(f'piece.{kind}')}"
    return f"{who}, {t('piece.awake' if active else 'piece.asleep')}"


def describe_position(s: GameState) -> str:
    """A text alternative of the whole position, top row first, runs of equal pieces merged."""
    o = s.options
    n = o.cols
    unit = t("unit.squares" if o.board_style == "squares" else "unit.lines")
    by_pt: dict[int, list[str]] = {}
    for p in s.pieces:
        by_pt.setdefault(p.pt, []).append(piece_text(p.kind, p.side, p.active))
    lines = [t("game.describeIntro")]
    for row in (2, 1, 0):
        runs: list[tuple[int, int, str]] = []
        for c in range(n):
            desc = "; ".join(by_pt.get(row * n + c, []))
            if not desc:
                continue
            if runs and runs[-1][2] == desc and runs[-1][1] == c - 1:
                runs[-1] = (runs[-1][0], c, desc)
            else:
                runs.append((c, c, desc))
        if runs:
            parts = [
                (f"{unit} {a + 1}" if a == b else f"{unit}s {a + 1}-{b + 1}")
                + f": {d}"
                + (f" ×{b - a + 1}" if a != b else "")
                for a, b, d in runs
            ]
            lines.append(f"{row_name(row).capitalize()}: " + "; ".join(parts) + ".")
        else:
            lines.append(f"{row_name(row).capitalize()}: {t('board.empty')}.")
    return "\n".join(lines)
