/** Terms exactly as supplied by the project owner. Do not add or "correct" Sámi words here. */
export interface GlossaryEntry {
  concept: string;
  term: string;
}

export const GLOSSARY: GlossaryEntry[] = [
  { concept: 'The game', term: 'sáhkku' },
  { concept: 'To play', term: 'sáhkkostallat' },
  { concept: 'Dice / to throw', term: 'bircu, birccut' },
  { concept: 'X throw', term: 'sáhkku, ruossa' },
  { concept: 'Zero', term: 'guoros' },
  { concept: 'Board', term: 'sáhkkufiellu, sáhkkulávdi' },
  { concept: 'Line(s) on the board', term: 'sárggis / sárgát' },
  { concept: 'The central point (Castle)', term: 'Šloahtta' },
  { concept: 'Soldiers', term: 'soalddáhat' },
  { concept: 'Men / women (the two armies)', term: 'olbmát / gálgut' },
  { concept: 'King', term: 'gonagas' },
  { concept: 'Queen', term: 'dronnet' },
  { concept: 'To capture ("to kill")', term: 'goddit' },
  { concept: 'Activate', term: 'luvvet, aktiveret' },
  { concept: 'Movement patterns', term: 'vuosttut, mieđut' },
];

/** Short pairs used next to English labels in the UI. */
export const TERMS = {
  castle: 'Šloahtta',
  men: 'olbmát',
  women: 'gálgut',
  king: 'gonagas',
  queen: 'dronnet',
  soldiers: 'soalddáhat',
  dice: 'birccut',
  capture: 'goddit',
  activate: 'luvvet',
  zero: 'guoros',
  board: 'sáhkkufiellu',
  line: 'sárggis',
  lines: 'sárgát',
  vuosttut: 'vuosttut',
  miedut: 'mieđut',
  game: 'sáhkku',
} as const;
