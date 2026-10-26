"""Plain, immutable data types for game state, actions and events."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from ..rules import Face, RuleOptions

Side = int  # 0 = bottom seat ("men"), 1 = top seat ("women")
PieceKind = Literal["soldier", "queen", "king"]
Phase = Literal["throw", "move", "over"]
WinReason = Literal["no-soldiers", "queen-captured"]
Transform = Literal["id", "rot", "rowflip", "colflip"]


@dataclass(frozen=True, slots=True)
class Piece:
    id: int
    kind: PieceKind
    side: Side | None  # None = neutral king
    active: bool
    pt: int  # row * cols + col; row 0 is seat 0's home row
    pi: int  # track index (active soldiers) / home slot (sleeping soldiers) / -1


@dataclass(frozen=True, slots=True)
class Die:
    face: Face
    used: bool


@dataclass(frozen=True, slots=True)
class Track:
    points: tuple[int, ...]
    loop_start: int


@dataclass(frozen=True, slots=True)
class StartThrow:
    side: Side
    faces: tuple[Face, ...]


# ----------------------------------------------------------------- events
@dataclass(frozen=True, slots=True)
class StartEvent:
    starter: Side
    log: tuple[StartThrow, ...]


@dataclass(frozen=True, slots=True)
class ThrowEvent:
    side: Side
    faces: tuple[Face, ...]


@dataclass(frozen=True, slots=True)
class RethrowEvent:
    side: Side
    faces: tuple[Face, ...]
    all: bool


@dataclass(frozen=True, slots=True)
class MoveEvent:
    side: Side
    piece: PieceKind
    piece_id: int
    from_pt: int
    to_pt: int
    face: Face
    activated: bool
    captured: tuple[PieceKind, ...]
    king: Literal["taken", "pushed", "removed"] | None = None


@dataclass(frozen=True, slots=True)
class TurnLostEvent:
    side: Side
    reason: Literal["no-legal-move", "fixed-order-blocked"]


@dataclass(frozen=True, slots=True)
class TurnEndEvent:
    side: Side


@dataclass(frozen=True, slots=True)
class WinEvent:
    winner: Side
    reason: WinReason


Event = StartEvent | ThrowEvent | RethrowEvent | MoveEvent | TurnLostEvent | TurnEndEvent | WinEvent


# ----------------------------------------------------------------- actions
@dataclass(frozen=True, slots=True)
class Throw:
    pass


@dataclass(frozen=True, slots=True)
class MoveAction:
    die: int
    piece_id: int
    to: int
    fate: Literal["take", "remove"] | None = None


@dataclass(frozen=True, slots=True)
class Rethrow:
    die: int


@dataclass(frozen=True, slots=True)
class RethrowAll:
    pass


Action = Throw | MoveAction | Rethrow | RethrowAll


# ----------------------------------------------------------------- move generation results
@dataclass(frozen=True, slots=True)
class KingChange:
    side: Side | None
    pt: int
    kind: Literal["taken", "pushed", "removed"]
    removed: bool = False


@dataclass(frozen=True, slots=True)
class Outcome:
    captures: tuple[int, ...] = ()
    king: KingChange | None = None


@dataclass(frozen=True, slots=True)
class Cand:
    """One candidate destination for a piece and die face (legal or not, with a reason code)."""

    piece_id: int
    to: int
    ok: bool
    reason: str | None = None
    fate: Literal["take", "remove"] | None = None
    new_pi: int = -1
    out: Outcome = Outcome()


@dataclass(frozen=True, slots=True)
class LegalMove:
    die: int
    face: Face
    cand: Cand

    @property
    def piece_id(self) -> int:
        return self.cand.piece_id

    @property
    def to(self) -> int:
        return self.cand.to

    @property
    def fate(self) -> Literal["take", "remove"] | None:
        return self.cand.fate


@dataclass(frozen=True, slots=True)
class GameState:
    options: RuleOptions
    tracks: tuple[Track, Track]
    home_slots: tuple[tuple[int, ...], tuple[int, ...]]
    transforms: tuple[Transform, Transform]
    pieces: tuple[Piece, ...]
    current: Side
    phase: Phase
    dice: tuple[Die, ...]
    winner: Side | None
    win_reason: WinReason | None
    turn_number: int
    miedut: bool
    equal_odds: bool
    start_log: tuple[StartThrow, ...]
    events: tuple[Event, ...]
