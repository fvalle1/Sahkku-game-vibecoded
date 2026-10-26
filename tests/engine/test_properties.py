"""Property tests: no reachable illegal state, and every game ends under random play."""

from __future__ import annotations

from dataclasses import replace

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from sahkku.engine import (
    MoveAction,
    SeededDice,
    apply_action,
    check_invariants,
    col_of,
    legal_actions,
    legal_moves,
    new_game,
    row_of,
    start_game,
)
from sahkku.engine.game import face_value
from sahkku.rules import VARIANTS, RuleOptions

settings.register_profile(
    "ci", max_examples=25, deadline=None, suppress_health_check=list(HealthCheck)
)
settings.load_profile("ci")

variants = st.sampled_from([v for v in VARIANTS if v.id != "custom"])


@given(
    variants,
    st.integers(1, 10**6),
    st.booleans(),
    st.booleans(),
    st.lists(st.integers(0, 10**6), min_size=40, max_size=300),
)
def test_no_illegal_state_reachable(rs, seed, miedut, equal_odds, picks):  # type: ignore[no-untyped-def]
    dice = SeededDice(seed)
    s = start_game(rs.options, dice, miedut=miedut, equal_odds=equal_odds)
    for pick in picks:
        if s.phase == "over":
            break
        acts = legal_actions(s)
        assert acts, "a running game always has a legal action"
        s = apply_action(s, acts[pick % len(acts)], dice)
        assert check_invariants(s) == []


@given(variants, st.integers(1, 10**6))
def test_legal_moves_respect_protection(rs, seed):  # type: ignore[no-untyped-def]
    """Where sleeping pieces are protected, no legal move lands on a sleeping piece."""
    o = rs.options
    dice = SeededDice(seed)
    s = start_game(o, dice)
    for i in range(150):
        if s.phase == "over":
            break
        if not o.captures_inactive:
            for m in legal_moves(s):
                assert not any(p.pt == m.to and not p.active and p.kind != "king" for p in s.pieces)
        acts = legal_actions(s)
        s = apply_action(s, acts[(i * 7 + seed) % len(acts)], dice)


@given(st.sampled_from(["lagesvuotna", "vuovdaguoika", "unjarga"]), st.integers(1, 10**6))
def test_captures_leave_no_enemies_sharing_a_line(vid, seed):  # type: ignore[no-untyped-def]
    from sahkku.rules import get_variant

    o: RuleOptions = get_variant(vid).options
    dice = SeededDice(seed)
    s = start_game(o, dice)
    for i in range(200):
        if s.phase == "over":
            break
        acts = legal_actions(s)
        a = acts[(i * 11 + seed) % len(acts)]
        s = apply_action(s, a, dice)
        by_pt: dict[int, set[int]] = {}
        for p in s.pieces:
            if p.side is not None:
                by_pt.setdefault(p.pt, set()).add(p.side)
        assert all(len(v) == 1 for v in by_pt.values())


@given(variants, st.integers(1, 10**6))
def test_every_game_terminates_under_random_play(rs, seed):  # type: ignore[no-untyped-def]
    import random

    rng = random.Random(seed)
    dice = SeededDice(seed)
    s = start_game(rs.options, dice, miedut=seed % 2 == 0)
    for _ in range(12000):
        if s.phase == "over":
            return
        acts = legal_actions(s)
        s = apply_action(s, acts[rng.randrange(len(acts))], dice)
    raise AssertionError("game did not terminate")


@given(st.integers(7, 21), st.integers(3, 7), st.integers(1, 1000))
def test_custom_geometry_stays_consistent(cols, per_side, seed):  # type: ignore[no-untyped-def]
    o, _ = replace(
        VARIANTS[1].options, cols=cols, soldiers_per_side=min(per_side, cols)
    ).normalized()
    assert o.validate() == []
    dice = SeededDice(seed)
    s = start_game(o, dice)
    for i in range(120):
        if s.phase == "over":
            break
        acts = legal_actions(s)
        s = apply_action(s, acts[(i * 5 + seed) % len(acts)], dice)
        assert check_invariants(s) == []


def test_activated_unjarga_soldier_is_on_same_column() -> None:
    o = next(v for v in VARIANTS if v.id == "unjarga").options
    s = new_game(o, starter=0)
    from sahkku.engine import throw_with

    s = throw_with(s, ["X", "II", "II"])
    m = next(m for m in legal_moves(s) if m.face == "X")
    piece = next(p for p in s.pieces if p.id == m.piece_id)
    assert row_of(o.cols, m.to) == 1 and col_of(o.cols, m.to) == col_of(o.cols, piece.pt)
    assert isinstance(apply_action(s, MoveAction(m.die, m.piece_id, m.to, m.fate)).dice, tuple)
    assert face_value(o, "X") == 1
