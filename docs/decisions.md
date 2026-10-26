# Decisions

Short records of choices made while porting the app from TypeScript to Python, and why.

## 1. NiceGUI was enough; no FastAPI fallback

The brief allowed switching to FastAPI plus one static HTML file only if NiceGUI could not meet the touch, accessibility or SVG requirements. It could, so the fallback was **not** used. Checked in a real browser (Chromium via Playwright):

- NiceGUI's native element tree renders correct SVG (`<svg>`, `<g>`, `<circle>`, `<path>`, in the SVG namespace), with `click`, `keydown.enter`, `keydown.space` and arrow-key handlers, `aria-label`, `role`, `tabindex` and `data-*` attributes.
- So the board is built from **Python-generated SVG elements**, not an HTML string with inline JavaScript. This also makes the board testable with NiceGUI's user simulation (`.mark("pt-14").click()`).
- SVG text uses `ui.html('<text …>', tag='g')` because `ui.element` has no text content.
- **The only JavaScript in the app** is one line in `ui/board.py` (`focus_point`): `document.querySelector('[data-pt="N"]')?.focus()`. NiceGUI has no Python API to move keyboard focus. It is used for arrow-key movement between points and to restore focus after the board is redrawn.
- `ui.add_css` carries the theme (plain CSS, no imports, no fonts, no `url()`).

## 2. Randomness is injected, not stored in the state

The TypeScript state carried an RNG number. In Python the state is pure data and all randomness goes through a `Dice` protocol (`roll(faces)`, `coin()`): `SeededDice(seed)` (wraps `random.Random`) and `ScriptedDice(rolls, coins)` for tests. `apply_action(state, action, dice)` needs the dice only for throws and re-throws. Undo restores `SeededDice.snapshot()` so an undone throw comes back with the **same** dice (no re-rolling by undoing), as in the TypeScript version.

`new_game(options, starter=…)` takes the starter explicitly; `start_game(options, dice)` decides it by throwing (first X, or most X, per the rule option) and records the throws.

## 3. Parity testing method

- Node is not installed on the project owner's machine. Bun is, so the fixtures were generated with **Bun** (not Node) running `legacy-ts/engine/tools/gen-parity-fixtures.ts`. This was a one-off; nothing in the Python app or its tests needs Bun or Node. Regenerate with: `cd legacy-ts && bun run engine/tools/gen-parity-fixtures.ts ../tests/parity/fixtures`.
- Seeds are never compared across languages. Fixtures use **scripted dice** (`throwWith` in TypeScript, `throw_with` in Python) and, for re-throws, a forced outcome (found by searching the TS rng for the wanted face).
- Fixtures: 48 setups (every variant × starter × mieđut × equal odds, with tracks and home slots), 60 hand-built scenarios (legal actions, every candidate destination with its reason code, and the result of applying each legal move), and 22 scripted walks totalling 4,149 steps over 11 option configurations.
- Result: **no behavioural differences were found** between the TypeScript engine and the Python port; all 136 parity tests passed on the first complete run after a fixture-helper fix (JavaScript `indexOf` returns -1 where Python's `tuple.index` raises, mirrored in the test helper only).
- Since nothing differed, there was no case of choosing between the two on the rules; the fixtures therefore encode the same readings of the rules as `docs/rules-notes.md`.

## 4. Things that are deliberately different from the TypeScript version

| TypeScript | Python | Why |
| --- | --- | --- |
| `state.rng` inside `GameState` | injected `Dice`; undo via snapshot | pure, typed state; testable dice |
| Tutorial text inline in a component | all text in `i18n/en.json` (`tut.*`) | the brief asks for i18n-ready text |
| Hard AI: node budget checked every 64 nodes | checked on **every** node and while scoring children | **bug found in Python**: one node can take tens of milliseconds, so the old check let Hard overrun a 0.2 s budget by 3 s. A test now guards it. |
| Hard AI could not be stopped | cancel button; the cancel flag is polled by the search | brief: "time budget … and cancel button" |
| Undo restored the RNG (TypeScript: it lived in the state, so it was automatic) | `SeededDice.snapshot()` taken **before** each action | **bug found in Python**: the first version snapshotted after the action, so undoing a throw let the player re-roll. `test_undo_returns_the_same_dice` guards it. |
| New-game option `equalOdds` etc. | same names in snake_case (`equal_odds`) | Python naming |
| Rules panel text `help.diceApplication` | `help.dice_application` | snake_case keys follow option names |
| Move log oldest first | newest first | no JavaScript needed for auto-scroll |
| Settings in browser local storage | JSON file in the user's config directory, with a reset button | brief section 2 |

## 5. Dependencies

- Runtime: `nicegui` only (it brings FastAPI, uvicorn, Quasar, etc.).
- Dev: `pytest`, `hypothesis`, `ruff`, `mypy` as required, plus **`pytest-asyncio`**: NiceGUI's user-simulation test support is built on it, and the brief asks for a UI smoke test through that support.
- `hatchling` is the build backend named in `pyproject.toml` (a build-time tool, not a runtime dependency).
- Playwright was **not** added. During development I looked at the running app with the Playwright library that was already on this machine from the TypeScript version; the repository's tests do not depend on it.

## 6. Fonts and glyphs

No font or icon files are bundled: the CSS uses the system font stack, and NiceGUI serves its own Quasar and icon assets locally. A request log of the running app in Chromium showed **no external requests**. Because no font is bundled there is nothing to licence-check; the glossary diacritics (á č đ ŋ š ŧ ž) are plain Latin Extended characters that standard system fonts (San Francisco, Segoe UI, Roboto, DejaVu) contain, and they rendered correctly in the verification screenshots. If a font is ever bundled it must be checked for these seven letters and its licence recorded here.

## 7. The computer player runs outside the UI thread

The Hard AI runs through `nicegui.run.cpu_bound` (a process pool), with `asyncio.to_thread` as a fallback if no pool is available. The UI shows a "thinking" indicator and a cancel button. Cancelling abandons the search and plays a quick Medium move; the worker process finishes its (time-limited) search harmlessly in the background. Easy and Medium are fast and run inline.

## 8. Session and persistence

Settings (rule set, opponent, accessibility options, last Custom options, "seen the notice") live in `settings.json` in the platform config directory (`~/Library/Application Support/sahkku`, `%APPDATA%\sahkku`, or `$XDG_CONFIG_HOME/sahkku`, overridable with `SAHKKU_CONFIG_DIR`). A game belongs to one browser tab; reloading the tab starts a new game. "Copy game record" exports the seed, options and every throw and move as text so a game can be replayed.

## 9. Retiring the old stack

Everything TypeScript moved to `legacy-ts/`. `node_modules/` and `dist/` were deleted (they are regenerable). `legacy-ts/` is kept only because the parity fixtures were derived from it and the generator lives there. **It is safe to delete once you no longer want to regenerate the fixtures**; the Python tests do not read it.
