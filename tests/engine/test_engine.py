from __future__ import annotations

from dataclasses import replace
from typing import Any, ClassVar

import pytest

from sahkku.engine import (
    MoveAction,
    ScriptedDice,
    SeededDice,
    apply_action,
    candidates_for,
    check_invariants,
    col_of,
    figure_eight,
    legal_actions,
    legal_moves,
    new_game,
    playable_dice_indices,
    pt_of,
    row_of,
    royal_destinations,
    start_game,
    xf_point,
)
from sahkku.rules import (
    LAGESVUOTNA,
    NAVUOTNA_MAZE,
    NAVUOTNA_RAISA,
    UNJARGA,
    VUOVDAGUOIKA,
)

from .helpers import P, S, scenario, sold

L = LAGESVUOTNA.options
V = VUOVDAGUOIKA.options
N = NAVUOTNA_RAISA.options
U = UNJARGA.options


def move(s, piece_id, to, die=0, fate=None):  # type: ignore[no-untyped-def]
    return apply_action(s, MoveAction(die, piece_id, to, fate))


def full_specs(o, **kw):  # type: ignore[no-untyped-def]
    g = new_game(o, **kw)
    return [
        (p.kind, p.side, row_of(o.cols, p.pt), col_of(o.cols, p.pt), p.active) for p in g.pieces
    ]


class TestSetup:
    def test_lagesvuotna_pieces(self) -> None:
        g = new_game(L)
        for side in (0, 1):
            assert sum(1 for p in g.pieces if p.kind == "soldier" and p.side == side) == 15
            assert sum(1 for p in g.pieces if p.kind == "queen" and p.side == side) == 1
        king = next(p for p in g.pieces if p.kind == "king")
        assert king.side is None
        assert king.pt == P(L, 1, 7)
        assert check_invariants(g) == []

    def test_queens_on_marked_points_on_owners_right(self) -> None:
        g = new_game(L)
        q = {p.side: p.pt for p in g.pieces if p.kind == "queen"}
        assert q[0] == P(L, 1, 11)
        assert q[1] == P(L, 1, 3)
        mirrored = new_game(replace(L, queen_start="left"))
        assert next(p for p in mirrored.pieces if p.kind == "queen" and p.side == 0).pt == P(
            L, 1, 3
        )

    def test_navuotna_rightmost_square_empty(self) -> None:
        g = new_game(N)
        mine = [p.pt for p in g.pieces if p.kind == "soldier" and p.side == 0]
        assert len(mine) == 12 and P(N, 0, 12) not in mine
        theirs = [p.pt for p in g.pieces if p.kind == "soldier" and p.side == 1]
        assert P(N, 2, 0) not in theirs

    def test_equal_odds(self) -> None:
        g = new_game(L, equal_odds=True)
        assert sum(1 for p in g.pieces if p.kind == "soldier" and p.active) == 6

    def test_start_game_is_reproducible_and_scriptable(self) -> None:
        a = start_game(L, SeededDice(99))
        b = start_game(L, SeededDice(99))
        assert a.current == b.current and a.start_log == b.start_log
        # scripted: coin -> side 0 throws first and has no X; side 1 then throws an X
        d = ScriptedDice(["II", "III", "blank", "II", "X", "blank"], [True])
        s = start_game(L, d)
        assert s.current == 1
        assert len(s.start_log) == 2

    def test_most_x_start_rule(self) -> None:
        o = replace(L, start_rule="most-x")
        d = ScriptedDice(["X", "II", "II", "X", "X", "II"], [True])
        assert start_game(o, d).current == 1


