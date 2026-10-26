/* Self-play harness: bun run ai/scripts/selfplay.ts [games=1000] [hardGames=6] */
import { VARIANTS, applyAction, checkInvariants, newGame } from '@engine';
import type { GameState, Side } from '@engine';
import { chooseAction, mulberry } from '../src';
import type { Level } from '../src';

const games = Number(process.argv[2] ?? 1000);
const hardGames = Number(process.argv[3] ?? 6);
const MAX_ACTIONS = 6000;

interface Result {
  finished: boolean;
  winner: Side | null;
  starter: Side;
  violations: string[];
  actions: number;
}

function play(
  opts: GameState['options'],
  seed: number,
  levels: [Level, Level],
  budget: number,
): Result {
  let s = newGame(opts, { seed, miedut: seed % 2 === 0, equalOdds: seed % 5 === 0 });
  const starter = s.current;
  const rand = mulberry(seed * 7919);
  const violations: string[] = [];
  let n = 0;
  while (s.phase !== 'over' && n < MAX_ACTIONS) {
    const a = chooseAction(s, levels[s.current], rand, budget);
    s = applyAction(s, a);
    const v = checkInvariants(s);
    if (v.length) {
      violations.push(...v);
      break;
    }
    n++;
  }
  return { finished: s.phase === 'over', winner: s.winner, starter, violations, actions: n };
}

let failed = false;
for (const rs of VARIANTS) {
  const t0 = Date.now();
  const stats = {
    finished: 0,
    unfinished: 0,
    violations: 0,
    seatWins: [0, 0],
    starterWins: 0,
    actions: 0,
  };
  const pairs: [Level, Level][] = [
    ['easy', 'easy'],
    ['medium', 'medium'],
    ['easy', 'medium'],
    ['medium', 'easy'],
  ];
  for (let i = 0; i < games; i++) {
    const lv = pairs[i % pairs.length];
    const r = play(rs.options, i + 1, lv, 0);
    if (r.violations.length) {
      stats.violations++;
      console.error(`  violation in ${rs.id} seed ${i + 1}:`, r.violations[0]);
    }
    if (r.finished) {
      stats.finished++;
      if (r.winner !== null) {
        stats.seatWins[r.winner]++;
        if (r.winner === r.starter) stats.starterWins++;
      }
      stats.actions += r.actions;
    } else stats.unfinished++;
  }
  let hardOk = 0;
  for (let i = 0; i < hardGames; i++) {
    const r = play(rs.options, 90000 + i, i % 2 ? ['hard', 'medium'] : ['medium', 'hard'], 60);
    if (r.finished && !r.violations.length) hardOk++;
  }
  const sw = stats.seatWins;
  const seatShare = sw[0] / Math.max(1, sw[0] + sw[1]);
  const starterShare = stats.starterWins / Math.max(1, stats.finished);
  const oneSided = seatShare < 0.35 || seatShare > 0.65;
  console.log(
    `${rs.name.padEnd(28)} games ${games}  finished ${stats.finished}  unfinished ${stats.unfinished}  ` +
      `violations ${stats.violations}  seat0 win ${(seatShare * 100).toFixed(1)}%  starter win ${(starterShare * 100).toFixed(1)}%  ` +
      `avg actions ${(stats.actions / Math.max(1, stats.finished)).toFixed(0)}  hard ${hardOk}/${hardGames}  ` +
      `${((Date.now() - t0) / 1000).toFixed(1)}s${oneSided ? '  ⚠ one-sided' : ''}`,
  );
  if (stats.unfinished || stats.violations || hardOk < hardGames) failed = true;
}
if (failed) {
  console.error('Self-play found problems.');
  process.exit(1);
}
