"""NiceGUI page wiring: tabs (Play / Learn the rules / About), dialogs and settings."""

from __future__ import annotations

import secrets
from dataclasses import dataclass

from nicegui import ui

from ..i18n import set_language, t
from ..rules import get_variant
from ..settings import Settings, load_settings, reset_settings, save_settings
from .about import build_about
from .controller import GameController
from .dialogs import GameConfig, first_run_dialog, new_game_dialog, settings_dialog
from .play import PlayView
from .theme import CSS
from .tutorial import Tutorial


@dataclass(slots=True)
class AppOptions:
    seed: int | None = None
    ai_delay: float = 0.6
    storage: bool = True


def _new_controller(settings: Settings, cfg: GameConfig | None, seed: int | None) -> GameController:
    if cfg is not None:
        return GameController.new(
            cfg.rules,
            seed=cfg.seed,
            opponent=cfg.opponent,
            human_side=cfg.human_side,
            equal_odds=cfg.equal_odds,
            miedut=cfg.miedut,
            explain=settings.explain,
        )
    rules = get_variant(settings.variant_id)
    if rules.id == "custom" and settings.custom_options:
        from ..rules import RuleOptions, RuleSet

        try:
            opts = RuleOptions.from_mapping(settings.custom_options)
            rules = RuleSet(
                rules.id,
                rules.name,
                rules.region,
                rules.status,
                rules.reconstruction_note,
                rules.credit,
                rules.uncertain,
                opts,
            )
        except (ValueError, TypeError):
            pass
    return GameController.new(
        rules,
        seed=seed if seed is not None else secrets.randbits(32),
        opponent=settings.opponent,
        human_side=settings.human_side,
        equal_odds=settings.equal_odds,
        explain=settings.explain,
    )


def register_pages(opts: AppOptions) -> None:
    @ui.page("/")
    def index() -> None:
        settings = load_settings()
        set_language(settings.language)
        ui.add_css(CSS)
        ui.dark_mode(None)  # follow the system light/dark setting
        ui.colors(
            primary="#3f6a85",
            secondary="#6b6358",
            accent="#3f6a85",
            positive="#2f7d4f",
            negative="#b04a2e",
        )

        def apply_body_classes() -> None:
            body = ui.query("body")
            body.classes(
                add="sk-cb" if settings.colorblind else "",
                remove="" if settings.colorblind else "sk-cb",
            )
            body.classes(
                add="" if settings.dice_anim else "sk-noanim",
                remove="sk-noanim" if settings.dice_anim else "",
            )

        apply_body_classes()
        session: dict[str, object] = {"ctrl": _new_controller(settings, None, opts.seed)}
        ctrl0: GameController = session["ctrl"]  # type: ignore[assignment]

        ui.html('<a class="sk-skip" href="#sk-main">Skip to content</a>', sanitize=False)
        with ui.element("header").classes("sk-top"):
            with ui.element("div"):
                ui.html(
                    f"<strong>{t('app.title')}</strong> <span class='sk-small'>{t('app.subtitle')}</span>",
                    sanitize=False,
                )
            with ui.row().classes("items-center"):
                with ui.tabs().props("dense no-caps").classes("sk-tabs") as tabs:
                    play_tab = ui.tab("play", label=t("nav.playTab")).mark("tab-play")
                    learn_tab = ui.tab("learn", label=t("nav.tutorial")).mark("tab-learn")
                    about_tab = ui.tab("about", label=t("nav.about")).mark("tab-about")
                ui.button(t("nav.settings"), on_click=lambda: settings_dlg.open()).props(
                    "no-caps outline"
                ).mark("open-settings")

        def persist() -> None:
            apply_body_classes()
            save_settings(settings)
            play.refresh()

        def do_reset() -> None:
            fresh = reset_settings()
            for f in (
                "dice_anim",
                "sound",
                "colorblind",
                "large_touch",
                "explain",
                "variant_id",
                "opponent",
                "human_side",
                "equal_odds",
                "custom_options",
                "seen_notice",
            ):
                setattr(settings, f, getattr(fresh, f))
            apply_body_classes()
            ui.notify(t("settings.resetDone"))
            play.refresh()

        settings_dlg = settings_dialog(settings, persist, do_reset)

        def start_game(cfg: GameConfig) -> None:
            session["ctrl"] = _new_controller(settings, cfg, None)
            save_settings(settings)
            tutorial.rules = cfg.rules
            tutorial.view.refresh()
            play.refresh()
            tabs.set_value("play")

        def restart() -> None:
            c: GameController = session["ctrl"]  # type: ignore[assignment]
            session["ctrl"] = GameController.new(
                c.rules,
                seed=secrets.randbits(32),
                opponent=c.opponent,
                human_side=c.human_side,
                equal_odds=c.state.equal_odds,
                miedut=c.state.miedut,
                explain=settings.explain,
            )
            play.refresh()

        def open_new() -> None:
            new_game_dialog(settings, start_game).open()

        with ui.element("main").classes("sk-main").props('id="sk-main"'):  # noqa: SIM117
            with (
                ui.tab_panels(tabs, value="play")
                .props("animated=false")
                .classes("w-full")
                .style("background:transparent")
            ):
                with ui.tab_panel("play").style("padding:0"):

                    @ui.refreshable
                    def play() -> None:
                        ctrl: GameController = session["ctrl"]  # type: ignore[assignment]
                        ctrl.explain = settings.explain
                        with ui.element("div").style("margin:4px 0 8px"):
                            ui.html(
                                f'<span class="sk-badge" style="font-size:1rem;font-weight:600" '
                                f'data-testid="variant-badge">{ctrl.rules.name}</span>'
                                f'<span class="sk-badge {"warn" if ctrl.rules.status != "documented" else ""}">'
                                f"{t('status.' + ctrl.rules.status)}</span>",
                                sanitize=False,
                            ).mark("variant-badge")
                        PlayView(
                            ctrl,
                            settings,
                            on_new=open_new,
                            on_restart=restart,
                            ai_delay=opts.ai_delay,
                        ).build()

                    play()
                with ui.tab_panel("learn").style("padding:0"):
                    tutorial = Tutorial(ctrl0.rules, settings, lambda: tabs.set_value("play"))
                    tutorial.build()
                with ui.tab_panel("about").style("padding:0"):
                    build_about()

        ui.html(
            "<div class='sk-small' style='text-align:center;padding:16px'>Unofficial hobby project by a "
            "non-Sámi developer. Rules are reconstructions. No tracking, no cookies, works offline.</div>",
            sanitize=False,
        )

        def accepted() -> None:
            settings.seen_notice = True
            save_settings(settings)

        if not settings.seen_notice:
            dlg = first_run_dialog(accepted, lambda: tabs.set_value("about"))
            ui.timer(0.2, dlg.open, once=True)
        _ = (play_tab, learn_tab, about_tab)


def run(
    *,
    host: str = "127.0.0.1",
    port: int = 8080,
    show: bool = True,
    seed: int | None = None,
    ai_delay: float = 0.6,
) -> None:
    register_pages(AppOptions(seed=seed, ai_delay=ai_delay))
    ui.run(
        host=host,
        port=port,
        show=show,
        reload=False,
        title="Sáhkku – unofficial web version",
        favicon="🎲",
        dark=None,
        reconnect_timeout=10,
    )