class TestTracks:
    def test_standard_loop_seat0(self) -> None:
        t = new_game(V).tracks[0]
        rc = [(row_of(15, p), col_of(15, p)) for p in t.points]
        assert rc[0] == (0, 0) and rc[14] == (0, 14)
        assert rc[15] == (1, 14) and rc[29] == (1, 0)
        assert rc[30] == (2, 0) and rc[44] == (2, 14)
        assert t.loop_start == 15 and len(t.points) == 45

    def test_figure_eight_returns_home(self) -> None:
        t = new_game(L).tracks[0]
        rc = [(row_of(15, p), col_of(15, p)) for p in t.points]
        assert len(t.points) == 60 and t.loop_start == 0
        assert rc[45] == (1, 14) and rc[59] == (1, 0)

    @pytest.mark.parametrize("o", [L, V, U], ids=["figure-eight", "loop", "from-middle"])
    def test_seat1_is_rotation_of_seat0(self, o) -> None:  # type: ignore[no-untyped-def]
        g = new_game(o)
        assert g.tracks[1].points == tuple(xf_point(o.cols, "rot", p) for p in g.tracks[0].points)

    def test_miedut_enters_middle_row_at_same_place(self) -> None:
        for starter in (0, 1):
            g = new_game(V, starter=starter, miedut=True)
            first = next(p for p in g.tracks[0].points if row_of(15, p) == 1)
            second = next(p for p in g.tracks[1].points if row_of(15, p) == 1)
            assert first == second

    def test_king_graph_same_for_both_seats(self) -> None:
        fig = figure_eight(15)
        rot = tuple(xf_point(15, "rot", p) for p in fig)
        for pt in range(45):
            for v in (1, 2, 3):
                a = royal_destinations(15, fig, "figure-eight", None, pt, v)
                b = royal_destinations(15, rot, "figure-eight", None, pt, v)
                assert a == b


class TestDice:
    def test_fixed_order_x_first(self) -> None:
        s = scenario(L, [sold(0, 1, 5), sold(1, 2, 3, False)], dice=["II", "X", "III"])
        assert [s.dice[i].face for i in playable_dice_indices(s)] == ["X"]

    def test_fixed_order_then_iii_before_ii(self) -> None:
        s = scenario(L, [sold(0, 1, 5), sold(1, 2, 3, False)], dice=["II", "X", "III"])
        m = next(m for m in legal_moves(s) if m.face == "X")
        s = move(s, m.piece_id, m.to, m.die)
        assert [s.dice[i].face for i in playable_dice_indices(s)] == ["III"]

    def test_fixed_order_lost_turn(self) -> None:
        s = scenario(
            L,
            [sold(0, 1, 8), sold(1, 1, 5, False), sold(1, 2, 0, False)],
            dice=["II", "III", "blank"],
        )
        assert s.current == 1
        assert any(type(e).__name__ == "TurnLostEvent" for e in s.events)

    def test_free_order(self) -> None:
        o = NAVUOTNA_MAZE.options
        s = scenario(o, [sold(0, 1, 5), sold(1, 2, 3)], dice=["III", "I"])
        assert len(playable_dice_indices(s)) == 2

    def test_blank_zero_and_four(self) -> None:
        a = scenario(L, [sold(0, 1, 9), sold(1, 2, 0, False)], dice=["blank"] * 3)
        assert a.current == 1
        b = scenario(
            V, [sold(0, 1, 9), sold(1, 2, 0, False)], dice=["blank", "III", "II"], hold=True
        )
        assert [c.to for c in candidates_for(b, 0, "blank") if c.ok] == [P(V, 1, 5)]

    def test_dice_never_summed(self) -> None:
        s = scenario(V, [sold(0, 1, 9), sold(1, 2, 0, False)], dice=["III", "II", "II"])
        assert {m.to for m in legal_moves(s)} == {P(V, 1, 6), P(V, 1, 7)}

    def test_rethrow_single_until_not_x(self) -> None:
        s = scenario(L, [sold(0, 1, 5), sold(1, 2, 3, False)], dice=["X", "III", "II"])
        assert any(type(a).__name__ == "Rethrow" for a in legal_actions(s))
        from sahkku.engine import Rethrow

        t = apply_action(s, Rethrow(0), ScriptedDice(["X", "X", "III"]))
        assert t.dice[0].face == "III"

    def test_rethrow_triple_needs_all_x(self) -> None:
        two = scenario(V, [sold(0, 1, 5), sold(1, 2, 3)], dice=["X", "X", "II"])
        assert not any(type(a).__name__ == "RethrowAll" for a in legal_actions(two))
        three = scenario(V, [sold(0, 1, 5), sold(1, 2, 3)], dice=["X", "X", "X"])
        assert any(type(a).__name__ == "RethrowAll" for a in legal_actions(three))


