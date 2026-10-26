"""Which rule options the UI shows and how the Custom editor edits them."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..rules import Face, OrderKey, RuleOptions


@dataclass(frozen=True, slots=True)
class Field:
    key: str
    kind: str  # select | number | bool
    choices: tuple[str, ...] = ()
    lo: int = 0
    hi: int = 0


FACE_SETS: dict[str, tuple[Face, ...]] = {
    "X,III,II,blank": ("X", "III", "II", "blank"),
    "X,I,II,III": ("X", "I", "II", "III"),
}
ORDER_SETS: dict[str, tuple[OrderKey, ...]] = {
    "X,3,2": ("X", 3, 2),
    "X,1,2,3": ("X", 1, 2, 3),
    "X,4,3,2": ("X", 4, 3, 2),
}

FIELDS: tuple[Field, ...] = (
    Field("cols", "number", lo=9, hi=17),
    Field("soldiers_per_side", "number", lo=3, hi=17),
    Field("board_style", "select", ("lines", "squares")),
    Field("extra_marks", "bool"),
    Field("dice_count", "select", ("2", "3")),
    Field("faces", "select", tuple(FACE_SETS)),
    Field("blank_value", "select", ("0", "4")),
    Field("dice_order", "select", ("fixed", "free")),
    Field("fixed_order", "select", tuple(ORDER_SETS)),
    Field("rethrow", "select", ("none", "single", "triple")),
    Field("start_rule", "select", ("first-x", "most-x")),
    Field("track", "select", ("loop", "loop-from-middle", "figure-eight")),
    Field("activation", "select", ("step", "up", "first-middle")),
    Field("activation_order", "select", ("front-first", "free")),
    Field("allow_miedut", "bool"),
    Field("captures_inactive", "bool"),
    Field("stacking", "select", ("allowed", "single")),
    Field("jump_own_soldiers", "bool"),
    Field("king_mode", "select", ("recruit", "push")),
    Field("king_movement", "select", ("track", "figure-eight")),
    Field("royal_vertical_crossing", "bool"),
    Field("royals_share_with_own", "bool"),
    Field("king_knock_out", "bool"),
    Field("king_acquire", "select", ("landing", "unjarga-first", "unjarga-every")),
    Field("queens", "bool"),
    Field("queen_start", "select", ("right", "left")),
    Field("queen_mark_index", "number", lo=1, hi=6),
    Field("king_alone_loses", "bool"),
)


def value_string(o: RuleOptions, key: str) -> str:
    v = getattr(o, key)
    if key == "faces":
        return next((k for k, f in FACE_SETS.items() if f == tuple(v)), ",".join(v))
    if key == "fixed_order":
        return next((k for k, f in ORDER_SETS.items() if f == tuple(v)), ",".join(map(str, v)))
    return str(v)


def set_field(o: RuleOptions, key: str, raw: Any) -> RuleOptions:
    value: Any = raw
    if key == "faces":
        value = FACE_SETS.get(str(raw), o.faces)
    elif key == "fixed_order":
        value = ORDER_SETS.get(str(raw), o.fixed_order)
    elif key == "blank_value":
        value = 4 if int(raw) == 4 else 0
    elif key in ("dice_count", "cols", "soldiers_per_side", "queen_mark_index"):
        value = int(raw)
    return o.with_changes(**{key: value})
