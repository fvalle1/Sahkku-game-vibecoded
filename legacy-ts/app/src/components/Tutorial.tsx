import { useMemo, useState } from 'react';
import { newGame } from '@engine';
import type { GameState, RuleSet } from '@engine';
import { Board } from './Board';
import { GameView } from './GameView';
import { RulesPanel } from './RulesPanel';
import { useT } from '../i18n';
import { dice, guards, scenario } from '../scenarios';
import type { PieceSpec } from '../scenarios';
import { TERMS } from '../glossary';

interface Step {
  title: string;
  body: string[];
  state?: () => GameState;
  hint?: string;
  showTrack?: boolean;
  staticBoard?: boolean;
}

function useSteps(rules: RuleSet): Step[] {
  const o = rules.options;
  const unit = o.boardStyle === 'squares' ? 'squares' : 'lines';
  const mid = Math.floor(o.cols / 2);
  const steps: Step[] = [];

  steps.push({
    title: 'The board and the armies',
    staticBoard: true,
    state: () => newGame(o, { seed: 5 }),
    body: [
      `The board (${TERMS.board}) has three rows of ${o.cols} ${unit} (${TERMS.lines}). Each player has a home row nearest them; the middle row is shared; the top row is the opponent's home row.`,
      `Each side has ${o.soldiersPerSide} soldiers (${TERMS.soldiers}). One side is called men (${TERMS.men}), the other women (${TERMS.women}). In this app men are round and women are triangular. Hollow pieces are asleep; filled pieces are awake.`,
      `The ring in the middle of the middle row is the Castle (${TERMS.castle}). The neutral king (${TERMS.king}, the diamond) starts there${o.queens ? `; each side also has a queen (${TERMS.queen}) on a marked point` : ''}.`,
    ],
  });

  steps.push({
    title: 'The dice',
    staticBoard: true,
    body: [
      `${o.diceCount} four-sided dice (${TERMS.dice}) are thrown. Faces: ${o.faces.map((f) => (f === 'blank' ? 'blank' : f)).join(', ')}. This app assumes every face is equally likely (25%), because no source says otherwise.`,
      o.faces.includes('blank')
        ? o.blankValue === 0
          ? `A blank is worth zero (${TERMS.zero}): no move.`
          : 'A blank is worth four moves.'
        : 'There is no blank face in this rule set.',
      `Each die is played as its own move; dice are never added together. ${
        o.diceOrder === 'fixed'
          ? `Dice must be played in a fixed order: ${o.fixedOrder.join(', then ')}. If the next die in that order has no legal move, the rest of your turn is lost.`
          : 'You may play the dice in any order.'
      }`,
      o.rethrow === 'single'
        ? 'When a die shows X you may use it or throw that die again until it shows something else.'
        : o.rethrow === 'triple'
          ? 'If all dice show X you may use them or throw all of them again.'
          : 'X cannot be re-thrown in this rule set.',
      `The first player to throw an X starts${o.startRule === 'most-x' ? ' (here: the player with most X on a throw)' : ''}.`,
    ],
  });

  steps.push({
    title: 'Waking a soldier with X',
    state: () => scenario(o, null, dice(o, 'X', 'II', 'II'), false),
    hint: 'Pick the X, then the glowing piece, then its destination.',
    body: [
      `Soldiers start asleep and cannot move. An X wakes (${TERMS.activate}) one soldier${
        o.activation === 'up'
          ? ' and moves it straight up onto the middle row'
          : o.activation === 'first-middle'
            ? ' and puts it on the first middle-row point'
            : ' and moves it one line forward'
      }.`,
      o.activationOrder === 'front-first'
        ? 'Soldiers must be woken in order, from the front of the row backwards.'
        : 'You may wake any soldier you like.',
      'An X can also move an awake piece one line instead.' +
        (o.queens ? ' An X also frees your queen.' : ''),
    ],
  });

  steps.push({
    title: 'The track',
    showTrack: true,
    state: () => scenario(o, null, dice(o, 'III', 'II', 'II'), true),
    hint: 'The arrows show the track of the Men. Try moving an awake soldier.',
    body: [
      o.track === 'figure-eight'
        ? 'Soldiers walk a figure of eight: right along the home row, left along the middle row, right along the far row, left along the middle row again, then back down into the home row.'
        : o.track === 'loop-from-middle'
          ? 'Soldiers walk left along the middle row, then right along the far row, and round and round, never returning to the home row (in this experimental reconstruction the track is a hypothesis).'
          : `Soldiers walk right along the home row, left along the middle row, right along the far row, and then round and round between the middle and far rows (${TERMS.vuosttut}, "against").`,
      o.allowMiedut
        ? `The player who does not start may choose ${TERMS.miedut} ("with"): they walk the mirrored track, so both armies enter the middle row at the same place. Choose it in the new-game dialog.`
        : '',
      'Each die value is the number of lines a piece moves along the track.',
    ].filter(Boolean),
  });

  const trackStart = (n: number) => n - 3;
  const capSpecs = (): PieceSpec[] => {
    const base = scenario(o, null, ['X'], false);
    return [
      { kind: 'soldier', side: 0, row: 1, col: trackStart(o.cols) },
      { kind: 'soldier', side: 1, row: 1, col: trackStart(o.cols) - 3 },
      ...guards(base),
      { kind: 'king', side: null, row: 1, col: mid },
    ];
  };
  steps.push({
    title: 'Capturing',
    state: () => scenario(o, capSpecs(), dice(o, 'III'), false),
    hint: 'Move the Men soldier three lines onto the enemy soldier.',
    body: [
      `Land on a line with enemy pieces and you capture (${TERMS.capture}) all of them.`,
      o.capturesInactive
        ? 'Sleeping soldiers can be captured too.'
        : 'Sleeping pieces are protected: they cannot be captured, and nothing may land on a line that holds one.',
      o.stacking === 'single'
        ? 'Only one piece may stand on a line, and soldiers may not jump over their own army.'
        : 'Several pieces of one army may share a line, which is risky: one capture takes them all.',
    ],
  });

  const kingSpecs = (): PieceSpec[] => {
    const base = scenario(o, null, ['X'], false);
    const dormant = o.kingAcquire !== 'landing';
    return [
      { kind: 'soldier', side: 0, row: 1, col: dormant ? 1 : mid + 3 },
      ...guards(base),
      { kind: 'king', side: null, row: 1, col: mid },
    ];
  };
  steps.push({
    title: `The king (${TERMS.king})`,
    state: () =>
      scenario(o, kingSpecs(), dice(o, o.kingAcquire !== 'landing' ? 'II' : 'III'), false),
    hint:
      o.kingAcquire !== 'landing'
        ? 'Walk the soldier onto the far home row to wake the king.'
        : 'Land the soldier on the king.',
    body: [
      o.kingAcquire !== 'landing'
        ? "In this reconstruction the king stands still until a soldier reaches the opponent's home row. That player takes the king."
        : o.kingMode === 'push'
          ? 'The king belongs to nobody at first. Landing on him pushes him one line forward (knocking out an enemy soldier there) and you take him. He can be pushed away again.'
          : 'The king belongs to nobody at first. Landing on him takes him over. He can never be captured, but the opponent can take him back the same way.',
      o.kingMovement === 'figure-eight'
        ? 'He moves forward or backward, and can cross between rows, but may not turn while using one die.'
        : 'He moves like your soldiers, with the dice values.',
      'He is on loan: you can still lose with the king if you have no soldiers' +
        (o.kingAloneLoses
          ? '.'
          : ' (here that depends on the option "a lone king does not save you").'),
    ],
  });

  if (o.queens) {
    steps.push({
      title: `The queen (${TERMS.queen})`,
      state: () => scenario(o, null, dice(o, 'X', 'II', 'II'), false),
      hint: 'Pick the X, then your glowing queen (right of the Castle), then a destination.',
      body: [
        'Each queen starts asleep on a marked point. She cannot move, be captured or be landed on until an X frees her.',
        'After that she moves like the king, but she can be captured like a soldier, and losing her loses the game.',
      ],
    });
  }

  steps.push({
    title: 'Winning',
    staticBoard: true,
    state: () => newGame(o, { seed: 5 }),
    body: [
      o.queens
        ? 'You win when the opponent has no soldiers left, or when you capture their queen.'
        : 'You win when the opponent has no soldiers left.',
      o.kingAloneLoses
        ? 'A player who has only the king has still lost.'
        : 'A player who has only the king can play on.',
      'Optionally, players may agree a value per soldier before play; the loser then pays that value for each soldier the winner has left. The app has a counter for this at the end of a game. No money is involved.',
    ],
  });

  return steps;
}