class TestActivation:
    def test_front_soldier_first_in_lagesvuotna(self) -> None:
        s = scenario(L, full_specs(L), dice=["X", "II", "II"])
        xs = [m for m in legal_moves(s) if m.face == "X" and s.pieces[m.piece_id].kind == "soldier"]
        assert len(xs) == 1 and xs[0].to == P(L, 1, 14)
        wrong = candidates_for(s, 0, "X")[0]
        assert not wrong.ok and wrong.reason == "not-front"

    def test_navuotna_any_soldier_wakes(self) -> None:
        s = scenario(N, full_specs(N), dice=["X", "II"], hold=True)
        wake = [
            candidates_for(s, p.id, "X")[0] for p in s.pieces if p.side == 0 and p.kind == "soldier"
        ]
        assert all(c.ok for c in wake)

    def test_non_x_cannot_wake(self) -> None:
        s = scenario(N, [sold(0, 0, 3, False), sold(1, 2, 3, False)], dice=["I", "II"])
        assert legal_moves(s) == []

    def test_unjarga_wakes_straight_up(self) -> None:
        for cur in (0, 1):
            s = scenario(U, full_specs(U), current=cur, dice=["X", "II", "II"])
            m = next(m for m in legal_moves(s) if m.face == "X")
            piece = s.pieces[m.piece_id]
            assert row_of(15, m.to) == 1 and col_of(15, m.to) == col_of(15, piece.pt)

    def test_unjarga_first_middle_option(self) -> None:
        o = replace(U, activation="first-middle")
        s = scenario(o, full_specs(o), dice=["X", "II", "II"], hold=True)
        assert candidates_for(s, 14, "X")[0].to == P(o, 1, 14)


class TestCapture:
    def test_stacked_capture(self) -> None:
        s = scenario(
            L,
            [
                sold(0, 1, 9),
                sold(1, 1, 6),
                sold(1, 1, 6),
                sold(1, 1, 6),
                sold(1, 2, 0, False),
                sold(0, 0, 0, False),
            ],
            dice=["III", "blank", "blank"],
        )
        t = move(s, 0, P(L, 1, 6))
        assert sum(1 for p in t.pieces if p.side == 1 and p.kind == "soldier") == 1
        assert check_invariants(t) == []

    def test_lagesvuotna_protects_sleeping(self) -> None:
        s = scenario(
            L,
            [sold(0, 1, 9), sold(1, 1, 6, False), sold(1, 2, 0, False)],
            dice=["III", "II", "blank"],
            hold=True,
        )
        c = next(c for c in candidates_for(s, 0, "III") if c.to == P(L, 1, 6))
        assert not c.ok and c.reason == "enemy-sleeping"

    @pytest.mark.parametrize("o", [V, N], ids=["vuovdaguoika", "navuotna"])
    def test_sleeping_capturable_elsewhere(self, o) -> None:  # type: ignore[no-untyped-def]
        dice = ["III", "II"] if o is N else ["III", "II", "II"]
        s = scenario(o, [sold(0, 1, 9), sold(1, 1, 6, False), sold(1, 2, 0, False)], dice=dice)
        c = next(c for c in candidates_for(s, 0, "III") if c.to == P(o, 1, 6))
        assert c.ok and len(c.out.captures) == 1

    def test_single_file(self) -> None:
        s = scenario(
            V,
            [sold(0, 1, 9), sold(0, 1, 8), sold(1, 2, 0, False)],
            dice=["II", "III", "III"],
            hold=True,
        )
        assert all(not c.ok for c in candidates_for(s, 0, "III"))
        free = scenario(
            replace(V, jump_own_soldiers=True),
            [sold(0, 1, 9), sold(0, 1, 8), sold(1, 2, 0, False)],
            dice=["II", "III", "III"],
            hold=True,
        )
        assert any(c.ok for c in candidates_for(free, 0, "III"))


