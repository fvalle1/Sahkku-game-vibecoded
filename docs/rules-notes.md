# Rules notes

How the rule sets were built, what was verified, and where I had to interpret. All text here is paraphrase.

## What was checked, and how

| Source                                                                                                     | Status                                                                                                                                                                                                                                                      |
| ---------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Berg-Nordlie's Reaidu pages (Norwegian), supplied locally as `docs/sources/reaidu-sahkku-no.txt`           | **Read in full.** Treated as primary. Not copied into the repo (the file is git-ignored). Live URL: https://result.uit.no/reaidu/ — a fetch from the build environment failed with a TLS "self signed certificate" error, so the live site was not checked. |
| Wikipedia, "Sáhkku" (English) — https://en.wikipedia.org/wiki/S%C3%A1hkku                                  | Fetched. Consistent with the Reaidu summary (three-row board, X-II-III-blank dice, regional differences, queens only in Lágesvuotna). Nothing new used.                                                                                                     |
| Norsk Folkemuseum event page — https://norskfolkemuseum.no/en/shkku-eahket--learn-to-play-a-smi-board-game | Appeared in a search; only used to confirm that the modern revival and teaching sessions exist.                                                                                                                                                             |
| Michaelsen, "Daldøs og Sakku" / norcom2019.math.aau.dk/Michaelsen.pdf                                      | **Not verified** (not fetched).                                                                                                                                                                                                                             |
| Depaulis, "An Arab Game in the North Pole?", Board Games Studies 4 (2001)                                  | **Not verified.**                                                                                                                                                                                                                                           |
| Fyhn et al., school mathematics paper (ovttas.no)                                                          | **Not verified.**                                                                                                                                                                                                                                           |
| Varanger Sámi Museum pages                                                                                 | **Not verified.**                                                                                                                                                                                                                                           |

## Where the primary text corrected the brief or my first implementation

1. **Návuotna activation.** The text allows several soldiers on one square and waking any soldier. My first draft refused to let a soldier step onto a neighbour's sleeping square for every variant; that made free activation impossible from the opening position. Now "nobody may land on a sleeping piece, including the owner" applies only where sleeping pieces are protected (Lágesvuotna).
2. **"Free soldiers" in Vuovdaguoika.** The text only lets soldiers pass each other; it does not allow two pieces on one line. So the option is `jumpOwnSoldiers`, separate from `stacking`.
3. **King moving "up and down".** The text says the Lágesvuotna king moves right, left, up and down, may not turn within one die, and treats a bend between rows as straight. The brief's more specific wording (II crosses home to enemy row, X crosses to the middle row) is not in the text I read. It is kept as the option `royalVerticalCrossing` (default on) and flagged uncertain.
4. **The "devil's game" nickname** is attributed in the text to leaders of the Læstadian revival movement, not to missionaries. See `CULTURAL_NOTES.md`.
5. **Queens' start points** match the brief (4th line from each end of the middle row, one queen each side of the king, on the owner's right as seen from their seat, per the photo caption).

## Rule options (every uncertain item is an option)

Defined in `src/sahkku/rules/options.py` (`RuleOptions`), values per variant in `src/sahkku/rules/variants.py`, labelled in `src/sahkku/i18n/en.json`. (The same text applied to the original TypeScript version, now in `legacy-ts/`.) Option names here are camelCase as in that version; in Python they are snake_case. Uncertain options carry a note shown in the Rules panel.

| Option                                                        | Why it is an option                                                                                                                                                     |
| ------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `faces` / equal odds                                          | No source states probabilities. 25% per face is an assumption.                                                                                                          |
| `blankValue` (0 or 4)                                         | Lágesvuotna 0; Vuovdaguoika/Gávkevuotna 4; Unjárga unknown (both suggested).                                                                                            |
| `diceOrder`, `fixedOrder`                                     | Fixed in Lágesvuotna (X, III, II) and Ráisa (X, I, II, III); free in Máze and Vuovdaguoika; unknown in Unjárga (offers X, 4, 3, 2).                                     |
| `rethrow`                                                     | `single`: any X die until non-X (Lágesvuotna, Návuotna, Unjárga A). `triple`: only when all dice show X (known inland of Deatnu/Anár, not from Gávkevuotna; Unjárga B). |
| `startRule`                                                   | First X (all); most X on three dice (also described for Lágesvuotna).                                                                                                   |
| `track`                                                       | Standard loop (Návuotna, Vuovdaguoika); figure-eight (Lágesvuotna); Unjárga unknown (default is a hypothesis; mieđut and figure-eight offered).                         |
| `activation`                                                  | Step one line (most); straight up (Unjárga, as the reconstructor reads it); first middle-row point (the alternative reading he mentions).                               |
| `activationOrder`                                             | Front-first everywhere except Návuotna (free). Unjárga's is a choice made by the reconstructor.                                                                         |
| `allowMiedut`                                                 | The player who does not start picks mieđut (Vuovdaguoika/Gávkevuotna; also offered for Unjárga).                                                                        |
| `capturesInactive`                                            | No in Lágesvuotna; yes in Návuotna, Vuovdaguoika, Unjárga.                                                                                                              |
| `stacking`, `jumpOwnSoldiers`                                 | Several per line in Lágesvuotna and Návuotna; one per line and no jumping in Vuovdaguoika; unknown in Unjárga (both offered).                                           |
| `kingMode`                                                    | Landing takes the king (Lágesvuotna, Návuotna, Unjárga); landing pushes it forward (Vuovdaguoika).                                                                      |
| `kingKnockOut`                                                | "Ohcejot gonagas": lander may take or remove the king; Unjárga option (b). Off by default and conflicts with "the king is never captured".                              |
| `kingAcquire`                                                 | Unjárga: the king waits until a soldier reaches the far home row; then (a) landing retakes (default), (b) knock-out, (c) reaching the far row takes it every time.      |
| `kingMovement`, `royalVerticalCrossing`, `royalsShareWithOwn` | See point 3 above and the text on royal pieces sharing lines.                                                                                                           |
| `kingAloneLoses`                                              | Yes in Lágesvuotna and Návuotna; the Unjárga reconstructor suggests yes; Vuovdaguoika's text says only "no pieces left".                                                |
| `queenStart`                                                  | Mirror layout option.                                                                                                                                                   |

An older account mentions that an X used for movement might count five steps with a re-throw. The primary text says one line, which is what is implemented; this stays open.

## Interpretations I made that the sources do not settle

- **Kings and queens capture by landing** on a line with enemy pieces, like soldiers (the text's example has the king capturing a soldier). Where sleeping pieces are protected, they cannot land there either.
- **A soldier may not land on a line holding its own king or queen** unless the option for royal pieces sharing lines is on. The text states the king/queen rule from the royal piece's point of view only.
- **Fixed dice order loses the turn** when the first die in the order has no legal action. A re-throw counts as a legal action for an X die.
- **Starting throws are simulated** at game creation (who throws first is random, from the seed), and the starter then makes a normal first throw. The throws are shown in the Rules panel.
- **Unjárga: nobody may land on the dormant king.** The text says the king "stands still"; letting enemy soldiers share his line would leave enemies on one line once he wakes.
- **Unjárga option (c)** is added on top of (a) landing, not instead of it.
- **Equal odds** wakes the three front soldiers in place. With "straight up" activation they stand on the middle row instead; when mieđut would put both armies on the same points, the second army uses the mirrored columns.
- **Stakes** are a counter in the UI only.
- **Dice**: faces are drawn uniformly from the four listed faces, using a seeded generator.

## Not implemented

Online play, Daldøs (a different game, deliberately kept separate), a Norwegian or Sámi interface.
