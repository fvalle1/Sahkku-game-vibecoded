"""The board as plain data (geometry, labels, states), independent of any UI toolkit.

``build_scene`` is the single source of truth for the SVG: the NiceGUI layer draws it as real
SVG elements, and ``Scene.to_svg()`` renders the same scene to a standalone SVG string (used by
tests and handy for documentation). Points are listed in keyboard focus order: along the track of
the player to move.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from html import escape
from typing import Literal

from ..engine import GameState, Piece, Track, col_of, pt_of, row_of
from ..i18n import t
from ..i18n.glossary import TERMS
from .format import piece_text, row_name

PAD_X = 34
PAD_Y = 30
ROW_H = 92

DestKind = Literal["ok", "capture", "blocked"]


@dataclass(frozen=True, slots=True)
class PieceNode:
    id: int
    kind: str
    side: int | None
    active: bool
    glow: bool
    selected: bool
    x: float
    y: float
    r: float


@dataclass(frozen=True, slots=True)
class PointNode:
    pt: int
    row: int
    col: int
    x: float
    y: float
    cell_w: float
    label: str
    castle: bool
    marked: bool
    dest: DestKind | None
    tabbable: bool
    glow: bool
    pieces: tuple[PieceNode, ...]


@dataclass(frozen=True, slots=True)
class Scene:
    width: float
    height: float
    cols: int
    board_style: str
    title: str
    top_label: str
    bottom_label: str
    row_centres: tuple[float, float, float]
    points: tuple[PointNode, ...]
    track: tuple[tuple[float, float], ...] | None = None
    min_width: float | None = None
    extras: dict[str, str] = field(default_factory=dict)

    def to_svg(self) -> str:
        """A standalone SVG rendering of the scene (neutral colours, no scripts)."""
        out = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.width:g} {self.height:g}" '
            f'role="group" aria-label="{escape(self.title)}">'
        ]
        for pn in self.points:
            out.append(f'<g data-pt="{pn.pt}" role="button" aria-label="{escape(pn.label)}">')
            out.append(f"<title>{escape(pn.label)}</title>")
            if self.board_style == "squares":
                out.append(
                    f'<rect x="{pn.x - pn.cell_w / 2 + 5:g}" y="{pn.y - pn.cell_w / 2 + 5:g}" '
                    f'width="{pn.cell_w - 10:g}" height="{pn.cell_w - 10:g}" fill="none" stroke="#8b7a5e"/>'
                )
            else:
                out.append(
                    f'<line x1="{pn.x:g}" x2="{pn.x:g}" y1="{pn.y - 38:g}" y2="{pn.y + 38:g}" stroke="#8b7a5e"/>'
                )
            for pc in pn.pieces:
                fill = "none" if not pc.active else ("#3b2f24" if pc.side == 0 else "#f6f0e4")
                out.append(
                    f'<circle cx="{pc.x:g}" cy="{pc.y:g}" r="{pc.r:g}" fill="{fill}" stroke="#3b2f24"/>'
                )
            out.append("</g>")
        out.append("</svg>")
        return "\n".join(out)


def focus_order(state: GameState) -> list[int]:
    """All points, along the track of the player to move first, then the rest by row and column."""
    o = state.options
    seen: list[int] = []
    track = state.tracks[state.current]
    for p in track.points:
        if p not in seen:
            seen.append(p)
    for p in range(o.cols * 3):
        if p not in seen:
            seen.append(p)
    return seen


def build_scene(
    state: GameState,
    *,
    dests: dict[int, DestKind] | None = None,
    movable: set[int] | None = None,
    selected_piece: int | None = None,
    track: Track | None = None,
    large: bool = False,
) -> Scene:
    o = state.options
    n = o.cols
    dests = dests or {}
    movable = movable or set()
    cw = 58.0 if large else 48.0
    width = PAD_X * 2 + n * cw
    height = PAD_Y * 2 + 3 * ROW_H
    mid = n // 2
    marks: set[int] = set()
    if o.extra_marks:
        marks = {o.queen_mark_index, n - 1 - o.queen_mark_index}
    unit = t("unit.squares" if o.board_style == "squares" else "unit.lines")

    def cx(col: int) -> float:
        return PAD_X + (col + 0.5) * cw

    def cy(row: int) -> float:
        return PAD_Y + (2 - row + 0.5) * ROW_H

    by_pt: dict[int, list[Piece]] = {}
    for p in state.pieces:
        by_pt.setdefault(p.pt, []).append(p)

    points: list[PointNode] = []
    for pt in focus_order(state):
        r, c = row_of(n, pt), col_of(n, pt)
        here = by_pt.get(pt, [])
        parts = [f"{row_name(r)}, {unit} {c + 1} / {n}"]
        castle = r == 1 and c == mid
        if castle:
            parts.append(t("pt.castle"))
        parts.extend(piece_text(p.kind, p.side, p.active) for p in here)
        d = dests.get(pt)
        if d == "ok":
            parts.append(t("board.destOk"))
        elif d == "capture":
            parts.append(t("board.destCapture"))
        elif d == "blocked":
            parts.append(t("board.destBlocked"))
        nodes = tuple(
            PieceNode(
                p.id,
                p.kind,
                p.side,
                p.active,
                p.id in movable,
                p.id == selected_piece,
                cx(c),
                cy(r) - min(i, 3) * 7 + min(len(here) - 1, 3) * 3.5,
                (13 if p.kind == "soldier" else 16) * (0.92 if cw < 50 else 1),
            )
            for i, p in enumerate(here)
        )
        tabbable = d in ("ok", "capture") or any(p.id in movable for p in here)
        points.append(
            PointNode(
                pt,
                r,
                c,
                cx(c),
                cy(r),
                cw,
                "; ".join(parts),
                castle,
                r == 1 and c in marks and not castle,
                d,
                tabbable,
                any(p.glow for p in nodes),
                nodes,
            )
        )
    track_pts: tuple[tuple[float, float], ...] | None = None
    if track is not None:
        seen: dict[int, int] = {}
        pts: list[tuple[float, float]] = []
        for p in track.points:
            k = seen.get(p, 0)
            seen[p] = k + 1
            pts.append((cx(col_of(n, p)) + k * 7, cy(row_of(n, p)) + k * 7))
        track_pts = tuple(pts)
    return Scene(
        width=width,
        height=height,
        cols=n,
        board_style=o.board_style,
        title=t("board.label", n=n, unit=unit + "s"),
        top_label=f"{t('side.1')} · {TERMS['women']}",
        bottom_label=f"{t('side.0')} · {TERMS['men']}",
        row_centres=(cy(0), cy(1), cy(2)),
        points=tuple(points),
        track=track_pts,
        min_width=width if large else None,
    )


__all__ = ["DestKind", "PieceNode", "PointNode", "Scene", "build_scene", "focus_order", "pt_of"]