class TestKingRecruit:
    base: ClassVar[list[tuple[Any, ...]]] = [
        sold(0, 1, 10),
        sold(1, 1, 3),
        S("queen", 0, 1, 12, False),
        S("queen", 1, 1, 2, False),
    ]

    def test_recruit_back_and_forth(self) -> None:
        s = scenario(L, [*self.base, S("king", None, 1, 7)], dice=["III", "blank", "blank"])
        s = move(s, 0, P(L, 1, 7))
        king = next(p for p in s.pieces if p.kind == "king")
        assert king.side == 0 and king.pt == P(L, 1, 7)
        back = scenario(
            L,
            [
                sold(0, 1, 7),
                sold(1, 1, 4),
                S("queen", 0, 1, 12, False),
                S("queen", 1, 1, 3, False),
                S("king", 0, 1, 7),
            ],
            current=1,
            dice=["III", "blank", "blank"],
        )
        t = move(back, 1, P(L, 1, 7), 0)
        assert next(p for p in t.pieces if p.kind == "king").side == 1
        assert t.winner == 1  # the only men soldier on that line was captured

    def test_row_crossing(self) -> None:
        fig = figure_eight(15)
        at = lambda r, c: pt_of(15, r, c)  # noqa: E731
        assert at(2, 5) in royal_destinations(15, fig, "figure-eight", None, at(0, 5), 2)
        assert at(1, 5) in royal_destinations(15, fig, "figure-eight", None, at(0, 5), 1)
        mid_x = royal_destinations(15, fig, "figure-eight", None, at(1, 5), 1)
        assert at(0, 5) in mid_x and at(2, 5) in mid_x
        assert at(2, 5) not in royal_destinations(15, fig, "figure-eight", None, at(0, 5), 3)
        assert at(2, 5) not in royal_destinations(15, fig, "figure-eight", None, at(0, 5), 2, False)

    def test_bend_counts_as_straight(self) -> None:
        fig = figure_eight(15)
        at = lambda r, c: pt_of(15, r, c)  # noqa: E731
        d3 = royal_destinations(15, fig, "figure-eight", None, at(0, 13), 3)
        assert at(1, 13) in d3 and at(0, 10) in d3
        assert at(1, 14) in royal_destinations(15, fig, "figure-eight", None, at(0, 13), 2)

    def test_recruiter_shares_line_but_nobody_else_joins(self) -> None:
        s = scenario(
            L,
            [sold(0, 1, 10), sold(0, 1, 9), *self.base[1:], S("king", None, 1, 7)],
            dice=["III", "II", "blank"],
        )
        s = move(s, 0, P(L, 1, 7), 0)
        c = next(c for c in candidates_for(s, 1, "II") if c.to == P(L, 1, 7))
        assert not c.ok and c.reason == "royal-no-share"

    def test_king_never_captured(self) -> None:
        s = scenario(L, [*self.base, S("king", None, 1, 7)], dice=["III", "blank", "blank"])
        assert any(p.kind == "king" for p in move(s, 0, P(L, 1, 7)).pieces)


class TestQueen:
    def mk(self, dice):  # type: ignore[no-untyped-def]
        return scenario(
            L,
            [
                sold(0, 1, 9),
                sold(1, 2, 0, False),
                S("queen", 0, 1, 11, False),
                S("queen", 1, 1, 3, False),
                S("king", None, 1, 7),
            ],
            dice=dice,
        )

    def test_x_frees_queen(self) -> None:
        s = self.mk(["X", "blank", "blank"])
        dests = {c.to for c in candidates_for(s, 2, "X") if c.ok}
        assert dests >= {P(L, 1, 10), P(L, 1, 12), P(L, 0, 11), P(L, 2, 11)}
        assert move(s, 2, P(L, 1, 10)).pieces[2].active

    def test_inactive_queen_cannot_be_landed_on(self) -> None:
        s = scenario(
            L,
            [
                sold(0, 1, 14),
                sold(1, 2, 5, False),
                S("queen", 0, 1, 12, False),
                S("queen", 1, 1, 11, False),
                S("king", None, 1, 7),
            ],
            dice=["II", "blank", "blank"],
            hold=True,
        )
        c = next(c for c in candidates_for(s, 0, "II") if c.to == P(L, 1, 12))
        assert not c.ok

    def test_queen_capture_ends_game(self) -> None:
        s = scenario(
            L,
            [
                sold(0, 1, 9),
                sold(1, 2, 0, False),
                S("queen", 0, 1, 11, False),
                S("queen", 1, 1, 6),
                S("king", None, 1, 7),
            ],
            dice=["III", "blank", "blank"],
        )
        t = move(s, 0, P(L, 1, 6))
        assert (t.phase, t.winner, t.win_reason) == ("over", 0, "queen-captured")

    def test_lone_king_does_not_save(self) -> None:
        s = scenario(
            L,
            [
                sold(0, 1, 9),
                sold(1, 1, 6),
                S("queen", 0, 1, 11, False),
                S("queen", 1, 1, 3, False),
                S("king", 1, 1, 2),
            ],
            dice=["III", "blank", "blank"],
        )
        t = move(s, 0, P(L, 1, 6))
        assert (t.winner, t.win_reason) == (0, "no-soldiers")

    def test_king_alone_option(self) -> None:
        o = replace(L, queens=False, king_alone_loses=False)
        s = scenario(
            o, [sold(0, 1, 9), sold(1, 1, 6), S("king", 1, 1, 2)], dice=["III", "blank", "blank"]
        )
        assert move(s, 0, P(o, 1, 6)).phase != "over"


