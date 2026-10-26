"""Sámi terms exactly as supplied by the project owner. Do not add, guess or "correct" any here.

Diacritics (á č đ ŋ š ŧ ž) are kept; the file is UTF-8. ``tests/test_cultural.py`` checks that the
UI only uses these terms.
"""

from __future__ import annotations

from typing import NamedTuple


class GlossaryEntry(NamedTuple):
    concept: str
    term: str


GLOSSARY: tuple[GlossaryEntry, ...] = (
    GlossaryEntry("The game", "sáhkku"),
    GlossaryEntry("To play", "sáhkkostallat"),
    GlossaryEntry("Dice / to throw", "bircu, birccut"),
    GlossaryEntry("X throw", "sáhkku, ruossa"),
    GlossaryEntry("Zero", "guoros"),
    GlossaryEntry("Board", "sáhkkufiellu, sáhkkulávdi"),
    GlossaryEntry("Line(s) on the board", "sárggis / sárgát"),
    GlossaryEntry("The central point (Castle)", "Šloahtta"),
    GlossaryEntry("Soldiers", "soalddáhat"),
    GlossaryEntry("Men / women (the two armies)", "olbmát / gálgut"),
    GlossaryEntry("King", "gonagas"),
    GlossaryEntry("Queen", "dronnet"),
    GlossaryEntry('To capture ("to kill")', "goddit"),
    GlossaryEntry("Activate", "luvvet, aktiveret"),
    GlossaryEntry("Movement patterns", "vuosttut, mieđut"),
)

#: Short terms shown next to English labels.
TERMS = {
    "castle": "Šloahtta",
    "men": "olbmát",
    "women": "gálgut",
    "king": "gonagas",
    "queen": "dronnet",
    "soldiers": "soalddáhat",
    "dice": "birccut",
    "capture": "goddit",
    "activate": "luvvet",
    "zero": "guoros",
    "board": "sáhkkufiellu",
    "line": "sárggis",
    "lines": "sárgát",
    "vuosttut": "vuosttut",
    "miedut": "mieđut",
    "game": "sáhkku",
}


def all_allowed_words() -> set[str]:
    """Every word that may appear in UI text with Sámi letters."""
    words: set[str] = set()
    for e in GLOSSARY:
        for w in e.term.replace(",", " ").replace("/", " ").split():
            words.add(w)
    words.update(TERMS.values())
    return words
