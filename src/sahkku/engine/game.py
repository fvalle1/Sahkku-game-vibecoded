"""Pure game logic: setup, move generation, applying actions and the win check.

Everything here is deterministic given the injected ``Dice``. State is immutable; every
function that "changes" the game returns a new ``GameState``.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Literal

from ..rules import Face, OrderKey, RuleOptions
from .dice import Dice
from .tracks import (
    base_home_slots,
    base_track,
    col_of,
    figure_eight,
    indices_of,
    next_index,
    pt_of,
    row_of,
    royal_destinations,
    transform_track,
    xf_point,
)
from .types import (
    Action,
    Cand,
    Die,
    Event,
    GameState,
    KingChange,
    LegalMove,
    MoveAction,
    MoveEvent,
    Outcome,
    Phase,
    Piece,
    PieceKind,
    Rethrow,
    RethrowAll,
    RethrowEvent,
    Side,
    StartEvent,
    StartThrow,
    Throw,
    ThrowEvent,
    Track,
    Transform,
    TurnEndEvent,
    TurnLostEvent,
    WinEvent,
    WinReason,
)


def other(s: Side) -> Side:
    return 1 if s == 0 else 0


# ---------------------------------------------------------------- dice


def face_value(o: RuleOptions, f: Face) -> int:
    if f in ("X", "I"):
        return 1
    if f == "II":
        return 2
    if f == "III":
        return 3
    return o.blank_value


def order_key(o: RuleOptions, f: Face) -> OrderKey:
    return "X" if f == "X" else face_value(o, f)


def _to_dice(o: RuleOptions, faces: tuple[Face, ...]) -> tuple[Die, ...]:
    # A blank worth 0 is "no move": it is spent immediately.
    return tuple(Die(f, f == "blank" and o.blank_value == 0) for f in faces)


def _roll_faces(o: RuleOptions, dice: Dice) -> tuple[Face, ...]:
    return tuple(dice.roll(o.faces) for _ in range(o.dice_count))


# ---------------------------------------------------------------- setup


def new_game(
    options: RuleOptions,
    *,
    starter: Side = 0,
    miedut: bool = False,
    equal_odds: bool = False,
    start_log: tuple[StartThrow, ...] = (),
) -> GameState:
    """Set up a game with a known starting player (see ``start_game`` to decide it by throwing)."""
    o = options
    use_miedut = miedut and o.allow_miedut and not o.queens
    transforms: tuple[Transform, Transform]
    if starter == 0:
        transforms = ("id", "rowflip" if use_miedut else "rot")
    else:
        transforms = ("colflip" if use_miedut else "id", "rot")

    n = o.cols
    bt = base_track(o.track, n)
    tracks = (
        transform_track(n, bt, transforms[0]),
        transform_track(n, bt, transforms[1]),
    )
    bh = base_home_slots(n, o.soldiers_per_side)
    home_slots = (
        tuple(xf_point(n, transforms[0], p) for p in bh),
        tuple(xf_point(n, transforms[1], p) for p in bh),
    )

    pieces: list[Piece] = []
    pid = 0
    for side in (0, 1):
        for j in range(o.soldiers_per_side):
            active = equal_odds and j >= o.soldiers_per_side - 3
            pt = home_slots[side][j]
            pi = j
            if active and o.activation != "step":
                col = col_of(n, pt)
                # With mieđut both sides would otherwise stand on the same middle-row points.
                if any(q.pt == pt_of(n, 1, col) for q in pieces):
                    col = n - 1 - col
                pt = pt_of(n, 1, col)
                pi = indices_of(tracks[side], pt)[0]
            pieces.append(Piece(pid, "soldier", side, active, pt, pi))
            pid += 1
        if o.queens:
            base_col = (
                n - 1 - o.queen_mark_index if o.queen_start == "right" else o.queen_mark_index
            )
            qpt = xf_point(n, "id" if side == 0 else "rot", pt_of(n, 1, base_col))
            pieces.append(Piece(pid, "queen", side, False, qpt, -1))
            pid += 1
    pieces.append(Piece(pid, "king", None, True, pt_of(n, 1, n // 2), -1))

    return GameState(
        options=o,
        tracks=tracks,
        home_slots=home_slots,
        transforms=transforms,
        pieces=tuple(pieces),
        current=starter,
        phase="throw",
        dice=(),
        winner=None,
        win_reason=None,
        turn_number=1,
        miedut=use_miedut,
        equal_odds=equal_odds,
        start_log=start_log,
        events=(StartEvent(starter, start_log),),
    )


def start_game(
    options: RuleOptions,
    dice: Dice,
    *,
    miedut: bool = False,
    equal_odds: bool = False,
) -> GameState:
    """Decide who starts by throwing (first X, or most X), then set up the game."""
    first: Side = 0 if dice.coin() else 1
    log: list[StartThrow] = []
    starter: Side = first
    for _ in range(1000):
        counts = [0, 0]
        decided = False
        for side in (first, other(first)):
            faces = _roll_faces(options, dice)
            log.append(StartThrow(side, faces))
            counts[side] = sum(1 for f in faces if f == "X")
            if options.start_rule == "first-x" and counts[side] > 0:
                starter = side
                decided = True
                break
        if decided:
            break
        if options.start_rule == "most-x" and counts[0] != counts[1]:
            starter = 0 if counts[0] > counts[1] else 1
            break
    return new_game(
        options, starter=starter, miedut=miedut, equal_odds=equal_odds, start_log=tuple(log)
    )


# ---------------------------------------------------------------- movement generation


def _king(s: GameState) -> Piece | None:
    for p in s.pieces:
        if p.kind == "king":
            return p
    return None


def _is_dormant(s: GameState) -> bool:
    k = _king(s)
    return k is not None and k.side is None and s.options.king_acquire != "landing"


def _enemy_home_row(side: Side) -> int:
    return 2 if side == 0 else 0


def _fail(piece_id: int, to: int, reason: str) -> Cand:
    return Cand(piece_id, to, False, reason)


def _eval_landing(s: GameState, mover: Piece, pt: int, new_pi: int) -> list[Cand]:
    """Evaluate a piece landing on ``pt``: one candidate per choice (two with king knock-out)."""
    o = s.options
    me = mover.side
    assert me is not None
    occ = [p for p in s.pieces if p.pt == pt and p.id != mover.id]
    king = next((p for p in occ if p.kind == "king"), None)
    others = [p for p in occ if p.kind != "king"]
    own = [p for p in others if p.side == me]
    enemy = [p for p in others if p.side != me]
    is_royal = mover.kind != "soldier"

    # Where sleeping pieces are protected, nobody may land on them (not even their owner).
    if any(not p.active for p in own) and not o.captures_inactive:
        return [_fail(mover.id, pt, "own-sleeping")]
    if any(not p.active for p in enemy) and not o.captures_inactive:
        return [_fail(mover.id, pt, "enemy-sleeping")]
    if own:
        if o.stacking == "single":
            return [_fail(mover.id, pt, "own-piece-here")]
        if is_royal and not o.royals_share_with_own:
            return [_fail(mover.id, pt, "royal-no-share")]
        if any(p.kind == "queen" for p in own) and not o.royals_share_with_own:
            return [_fail(mover.id, pt, "queen-no-share")]
    if king is not None and _is_dormant(s):
        return [_fail(mover.id, pt, "king-dormant")]
    if king is not None and king.side == me:
        if o.stacking == "single":
            return [_fail(mover.id, pt, "own-piece-here")]
        if not o.royals_share_with_own:
            return [_fail(mover.id, pt, "royal-no-share")]

    captures = tuple(p.id for p in enemy)
    base = Cand(mover.id, pt, True, new_pi=new_pi, out=Outcome(captures))

    if king is not None and king.side != me and not _is_dormant(s) and mover.kind != "king":
        track = s.tracks[me]
        knock = o.king_knock_out
        if o.king_mode == "recruit":
            take = replace(
                base,
                fate="take" if knock else None,
                out=Outcome(captures, KingChange(me, king.pt, "taken")),
            )
            if not knock:
                return [take]
            rem = replace(
                base,
                fate="remove",
                out=Outcome(captures, KingChange(None, king.pt, "removed", True)),
            )
            return [take, rem]
        # push: the king is driven one line forward along the lander's track
        if new_pi < 0:
            return [_fail(mover.id, pt, "cannot-push")]
        dest = track.points[next_index(track, new_pi)]
        there = [p for p in s.pieces if p.pt == dest and p.id != mover.id and p.kind != "king"]
        if any(p.side == me for p in there):
            return [_fail(mover.id, pt, "cannot-push-onto-own")]
        if any(not p.active for p in there) and not o.captures_inactive:
            return [_fail(mover.id, pt, "enemy-sleeping")]
        caps = captures + tuple(p.id for p in there)
        push = replace(
            base,
            fate="take" if knock else None,
            out=Outcome(caps, KingChange(me, dest, "pushed")),
        )
        if not knock:
            return [push]
        rem = replace(
            base,
            fate="remove",
            out=Outcome(captures, KingChange(None, king.pt, "removed", True)),
        )
        return [push, rem]

    the_king = _king(s)
    if (
        the_king is not None
        and mover.kind == "soldier"
        and o.king_acquire != "landing"
        and row_of(o.cols, pt) == _enemy_home_row(me)
        and (_is_dormant(s) or (o.king_acquire == "unjarga-every" and the_king.side != me))
    ):
        return [replace(base, out=Outcome(captures, KingChange(me, the_king.pt, "taken")))]
    return [base]


def _activation_target(s: GameState, p: Piece) -> tuple[int, int]:
    o = s.options
    side = p.side
    assert side is not None
    track = s.tracks[side]
    if o.activation == "first-middle":
        return track.points[0], 0
    if o.activation == "up":
        pt = pt_of(o.cols, 1, col_of(o.cols, p.pt))
        return pt, indices_of(track, pt)[0]
    pi = next_index(track, p.pi)
    return track.points[pi], pi


def _soldier_cands(s: GameState, p: Piece, face: Face) -> list[Cand]:
    o = s.options
    side = p.side
    assert side is not None
    track = s.tracks[side]
    v = face_value(o, face)
    if not p.active:
        if face != "X":
            return []
        if o.activation_order == "front-first":
            front = max(
                q.pi for q in s.pieces if q.kind == "soldier" and q.side == side and not q.active
            )
            if p.pi != front:
                pt, _ = _activation_target(s, p)
                return [_fail(p.id, pt, "not-front")]
        pt, pi = _activation_target(s, p)
        return [replace(c, new_pi=pi) for c in _eval_landing(s, p, pt, pi)]
    if v <= 0:
        return []
    idx = p.pi
    blocked = False
    for k in range(1, v + 1):
        idx = next_index(track, idx)
        if (
            k < v
            and not o.jump_own_soldiers
            and any(q.pt == track.points[idx] and q.side == side and q.id != p.id for q in s.pieces)
        ):
            blocked = True
    if blocked:
        return [_fail(p.id, track.points[idx], "cannot-jump-own")]
    return [replace(c, new_pi=idx) for c in _eval_landing(s, p, track.points[idx], idx)]


def _royal_cands(s: GameState, p: Piece, face: Face) -> list[Cand]:
    o = s.options
    side = p.side
    if side is None:
        return []
    v = face_value(o, face)
    if v <= 0:
        return []
    if not p.active and face != "X":
        return []
    dests = royal_destinations(
        o.cols,
        figure_eight(o.cols),
        o.king_movement,
        s.tracks[side],
        p.pt,
        v,
        o.royal_vertical_crossing,
    )
    res: list[Cand] = []
    for d in dests:
        res.extend(_eval_landing(s, p, d, -1))
    return res


def candidates_for(s: GameState, piece_id: int, face: Face) -> list[Cand]:
    """Every destination for a piece and die face, legal or not (illegal ones carry a reason)."""
    for p in s.pieces:
        if p.id == piece_id:
            if p.side != s.current:
                return []
            return _soldier_cands(s, p, face) if p.kind == "soldier" else _royal_cands(s, p, face)
    return []


# ---------------------------------------------------------------- legal actions


def playable_dice_indices(s: GameState) -> list[int]:
    """Indices of dice that may be played now (one representative per distinct face)."""
    o = s.options
    unused = [(i, d) for i, d in enumerate(s.dice) if not d.used]
    pool = unused
    if o.dice_order == "fixed" and unused:

        def rank(f: Face) -> int:
            k = order_key(o, f)
            return o.fixed_order.index(k) if k in o.fixed_order else 999

        best = min(rank(d.face) for _, d in unused)
        pool = [(i, d) for i, d in unused if rank(d.face) == best]
    seen: set[str] = set()
    out: list[int] = []
    for i, d in pool:
        if d.face not in seen:
            seen.add(d.face)
            out.append(i)
    return out


def legal_moves(s: GameState) -> list[LegalMove]:
    if s.phase != "move":
        return []
    moves: list[LegalMove] = []
    for di in playable_dice_indices(s):
        face = s.dice[di].face
        for p in s.pieces:
            if p.side != s.current:
                continue
            for c in candidates_for(s, p.id, face):
                if c.ok:
                    moves.append(LegalMove(di, face, c))
    return moves


def legal_actions(s: GameState) -> list[Action]:
    if s.phase == "over":
        return []
    if s.phase == "throw":
        return [Throw()]
    acts: list[Action] = [MoveAction(m.die, m.piece_id, m.to, m.fate) for m in legal_moves(s)]
    o = s.options
    for di in playable_dice_indices(s):
        if o.rethrow == "single" and s.dice[di].face == "X":
            acts.append(Rethrow(di))
    if (
        o.rethrow == "triple"
        and len(s.dice) > 1
        and all((not d.used) and d.face == "X" for d in s.dice)
    ):
        acts.append(RethrowAll())
    return acts


DieStatus = Literal["ready", "used", "out-of-order", "no-move"]


def die_status(s: GameState, di: int) -> DieStatus:
    """Why a die can or cannot be played right now (for the UI)."""
    if di >= len(s.dice) or s.dice[di].used:
        return "used"
    d = s.dice[di]
    playable = playable_dice_indices(s)
    if not any(s.dice[i].face == d.face for i in playable):
        return "out-of-order"
    has = any(s.dice[m.die].face == d.face for m in legal_moves(s)) or (
        s.options.rethrow == "single" and d.face == "X"
    )
    return "ready" if has else "no-move"


# ---------------------------------------------------------------- apply


def _check_win(s: GameState) -> tuple[Side, WinReason] | None:
    o = s.options
    king = _king(s)
    for side in (other(s.current), s.current):
        if o.queens and not any(p.kind == "queen" and p.side == side for p in s.pieces):
            return other(side), "queen-captured"
        has_soldiers = any(p.kind == "soldier" and p.side == side for p in s.pieces)
        if not has_soldiers and (o.king_alone_loses or king is None or king.side != side):
            return other(side), "no-soldiers"
    return None


def _end_turn(s: GameState, events: list[Event]) -> GameState:
    events.append(TurnEndEvent(s.current))
    return replace(
        s, current=other(s.current), phase="throw", dice=(), turn_number=s.turn_number + 1
    )


def _settle(s: GameState, events: list[Event]) -> GameState:
    """After any action: end the turn if nothing more can be played."""
    if s.phase != "move":
        return s
    if all(d.used for d in s.dice):
        return _end_turn(s, events)
    if not legal_actions(s):
        fixed_blocked = s.options.dice_order == "fixed" and any(not d.used for d in s.dice)
        events.append(
            TurnLostEvent(s.current, "fixed-order-blocked" if fixed_blocked else "no-legal-move")
        )
        return _end_turn(s, events)
    return s


def throw_with(s: GameState, faces: tuple[Face, ...] | list[Face]) -> GameState:
    """Set the dice by hand (tests, tutorial, AI search)."""
    if s.phase != "throw":
        raise ValueError("Not in throw phase")
    fs = tuple(faces)
    events: list[Event] = [ThrowEvent(s.current, fs)]
    nxt = replace(s, phase="move", dice=_to_dice(s.options, fs))
    settled = _settle(nxt, events)
    return replace(settled, events=tuple(events))


def apply_action(s: GameState, a: Action, dice: Dice | None = None) -> GameState:
    """Apply one action and return the new state. ``dice`` is needed for throws and re-throws."""
    if s.phase == "over":
        raise ValueError("Game is over")
    o = s.options
    events: list[Event] = []

    if isinstance(a, Throw):
        if s.phase != "throw":
            raise ValueError("Cannot throw now")
        if dice is None:
            raise ValueError("A Dice is required to throw")
        return throw_with(s, _roll_faces(o, dice))
    if s.phase != "move":
        raise ValueError("Throw the dice first")

    if isinstance(a, Rethrow):
        if dice is None:
            raise ValueError("A Dice is required to re-throw")
        if o.rethrow != "single" or a.die >= len(s.dice):
            raise ValueError("Illegal re-throw")
        d = s.dice[a.die]
        if d.used or d.face != "X":
            raise ValueError("Illegal re-throw")
        if a.die not in playable_dice_indices(s):
            raise ValueError("Illegal re-throw (order)")
        face: Face = "X"
        for _ in range(1000):
            if face != "X":
                break
            face = dice.roll(o.faces)
        new_dice = tuple(_to_dice(o, (face,))[0] if i == a.die else x for i, x in enumerate(s.dice))
        events.append(RethrowEvent(s.current, (face,), False))
        return _finish(_settle(replace(s, dice=new_dice), events), events)

    if isinstance(a, RethrowAll):
        if dice is None:
            raise ValueError("A Dice is required to re-throw")
        if not any(isinstance(x, RethrowAll) for x in legal_actions(s)):
            raise ValueError("Illegal re-throw of all dice")
        faces = _roll_faces(o, dice)
        events.append(RethrowEvent(s.current, faces, True))
        return _finish(_settle(replace(s, dice=_to_dice(o, faces)), events), events)

    face_of = s.dice[a.die].face if a.die < len(s.dice) else None
    mv = next(
        (
            m
            for m in legal_moves(s)
            if m.face == face_of and m.piece_id == a.piece_id and m.to == a.to and m.fate == a.fate
        ),
        None,
    )
    if mv is None:
        raise ValueError("Illegal move")

    mover = next(p for p in s.pieces if p.id == mv.piece_id)
    removed = set(mv.cand.out.captures)
    captured: tuple[PieceKind, ...] = tuple(p.kind for p in s.pieces if p.id in removed)
    pieces = [
        replace(p, pt=mv.to, active=True, pi=mv.cand.new_pi if mover.kind == "soldier" else -1)
        if p.id == mover.id
        else p
        for p in s.pieces
        if p.id not in removed
    ]
    kc = mv.cand.out.king
    if kc is not None:
        if kc.removed:
            pieces = [p for p in pieces if p.kind != "king"]
        else:
            pieces = [replace(p, side=kc.side, pt=kc.pt) if p.kind == "king" else p for p in pieces]
    new_dice = tuple(replace(d, used=True) if i == mv.die else d for i, d in enumerate(s.dice))
    events.append(
        MoveEvent(
            s.current,
            mover.kind,
            mover.id,
            mover.pt,
            mv.to,
            mv.face,
            not mover.active,
            captured,
            kc.kind if kc else None,
        )
    )
    nxt = replace(s, pieces=tuple(pieces), dice=new_dice)
    win = _check_win(nxt)
    if win is not None:
        events.append(WinEvent(win[0], win[1]))
        phase: Phase = "over"
        return replace(nxt, phase=phase, winner=win[0], win_reason=win[1], events=tuple(events))
    return _finish(_settle(nxt, events), events)


def _finish(s: GameState, events: list[Event]) -> GameState:
    return replace(s, events=tuple(events))


def state_key(s: GameState) -> str:
    """A compact string identifying a position (used for memoisation in search)."""
    dice = "".join(d.face[0] + ("u" if d.used else "") for d in s.dice)
    pieces = ",".join(f"{p.id}:{p.pt}:{p.side}:{int(p.active)}:{p.pi}" for p in s.pieces)
    return f"{s.current}{s.phase[0]}|{dice}|{pieces}"


__all__ = [
    "Track",
    "apply_action",
    "candidates_for",
    "die_status",
    "face_value",
    "legal_actions",
    "legal_moves",
    "new_game",
    "order_key",
    "other",
    "playable_dice_indices",
    "start_game",
    "state_key",
    "throw_with",
]