class TestPushMode:
    def test_push_ram_and_own_block(self) -> None:
        s = scenario(
            V,
            [sold(0, 1, 10), sold(1, 2, 0, False), S("king", None, 1, 7)],
            dice=["III", "II", "II"],
        )
        k = next(p for p in move(s, 0, P(V, 1, 7)).pieces if p.kind == "king")
        assert k.side == 0 and k.pt == P(V, 1, 6)
        ram = scenario(
            V,
            [sold(0, 1, 10), sold(1, 1, 6), sold(1, 2, 0, False), S("king", None, 1, 7)],
            dice=["III", "II", "II"],
        )
        assert sum(1 for p in move(ram, 0, P(V, 1, 7)).pieces if p.side == 1) == 1
        own = scenario(
            V,
            [sold(0, 1, 10), sold(0, 1, 6), sold(1, 2, 0, False), S("king", None, 1, 7)],
            dice=["III", "II", "II"],
            hold=True,
        )
        c = next(c for c in candidates_for(own, 0, "III") if c.to == P(V, 1, 7))
        assert c.reason == "cannot-push-onto-own"

    def test_knock_out(self) -> None:
        o = replace(V, king_knock_out=True)
        s = scenario(
            o,
            [sold(0, 1, 10), sold(1, 2, 0, False), S("king", None, 1, 7)],
            dice=["III", "II", "II"],
        )
        cs = [c for c in candidates_for(s, 0, "III") if c.to == P(o, 1, 7)]
        assert sorted(str(c.fate) for c in cs) == ["remove", "take"]
        assert not any(p.kind == "king" for p in move(s, 0, P(o, 1, 7), 0, "remove").pieces)


class TestUnjargaKing:
    def test_wakes_when_soldier_reaches_far_home_row(self) -> None:
        s = scenario(
            U, [sold(0, 1, 1), sold(1, 2, 3, False), S("king", None, 1, 7)], dice=["II", "II", "II"]
        )
        assert next(p for p in s.pieces if p.kind == "king").side is None
        t = move(s, 0, P(U, 2, 0))
        assert next(p for p in t.pieces if p.kind == "king").side == 0

    def test_nobody_lands_on_dormant_king(self) -> None:
        s = scenario(
            U,
            [sold(0, 1, 9), sold(1, 2, 3, False), S("king", None, 1, 7)],
            dice=["II", "II", "II"],
            hold=True,
        )
        c = next(c for c in candidates_for(s, 0, "II") if c.to == P(U, 1, 7))
        assert c.reason == "king-dormant"


class TestOptions:
    def test_validate_and_normalize(self) -> None:
        assert L.validate() == []
        assert replace(L, cols=3).validate()
        assert replace(L, faces=("II", "II", "III", "blank")).validate()  # no X
        o, notes = replace(L, track="loop-from-middle", activation="step").normalized()
        assert o.activation == "up" and notes

    def test_roundtrip_dict(self) -> None:
        from sahkku.rules import RuleOptions

        assert RuleOptions.from_mapping(L.to_dict()) == L
        with pytest.raises(ValueError):
            RuleOptions.from_mapping({"nonsense": 1})
