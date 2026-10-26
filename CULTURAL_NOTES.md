# Cultural notes

Sáhkku is a traditional Sámi game. This project is an **unofficial hobby implementation by a non-Sámi developer**. These notes explain the constraints the project follows and what should happen before anything is published.

## Constraints followed in this repository

- **No decorative Sámi culture.** No Sámi flag or its colours as branding, no gákti or duodji patterns, no drum (runebomme) motifs, no sieidi imagery, no joik, no "mystic / shaman / reindeer-herder" styling, no fake-runic fonts. The look is a calm neutral wood-toned palette with plain system fonts.
- **Neutral pieces.** Pieces are plain geometric shapes (discs, triangles, a diamond for the king). Hat shapes and sieidi-like king shapes are avoided on purpose. _TODO: replace with pieces designed or approved by Sámi duojárs if available._
- **No invented Sámi text.** The only Sámi words in the app are the glossary terms supplied by the project owner (`src/sahkku/i18n/glossary.py`, guarded by `tests/test_cultural.py`), with their diacritics (á č đ ŋ š ŧ ž) kept. They always appear next to English labels, never instead of them. Plain "sahkku" appears only in file names, URLs and package names. Variant and place names (Lágesvuotna, Návuotna, Ráisa, Máze, Unjárga, Vuovdaguoika, Gávkevuotna, Ohcejohka) are used as given in the brief.
- **No claim of authority.** The app never calls itself the official or correct sáhkku. It says the rules are reconstructed and vary, and always shows which variant is active and which options are uncertain.
- **Credit.** The About & credits page credits the reconstructors and sources, says this is unofficial, and invites corrections. The contact links in it are placeholders that must be replaced.
- **No copying of other implementations.** Nothing was taken from other digital versions (e.g. itch.io, Ludii, Bead Game). Code, art and text are original.
- **No republishing of rule texts.** All rules text is paraphrased. The primary source file placed in `docs/sources/` is the author's own text; it is listed in `.gitignore` so it is read locally and not republished.
- **No tracking.** No analytics, no cookies. The app writes one small settings file (display settings, last rule set, a "seen the notice" flag) to your config directory. Everything runs offline; no font, script or image is loaded from the internet.

## A note on a nickname

Some sources record that the game was once given a hostile nickname that equated it with the devil. This is not a name used by the people who played it and it is **not used anywhere in this project**. One point to check with experts: the primary source I read attributes that nickname to leaders of the Sámi Læstadian revival movement, whereas the project brief called it a missionary label. The About page therefore says only that it was "given by critics".

## Before any public release, please ask Sámi experts

Do not publish before people from the community have looked at this. Candidates to contact (I did not contact anyone):

- **Mikkel Berg-Nordlie**, who reconstructed and published the rule sets that this app relies on: are my readings of the rules right? Do you want the rules summarised this way, credited this way, or not at all in a web app?
- **Várjjat Sámi Musea / Varanger Sámi Museum**, which holds the Isak Saba set and has hosted sáhkku events.
- **The Sámi Parliament in Norway** (Sámediggi) for guidance on respectful use of Sámi cultural heritage, language and naming in software.
- **Sámi duojárs** who make sáhkku sets: would they design or approve piece shapes?
- A Sámi language specialist to check every Sámi term and its use in context (the glossary is as supplied and has not been independently checked).

Questions worth asking: Is a free web version welcome at all? Is the name acceptable? Should the Sámi terms appear in this way? Should a Sámi-language interface be offered, and by whom? How should credit and corrections be handled?
