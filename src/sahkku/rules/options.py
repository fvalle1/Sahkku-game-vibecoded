"""Rule options as data. Every variant is a ``RuleSet`` holding one ``RuleOptions``."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, fields, replace
from typing import Any, Literal, get_args, get_type_hints

Face = Literal["X", "I", "II", "III", "blank"]
FACES: tuple[str, ...] = get_args(Face)
#: Fixed-order keys: the string "X" or a die value.
OrderKey = int | str


@dataclass(frozen=True, slots=True)
class RuleOptions:
    # --- board ---
    cols: int = 15
    """Number of lines (or squares) per row."""
    board_style: Literal["lines", "squares"] = "lines"
    """Display only."""
    extra_marks: bool = True
    """Display only: mark the points 4th from each end of the middle row."""
    soldiers_per_side: int = 15

    # --- queens ---
    queens: bool = False
    queen_start: Literal["right", "left"] = "right"
    queen_mark_index: int = 3
    """Zero-based index from each end of the middle row (3 = "4th line")."""

    # --- dice ---
    dice_count: int = 3
    faces: tuple[Face, ...] = ("X", "III", "II", "blank")
    """Four faces per die, each assumed equally likely (no source states probabilities)."""
    blank_value: Literal[0, 4] = 0
    dice_application: Literal["separate"] = "separate"
    """Every die is its own move; dice are never added together."""
    dice_order: Literal["fixed", "free"] = "free"
    fixed_order: tuple[OrderKey, ...] = ("X", 3, 2)
    rethrow: Literal["none", "single", "triple"] = "none"
    start_rule: Literal["first-x", "most-x"] = "first-x"

    # --- movement ---
    track: Literal["loop", "loop-from-middle", "figure-eight"] = "loop"
    activation: Literal["step", "up", "first-middle"] = "step"
    activation_order: Literal["front-first", "free"] = "front-first"
    allow_miedut: bool = False
    captures_inactive: bool = True
    stacking: Literal["allowed", "single"] = "single"
    jump_own_soldiers: bool = False

    # --- king ---
    king_mode: Literal["recruit", "push"] = "recruit"
    king_movement: Literal["figure-eight", "track"] = "track"
    royals_share_with_own: bool = False
    king_knock_out: bool = False
    king_acquire: Literal["landing", "unjarga-first", "unjarga-every"] = "landing"
    king_alone_loses: bool = True
    royal_vertical_crossing: bool = True

    # ------------------------------------------------------------------ helpers
    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for f in fields(self):
            v = getattr(self, f.name)
            out[f.name] = list(v) if isinstance(v, tuple) else v
        return out

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> RuleOptions:
        """Build from a mapping with snake_case keys (unknown keys are rejected)."""
        known = {f.name for f in fields(cls)}
        unknown = set(data) - known
        if unknown:
            raise ValueError(f"unknown rule option(s): {sorted(unknown)}")
        kwargs: dict[str, Any] = {}
        for k, v in data.items():
            kwargs[k] = tuple(v) if isinstance(v, list) else v
        return cls(**kwargs)

    def with_changes(self, **changes: Any) -> RuleOptions:
        return replace(self, **changes)

    # ------------------------------------------------------------------ validation
    def validate(self) -> list[str]:
        """Return problems that would make the options unusable (empty list = fine)."""
        problems: list[str] = []
        hints = get_type_hints(type(self))
        for f in fields(self):
            allowed = _literal_values(hints[f.name])
            v = getattr(self, f.name)
            if allowed is not None and v not in allowed:
                problems.append(f"{f.name}: {v!r} is not one of {allowed}")
        if not 7 <= self.cols <= 25:
            problems.append("cols must be between 7 and 25")
        if not 3 <= self.soldiers_per_side <= self.cols:
            problems.append("soldiers_per_side must be between 3 and the number of lines")
        if self.dice_count not in (1, 2, 3, 4):
            problems.append("dice_count must be 1-4")
        if len(self.faces) != 4 or any(f not in FACES for f in self.faces):
            problems.append("faces must list exactly four known faces")
        if "X" not in self.faces:
            problems.append("faces must include X (it wakes soldiers)")
        if self.queens and not 0 < self.queen_mark_index < self.cols // 2:
            problems.append("queen_mark_index must lie between the end and the Castle")
        return problems

    def normalized(self) -> tuple[RuleOptions, list[str]]:
        """Repair combinations that cannot work together. Returns (options, notes)."""
        notes: list[str] = []
        o = self
        if o.activation == "step" and o.track == "loop-from-middle":
            o = replace(o, activation="up")
            notes.append('A track without a home row needs "straight up" activation.')
        if o.activation == "first-middle" and o.track != "loop-from-middle":
            o = replace(o, activation="step" if o.track == "loop" else "up")
            notes.append(
                '"First middle point" activation needs a track that starts on the middle row.'
            )
        if o.soldiers_per_side > o.cols:
            o = replace(o, soldiers_per_side=o.cols)
            notes.append("Soldiers cannot outnumber the lines of the home row.")
        if o.queens and o.allow_miedut:
            notes.append("Mieđut is ignored when queens are in play.")
        if o.queens and o.queen_mark_index >= o.cols // 2:
            o = replace(o, queen_mark_index=max(0, o.cols // 2 - 1))
            notes.append("Queen marks were moved to stay on their own side of the Castle.")
        return o, notes


def _literal_values(tp: Any) -> tuple[Any, ...] | None:
    if getattr(tp, "__origin__", None) is Literal:
        return get_args(tp)
    return None


@dataclass(frozen=True, slots=True)
class RuleSet:
    id: str
    name: str
    region: str
    status: Literal["documented", "experimental", "custom"]
    reconstruction_note: str
    credit: str
    uncertain: Mapping[str, str]
    """Option name -> why it is uncertain or disputed."""
    options: RuleOptions
