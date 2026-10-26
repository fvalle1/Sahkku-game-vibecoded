"""About & credits page. All text is my own wording."""

from __future__ import annotations

from html import escape

from nicegui import ui

from ..i18n import t
from ..i18n.glossary import GLOSSARY

# TODO: replace these placeholders before any public release.
REPORT_MAILTO = (
    "mailto:REPLACE-WITH-CONTACT@example.invalid?subject=Rules%20or%20cultural%20problem"
)
REPORT_ISSUES = "https://example.invalid/REPLACE-WITH-ISSUE-TRACKER"

SOURCES: tuple[tuple[str, str | None], ...] = (
    ("Reaidu – Berg-Nordlie’s rule pages (Norwegian)", "https://result.uit.no/reaidu/"),
    ("Wikipedia: Sáhkku", "https://en.wikipedia.org/wiki/S%C3%A1hkku"),
    ("Michaelsen: “Daldøs og Sakku”", "http://norcom2019.math.aau.dk/Michaelsen.pdf"),
    ("Depaulis, “An Arab Game in the North Pole?”, Board Games Studies 4 (2001)", None),
    (
        "Norsk Folkemuseum: learn to play sáhkku",
        "https://norskfolkemuseum.no/en/shkku-eahket--learn-to-play-a-smi-board-game",
    ),
)

CREDITS: tuple[str, ...] = (
    "Mikkel Berg-Nordlie: the published collection of rule sets (Reaidu, UiT / OsloMet), the main source for this app.",
    "Edmund Johansen: reconstruction of the Lágesvuotna rules, and the tradition of making sets.",
    "Hans Aslak Guttorm: documentation of the Vuovdaguoika rules, passed on in his family.",
    "Yngvar Mejland: the Návuotna (Ráisa) rules, written down in the 1950s.",
    "J. A. Friis: an 1871 description of the game.",
    "Peter Michaelsen: research on Nordic running-fight games.",
    "Thierry Depaulis: comparative research on the wider family of games.",
    "Várjjat Sámi Musea (Varanger Sámi Museum) and the Sámi sáhkku cups: for keeping the game alive in modern times.",
)


def build_about() -> None:
    with ui.element("div").classes("sk-page"):
        ui.html(f"<h1>{t('about.title')}</h1>", sanitize=False).mark("about-title")
        ui.html("<h2>An unofficial project</h2>", sanitize=False)
        ui.label(
            "This is an unofficial hobby implementation made by a developer who is not Sámi. Sáhkku "
            "belongs to Sámi culture and tradition. This app is not made, checked or endorsed by any "
            "Sámi person, organisation or institution, and it has no connection to any of them."
        )
        ui.label(
            "Nothing here is the “official” or “correct” sáhkku. The rule sets are modern "
            "reconstructions. They differ between regions and families, and some details are guesses "
            "that the reconstructors themselves mark as uncertain. The Rules panel always shows which "
            "variant is active and which options are uncertain."
        )
        ui.label(
            "The pieces are deliberately plain shapes. They are placeholders: pieces designed or "
            "approved by Sámi duojárs would be better."
        )
        ui.html("<h2>Short history</h2>", sanitize=False)
        ui.label(
            "A dice-and-board game of this kind may be mentioned in writing from the 1600s, and by the "
            "middle of the 1800s sáhkku was played in places far apart in Sápmi. During the 1900s it "
            "nearly vanished: religious pressure against games, assimilation policy and racism, and "
            "the destruction of the war years all played a part. Since the 1980s people have taught the "
            "rules again, and interest grew again after 2018 with new sets, courses and cups."
        )
        ui.html("<h2>Rule reconstructions and credits</h2>", sanitize=False)
        ui.html(
            "<ul>" + "".join(f"<li>{escape(c)}</li>" for c in CREDITS) + "</ul>", sanitize=False
        )
        ui.label(
            "All rule descriptions in this app are my own summaries. If you spot a mistake, please say so using the link below."
        ).classes("sk-small")
        ui.html("<h2>Sources</h2>", sanitize=False)
        items = []
        for title, url in SOURCES:
            if url:
                items.append(
                    f'<li><a href="{url}" target="_blank" rel="noreferrer noopener">{escape(title)}</a></li>'
                )
            else:
                items.append(f"<li>{escape(title)}</li>")
        ui.html("<ul>" + "".join(items) + "</ul>", sanitize=False)
        ui.html("<h2>Terms used in the app</h2>", sanitize=False)
        ui.label(
            "Sámi words appear next to the English labels, never instead of them, and are used exactly as supplied."
        ).classes("sk-small")
        rows = "".join(
            f'<tr><td>{escape(g.concept)}</td><td lang="se">{escape(g.term)}</td></tr>'
            for g in GLOSSARY
        )
        ui.html(
            f'<table class="sk-glossary"><thead><tr><th scope="col">Concept</th><th scope="col">Term</th></tr></thead><tbody>{rows}</tbody></table>',
            sanitize=False,
        ).mark("glossary")
        ui.label(
            "Some old accounts use a hostile nickname for the game that was given by critics. It is not "
            "a name the players used, and it is not used here."
        ).classes("sk-small")
        ui.html("<h2>Corrections</h2>", sanitize=False)
        ui.html(
            f'Spotted a rules or cultural problem? Please tell me: <a href="{REPORT_MAILTO}">send a message</a> '
            f'or <a href="{REPORT_ISSUES}">open an issue</a>. (These two links are placeholders until a real contact is set up.)',
            sanitize=False,
        )