export function Tutorial({ rules, onDone }: { rules: RuleSet; onDone: () => void }) {
  const t = useT();
  const steps = useSteps(rules);
  const [i, setI] = useState(0);
  const [nonce, setNonce] = useState(0);
  const step = steps[i];
  const state = useMemo(() => step.state?.(), [step, nonce]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="page tutorial">
      <h1>{t('tutorial.title')}</h1>
      <p className="small">
        {t('tutorial.usingVariant')} <strong>{rules.name}</strong> ·{' '}
        {t('tutorial.step', { n: i + 1, total: steps.length })}
      </p>
      <h2>{step.title}</h2>
      {step.body.map((b, k) => (
        <p key={k}>{b}</p>
      ))}
      {state &&
        (step.staticBoard ? (
          <Board
            state={state}
            dests={new Map()}
            movable={new Set()}
            selectedPieceId={null}
            onPoint={() => {}}
            interactive={false}
          />
        ) : (
          <GameView
            key={`${i}-${nonce}`}
            rules={rules}
            initial={state}
            opponent="human"
            compact
            track={step.showTrack ? state.tracks[0] : null}
            hint={step.hint ? `${t('tutorial.try')} ${step.hint}` : undefined}
          />
        ))}
      <div className="actions">
        <button type="button" disabled={i === 0} onClick={() => setI(i - 1)}>
          {t('tutorial.back')}
        </button>
        {!step.staticBoard && (
          <button type="button" onClick={() => setNonce(nonce + 1)}>
            {t('tutorial.reset')}
          </button>
        )}
        {i < steps.length - 1 ? (
          <button type="button" className="primary" onClick={() => setI(i + 1)}>
            {t('tutorial.next')}
          </button>
        ) : (
          <button type="button" className="primary" onClick={onDone}>
            {t('tutorial.done')}
          </button>
        )}
      </div>
      <RulesPanel rules={rules} />
    </div>
  );
}
