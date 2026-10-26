import type { RuleOptions, RuleSet } from './types';

const base: RuleOptions = {
  cols: 15,
  boardStyle: 'lines',
  extraMarks: true,
  soldiersPerSide: 15,
  queens: false,
  queenStart: 'right',
  queenMarkIndex: 3,
  diceCount: 3,
  faces: ['X', 'III', 'II', 'blank'],
  blankValue: 0,
  diceApplication: 'separate',
  diceOrder: 'free',
  fixedOrder: ['X', 3, 2],
  rethrow: 'none',
  startRule: 'first-x',
  track: 'loop',
  activation: 'step',
  activationOrder: 'front-first',
  allowMiedut: false,
  capturesInactive: true,
  stacking: 'single',
  jumpOwnSoldiers: false,
  kingMode: 'recruit',
  kingMovement: 'track',
  royalsShareWithOwn: false,
  kingKnockOut: false,
  kingAcquire: 'landing',
  kingAloneLoses: true,
  royalVerticalCrossing: true,
};

export const LAGESVUOTNA: RuleSet = {
  id: 'lagesvuotna',
  name: 'Lágesvuotna',
  region: 'Lágesvuotna (Laksefjord area), with queens',
  status: 'documented',
  reconstructionNote:
    'A published reconstruction of the form played at modern Sámi cups. Two sources I could not check directly may differ on small details; see the notes.',
  credit: 'Edmund Johansen (reconstruction); Mikkel Berg-Nordlie (published rule collection).',
  uncertain: {
    startRule: 'Two ways of deciding who starts are described; first-X is the default here.',
    queenStart:
      'Which marked point each queen takes follows a photo caption; a mirrored layout is offered.',
    faces: 'No source states face probabilities. Equal odds (25% each) is an assumption.',
    royalsShareWithOwn: 'Exact wording of when the king or queen may share a line is interpreted.',
    royalVerticalCrossing:
      'The source says the king moves up and down; the exact crossing distances are my reading.',
  },
  options: {
    ...base,
    queens: true,
    diceOrder: 'fixed',
    fixedOrder: ['X', 3, 2],
    rethrow: 'single',
    track: 'figure-eight',
    capturesInactive: false,
    stacking: 'allowed',
    jumpOwnSoldiers: true,
    kingMode: 'recruit',
    kingMovement: 'figure-eight',
    royalsShareWithOwn: false,
  },
};

export const VUOVDAGUOIKA: RuleSet = {
  id: 'vuovdaguoika',
  name: 'Vuovdaguoika / Gávkevuotna',
  region: 'Vuovdaguoika and Gávkevuotna (Ohcejohka area), no queens',
  status: 'documented',
  reconstructionNote:
    'Documented from the Ohcejohka area. Whether the triple-X re-throw was used in Gávkevuotna itself is not known, so it is an option (on by default). No dice order is recorded, so order is free.',
  credit: 'Hans Aslak Guttorm (documentation); Mikkel Berg-Nordlie (published rule collection).',
  uncertain: {
    rethrow: 'Known from the inland area; unknown for Gávkevuotna.',
    diceOrder: 'No dice order is recorded; free order is used.',
    kingKnockOut:
      'A local rule from elsewhere in the area that conflicts with the usual "king is never captured".',
    faces: 'No source states face probabilities.',
  },
  options: {
    ...base,
    blankValue: 4,
    diceOrder: 'free',
    rethrow: 'triple',
    allowMiedut: true,
    capturesInactive: true,
    stacking: 'single',
    jumpOwnSoldiers: false,
    kingMode: 'push',
    kingMovement: 'track',
    kingKnockOut: false,
  },
};

