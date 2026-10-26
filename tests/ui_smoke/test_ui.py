"""Smoke tests through NiceGUI's user simulation: no real browser, the real page code."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from nicegui import ui
from nicegui.testing import User

from sahkku.ui.app import AppOptions, register_pages


def _els(user: User, marker_prefix: str) -> list[Any]:
    out = []
    for el in user.client.elements.values():
        if any(m.startswith(marker_prefix) for m in el._markers):
            out.append(el)
    return out


async def _click(user: User, marker: str) -> None:
    user.find(marker=marker).click()
    await asyncio.sleep(0.05)  # let the async handlers and the refresh run


def _marker(el: Any, prefix: str) -> str:
    return next(m for m in el._markers if m.startswith(prefix))


def _has_marker(user: User, name: str) -> bool:
    return any(name in el._markers for el in user.client.elements.values())


async def _dismiss(user: User) -> None:
    await user.open("/")
    await user.should_see("I understand")
    user.find("I understand").click()


async def test_first_run_notice_and_about(user: User) -> None:
    register_pages(AppOptions(seed=11, ai_delay=0))
    await user.open("/")
    await user.should_see("unofficial implementation of a traditional Sámi game")
    user.find("I understand").click()
    await _click(user, "tab-about")
    await user.should_see("An unofficial project")
    await user.should_see("who is not Sámi")
    await user.should_see("Mikkel Berg-Nordlie")
    await user.should_see("Šloahtta")


async def test_rules_panel_shows_variant_and_uncertain_flags(user: User) -> None:
    register_pages(AppOptions(seed=11, ai_delay=0))
    await _dismiss(user)
    await user.should_see("Lágesvuotna")
    await user.should_see("Rules in this game")
    await user.should_see("Uncertain")


async def test_play_a_short_hot_seat_game(user: User) -> None:
    register_pages(AppOptions(seed=11, ai_delay=0))
    await _dismiss(user)
    moves = 0
    for _ in range(400):
        if moves >= 12:
            break
        if _has_marker(user, "throw"):
            await _click(user, "throw")
            continue
        dice = [
            el
            for el in _els(user, "die-")
            if getattr(el, "enabled", True)
            and not any(m.startswith("rethrow") for m in el._markers)
        ]
        progressed = False
        for die in dice:
            await _click(user, _marker(die, "die-"))
            for g in [el for el in _els(user, "pt-") if "has-glow" in el._classes]:
                await _click(user, _marker(g, "pt-"))
                dests = [
                    el
                    for el in _els(user, "pt-")
                    if any(c in el._classes for c in ("dest-ok", "dest-capture"))
                ]
                if dests:
                    await _click(user, _marker(dests[0], "pt-"))
                    moves += 1
                    progressed = True
                    break
            if progressed:
                break
    assert moves >= 12
    # the move log recorded what happened, and the position has a text alternative
    await user.should_see("Move history")
    await user.should_see("Position as text")


async def test_copy_game_record_dialog(user: User) -> None:
    register_pages(AppOptions(seed=11, ai_delay=0))
    await _dismiss(user)
    await _click(user, "copy-record")
    await user.should_see("copy or save to replay")
    areas = [el for el in user.client.elements.values() if isinstance(el, ui.textarea)]
    assert areas and "seed: 11" in str(areas[0].value)


async def test_settings_persist_and_reset(user: User, isolated_config: Path) -> None:
    register_pages(AppOptions(seed=11, ai_delay=0))
    await _dismiss(user)
    await _click(user, "open-settings")
    await _click(user, "setting-colorblind")
    saved = json.loads((isolated_config / "settings.json").read_text(encoding="utf-8"))
    assert saved["colorblind"] is True
    await _click(user, "reset-settings")
    assert not (isolated_config / "settings.json").exists() or not json.loads(
        (isolated_config / "settings.json").read_text(encoding="utf-8")
    ).get("colorblind")


async def test_tutorial_walks_through(user: User) -> None:
    register_pages(AppOptions(seed=11, ai_delay=0))
    await _dismiss(user)
    await _click(user, "tab-learn")
    await user.should_see("The board and the armies")
    for _ in range(12):
        if _has_marker(user, "tutorial-done"):
            break
        await _click(user, "tutorial-next")
    assert _has_marker(user, "tutorial-done")
