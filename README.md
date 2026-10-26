# Sáhkku – unofficial Python version

A small app for playing **sáhkku**, a traditional Sámi board game, against another person on one device or against the computer. It is pure Python ([NiceGUI](https://nicegui.io) serves a local web page); no Node, no JavaScript tooling, and no network is needed to run it.

> **This is an unofficial hobby project by a non-Sámi developer.** The game belongs to Sámi culture and tradition. The rule sets are modern *reconstructions* that differ between regions; nothing here is "the official" or "the correct" sáhkku. Read [`CULTURAL_NOTES.md`](CULTURAL_NOTES.md) and, ideally, talk to Sámi experts before sharing this publicly.

## Run it

You need Python 3.11 or newer.

**macOS / Linux**

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
python -m sahkku
```

**Windows (PowerShell)**

```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -e .
python -m sahkku
```

**With [uv](https://docs.astral.sh/uv/)** (one command; it creates the environment itself): `uv run python -m sahkku`

`pip install -r requirements.txt` also works instead of `pip install -e .` if you only want the dependencies.

Options: `python -m sahkku --port 8080 --no-browser --seed 123 --host 127.0.0.1`. The app listens on `127.0.0.1` by default. `--host 0.0.0.0` lets phones on **your local network only** open it at `http://<your-computer>:8080`; do not expose it to the internet. `--ai-delay 0` removes the computer's pause before each move.

Settings (rule set, opponent, accessibility options) are saved in a small JSON file in your config directory (macOS `~/Library/Application Support/sahkku`, Windows `%APPDATA%\sahkku`, Linux `~/.config/sahkku`); the Settings dialog has a "Reset settings" button.

## What you can do

- Two players on one device, or play against the computer (Easy, Medium, Hard). Hard runs in a worker process with a time budget, a "thinking" indicator and a cancel button.
- Rule sets: **Lágesvuotna** (default), **Vuovdaguoika / Gávkevuotna**, **Návuotna** (Ráisa and Máze), **Unjárga** (experimental) and **Custom**, each with a plain-language note, credit line and a flag on every uncertain rule. The **Rules panel** shows every active option.
- Legal moves are highlighted; clicking an illegal point explains why. Undo (two-player games), restart, move history, **Copy game record** (seed, options, every throw and move, as text), and a text description of the whole position.
- A tutorial that follows the chosen rule set, an About & credits page, and a first-run notice.
- Accessibility: every board point and piece has an accessible name; keyboard focus follows the track of the player to move (Enter/Space selects, arrow keys move); visible focus rings; shapes **and** colours distinguish the armies; colour-blind-safe palette; large touch targets; reduced-motion respected; works on a phone browser.

## Developing

```sh
pip install -e ".[dev]"      # or: uv sync --extra dev
ruff check src tests && ruff format --check src tests
mypy                          # strict, for engine, rules and ai
pytest                        # unit, property (hypothesis), parity, AI and UI smoke tests
python -m sahkku.ai.selfplay  # 1000 AI-vs-AI games per variant (add --games 100 --workers 1 for a quick run)
```

| Path | What |
| --- | --- |
| `src/sahkku/rules/` | `RuleOptions` / `RuleSet` dataclasses, validation, the variant registry. |
| `src/sahkku/engine/` | Pure game logic: board graph, tracks, dice interface, move generation, `apply_action`, win check. **No UI imports.** |
| `src/sahkku/ai/` | Evaluation, Easy / Medium / Hard (expectimax), self-play harness. **No UI imports.** |
| `src/sahkku/i18n/` | `en.json` (all UI text) and the glossary with the exact Sámi terms. |
| `src/sahkku/ui/` | NiceGUI pages, SVG board renderer, dice tray, log, tutorial, About. Only this package imports `nicegui`. |
| `tests/` | `engine/`, `ai/`, `ui_smoke/`, `parity/` (fixtures derived from the original TypeScript engine). |
| `docs/` | `rules-notes.md`, `decisions.md`, `port-inventory.md`, `packaging.md`. |
| `legacy-ts/` | The original TypeScript app, kept only for the parity fixtures. Safe to delete (see `docs/decisions.md`). |

### How the engine is used

```python
from sahkku.engine import SeededDice, apply_action, legal_actions, start_game
from sahkku.rules import LAGESVUOTNA

dice = SeededDice(42)                      # all randomness is injected
state = start_game(LAGESVUOTNA.options, dice)
while state.phase != "over":
    action = legal_actions(state)[0]       # Throw / MoveAction / Rethrow / RethrowAll
    state = apply_action(state, action, dice)   # returns a new state; state.events says what happened
```

States are frozen dataclasses. `ScriptedDice([...])` supplies fixed throws for tests. `candidates_for(state, piece_id, face)` lists every destination, including illegal ones with a reason code (used for the "why not?" messages). Tracks are data (`state.tracks[side].points`, `loop_start`) and are drawn from the same source they are tested against.

### Rule options and adding a variant

Everything a variant does is a field of `RuleOptions` (`src/sahkku/rules/options.py`): dice, order, re-throw, start rule, track, activation, protection of sleeping pieces, stacking, king and queen behaviour, win condition. A `RuleSet` adds a name, region, reconstruction note, credit and an `uncertain` map (option → why it is uncertain), which the Rules panel shows as badges. The Custom editor edits these fields with validation (`RuleOptions.validate()`, `.normalized()`).

To add a variant: add a `RuleSet` in `rules/variants.py` (use `dataclasses.replace` on `BASE` or another variant) and list it in `VARIANTS`; write the note, credit and `uncertain` entries in your own words; add engine tests (property tests and the self-play harness pick it up automatically). A new option needs a field in `RuleOptions`, use in `engine/game.py`, an entry in `ui/rule_schema.py` and labels in `i18n/en.json` (`opt.<name>`, `val.<name>.<value>`).

### Parity with the TypeScript version

`tests/parity/` replays fixtures generated from the original TypeScript engine with **scripted dice** (never seeds): 48 setups, 60 scenarios with every legal move and candidate reason, and 22 scripted walks of 4,149 steps. See `docs/decisions.md` for the method and the outcome.

### Internationalisation

All UI text is in `src/sahkku/i18n/en.json`. To add a language, copy it to e.g. `nb.json`, translate the values and select it in `settings.json` (`"language": "nb"`). Missing keys fall back to English. Not provided: Norwegian bokmål (I could not guarantee its quality) and any Sámi UI strings beyond the glossary. The About page text is currently inline English in `ui/about.py`.

## Known uncertainties

Each is a visible option; the table is in [`docs/rules-notes.md`](docs/rules-notes.md). In short: face probabilities (assumed equal), blank = 0 or 4, dice order where unrecorded, re-throw forms, the Unjárga track, activation and king rules (explicitly hypothetical), stacking in Unjárga, and the interpretations listed there. The rules follow a local copy of the primary source (`docs/sources/reaidu-sahkku-no.txt`, git-ignored because it is the author's text and must not be republished). Michaelsen, Depaulis, Fyhn et al. and the museum pages were **not** checked.

## Pieces

TODO: Replace the simple shapes with pieces designed or approved by Sámi duojárs if available.

## Play-test checklist

- [ ] First run shows the notice about the unofficial implementation; "About & credits" opens.
- [ ] New game → each rule set starts; the badge and Rules panel show the right variant and "Uncertain" notes.
- [ ] Throw dice → pick a die → eligible pieces glow → destinations are marked → move.
- [ ] Lágesvuotna: only the front soldier wakes; an X can free a queen; a stuck III loses the turn; sleeping pieces cannot be landed on.
- [ ] Návuotna: any soldier can wake; a sleeping soldier can be captured.
- [ ] Vuovdaguoika: landing on the king pushes it; soldiers cannot jump their own army; mieđut can be chosen.
- [ ] Unjárga: woken soldiers go straight up; the king waits until a soldier reaches the far home row.
- [ ] Clicking an illegal destination explains why (Settings → "Explain…").
- [ ] Undo works in two-player games only; restart and new game work; "Copy game record" shows the seed and moves.
- [ ] A whole game against Easy, Medium and Hard finishes; Hard shows "thinking" and can be cancelled.
- [ ] Keyboard only: Tab goes along the track to pieces and destinations, arrows move, Enter selects.
- [ ] Phone browser over the local network: no sideways scrolling of the page; "Large touch targets" enlarges the board.
- [ ] Reduced-motion system setting: no dice animation. Unplug the network: everything still works.

## Licence

Code: MIT (see `LICENSE`). The rule descriptions are the author's own summaries of other people's reconstructions, and the game itself is not claimed by this licence.
