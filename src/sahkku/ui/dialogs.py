"""Dialogs: new game (with the Custom rules editor), settings, and the first-run notice."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from nicegui import ui

from ..engine import Side
from ..i18n import t
from ..rules import VARIANTS, RuleOptions, RuleSet, get_variant
from ..settings import Settings
from .play import value_text
from .rule_schema import FIELDS, set_field, value_string

OPPONENTS = ("human", "easy", "medium", "hard")


@dataclass(slots=True)
class GameConfig:
    rules: RuleSet
    opponent: str
    human_side: Side
    seed: int
    equal_odds: bool
    miedut: bool


def new_game_dialog(
    settings: Settings,
    on_start: Callable[[GameConfig], None],
    default_seed: int | None = None,
) -> ui.dialog:
    """Build (and return, unopened) the new-game dialog."""
    custom: dict[str, Any] = {"o": _custom_options(settings)}
    state: dict[str, Any] = {
        "variant": settings.variant_id,
        "opponent": settings.opponent,
        "side": settings.human_side,
        "equal": settings.equal_odds,
        "miedut": False,
        "seed": "" if default_seed is None else str(default_seed),
    }

    def current_rules() -> RuleSet:
        base = get_variant(state["variant"])
        if base.id == "custom":
            return RuleSet(
                base.id,
                base.name,
                base.region,
                base.status,
                base.reconstruction_note,
                base.credit,
                base.uncertain,
                custom["o"],
            )
        return base

    with (
        ui.dialog().props("persistent=false") as dlg,
        ui.card().classes("w-full").style("max-width:600px;max-height:90vh;overflow:auto"),
    ):
        ui.label(t("new.title")).classes("text-h6")
        ui.select(
            {v.id: v.name for v in VARIANTS},
            value=state["variant"],
            label=t("new.variant"),
            on_change=lambda e: (state.update(variant=e.value), body.refresh()),
        ).classes("w-full").mark("variant-select")

        @ui.refreshable
        def body() -> None:
            rs = current_rules()
            o = rs.options
            with ui.element("div").classes("sk-panel"):
                ui.html(f"<strong>{rs.region}</strong>", sanitize=False)
                ui.html(
                    f'<span class="sk-badge {"warn" if rs.status != "documented" else ""}">{t("status." + rs.status)}</span>',
                    sanitize=False,
                )
                ui.label(rs.reconstruction_note).classes("sk-small")
                ui.label(f"{t('rules.credit')}: {rs.credit}").classes("sk-small")
                ui.label(t("rules.unofficial")).classes("sk-small")
            if rs.id == "custom":
                _custom_editor(custom, body.refresh)
            ui.select(
                {k: t(f"new.opp.{k}") for k in OPPONENTS},
                value=state["opponent"],
                label=t("new.opponent"),
                on_change=lambda e: (state.update(opponent=e.value), body.refresh()),
            ).classes("w-full").mark("opponent-select")
            if state["opponent"] != "human":
                ui.select(
                    {0: t("side.0"), 1: t("side.1")},
                    value=state["side"],
                    label=t("new.side"),
                    on_change=lambda e: state.update(side=e.value),
                ).classes("w-full")
            ui.checkbox(
                t("new.equalOdds"),
                value=state["equal"],
                on_change=lambda e: state.update(equal=e.value),
            )
            if o.allow_miedut and not o.queens:
                ui.checkbox(
                    t("new.miedut"),
                    value=state["miedut"],
                    on_change=lambda e: state.update(miedut=e.value),
                )
            ui.input(
                t("new.seed"),
                value=state["seed"],
                on_change=lambda e: state.update(
                    seed="".join(ch for ch in e.value if ch.isdigit())
                ),
            ).classes("w-full")

        body()

        def start() -> None:
            import secrets

            rs = current_rules()
            options, _ = rs.options.normalized()
            seed = int(state["seed"]) if state["seed"] else secrets.randbits(32)
            miedut = bool(state["miedut"]) and options.allow_miedut and not options.queens
            settings.variant_id = rs.id
            settings.opponent = state["opponent"]
            settings.human_side = int(state["side"])
            settings.equal_odds = bool(state["equal"])
            if rs.id == "custom":
                settings.custom_options = custom["o"].to_dict()
            dlg.close()
            on_start(
                GameConfig(
                    RuleSet(
                        rs.id,
                        rs.name,
                        rs.region,
                        rs.status,
                        rs.reconstruction_note,
                        rs.credit,
                        rs.uncertain,
                        options,
                    ),
                    state["opponent"],
                    int(state["side"]),
                    seed,
                    bool(state["equal"]),
                    miedut,
                )
            )

        with ui.row():
            ui.button(t("new.start"), on_click=start, color="primary").props("no-caps").mark(
                "start-game"
            )
            ui.button(t("new.cancel"), on_click=dlg.close).props("no-caps flat")
    return dlg


def _custom_options(settings: Settings) -> RuleOptions:
    if settings.custom_options:
        try:
            return RuleOptions.from_mapping(settings.custom_options)
        except (ValueError, TypeError):
            pass
    return get_variant("lagesvuotna").options


def _custom_editor(custom: dict[str, Any], refresh: Callable[[], None]) -> None:
    with ui.element("fieldset").classes("sk-panel"):
        ui.html(f"<legend>{t('new.customEditor')}</legend>", sanitize=False)
        ui.select(
            {v.id: v.name for v in VARIANTS if v.id != "custom"},
            value=None,
            label=t("new.customBase"),
            on_change=lambda e: (
                (custom.update(o=get_variant(e.value).options), refresh()) if e.value else None
            ),
        ).classes("w-full")
        o: RuleOptions = custom["o"]
        for f in FIELDS:
            label = t(f"opt.{f.key}")
            val = value_string(o, f.key)

            def upd(e: Any, key: str = f.key) -> None:
                custom["o"] = set_field(custom["o"], key, e.value)
                refresh()

            if f.kind == "bool":
                ui.checkbox(label, value=val == "True", on_change=upd)
            elif f.kind == "number":
                ui.number(
                    label,
                    value=int(val),
                    min=f.lo,
                    max=f.hi,
                    precision=0,
                    on_change=lambda e, k=f.key: None if e.value is None else upd(e, k),
                ).classes("w-full")
            else:
                ui.select(
                    {c: value_text(f.key, c) for c in f.choices},
                    value=val,
                    label=label,
                    on_change=upd,
                ).classes("w-full")
        problems = o.validate()
        _, notes = o.normalized()
        for p in problems:
            ui.label(p).classes("text-negative")
        if notes:
            ui.label(" ".join(notes)).classes("sk-small")


def settings_dialog(
    settings: Settings, on_change: Callable[[], None], on_reset: Callable[[], None]
) -> ui.dialog:
    with ui.dialog() as dlg, ui.card().style("max-width:520px"):
        ui.label(t("settings.title")).classes("text-h6")
        for key in ("dice_anim", "sound", "colorblind", "large_touch", "explain"):
            camel = {"dice_anim": "diceAnim", "large_touch": "largeTouch"}.get(key, key)

            def upd(e: Any, k: str = key) -> None:
                setattr(settings, k, e.value)
                on_change()

            ui.checkbox(t(f"settings.{camel}"), value=getattr(settings, key), on_change=upd).mark(
                f"setting-{key}"
            )
        ui.label(t("settings.reduced")).classes("sk-small")
        with ui.row():
            ui.button(t("settings.close"), on_click=dlg.close, color="primary").props("no-caps")
            ui.button(t("settings.reset"), on_click=lambda: (on_reset(), dlg.close())).props(
                "no-caps outline"
            ).mark("reset-settings")
    return dlg


def first_run_dialog(on_ok: Callable[[], None], on_about: Callable[[], None]) -> ui.dialog:
    with ui.dialog().props("persistent") as dlg, ui.card().style("max-width:520px"):
        ui.label(t("firstrun.title")).classes("text-h6")
        ui.label(t("firstrun.body")).mark("first-run-text")
        with ui.row():
            ui.button(
                t("firstrun.ok"), on_click=lambda: (dlg.close(), on_ok()), color="primary"
            ).props("no-caps").mark("first-run-ok")
            ui.button(
                t("firstrun.about"), on_click=lambda: (dlg.close(), on_ok(), on_about())
            ).props("no-caps outline")
    return dlg
