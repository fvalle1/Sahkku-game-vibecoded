"""Draw a ``Scene`` as real SVG elements with NiceGUI.

Each board point is a focusable ``<g role="button">`` with an ``aria-label``. Mouse and touch use
``click``; the keyboard uses Enter or Space to select and the arrow keys to move focus. The only
JavaScript is one ``focus()`` call (see ``focus_point``), documented in docs/decisions.md.
"""

from __future__ import annotations

from collections.abc import Callable

from nicegui import ui

from .scene import PieceNode, PointNode, Scene

_DEFS = (
    '<defs><marker id="sk-arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="5" '
    'markerHeight="5" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" '
    'fill="var(--sk-track)"/></marker></defs>'
)


def _svg_text(x: float, y: float, text: str, cls: str) -> None:
    ui.html(f'<text x="{x:g}" y="{y:g}" class="{cls}">{text}</text>', sanitize=False, tag="g")


def _piece(pc: PieceNode) -> None:
    side = "neutral" if pc.side is None else f"side{pc.side}"
    cls = (
        f"sk-piece {side} {pc.kind} {'active' if pc.active else 'asleep'}"
        + (" glow" if pc.glow else "")
        + (" selected" if pc.selected else "")
    )
    x, y, r = pc.x, pc.y, pc.r
    with ui.element("g").classes(cls):
        if pc.kind == "king":
            ui.element("path").props(
                f'd="M {x:g} {y - r - 2:g} L {x + r + 2:g} {y:g} L {x:g} {y + r + 2:g} L {x - r - 2:g} {y:g} Z"'
            )
            if pc.side is not None:
                ui.element("circle").props(f'cx="{x:g}" cy="{y:g}" r="{r * 0.4:g}"').classes(
                    f"inner own{pc.side}"
                )
        elif pc.side == 1:
            ui.element("path").props(
                f'd="M {x:g} {y - r:g} L {x + r:g} {y + r * 0.85:g} L {x - r:g} {y + r * 0.85:g} Z"'
            )
            if pc.kind == "queen":
                ui.element("circle").props(f'cx="{x:g}" cy="{y + 2:g}" r="{r * 0.45:g}"').classes(
                    "inner"
                )
        else:
            ui.element("circle").props(f'cx="{x:g}" cy="{y:g}" r="{r:g}"')
            if pc.kind == "queen":
                ui.element("circle").props(f'cx="{x:g}" cy="{y:g}" r="{r * 0.45:g}"').classes(
                    "inner"
                )


def _point(
    sc: Scene,
    pn: PointNode,
    on_point: Callable[[int], None],
    on_arrow: Callable[[int, str], None],
    marker_prefix: str = "pt-",
) -> None:
    cw = pn.cell_w
    row_h = 84
    cls = "sk-pt" + (f" dest-{pn.dest}" if pn.dest else "") + (" has-glow" if pn.glow else "")
    g = (
        ui.element("g")
        .props(
            f'data-pt="{pn.pt}" role="button" tabindex="{0 if pn.tabbable else -1}" '
            f'aria-label="{_attr(pn.label)}"'
        )
        .classes(cls)
        .mark(f"{marker_prefix}{pn.pt}")
    )
    g.on("click", lambda _e, p=pn.pt: on_point(p))
    for key in ("enter", "space"):
        g.on(f"keydown.{key}.prevent", lambda _e, p=pn.pt: on_point(p))
    for key in ("left", "right", "up", "down"):
        g.on(f"keydown.{key}.prevent", lambda _e, p=pn.pt, k=key: on_arrow(p, k))
    with g:
        ui.element("rect").props(
            f'x="{pn.x - cw / 2:g}" y="{pn.y - row_h / 2:g}" width="{cw:g}" height="{row_h}"'
        ).classes("sk-hit")
        if pn.castle:
            ui.element("circle").props(f'cx="{pn.x:g}" cy="{pn.y:g}" r="{cw * 0.42:g}"').classes(
                "sk-castle"
            )
        elif pn.marked:
            ui.element("circle").props(f'cx="{pn.x:g}" cy="{pn.y - 34:g}" r="3.5"').classes(
                "sk-mark"
            )
        if sc.board_style == "squares":
            ui.element("rect").props(
                f'x="{pn.x - cw / 2 + 5:g}" y="{pn.y - cw / 2 + 5:g}" width="{cw - 10:g}" '
                f'height="{cw - 10:g}" rx="4"'
            ).classes("sk-cell")
        else:
            ui.element("line").props(
                f'x1="{pn.x:g}" x2="{pn.x:g}" y1="{pn.y - 38:g}" y2="{pn.y + 38:g}"'
            ).classes("sk-cell-line")
        if pn.dest:
            ring_cls = {"ok": "sk-ring", "capture": "sk-ring capture", "blocked": "sk-ring no"}[
                pn.dest
            ]
            with ui.element("g").classes(ring_cls):
                ui.element("circle").props(f'cx="{pn.x:g}" cy="{pn.y:g}" r="{cw * 0.46:g}"')
                if pn.dest == "capture":
                    _svg_text(pn.x + cw * 0.3, pn.y - cw * 0.3, "×", "")
                elif pn.dest == "blocked":
                    _svg_text(pn.x + cw * 0.3, pn.y - cw * 0.3, "⊘", "")
        for pc in pn.pieces:
            _piece(pc)
        if len(pn.pieces) > 1:
            _svg_text(pn.x + 12, pn.y + 26, str(len(pn.pieces)), "sk-count")


def _attr(text: str) -> str:
    return text.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")


def draw_scene(
    sc: Scene,
    on_point: Callable[[int], None],
    on_arrow: Callable[[int, str], None],
    marker_prefix: str = "pt-",
) -> None:
    """Build the board inside the current NiceGUI container."""
    with ui.element("div").classes("sk-board-scroll"):
        style = f"min-width:{sc.min_width:g}px" if sc.min_width else ""
        with (
            ui.element("svg")
            .props(
                f'viewBox="0 0 {sc.width:g} {sc.height:g}" role="group" aria-label="{_attr(sc.title)}"'
            )
            .classes("sk-board")
            .style(style)
        ):
            ui.html(_DEFS, sanitize=False, tag="g")
            for r, cy in enumerate(sc.row_centres):
                ui.element("rect").props(
                    f'x="26" y="{cy - 42:g}" width="{sc.width - 52:g}" height="84" rx="10"'
                ).classes("sk-row-mid" if r == 1 else "sk-row-home")
            _svg_text(26, 20, _attr(sc.top_label), "sk-side-label")
            _svg_text(26, sc.height - 8, _attr(sc.bottom_label), "sk-side-label")
            for pn in sc.points:
                _point(sc, pn, on_point, on_arrow, marker_prefix)
            if sc.track:
                with ui.element("g").classes("sk-track").props('aria-hidden="true"'):
                    pts = " ".join(f"{x:g},{y:g}" for x, y in sc.track)
                    ui.element("polyline").props(
                        f'points="{pts}" marker-mid="url(#sk-arrow)" marker-end="url(#sk-arrow)"'
                    )
                    ui.element("circle").props(
                        f'cx="{sc.track[0][0]:g}" cy="{sc.track[0][1]:g}" r="5"'
                    )


def focus_point(pt: int) -> None:
    """Put keyboard focus on a board point (the one small piece of JavaScript in the app)."""
    ui.run_javascript(f"document.querySelector('[data-pt=\"{pt}\"]')?.focus()")
