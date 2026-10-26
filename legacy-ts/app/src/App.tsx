import { useEffect, useMemo, useState } from 'react';
import { LAGESVUOTNA, getVariant, newGame } from '@engine';
import type { RuleOptions } from '@engine';
import { GameView } from './components/GameView';
import { NewGameDialog } from './components/NewGameDialog';
import type { GameConfig } from './components/NewGameDialog';
import { Tutorial } from './components/Tutorial';
import { About } from './components/About';
import { I18nContext, makeT } from './i18n';
import {
  DEFAULT_SETTINGS,
  SettingsContext,
  getFlag,
  loadSettings,
  prefersReducedMotion,
  saveSettings,
  setFlag,
} from './settings';
import type { Settings } from './settings';

function useHash(): string {
  const [h, setH] = useState(location.hash);
  useEffect(() => {
    const f = () => setH(location.hash);
    addEventListener('hashchange', f);
    return () => removeEventListener('hashchange', f);
  }, []);
  return h;
}

function makeGame(c: GameConfig) {
  return newGame(c.rules.options, { seed: c.seed, miedut: c.miedut, equalOdds: c.equalOdds });
}

export default function App() {
  const t = useMemo(() => makeT('en'), []);
  const hash = useHash();
  const [settings, setSettings] = useState<Settings>(() => loadSettings());
  const [showSettings, setShowSettings] = useState(false);
  const [firstRun, setFirstRun] = useState(() => !getFlag('seenNotice'));
  const [dialog, setDialog] = useState(false);
  const [custom, setCustom] = useState<RuleOptions>({ ...LAGESVUOTNA.options });
  const [config, setConfig] = useState<GameConfig>(() => ({
    rules: LAGESVUOTNA,
    opponent: 'medium',
    humanSide: 0,
    seed: (Math.random() * 2 ** 32) >>> 0,
    equalOdds: false,
    miedut: false,
  }));
  const [gameNo, setGameNo] = useState(0);
  const initial = useMemo(() => makeGame(config), [config, gameNo]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => saveSettings(settings), [settings]);
  useEffect(() => {
    const r = document.documentElement;
    r.dataset.cb = settings.colorblind ? '1' : '0';
    r.dataset.noanim = !settings.diceAnim || prefersReducedMotion() ? '1' : '0';
  }, [settings]);

  const page = hash.startsWith('#/tutorial')
    ? 'tutorial'
    : hash.startsWith('#/about')
      ? 'about'
      : 'play';
  const set = (k: keyof Settings, v: boolean) => setSettings({ ...settings, [k]: v });

  return (
    <I18nContext.Provider value={t}>
      <SettingsContext.Provider value={settings}>
        <a className="skip" href="#main">
          Skip to content
        </a>
        <header className="top">
          <div className="brand">
            <strong>{t('app.title')}</strong>
            <span className="small"> {t('app.subtitle')}</span>
          </div>
          <nav aria-label="Main">
            <a href="#/" aria-current={page === 'play' ? 'page' : undefined}>
              {t('nav.play')}
            </a>
            <a href="#/tutorial" aria-current={page === 'tutorial' ? 'page' : undefined}>
              {t('nav.tutorial')}
            </a>
            <a href="#/about" aria-current={page === 'about' ? 'page' : undefined}>
              {t('nav.about')}
            </a>
            <button type="button" onClick={() => setShowSettings(true)}>
              {t('nav.settings')}
            </button>
          </nav>
        </header>
        <main id="main">
          {page === 'play' && (
            <>
              <p className="badge-line">
                <span className="badge big" data-testid="variant-badge">
                  {config.rules.name}
                </span>
                <span className={`badge status-${config.rules.status}`}>
                  {t('status.' + config.rules.status)}
                </span>
              </p>
              <GameView
                key={gameNo}
                rules={config.rules}
                initial={initial}
                opponent={config.opponent}
                humanSide={config.humanSide}
                onNewGame={() => setDialog(true)}
                onRestart={() => setGameNo(gameNo + 1)}
              />
            </>
          )}
          {page === 'tutorial' && (
            <Tutorial rules={config.rules} onDone={() => (location.hash = '#/')} />
          )}
          {page === 'about' && <About />}
        </main>
        <footer className="foot small">
          Unofficial hobby project by a non-Sámi developer. Rules are reconstructions. No tracking,
          no cookies. <a href="#/about">{t('nav.about')}</a>
        </footer>

        {dialog && (
          <NewGameDialog
            initial={{
              variantId: config.rules.id,
              custom,
              opponent: config.opponent,
              equalOdds: config.equalOdds,
            }}
            onCancel={() => setDialog(false)}
            onStart={(c, cust) => {
              setCustom(cust);
              setConfig(c);
              setGameNo(gameNo + 1);
              setDialog(false);
              if (c.rules.id !== 'custom') getVariant(c.rules.id);
            }}
          />
        )}

        {showSettings && (
          <div className="overlay" onKeyDown={(e) => e.key === 'Escape' && setShowSettings(false)}>
            <div className="dialog" role="dialog" aria-modal="true" aria-labelledby="set-title">
              <h2 id="set-title">{t('settings.title')}</h2>
              {(['diceAnim', 'sound', 'colorblind', 'largeTouch', 'explain'] as const).map((k) => (
                <label className="check" key={k}>
                  <input
                    type="checkbox"
                    checked={settings[k]}
                    onChange={(e) => set(k, e.target.checked)}
                  />{' '}
                  {t('settings.' + k)}
                </label>
              ))}
              {prefersReducedMotion() && <p className="small">{t('settings.reduced')}</p>}
              <div className="actions">
                <button
                  type="button"
                  className="primary"
                  autoFocus
                  onClick={() => setShowSettings(false)}
                >
                  {t('settings.close')}
                </button>
                <button type="button" onClick={() => setSettings(DEFAULT_SETTINGS)}>
                  Reset
                </button>
              </div>
            </div>
          </div>
        )}

        {firstRun && (
          <div className="overlay">
            <div
              className="dialog"
              role="alertdialog"
              aria-modal="true"
              aria-labelledby="fr-title"
              aria-describedby="fr-body"
            >
              <h2 id="fr-title">{t('firstrun.title')}</h2>
              <p id="fr-body">{t('firstrun.body')}</p>
              <div className="actions">
                <button
                  type="button"
                  className="primary"
                  autoFocus
                  onClick={() => {
                    setFlag('seenNotice');
                    setFirstRun(false);
                  }}
                >
                  {t('firstrun.ok')}
                </button>
                <a
                  className="btn"
                  href="#/about"
                  onClick={() => {
                    setFlag('seenNotice');
                    setFirstRun(false);
                  }}
                >
                  {t('firstrun.about')}
                </a>
              </div>
            </div>
          </div>
        )}
      </SettingsContext.Provider>
    </I18nContext.Provider>
  );
}
