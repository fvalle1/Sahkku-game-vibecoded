"""The variant registry. Notes and credits are my own wording; see docs/rules-notes.md."""

from __future__ import annotations

from dataclasses import replace

from .options import RuleOptions, RuleSet

BASE = RuleOptions()

LAGESVUOTNA = RuleSet(
    id="lagesvuotna",
    name="Lágesvuotna",
    region="Lágesvuotna (Laksefjord area), with queens",
    status="documented",
    reconstruction_note=(
        "A published reconstruction of the form played at modern Sámi cups. Two sources I could "
        "not check directly may differ on small details; see the notes."
    ),
    credit="Edmund Johansen (reconstruction); Mikkel Berg-Nordlie (published rule collection).",
    uncertain={
        "start_rule": "Two ways of deciding who starts are described; first-X is the default here.",
        "queen_start": "Which marked point each queen takes follows a photo caption; a mirrored layout is offered.",
        "faces": "No source states face probabilities. Equal odds (25% each) is an assumption.",
        "royals_share_with_own": "Exact wording of when the king or queen may share a line is interpreted.",
        "royal_vertical_crossing": "The source says the king moves up and down; the exact crossing distances are my reading.",
    },
    options=replace(
        BASE,
        queens=True,
        dice_order="fixed",
        fixed_order=("X", 3, 2),
        rethrow="single",
        track="figure-eight",
        captures_inactive=False,
        stacking="allowed",
        jump_own_soldiers=True,
        king_mode="recruit",
        king_movement="figure-eight",
        royals_share_with_own=False,
    ),
)

VUOVDAGUOIKA = RuleSet(
    id="vuovdaguoika",
    name="Vuovdaguoika / Gávkevuotna",
    region="Vuovdaguoika and Gávkevuotna (Ohcejohka area), no queens",
    status="documented",
    reconstruction_note=(
        "Documented from the Ohcejohka area. Whether the triple-X re-throw was used in Gávkevuotna "
        "itself is not known, so it is an option (on by default). No dice order is recorded, so "
        "order is free."
    ),
    credit="Hans Aslak Guttorm (documentation); Mikkel Berg-Nordlie (published rule collection).",
    uncertain={
        "rethrow": "Known from the inland area; unknown for Gávkevuotna.",
        "dice_order": "No dice order is recorded; free order is used.",
        "king_knock_out": 'A local rule from elsewhere in the area that conflicts with the usual "king is never captured".',
        "faces": "No source states face probabilities.",
    },
    options=replace(
        BASE,
        blank_value=4,
        dice_order="free",
        rethrow="triple",
        allow_miedut=True,
        captures_inactive=True,
        stacking="single",
        jump_own_soldiers=False,
        king_mode="push",
        king_movement="track",
        king_knock_out=False,
    ),
)

NAVUOTNA_RAISA = RuleSet(
    id="navuotna-raisa",
    name="Návuotna – Ráisa",
    region="Návuotna (Kvænangen), Ráisa style: fixed dice order",
    status="documented",
    reconstruction_note=(
        "Board of squares, two dice. Dice are played in a fixed order, which makes it very "
        "luck-dependent."
    ),
    credit="Yngvar Mejland (Ráisa rules); Mikkel Berg-Nordlie (published rule collection).",
    uncertain={"faces": "No source states face probabilities."},
    options=replace(
        BASE,
        cols=13,
        board_style="squares",
        extra_marks=False,
        soldiers_per_side=12,
        dice_count=2,
        faces=("X", "I", "II", "III"),
        dice_order="fixed",
        fixed_order=("X", 1, 2, 3),
        rethrow="single",
        captures_inactive=True,
        stacking="allowed",
        jump_own_soldiers=True,
        activation_order="free",
        king_mode="recruit",
        king_movement="track",
        royals_share_with_own=True,
    ),
)

NAVUOTNA_MAZE = RuleSet(
    id="navuotna-maze",
    name="Návuotna – Máze",
    region="Návuotna (Kvænangen), Máze style: free dice order",
    status="documented",
    reconstruction_note="Same as the Ráisa style but the dice may be played in any order.",
    credit="Mikkel Berg-Nordlie (published rule collection).",
    uncertain=NAVUOTNA_RAISA.uncertain,
    options=replace(NAVUOTNA_RAISA.options, dice_order="free"),
)

UNJARGA = RuleSet(
    id="unjarga",
    name="Unjárga (experimental)",
    region="Unjárga (Nesseby) – experimental reconstruction",
    status="experimental",
    reconstruction_note=(
        "Explicitly hypothetical: the surviving knowledge is thin and the reconstructor filled "
        "gaps. Many choices below are open and offered as options."
    ),
    credit="Mikkel Berg-Nordlie (reconstruction).",
    uncertain={
        "blank_value": "Blank is worth 0 or 4; both are offered.",
        "dice_order": "Dice order is unknown.",
        "rethrow": "Two re-throw forms are documented.",
        "track": "The track is unknown; the default is a hypothesis.",
        "stacking": "Whether stacking was allowed is unknown.",
        "king_acquire": "Three ways of taking the king are suggested.",
        "king_knock_out": "Option (b) of the king rules: the lander may remove the king.",
        "king_alone_loses": "The reconstructor suggests that a lone king counts as a loss.",
        "activation": (
            "Straight up from the home line, or to the first middle-row point: the reconstructor "
            "reads the sources the first way but notes doubt."
        ),
        "activation_order": "The sources do not say; front-first is used because the king rule needs it.",
        "royal_vertical_crossing": 'Not described for Unjárga beyond "four directions".',
    },
    options=replace(
        BASE,
        faces=("X", "II", "III", "blank"),
        blank_value=0,
        dice_order="free",
        fixed_order=("X", 4, 3, 2),
        rethrow="single",
        track="loop-from-middle",
        activation="up",
        allow_miedut=True,
        captures_inactive=True,
        stacking="allowed",
        jump_own_soldiers=True,
        king_mode="recruit",
        king_movement="figure-eight",
        royals_share_with_own=False,
        king_acquire="unjarga-first",
        king_alone_loses=True,
    ),
)

CUSTOM = RuleSet(
    id="custom",
    name="Custom",
    region="Your own combination of options",
    status="custom",
    reconstruction_note="Every option can be edited. This is not a historical variant.",
    credit="Options are drawn from the other rule sets.",
    uncertain={},
    options=LAGESVUOTNA.options,
)

VARIANTS: tuple[RuleSet, ...] = (
    LAGESVUOTNA,
    VUOVDAGUOIKA,
    NAVUOTNA_RAISA,
    NAVUOTNA_MAZE,
    UNJARGA,
    CUSTOM,
)


def get_variant(variant_id: str) -> RuleSet:
    for v in VARIANTS:
        if v.id == variant_id:
            return v
    raise KeyError(f"Unknown variant {variant_id!r}")
