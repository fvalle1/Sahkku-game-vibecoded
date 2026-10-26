"""Controller and scene logic (no NiceGUI needed): accessibility labels, undo, explanations, record."""

from __future__ import annotations

import re

from sahkku.engine import MoveAction, legal_moves
from sahkku.rules import LAGESVUOTNA, NAVUOTNA_RAISA, VUOVDAGUOIKA
from sahkku.ui.controller import GameController
from sahkku.ui.scene import build_scene


def _first_playable(c: GameController) -> None:
    while c.state.phase == "throw":
        c.throw()


def test_every_point_has_an_accessible_name_in_track_order() -> None:
    c = GameController.new(LAGESVUOTNA, seed=4)
    sc = build_scene(c.state)
    assert len(sc.points) == 45
    assert all(p.label for p in sc.points)
    # focus order follows the track of the player to move
    track = c.state.tracks[c.state.current].points
    first_visits = list(dict.fromkeys(track))
    assert [p.pt for p in sc.points][: len(first_visits)] == first_visits
    castle = next(p for p in sc.points if p.castle)
    assert "Šloahtta" in castle.label
    assert "neutral king" in castle.label
    assert re.search(r"Men soldier, asleep", next(p for p in sc.points if p.row == 0).label)


def test_scene_marks_destinations_with_more_than_colour() -> None:
    c = GameController.new(NAVUOTNA_RAISA, seed=2)
    c.throw()
    while c.state.phase == "throw":
        c.throw()
    if not c.moves:
        return
    m = c.moves[0]
    c.select_die(m.die)
    c.click_point(c.state.pieces[m.piece_id].pt)
    sc = build_scene(c.state, dests=c.dests, movable=c.movable, selected_piece=c.sel_piece)
    dest = next(p for p in sc.points if p.dest)
    assert "destination" in dest.label
    assert dest.tabbable


def test_scene_to_svg_has_titles_and_roles() -> None:
    svg = build_scene(GameController.new(VUOVDAGUOIKA, seed=1).state).to_svg()
    assert svg.startswith("<svg") and 'role="group"' in svg and "<title>" in svg


def test_undo_returns_the_same_dice() -> None:
    from sahkku.engine import ThrowEvent

    def thrown(c: GameController) -> tuple[str, ...]:
        e = next(e for e in c.state.events if isinstance(e, ThrowEvent))
        return tuple(e.faces)

    c = GameController.new(VUOVDAGUOIKA, seed=21)
    assert c.can_undo is False
    c.throw()
    first = thrown(c)
    c.undo()
    assert c.state.phase == "throw"
    c.throw()
    assert thrown(c) == first  # undo cannot be used to re-roll


def test_no_undo_against_the_computer() -> None:
    c = GameController.new(VUOVDAGUOIKA, seed=21, opponent="easy")
    assert c.can_undo is False


def test_clicking_an_illegal_point_explains_why() -> None:
    c = GameController.new(LAGESVUOTNA, seed=11)
    # find a throw with an X so that soldiers can be woken
    for _ in range(40):
        _first_playable(c)
        if c.state.phase == "move" and any(d.face == "X" and not d.used for d in c.state.dice):
            break
        c.state = c.state  # next turn already handled by the engine
        while c.state.phase == "move" and c.moves:
            m = c.moves[0]
            c.do_action(MoveAction(m.die, m.piece_id, m.to, m.fate))
    xs = [i for i, d in enumerate(c.state.dice) if d.face == "X" and not d.used]
    if not xs:
        return
    c.select_die(xs[0])
    rear = next(
        p
        for p in c.state.pieces
        if p.kind == "soldier" and p.side == c.state.current and not p.active and p.pi == 0
    )
    c.click_point(rear.pt)
    assert "front of the row" in c.message or c.sel_piece is not None


def test_game_record_contains_seed_options_and_dice() -> None:
    c = GameController.new(VUOVDAGUOIKA, seed=77)
    c.throw()
    rec = c.game_record()
    assert "seed: 77" in rec and "rule set: vuovdaguoika" in rec and "threw" in rec
    assert "Current position" in rec


def test_position_text_covers_every_row() -> None:
    text = GameController.new(LAGESVUOTNA, seed=1).position_text()
    assert text.count("row:") == 3
    assert "Šloahtta" not in text  # the Castle is named on the board; the text lists pieces
    assert "neutral king" in text


def test_legal_moves_are_consistent_with_controller_view() -> None:
    c = GameController.new(NAVUOTNA_RAISA, seed=5)
    _first_playable(c)
    if c.state.phase == "move":
        assert {m.piece_id for m in legal_moves(c.state)} >= c.movable
