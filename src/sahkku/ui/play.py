"""The play view: board, dice tray, controls, log and rules panel for one ``GameController``."""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import Awaitable, Callable
from html import escape

from nicegui import run, ui

from ..ai import Level, choose_action_job
from ..engine import Action, Side, col_of, pt_of, row_of
from ..i18n import t
from ..i18n.glossary import TERMS
from ..rules import RuleSet
from ..settings import Settings
from .board import draw_scene, focus_point
from .controller import GameController
from .format import face_text
from .rule_schema import FIELDS, value_string
from .scene import build_scene

AI_BUDGET_MS = {"easy": 50.0, "medium": 50.0, "hard": 1200.0}


def value_text(key: str, value: str) -> str:
    if value == "True":
        return t("common.yes")
    if value == "False":
        return t("common.no")
    k = f"val.{key}.{value}"
    s = t(k)
    return value if s == k else s


class PlayView:
    def _m(self, name: str) -> str:
        return f"{self.mp}{name}"

    def __init__(
        self,
        ctrl: GameController,
        settings: Settings,
        *,
        compact: bool = False,
        show_track: bool = False,
        on_new: Callable[[], None] | None = None,
        on_restart: Callable[[], None] | None = None,
        ai_delay: float = 0.6,
        marker_prefix: str = "",
    ) -> None:
        self.mp = marker_prefix
        self.ctrl = ctrl
        self.settings = settings
        self.compact = compact
        self.show_track = show_track
        self.on_new = on_new
        self.on_restart = on_restart
        self.ai_delay = ai_delay
        self._ai_busy = False
        self._focus: int | None = None
        self._cancel_event = asyncio.Event()

    # ------------------------------------------------------------------ building
    def build(self) -> None:
        self.panel()
        if self.ctrl.ai_turn:
            ui.timer(0.2, self.run_ai, once=True)

    def refresh(self) -> None:
        with contextlib.suppress(RuntimeError, KeyError):  # the page may have been closed
            self.panel.refresh()

    @ui.refreshable_method
    def panel(self) -> None:
        c = self.ctrl
        grid = "sk-game compact" if self.compact else "sk-game"
        with ui.element("div").classes(grid):
            with ui.element("div").style("min-width:0"):
                self._status()
                self._board()
                self._guide()
            with ui.element("div").style("min-width:0"):
                self._controls()
                if c.state.dice:
                    self._dice()
                self._thinking()
                if c.over:
                    self._stakes()
                if not self.compact:
                    self._log()
                    self._rules()
        if self._focus is not None:
            focus_point(self._focus)
            self._focus = None

    # ------------------------------------------------------------------ parts
    def _status(self) -> None:
        c = self.ctrl
        with (
            ui.element("div").props('aria-live="polite"').style("min-height:28px;margin-bottom:4px")
        ):
            ui.html(
                f"<strong>{escape(c.status_text())}</strong> "
                f'<span class="sk-small"> · {escape(c.king_text())}</span>',
                sanitize=False,
            ).mark(self._m("status"))

    def _board(self) -> None:
        c = self.ctrl
        track = c.state.tracks[0] if self.show_track else None
        sc = build_scene(
            c.state,
            dests=c.dests if c.human_turn else {},
            movable=c.movable if c.human_turn else set(),
            selected_piece=c.sel_piece,
            track=track,
            large=self.settings.large_touch,
        )
        draw_scene(sc, self._on_point, self._on_arrow, self.mp + "pt-")

    def _guide(self) -> None:
        c = self.ctrl
        with ui.element("div").classes("sk-guide").props('aria-live="polite"'):
            if c.fate_prompt:
                ui.label(t("game.chooseFate"))
                with ui.row():
                    for cand in c.fate_prompt:
                        fate = cand.fate or "take"
                        ui.button(
                            t(f"game.fate.{fate}"), on_click=lambda _e, f=fate: self._fate(f)
                        ).props("no-caps outline")
            else:
                ui.label(c.guide_text()).mark(self._m("guide"))

    def _controls(self) -> None:
        c = self.ctrl
        with ui.element("div").classes("sk-controls"):
            if c.state.phase == "throw" and c.human_turn:
                ui.button(
                    f"{t('game.throw')} ({TERMS['dice']})", on_click=self._throw, color="primary"
                ).props("no-caps").mark(self._m("throw"))
            if not self.compact:
                ui.button(t("game.new"), on_click=lambda: self.on_new and self.on_new()).props(
                    "no-caps outline"
                ).mark(self._m("new-game"))
                ui.button(
                    t("game.restart"), on_click=lambda: self.on_restart and self.on_restart()
                ).props("no-caps outline").mark(self._m("restart"))
                undo = (
                    ui.button(t("game.undo"), on_click=self._undo)
                    .props("no-caps outline")
                    .mark(self._m("undo"))
                )
                undo.set_enabled(c.can_undo)
                if c.is_ai:
                    undo.tooltip(t("game.undoUnavailable"))
                ui.button(t("game.copyRecord"), on_click=self._show_record).props(
                    "no-caps outline"
                ).mark(self._m("copy-record"))

    def _dice(self) -> None:
        c = self.ctrl
        o = c.state.options
        order = (
            t("dice.order.fixed", order=" → ".join(str(k) for k in o.fixed_order))
            if o.dice_order == "fixed"
            else t("dice.order.free")
        )
        with ui.element("section").classes("sk-panel").props(f'aria-label="{t("dice.title")}"'):
            ui.html(
                f'<h2>{t("dice.title")} <span class="sk-term">{TERMS["dice"]}</span></h2>',
                sanitize=False,
            )
            ui.label(order).classes("sk-small")
            with ui.element("div").classes("sk-dice").props('role="list"'):
                for i, d in enumerate(c.state.dice):
                    self._die(i, d.face)
            if c.can_rethrow_all:
                ui.button(t("game.rethrowAll"), on_click=self._rethrow_all).props("no-caps outline")

    def _die(self, i: int, face: str) -> None:
        c = self.ctrl
        o = c.state.options
        status = c.die_status(i)
        value = (
            o.blank_value
            if face == "blank"
            else ("" if face == "X" else {"I": 1, "II": 2, "III": 3}[face])
        )
        if face == "blank":
            note = t("die.blank0") if o.blank_value == 0 else t("die.blank4")
        elif status == "ready":
            note = t("die.x") if face == "X" else t("die.ready")
        else:
            note = t(f"die.{status}")
        selected = c.die == i and c.human_turn
        cls = (
            f"sk-die {status}"
            + (" sel" if selected else "")
            + (" roll" if self.settings.dice_anim else "")
        )
        with ui.element("div").classes("sk-die-wrap").props('role="listitem"'):
            btn = (
                ui.button(on_click=lambda _e, k=i: self._pick_die(k))
                .props("flat no-caps")
                .classes(cls)
            )
            btn.props(
                f'aria-label="{face_text(face) if face != "blank" else "blank"}, {note}" aria-pressed="{str(selected).lower()}"'
            )
            btn.mark(self._m(f"die-{i}"))
            with btn:
                ui.label(face_text(face))
                ui.label(str(value)).classes("val")
            btn.set_enabled(c.human_turn and status == "ready")
            if c.human_turn and c.can_rethrow(i):
                ui.button(t("game.rethrow"), on_click=lambda _e, k=i: self._rethrow(k)).props(
                    "flat no-caps dense"
                ).classes("sk-link").mark(self._m(f"rethrow-{i}"))
            if face == "blank" and o.blank_value == 0:
                ui.label(t("die.blank0")).classes("sk-small")
            elif status != "ready":
                ui.label(t(f"die.{status}")).classes("sk-small")

    def _thinking(self) -> None:
        c = self.ctrl
        if not c.thinking:
            return
        with ui.row().classes("items-center"):
            ui.spinner(size="sm")
            ui.label(t("game.aiThinking")).props('role="status"')
            if c.opponent == "hard":
                ui.button(t("game.cancelThinking"), on_click=self._cancel).props(
                    "no-caps outline dense"
                ).mark(self._m("cancel-ai"))

    def _stakes(self) -> None:
        c = self.ctrl
        with ui.element("section").classes("sk-panel"):
            ui.html(f"<h2>{t('game.stakes')}</h2>", sanitize=False)
            box = ui.number(t("game.stakes.value"), value=1, min=0, step=1, precision=0)
            result = ui.label()

            def upd() -> None:
                v = int(box.value or 0)
                result.set_text(
                    f"{t('game.stakes.result', n=c.stake_remaining(), v=v)} = {c.stake_remaining() * v}"
                )

            box.on_value_change(upd)
            upd()

    def _log(self) -> None:
        c = self.ctrl
        with ui.element("section").classes("sk-panel").props(f'aria-label="{t("log.title")}"'):
            ui.html(
                f'<h2>{t("log.title")} <span class="sk-small">({t("game.logNewestFirst")})</span></h2>',
                sanitize=False,
            )
            with (
                ui.element("ol")
                .classes("sk-loglist")
                .props(f'role="log" aria-live="polite" tabindex="0" aria-label="{t("log.title")}"')
                .mark(self._m("log"))
            ):
                if not c.log:
                    ui.html(
                        f"<span class='sk-small'>{t('log.empty')}</span>", sanitize=False, tag="li"
                    )
                for line in reversed(c.log[-80:]):
                    ui.html(escape(line), sanitize=False, tag="li")
            with ui.expansion(t("game.positionText")).classes("w-full"):
                ui.html(escape(c.position_text()).replace("\n", "<br>"), sanitize=False).mark(
                    self._m("position-text")
                )

    def _rules(self) -> None:
        rules: RuleSet = self.ctrl.rules
        o = self.ctrl.state.options
        with ui.element("section").classes("sk-panel").props(f'aria-label="{t("rules.title")}"'):  # noqa: SIM117
            with ui.expansion(t("rules.title")).classes("w-full").mark(self._m("rules-panel")):
                ui.html(
                    f'<span class="sk-badge">{escape(rules.name)}</span>'
                    f'<span class="sk-badge">{t("status." + rules.status)}</span>',
                    sanitize=False,
                )
                ui.label(t("rules.unofficial")).classes("sk-small")
                ui.label(rules.reconstruction_note).classes("sk-small")
                ui.label(f"{t('rules.credit')}: {rules.credit}").classes("sk-small")
                s = self.ctrl.state
                if s.start_log:
                    thr = " · ".join(
                        f"{t(f'side.{x.side}')}: {' '.join(map(face_text, x.faces))}"
                        for x in s.start_log
                    )
                    ui.label(f"{t('rules.start')}: {thr}").classes("sk-small")
                for f in FIELDS:
                    if f.key in ("extra_marks", "board_style"):
                        continue
                    unc = rules.uncertain.get(f.key)
                    with ui.element("div").classes("sk-rule-row"):
                        with ui.element("div"):
                            ui.html(
                                f"<strong>{t('opt.' + f.key)}</strong>"
                                + (
                                    f' <span class="sk-badge warn" title="{escape(unc)}">{t("rules.uncertain")}</span>'
                                    if unc
                                    else ""
                                ),
                                sanitize=False,
                            )
                        with ui.element("div"):
                            ui.label(value_text(f.key, value_string(o, f.key)))
                            if unc:
                                ui.label(unc).classes("sk-small")
                            help_key = f"help.{f.key}"
                            if t(help_key) != help_key:
                                ui.label(t(help_key)).classes("sk-small")
                ui.label(t("help.dice_application")).classes("sk-small")
                ui.label(t("help.faces")).classes("sk-small")

    # ------------------------------------------------------------------ events
    async def _after(self, focus: int | None = None) -> None:
        self._focus = focus
        self.refresh()
        if self.ctrl.ai_turn:
            await self.run_ai()

    async def _on_point(self, pt: int) -> None:
        self.ctrl.click_point(pt)
        await self._after(pt if self.ctrl.sel_piece is not None else None)

    def _on_arrow(self, pt: int, key: str) -> None:
        n = self.ctrl.state.options.cols
        r, c = row_of(n, pt), col_of(n, pt)
        dr, dc = {"left": (0, -1), "right": (0, 1), "up": (1, 0), "down": (-1, 0)}[key]
        nr, nc = r + dr, c + dc
        if 0 <= nr < 3 and 0 <= nc < n:
            focus_point(pt_of(n, nr, nc))

    async def _throw(self) -> None:
        self.ctrl.throw()
        await self._after()

    async def _pick_die(self, i: int) -> None:
        self.ctrl.select_die(i)
        await self._after()

    async def _rethrow(self, i: int) -> None:
        self.ctrl.rethrow(i)
        await self._after()

    async def _rethrow_all(self) -> None:
        self.ctrl.rethrow_all()
        await self._after()

    async def _fate(self, fate: str) -> None:
        self.ctrl.choose_fate(fate)
        await self._after()

    async def _undo(self) -> None:
        self.ctrl.undo()
        await self._after()

    def _cancel(self) -> None:
        self.ctrl.cancel_requested = True
        self._cancel_event.set()

    def _show_record(self) -> None:
        record = self.ctrl.game_record()
        with ui.dialog() as dlg, ui.card().classes("w-full").style("max-width:760px"):
            ui.label(t("game.copyTitle")).classes("text-h6")
            ui.textarea(value=record).props("readonly outlined autogrow").classes("w-full").mark(
                self._m("record-text")
            )
            with ui.row():

                async def copy() -> None:
                    ui.clipboard.write(record)
                    ui.notify(t("game.recordCopied"))

                ui.button(t("game.copy"), on_click=copy).props("no-caps").mark(
                    self._m("record-copy")
                )
                ui.button(
                    t("game.saveFile"),
                    on_click=lambda: ui.download.content(record.encode("utf-8"), "sahkku-game.txt"),
                ).props("no-caps outline")
                ui.button(t("game.close"), on_click=dlg.close).props("no-caps flat")
        dlg.open()

    # ------------------------------------------------------------------ computer player
    async def _compute(self) -> Action:
        c = self.ctrl
        level: Level = c.opponent  # type: ignore[assignment]
        budget = AI_BUDGET_MS[level]
        if c.state.phase == "throw" or level != "hard":
            return c.ai_choice(level, budget)
        seed = c._ai_rng.getrandbits(32)
        self._cancel_event.clear()
        s = c.state
        try:
            fut: Awaitable[Action] = run.cpu_bound(choose_action_job, s, level, seed, budget)
        except Exception:
            fut = asyncio.to_thread(c.ai_choice, level, budget)
        task = asyncio.ensure_future(fut)
        cancel = asyncio.ensure_future(self._cancel_event.wait())
        try:
            done, _ = await asyncio.wait({task, cancel}, return_when=asyncio.FIRST_COMPLETED)
            if task in done and task.exception() is None:
                return task.result()
        except Exception:
            pass
        finally:
            cancel.cancel()
        task.cancel()
        return c.ai_choice("medium", 0)  # cancelled (or failed): play a quick move instead

    async def run_ai(self) -> None:
        if self._ai_busy:
            return
        self._ai_busy = True
        c = self.ctrl
        try:
            while c.ai_turn:
                c.thinking = True
                c.cancel_requested = False
                self.refresh()
                await asyncio.sleep(self.ai_delay)
                action = await self._compute()
                c.apply_ai(action)
                self.refresh()
        finally:
            c.thinking = False
            self._ai_busy = False
            self.refresh()


__all__ = ["PlayView", "Side", "value_text"]