export const NAVUOTNA_RAISA: RuleSet = {
  id: 'navuotna-raisa',
  name: 'Návuotna – Ráisa',
  region: 'Návuotna (Kvænangen), Ráisa style: fixed dice order',
  status: 'documented',
  reconstructionNote:
    'Board of squares, two dice. Dice are played in a fixed order, which makes it very luck-dependent.',
  credit: 'Yngvar Mejland (Ráisa rules); Mikkel Berg-Nordlie (published rule collection).',
  uncertain: { faces: 'No source states face probabilities.' },
  options: {
    ...base,
    cols: 13,
    boardStyle: 'squares',
    extraMarks: false,
    soldiersPerSide: 12,
    diceCount: 2,
    faces: ['X', 'I', 'II', 'III'],
    diceOrder: 'fixed',
    fixedOrder: ['X', 1, 2, 3],
    rethrow: 'single',
    capturesInactive: true,
    stacking: 'allowed',
    jumpOwnSoldiers: true,
    activationOrder: 'free',
    kingMode: 'recruit',
    kingMovement: 'track',
    royalsShareWithOwn: true,
  },
};

export const NAVUOTNA_MAZE: RuleSet = {
  ...NAVUOTNA_RAISA,
  id: 'navuotna-maze',
  name: 'Návuotna – Máze',
  region: 'Návuotna (Kvænangen), Máze style: free dice order',
  reconstructionNote: 'Same as the Ráisa style but the dice may be played in any order.',
  credit: 'Mikkel Berg-Nordlie (published rule collection).',
  options: { ...NAVUOTNA_RAISA.options, diceOrder: 'free' },
};

export const UNJARGA: RuleSet = {
  id: 'unjarga',
  name: 'Unjárga (experimental)',
  region: 'Unjárga (Nesseby) – experimental reconstruction',
  status: 'experimental',
  reconstructionNote:
    'Explicitly hypothetical: the surviving knowledge is thin and the reconstructor filled gaps. Many choices below are open and offered as options.',
  credit: 'Mikkel Berg-Nordlie (reconstruction).',
  uncertain: {
    blankValue: 'Blank is worth 0 or 4; both are offered.',
    diceOrder: 'Dice order is unknown.',
    rethrow: 'Two re-throw forms are documented.',
    track: 'The track is unknown; the default is a hypothesis.',
    stacking: 'Whether stacking was allowed is unknown.',
    kingAcquire: 'Three ways of taking the king are suggested.',
    kingKnockOut: 'Option (b) of the king rules: the lander may remove the king.',
    kingAloneLoses: 'The reconstructor suggests that a lone king counts as a loss.',
    activation:
      'Straight up from the home line, or to the first middle-row point: the reconstructor reads the sources the first way but notes doubt.',
    activationOrder: 'The sources do not say; front-first is used because the king rule needs it.',
    royalVerticalCrossing: 'Not described for Unjárga beyond "four directions".',
  },
  options: {
    ...base,
    faces: ['X', 'II', 'III', 'blank'],
    blankValue: 0,
    diceOrder: 'free',
    fixedOrder: ['X', 4, 3, 2],
    rethrow: 'single',
    track: 'loop-from-middle',
    activation: 'up',
    allowMiedut: true,
    capturesInactive: true,
    stacking: 'allowed',
    jumpOwnSoldiers: true,
    kingMode: 'recruit',
    kingMovement: 'figure-eight',
    royalsShareWithOwn: false,
    kingAcquire: 'unjarga-first',
    kingAloneLoses: true,
  },
};

export const CUSTOM: RuleSet = {
  id: 'custom',
  name: 'Custom',
  region: 'Your own combination of options',
  status: 'custom',
  reconstructionNote: 'Every option can be edited. This is not a historical variant.',
  credit: 'Options are drawn from the other rule sets.',
  uncertain: {},
  options: { ...LAGESVUOTNA.options },
};

export const VARIANTS: RuleSet[] = [
  LAGESVUOTNA,
  VUOVDAGUOIKA,
  NAVUOTNA_RAISA,
  NAVUOTNA_MAZE,
  UNJARGA,
  CUSTOM,
];

export function getVariant(id: string): RuleSet {
  const v = VARIANTS.find((x) => x.id === id);
  if (!v) throw new Error(`Unknown variant ${id}`);
  return v;
}
