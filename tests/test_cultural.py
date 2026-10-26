"""Guard rails for the cultural-respect constraints (see CULTURAL_NOTES.md)."""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from sahkku.i18n.glossary import GLOSSARY, TERMS, all_allowed_words

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "sahkku"
SAMI_LETTERS = set("áčđŋšŧžÁČĐŊŠŦŽ")

# The glossary exactly as supplied by the project owner.
EXPECTED_GLOSSARY = {
    "sáhkku", "sáhkkostallat", "bircu, birccut", "sáhkku, ruossa", "guoros",
    "sáhkkufiellu, sáhkkulávdi", "sárggis / sárgát", "Šloahtta", "soalddáhat",
    "olbmát / gálgut", "gonagas", "dronnet", "goddit", "luvvet, aktiveret", "vuosttut, mieđut",
}  # fmt: skip

# Words with Sámi letters that are NOT glossary terms but are names the brief itself uses
# (places, people, institutions, variants) or ordinary words from the credits. Anything new
# must be reviewed by a person before it is added here.
REVIEWED_NAMES = {
    "Lágesvuotna", "Návuotna", "Máze", "Ráisa", "Unjárga", "Vuovdaguoika", "Gávkevuotna",
    "Ohcejohka", "Deatnu", "Anár", "Sámi", "Sápmi", "Várjjat", "duojárs", "Mieđut", "mieđut",
    "Ohcejot", "Šloahtta", "Berg-Nordlie", "sáhkku", "Sáhkku", "sáhkkostallat", "gálgut", "olbmát",
    "Lagesvuotna",
}  # fmt: skip


def _words(text: str) -> set[str]:
    """Every word (letters only) that contains at least one Sámi letter."""
    return {w for w in re.findall(r"[^\W\d_]+", text) if any(c in SAMI_LETTERS for c in w)}


def test_glossary_is_exactly_the_supplied_one() -> None:
    assert {g.term for g in GLOSSARY} == EXPECTED_GLOSSARY


def test_glossary_is_normalised_utf8() -> None:
    for g in GLOSSARY:
        assert unicodedata.normalize("NFC", g.term) == g.term
    for v in TERMS.values():
        assert unicodedata.normalize("NFC", v) == v
    raw = (SRC / "i18n" / "glossary.py").read_bytes()
    assert "Šloahtta".encode() in raw and "mieđut".encode() in raw


def test_no_unreviewed_samí_words_in_ui_text() -> None:
    allowed = all_allowed_words() | REVIEWED_NAMES
    sources = [json.loads((SRC / "i18n" / "en.json").read_text(encoding="utf-8")).values()]
    texts = [str(x) for group in sources for x in group]
    for py in (SRC / "ui").glob("*.py"):
        texts.append(py.read_text(encoding="utf-8"))
    for py in (SRC / "rules").glob("*.py"):
        texts.append(py.read_text(encoding="utf-8"))
    found: set[str] = set()
    for text in texts:
        found |= _words(text)
    found = {w for w in found if w.lower() not in {a.lower() for a in allowed}}
    assert not found, (
        f"unreviewed words with Sámi letters (review, then add to REVIEWED_NAMES): {sorted(found)}"
    )


def test_no_forbidden_motifs_in_source() -> None:
    forbidden = ["reindeer", "shaman", "sieidi", "runebomme", "joik", "lappish", "devil"]
    for path in SRC.rglob("*"):
        if path.suffix not in {".py", ".json", ".css"}:
            continue
        text = path.read_text(encoding="utf-8").lower()
        for word in forbidden:
            if word == "devil":
                continue  # only the nickname note may mention it; checked separately below
            assert word not in text, f"{word!r} found in {path.relative_to(ROOT)}"
    # the hostile nickname is not used anywhere in the app (it is only discussed in docs)
    for path in SRC.rglob("*.py"):
        assert "devil's game" not in path.read_text(encoding="utf-8").lower()


def test_no_runtime_network_resources() -> None:
    """Everything works offline: no CDN scripts, web fonts, analytics or remote assets."""
    bad: list[str] = []
    for path in SRC.rglob("*"):
        if path.suffix not in {".py", ".css", ".json"}:
            continue
        text = path.read_text(encoding="utf-8")
        for m in re.finditer(
            r"""(src|href)\s*=\s*["']https?://|@import|url\(\s*["']?https?:""", text
        ):
            if path.name == "about.py":
                continue  # outbound links in the credits page are not loaded automatically
            bad.append(f"{path.relative_to(ROOT)}: {m.group(0)}")
    assert not bad, bad
    assert "<script" not in (SRC / "ui" / "theme.py").read_text(encoding="utf-8")


def test_about_page_states_the_required_things() -> None:
    about = (SRC / "ui" / "about.py").read_text(encoding="utf-8")
    for phrase in (
        "unofficial hobby implementation",
        "not Sámi",
        "reconstructions",
        "no connection",
        "Mikkel Berg-Nordlie",
        "Edmund Johansen",
        "Hans Aslak Guttorm",
        "Yngvar Mejland",
        "J. A. Friis",
        "Peter Michaelsen",
        "Thierry Depaulis",
        "Várjjat Sámi Musea",
        "1600s",
        "1980s",
        "2018",
        "placeholders",
    ):
        assert phrase in about, phrase
