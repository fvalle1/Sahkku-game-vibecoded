from __future__ import annotations

import random
import time

import pytest

from sahkku.ai import LEVELS, Level, choose_action, evaluate
from sahkku.ai.selfplay import play_one, run_variant
from sahkku.engine import SeededDice, apply_action, legal_actions, start_game
from sahkku.rules import VARIANTS, get_variant

PLAYABLE = [v for v in VARIANTS if v.id != "custom"]


@pytest.mark.parametrize("level", LEVELS)
@pytest.mark.parametrize("rs", PLAYABLE, ids=lambda v: v.id)
def test_every_level_only_plays_legal_actions(rs, level: Level) -> None:  # type: ignore[no-untyped-def]
    dice = SeededDice(5)
    rng = random.Random(5)
    s = start_game(rs.options, dice, equal_odds=True)
    for _ in range(40):
        if s.phase == "over":
            break
        a = choose_action(s, level, rng, 30.0)
        assert a in legal_actions(s)
        s = apply_action(s, a, dice)


def test_hard_respects_its_time_budget() -> None:
    rs = get_variant("lagesvuotna")
    dice = SeededDice(3)
    rng = random.Random(3)
    s = start_game(rs.options, dice, equal_odds=True)
    worst = 0.0
    for _ in range(60):
        if s.phase == "over":
            break
        t0 = time.perf_counter()
        a = choose_action(s, "hard", rng, 200.0)
        if s.phase == "move":
            worst = max(worst, time.perf_counter() - t0)
        s = apply_action(s, a, dice)
    assert worst < 0.2 + 0.35, f"hard took {worst:.2f}s with a 0.2s budget"


def test_hard_can_be_cancelled() -> None:
    rs = get_variant("lagesvuotna")
    dice = SeededDice(8)
    s = start_game(rs.options, dice, equal_odds=True)
    s = apply_action(s, legal_actions(s)[0], dice)
    t0 = time.perf_counter()
    choose_action(s, "hard", random.Random(1), 5000.0, cancelled=lambda: True)
    assert time.perf_counter() - t0 < 1.0


def test_evaluation_sees_wins_and_losses() -> None:
    from dataclasses import replace

    s = start_game(get_variant("vuovdaguoika").options, SeededDice(1))
    won = replace(s, phase="over", winner=0)
    assert evaluate(won, 0) > 1e5 > -1e5 > evaluate(won, 1)


def test_medium_beats_easy_most_of_the_time() -> None:
    wins = 0
    games = 16
    for g in range(games):
        medium_seat = g % 2
        levels: tuple[Level, Level] = ("medium", "easy") if medium_seat == 0 else ("easy", "medium")
        r = play_one("navuotna-maze", 700 + g, levels)
        assert r.finished
        wins += r.winner == medium_seat
    assert wins >= games * 0.6


def test_selfplay_report_is_clean_for_a_small_sample() -> None:
    rep = run_variant(get_variant("unjarga"), 8, 1, None)
    assert rep.clean
    assert rep.finished == 8
