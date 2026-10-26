import { useT } from '../i18n';
import { GLOSSARY } from '../glossary';

// TODO: replace these placeholders before any public release.
export const REPORT_MAILTO =
  'mailto:REPLACE-WITH-CONTACT@example.invalid?subject=Rules%20or%20cultural%20problem';
export const REPORT_ISSUES = 'https://example.invalid/REPLACE-WITH-ISSUE-TRACKER';

export function About() {
  const t = useT();
  return (
    <div className="page about">
      <h1>{t('about.title')}</h1>

      <section>
        <h2>An unofficial project</h2>
        <p>
          This is an unofficial hobby implementation made by a developer who is not Sámi. Sáhkku
          belongs to Sámi culture and tradition. This app is not made, checked or endorsed by any
          Sámi person, organisation or institution, and it has no connection to any of them.
        </p>
        <p>
          Nothing here is the “official” or “correct” sáhkku. The rule sets are modern
          reconstructions. They differ between regions and families, and some details are guesses
          that the reconstructors themselves mark as uncertain. The Rules panel always shows which
          variant is active and which options are uncertain.
        </p>
        <p>
          The pieces are deliberately plain shapes. They are placeholders: pieces designed or
          approved by Sámi duojárs would be better.
        </p>
      </section>

      <section>
        <h2>Short history</h2>
        <p>
          A dice-and-board game of this kind may be mentioned in writing from the 1600s, and by the
          middle of the 1800s sáhkku was played in places far apart in Sápmi. During the 1900s it
          nearly vanished: religious pressure against games, assimilation policy and racism, and the
          destruction of the war years all played a part. Since the 1980s people have taught the
          rules again, and interest grew again after 2018 with new sets, courses and cups.
        </p>
      </section>

      <section>
        <h2>Rule reconstructions and credits</h2>
        <ul>
          <li>
            Mikkel Berg-Nordlie: the published collection of rule sets (Reaidu, UiT / OsloMet), the
            main source for this app.
          </li>
          <li>
            Edmund Johansen: reconstruction of the Lágesvuotna rules, and the tradition of making
            sets.
          </li>
          <li>
            Hans Aslak Guttorm: documentation of the Vuovdaguoika rules, passed on in his family.
          </li>
          <li>Yngvar Mejland: the Návuotna (Ráisa) rules, written down in the 1950s.</li>
          <li>J. A. Friis: an 1871 description of the game.</li>
          <li>Peter Michaelsen: research on Nordic running-fight games.</li>
          <li>Thierry Depaulis: comparative research on the wider family of games.</li>
          <li>
            Várjjat Sámi Musea (Varanger Sámi Museum) and the Sámi sáhkku cups: for keeping the game
            alive in modern times.
          </li>
        </ul>
        <p className="small">
          All rule descriptions in this app are my own summaries. If you spot a mistake, please say
          so using the link below.
        </p>
      </section>

      <section>
        <h2>Sources</h2>
        <ul>
          <li>
            <a href="https://result.uit.no/reaidu/" rel="noreferrer noopener" target="_blank">
              Reaidu – Berg-Nordlie’s rule pages
            </a>{' '}
            (Norwegian)
          </li>
          <li>
            <a
              href="https://en.wikipedia.org/wiki/S%C3%A1hkku"
              rel="noreferrer noopener"
              target="_blank"
            >
              Wikipedia: Sáhkku
            </a>
          </li>
          <li>
            <a
              href="http://norcom2019.math.aau.dk/Michaelsen.pdf"
              rel="noreferrer noopener"
              target="_blank"
            >
              Michaelsen: “Daldøs og Sakku”
            </a>
          </li>
          <li>Depaulis, “An Arab Game in the North Pole?”, Board Games Studies 4 (2001)</li>
          <li>
            <a
              href="https://norskfolkemuseum.no/en/shkku-eahket--learn-to-play-a-smi-board-game"
              rel="noreferrer noopener"
              target="_blank"
            >
              Norsk Folkemuseum: learn to play sáhkku
            </a>
          </li>
        </ul>
      </section>

      <section>
        <h2>Terms used in the app</h2>
        <p className="small">
          Sámi words appear next to the English labels, never instead of them, and are used exactly
          as supplied.
        </p>
        <table className="glossary">
          <thead>
            <tr>
              <th scope="col">Concept</th>
              <th scope="col">Term</th>
            </tr>
          </thead>
          <tbody>
            {GLOSSARY.map((g) => (
              <tr key={g.concept}>
                <td>{g.concept}</td>
                <td lang="se">{g.term}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="small">
          Some old accounts use a hostile nickname for the game that was given by critics. It is not
          a name the players used, and it is not used here.
        </p>
      </section>

      <section>
        <h2>Corrections</h2>
        <p>
          Spotted a rules or cultural problem? Please tell me:{' '}
          <a href={REPORT_MAILTO}>send a message</a> or <a href={REPORT_ISSUES}>open an issue</a>.
          (These two links are placeholders until a real contact is set up.)
        </p>
      </section>
    </div>
  );
}
