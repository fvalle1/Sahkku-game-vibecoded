import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { applyAction, candidatesFor, legalActions, legalMoves, playableDiceIndices } from '@engine';
import type { Action, Cand, GameState, RuleSet, Side } from '@engine';
import type { Level } from '@ai';
import { Board } from './Board';
import type { DestInfo } from './Board';
import { DiceTray } from './DiceTray';
import { RulesPanel } from './RulesPanel';
import { useT } from '../i18n';
import { beep, prefersReducedMotion, useSettings } from '../settings';
import { askAI } from '../aiClient';
import { describeEvent, sideName, winText } from '../format';
import { TERMS } from '../glossary';

export type Opponent = 'human' | Level;

interface LogEntry {
  key: number;
  text: string;
}

interface Props {
  rules: RuleSet;
  initial: GameState;
  opponent: Opponent;
  humanSide?: Side;
  /** Compact mode (tutorial): no log, no rules panel, no undo/restart chrome. */
  compact?: boolean;
  track?: GameState['tracks'][0] | null;
  onNewGame?: () => void;
  onRestart?: () => void;
  hint?: string;
}

export function GameView({
  rules,
  initial,
  opponent,
  humanSide = 0,
  compact,
  track,
  onNewGame,
  onRestart,
  hint,
}: Props) {
  const t = useT();
  const settings = useSettings();
  const [state, setState] = useState<GameState>(initial);
  const [history, setHistory] = useState<GameState[]>([]);
  const [log, setLog] = useState<LogEntry[]>(() => toLog(initial));
  const [selDie, setSelDie] = useState<number | null>(null);
  const [selPiece, setSelPiece] = useState<number | null>(null);
  const [msg, setMsg] = useState<string>('');
  const [fatePrompt, setFatePrompt] = useState<Cand[] | null>(null);
  const [thinking, setThinking] = useState(false);
  const [stake, setStake] = useState(1);
  const logKey = useRef(1);
  const aiSeed = useRef(initial.rng ^ 0x9e3779b9);

  function toLog(s: GameState): LogEntry[] {
    return s.events
      .map((e) => describeEvent(t, s.options, e))
      .filter((x): x is string => !!x)
      .map((text, i) => ({ key: -i - 1, text }));
  }

  // Reset when a new game is handed in.
  useEffect(() => {
    setState(initial);
    setHistory([]);
    setLog(toLog(initial));
    setSelDie(null);
    setSelPiece(null);
    setMsg('');
    setFatePrompt(null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initial]);

  const o = state.options;
  const isAI = opponent !== 'human';
  const humanTurn = state.phase !== 'over' && (!isAI || state.current === humanSide);
  const actions = useMemo(() => (humanTurn ? legalActions(state) : []), [state, humanTurn]);
  const moves = useMemo(() => (humanTurn ? legalMoves(state) : []), [state, humanTurn]);

  const commit = useCallback(
    (next: GameState, prev: GameState) => {
      setHistory((h) => [...h, prev]);
      setState(next);
      const lines = next.events
        .map((e) => describeEvent(t, next.options, e))
        .filter((x): x is string => !!x)
        .map((text) => ({ key: logKey.current++, text }));
      setLog((l) => [...l, ...lines]);
      if (settings.sound) {
        const last = next.events.find((e) => e.type === 'move');
        beep(last && last.type === 'move' && last.captured.length ? 220 : 440);
      }
    },
    [t, settings.sound],
  );

  const doAction = useCallback(
    (a: Action) => {
      try {
        commit(applyAction(state, a), state);
      } catch (err) {
        setMsg(String((err as Error).message));
        return;
      }
      setSelDie(null);
      setSelPiece(null);
      setFatePrompt(null);
      setMsg('');
    },
    [state, commit],
  );

  // Computer opponent
  useEffect(() => {
    if (!isAI || state.phase === 'over' || state.current === humanSide) return;
    let cancelled = false;
    setThinking(true);
    const fast = new URLSearchParams(location.search).has('fast'); // test hook: no thinking delay
    const delay = fast ? 0 : prefersReducedMotion() ? 120 : state.phase === 'throw' ? 500 : 650;
    const id = setTimeout(async () => {
      const a = await askAI(
        state,
        opponent as Level,
        (aiSeed.current = (aiSeed.current * 1664525 + 1013904223) >>> 0),
      );
      if (cancelled) return;
      setThinking(false);
      commit(applyAction(state, a), state);
    }, delay);
    return () => {
      cancelled = true;
      clearTimeout(id);
    };
  }, [state, isAI, opponent, humanSide, commit]);

  // Which die is in use?
  const playable = state.phase === 'move' ? playableDiceIndices(state) : [];
  const faces = new Set(playable.map((i) => state.dice[i].face));
  let die: number | null = null;
  if (humanTurn && state.phase === 'move') {
    if (
      selDie !== null &&
      playable.some((i) => state.dice[i].face === state.dice[selDie].face) &&
      !state.dice[selDie].used
    )
      die = selDie;
    else if (faces.size === 1) die = playable[0];
  }
  const face = die !== null ? state.dice[die].face : null;

  const movable = useMemo(() => {
    const set = new Set<number>();
    if (face) for (const m of moves) if (m.face === face) set.add(m.pieceId);
    return set;
  }, [moves, face]);

  const cands: Cand[] = useMemo(
    () => (humanTurn && selPiece !== null && face ? candidatesFor(state, selPiece, face) : []),
    [state, selPiece, face, humanTurn],
  );
  const dests = useMemo(() => {
    const map = new Map<number, DestInfo>();
    for (const c of cands) {
      const prev = map.get(c.to);
      map.set(c.to, {
        ok: (prev?.ok ?? false) || c.ok,
        capture: (prev?.capture ?? false) || (c.ok && c.out.captures.length > 0),
      });
    }
    return map;
  }, [cands]);

  function explain(pt: number): string {
    if (die === null) return t('reason.pick-die');
    const here = state.pieces.filter((p) => p.pt === pt && p.side === state.current);
    if (selPiece === null) {
      if (!here.length) return t('game.pickPiece');
      const p = here[0];
      if (!p.active && face !== 'X') return t('reason.only-x-wakes');
      const cs = candidatesFor(state, p.id, face!);
      const bad = cs.find((c) => c.reason);
      return bad?.reason ? t('reason.' + bad.reason) : t('reason.no-moves-piece');
    }
    const c = cands.find((x) => x.to === pt && !x.ok);
    if (c?.reason) return t('reason.' + c.reason);
    return t('reason.not-reachable');
  }

  function onPoint(pt: number) {
    if (!humanTurn) return;
    if (state.phase !== 'move') {
      setMsg(t('game.throw'));
      return;
    }
    // choose a destination?
    if (selPiece !== null) {
      const ok = cands.filter((c) => c.to === pt && c.ok);
      if (ok.length === 1 && die !== null) {
        doAction({ type: 'move', die, pieceId: selPiece, to: pt, fate: ok[0].fate });
        return;
      }
      if (ok.length > 1) {
        setFatePrompt(ok);
        return;
      }
    }
    // choose a piece?
    const here = state.pieces.filter((p) => p.pt === pt && movable.has(p.id));
    if (here.length) {
      const i = here.findIndex((p) => p.id === selPiece);
      const next = here[(i + 1) % here.length];
      setSelPiece(next.id);
      setFatePrompt(null);
      setMsg(t('game.pickDest'));
      return;
    }
    if (settings.explain) setMsg(explain(pt));
  }

  const status = (() => {
    if (state.phase === 'over') return winText(t, state);
    if (thinking && isAI && state.current !== humanSide) return t('game.aiThinking');
    if (state.phase === 'throw')
      return humanTurn ? `${t('game.yourTurn')} · ${sideName(t, state.current)}` : '';
    return t('game.turn', { side: sideName(t, state.current) });
  })();

  const guide = (() => {
    if (!humanTurn || state.phase !== 'move') return '';
    if (die === null) return t('game.pickDie');
    if (selPiece === null) return t('game.pickPiece');
    return t('game.pickDest');
  })();

  const remaining =
    state.winner === null
      ? 0
      : state.pieces.filter((p) => p.kind === 'soldier' && p.side === state.winner).length;
  const kingOwner = state.pieces.find((p) => p.kind === 'king');
  const canUndo = opponent === 'human' && history.length > 0;

  return (
    <div className={compact ? 'game compact' : 'game'}>
      <div className="board-col">
        <div className="statusbar" aria-live="polite">
          <strong>{status}</strong>
          {kingOwner ? (
            <span className="small">
              {' · '}
              {t(kingOwner.side === null ? 'king.owner.none' : `king.owner.${kingOwner.side}`)} (
              {TERMS.king})
            </span>
          ) : (
            <span className="small"> · {t('king.removed')}</span>
          )}
        </div>
        <Board
          state={state}
          dests={dests}
          movable={humanTurn ? movable : new Set()}
          selectedPieceId={selPiece}
          onPoint={onPoint}
          track={track}
          large={settings.largeTouch}
        />
        <p className="guide" aria-live="polite">
          {fatePrompt ? (
            <>
              {t('game.chooseFate')}{' '}
              {fatePrompt.map((c) => (
                <button
                  key={c.fate}
                  type="button"
                  onClick={() =>
                    die !== null &&
                    doAction({ type: 'move', die, pieceId: c.pieceId, to: c.to, fate: c.fate })
                  }
                >
                  {t('game.fate.' + c.fate)}
                </button>
              ))}
            </>
          ) : (
            msg || hint || guide
          )}
        </p>
      </div>

      <div className="side-col">
        <div className="controls">
          {state.phase === 'throw' && humanTurn && (
            <button type="button" className="primary" onClick={() => doAction({ type: 'throw' })}>
              {t('game.throw')} <span className="term">({TERMS.dice})</span>
            </button>
          )}
          {!compact && (
            <>
              <button type="button" onClick={onNewGame}>
                {t('game.new')}
              </button>
              <button type="button" onClick={onRestart}>
                {t('game.restart')}
              </button>
              <button
                type="button"
                disabled={!canUndo}
                title={opponent !== 'human' ? t('game.undoUnavailable') : undefined}
                onClick={() => {
                  const prev = history[history.length - 1];
                  setHistory(history.slice(0, -1));
                  setState(prev);
                  setSelDie(null);
                  setSelPiece(null);
                  setLog((l) =>
                    l.slice(
                      0,
                      Math.max(
                        0,
                        l.length - state.events.filter((e) => describeEvent(t, o, e)).length,
                      ),
                    ),
                  );
                }}
              >
                {t('game.undo')}
              </button>
            </>
          )}
        </div>
        {state.dice.length > 0 && (
          <DiceTray
            state={state}
            actions={actions}
            selected={die}
            onSelect={(i) => {
              setSelDie(i);
              setSelPiece(null);
              setFatePrompt(null);
              setMsg('');
            }}
            onAction={doAction}
            disabled={!humanTurn}
          />
        )}
        {state.phase === 'move' && humanTurn && playable.length === 0 && (
          <p className="small">{t('game.noMove')}</p>
        )}

        {state.phase === 'over' && (
          <section className="panel stakes">
            <h2>{t('game.stakes')}</h2>
            <label>
              {t('game.stakes.value')}{' '}
              <input
                type="number"
                min={0}
                value={stake}
                onChange={(e) => setStake(Number(e.target.value))}
              />
            </label>
            <p>
              {t('game.stakes.result', { n: remaining, v: stake })} = {remaining * stake}
            </p>
          </section>
        )}

        {!compact && (
          <>
            <section className="panel log" aria-label={t('log.title')}>
              <h2>{t('log.title')}</h2>
              <ol className="loglist" tabIndex={0}>
                {log.length === 0 && <li className="small">{t('log.empty')}</li>}
                {log.slice(-80).map((l) => (
                  <li key={l.key}>{l.text}</li>
                ))}
              </ol>
            </section>
            <RulesPanel rules={rules} state={state} />
          </>
        )}
      </div>
    </div>
  );
}
