"""Interactive rules walkthrough that follows the selected rule set."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from nicegui import ui

from ..engine import GameState, SeededDice
from ..i18n import t
from ..i18n.glossary import TERMS
from ..rules import Face, RuleSet
from ..settings import Settings
from .board import draw_scene
from .controller import GameController
from .play import PlayView
from .scenarios import Spec, guards, opening, scenario
from .scene import build_scene


@dataclass(frozen=True, slots=True)
class Step:
    title: str
    body: tuple[str, ...]
    state: Callable[[], GameState] | None = None
    hint: str | None = None
    show_track: bool = False
    static: bool = False


def build_steps(rules: RuleSet) -> list[Step]:
    o = rules.options
    unit = t("unit.squares" if o.board_style == "squares" else "unit.lines")
    mid = o.cols // 2
    terms = {k: v for k, v in TERMS.items()}
    steps: list[Step] = []

    p3 = t("tut.board.p3", **terms) + (" " + t("tut.board.queens", **terms) if o.queens else "")
    steps.append(
        Step(
            t("tut.board.title"),
            (
                t("tut.board.p1", cols=o.cols, unit=unit, **terms),
                t("tut.board.p2", soldiers_n=o.soldiers_per_side, **terms),
                p3,
            ),
            lambda: opening(o),
            static=True,
        )
    )

    faces = ", ".join("blank" if f == "blank" else f for f in o.faces)
    blank = (
        (t("tut.dice.blank0", **terms) if o.blank_value == 0 else t("tut.dice.blank4"))
        if "blank" in o.faces
        else t("tut.dice.noblank")
    )
    order = (
        t("tut.dice.fixed", order=", then ".join(str(k) for k in o.fixed_order))
        if o.dice_order == "fixed"
        else t("tut.dice.free")
    )
    steps.append(
        Step(
            t("tut.dice.title"),
            (
                t("tut.dice.p1", count=o.dice_count, faces=faces, **terms),
                blank,
                f"{t('tut.dice.separate')} {order}",
                t(f"tut.dice.rethrow.{o.rethrow}"),
                t(f"tut.dice.start.{o.start_rule}"),
            ),
            lambda: opening(o),
            static=True,
        )
    )

    def faces_for(*f: Face) -> list[Face]:
        return list(f)

    steps.append(
        Step(
            t("tut.activate.title"),
            (
                t(f"tut.activate.p1.{o.activation}", **terms),
                t(f"tut.activate.order.{o.activation_order}"),
                t("tut.activate.p3") + (" " + t("tut.activate.queen") if o.queens else ""),
            ),
            lambda: scenario(o, None, faces_for("X", "II", "II")),
            hint=t("tut.activate.hint"),
        )
    )

    track_body = [t(f"tut.track.{o.track}", **terms)]
    if o.allow_miedut:
        track_body.append(t("tut.track.miedut", **terms))
    track_body.append(t("tut.track.p3"))
    steps.append(
        Step(
            t("tut.track.title"),
            tuple(track_body),
            lambda: scenario(o, None, faces_for("III", "II", "II"), equal_odds=True),
            hint=t("tut.track.hint"),
            show_track=True,
        )
    )

    def capture_state() -> GameState:
        base = scenario(o, None, ["X"])
        start = o.cols - 3
        specs: list[Spec] = [
            ("soldier", 0, 1, start, True),
            ("soldier", 1, 1, start - 3, True),
            *guards(base),
            ("king", None, 1, mid, True),
        ]
        return scenario(o, specs, faces_for("III"))

    steps.append(
        Step(
            t("tut.capture.title"),
            (
                t("tut.capture.p1", **terms),
                t("tut.capture.sleeping.yes" if o.captures_inactive else "tut.capture.sleeping.no"),
                t(f"tut.capture.stack.{o.stacking}"),
            ),
            capture_state,
            hint=t("tut.capture.hint"),
        )
    )

    dormant = o.king_acquire != "landing"

    def king_state() -> GameState:
        base = scenario(o, None, ["X"])
        specs: list[Spec] = [
            ("soldier", 0, 1, 1 if dormant else mid + 3, True),
            *guards(base),
            ("king", None, 1, mid, True),
        ]
        return scenario(o, specs, faces_for("II" if dormant else "III"))

    king_p1 = "tut.king.p1.unjarga" if dormant else f"tut.king.p1.{o.king_mode}"
    steps.append(
        Step(
            t("tut.king.title", **terms),
            (
                t(king_p1),
                t(f"tut.king.move.{o.king_movement}"),
                t("tut.king.alone.yes" if o.king_alone_loses else "tut.king.alone.no"),
            ),
            king_state,
            hint=t("tut.king.hint.unjarga" if dormant else "tut.king.hint.landing"),
        )
    )

    if o.queens:
        steps.append(
            Step(
                t("tut.queen.title", **terms),
                (t("tut.queen.p1"), t("tut.queen.p2")),
                lambda: scenario(o, None, faces_for("X", "II", "II")),
                hint=t("tut.queen.hint"),
            )
        )

    steps.append(
        Step(
            t("tut.win.title"),
            (
                t("tut.win.queens" if o.queens else "tut.win.noqueens"),
                t("tut.win.alone.yes" if o.king_alone_loses else "tut.win.alone.no"),
                t("tut.win.stakes"),
            ),
            lambda: opening(o),
            static=True,
        )
    )
    return steps


class Tutorial:
    def __init__(self, rules: RuleSet, settings: Settings, on_done: Callable[[], None]) -> None:
        self.rules = rules
        self.settings = settings
        self.on_done = on_done
        self.index = 0
        self.nonce = 0

    def build(self) -> None:
        self.view()

    @ui.refreshable_method
    def view(self) -> None:
        steps = build_steps(self.rules)
        self.index = min(self.index, len(steps) - 1)
        step = steps[self.index]
        with ui.element("div").classes("sk-page"):
            ui.html(f"<h1>{t('tutorial.title')}</h1>", sanitize=False)
            ui.label(
                f"{t('tutorial.usingVariant')} {self.rules.name} · "
                f"{t('tutorial.step', n=self.index + 1, total=len(steps))}"
            ).classes("sk-small").mark("tutorial-step")
            ui.html(f"<h2>{step.title}</h2>", sanitize=False)
            for para in step.body:
                ui.label(para)
            if step.state:
                st = step.state()
                if step.static:
                    draw_scene(
                        build_scene(st, large=self.settings.large_touch),
                        lambda _p: None,
                        lambda _p, _k: None,
                        "spt-",
                    )
                else:
                    ctrl = GameController.from_state(
                        self.rules,
                        st,
                        SeededDice(self.index + 1),
                        self.index + 1,
                        "human",
                        0,
                        explain=True,
                        hint=step.hint,
                    )
                    PlayView(
                        ctrl,
                        self.settings,
                        compact=True,
                        show_track=step.show_track,
                        ai_delay=0,
                        marker_prefix="tut-",
                    ).build()
            with ui.row().classes("q-mt-md"):
                back = ui.button(t("tutorial.back"), on_click=lambda: self._go(-1)).props(
                    "no-caps outline"
                )
                back.set_enabled(self.index > 0)
                back.mark("tutorial-back")
                if not step.static:
                    ui.button(t("tutorial.reset"), on_click=self.view.refresh).props(
                        "no-caps outline"
                    )
                if self.index < len(steps) - 1:
                    ui.button(
                        t("tutorial.next"), on_click=lambda: self._go(1), color="primary"
                    ).props("no-caps").mark("tutorial-next")
                else:
                    ui.button(t("tutorial.done"), on_click=self.on_done, color="primary").props(
                        "no-caps"
                    ).mark("tutorial-done")

    def _go(self, d: int) -> None:
        self.index += d
        self.view.refresh()
