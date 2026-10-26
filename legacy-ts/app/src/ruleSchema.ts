import type { Face, OrderKey, RuleOptions } from '@engine';

export type FieldType = 'select' | 'number' | 'bool';
export interface Field {
  key: keyof RuleOptions;
  type: FieldType;
  choices?: string[]; // select values (stringified)
  min?: number;
  max?: number;
  group: 'board' | 'dice' | 'moves' | 'king' | 'queen' | 'end';
}

export const FACE_SETS: Record<string, Face[]> = {
  'X,III,II,blank': ['X', 'III', 'II', 'blank'],
  'X,I,II,III': ['X', 'I', 'II', 'III'],
};
export const ORDER_SETS: Record<string, OrderKey[]> = {
  'X,3,2': ['X', 3, 2],
  'X,1,2,3': ['X', 1, 2, 3],
  'X,4,3,2': ['X', 4, 3, 2],
};

export const FIELDS: Field[] = [
  { key: 'cols', type: 'number', min: 9, max: 17, group: 'board' },
  { key: 'soldiersPerSide', type: 'number', min: 3, max: 17, group: 'board' },
  { key: 'boardStyle', type: 'select', choices: ['lines', 'squares'], group: 'board' },
  { key: 'extraMarks', type: 'bool', group: 'board' },
  { key: 'diceCount', type: 'select', choices: ['2', '3'], group: 'dice' },
  { key: 'faces', type: 'select', choices: Object.keys(FACE_SETS), group: 'dice' },
  { key: 'blankValue', type: 'select', choices: ['0', '4'], group: 'dice' },
  { key: 'diceOrder', type: 'select', choices: ['fixed', 'free'], group: 'dice' },
  { key: 'fixedOrder', type: 'select', choices: Object.keys(ORDER_SETS), group: 'dice' },
  { key: 'rethrow', type: 'select', choices: ['none', 'single', 'triple'], group: 'dice' },
  { key: 'startRule', type: 'select', choices: ['first-x', 'most-x'], group: 'dice' },
  {
    key: 'track',
    type: 'select',
    choices: ['loop', 'loop-from-middle', 'figure-eight'],
    group: 'moves',
  },
  { key: 'activation', type: 'select', choices: ['step', 'up', 'first-middle'], group: 'moves' },
  { key: 'activationOrder', type: 'select', choices: ['front-first', 'free'], group: 'moves' },
  { key: 'allowMiedut', type: 'bool', group: 'moves' },
  { key: 'capturesInactive', type: 'bool', group: 'moves' },
  { key: 'stacking', type: 'select', choices: ['allowed', 'single'], group: 'moves' },
  { key: 'jumpOwnSoldiers', type: 'bool', group: 'moves' },
  { key: 'kingMode', type: 'select', choices: ['recruit', 'push'], group: 'king' },
  { key: 'kingMovement', type: 'select', choices: ['track', 'figure-eight'], group: 'king' },
  { key: 'royalVerticalCrossing', type: 'bool', group: 'king' },
  { key: 'royalsShareWithOwn', type: 'bool', group: 'king' },
  { key: 'kingKnockOut', type: 'bool', group: 'king' },
  {
    key: 'kingAcquire',
    type: 'select',
    choices: ['landing', 'unjarga-first', 'unjarga-every'],
    group: 'king',
  },
  { key: 'queens', type: 'bool', group: 'queen' },
  { key: 'queenStart', type: 'select', choices: ['right', 'left'], group: 'queen' },
  { key: 'queenMarkIndex', type: 'number', min: 1, max: 6, group: 'queen' },
  { key: 'kingAloneLoses', type: 'bool', group: 'end' },
];

export function fieldValueString(o: RuleOptions, key: keyof RuleOptions): string {
  const v = o[key];
  if (key === 'faces') {
    const hit = Object.entries(FACE_SETS).find(([, f]) => f.join() === (v as Face[]).join());
    return hit ? hit[0] : (v as Face[]).join(',');
  }
  if (key === 'fixedOrder') {
    const hit = Object.entries(ORDER_SETS).find(([, f]) => f.join() === (v as OrderKey[]).join());
    return hit ? hit[0] : (v as OrderKey[]).join(',');
  }
  return String(v);
}

export function setField(
  o: RuleOptions,
  key: keyof RuleOptions,
  raw: string | boolean | number,
): RuleOptions {
  const next: Record<string, unknown> = { ...o };
  if (key === 'faces') next[key] = FACE_SETS[String(raw)] ?? o.faces;
  else if (key === 'fixedOrder') next[key] = ORDER_SETS[String(raw)] ?? o.fixedOrder;
  else if (key === 'blankValue') next[key] = Number(raw) === 4 ? 4 : 0;
  else if (
    key === 'diceCount' ||
    key === 'cols' ||
    key === 'soldiersPerSide' ||
    key === 'queenMarkIndex'
  )
    next[key] = Number(raw);
  else next[key] = raw;
  return next as unknown as RuleOptions;
}
