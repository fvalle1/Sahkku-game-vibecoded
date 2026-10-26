export type Side = 0 | 1;
export type Face = 'X' | 'I' | 'II' | 'III' | 'blank';
export type PieceKind = 'soldier' | 'queen' | 'king';

/** Which die face is "playable" in fixed-order play: X first, then numeric values. */
export type OrderKey = 'X' | number;

export interface RuleOptions {
  /** Number of lines (or squares) per row. */
  cols: number;
  /** Display only: draw short lines or squares. */
  boardStyle: 'lines' | 'squares';
  /** Display only: mark the points 4th from each end of the middle row. */
  extraMarks: boolean;
  soldiersPerSide: number;

  // --- queens ---
  queens: boolean;
  /** Queen starts on the marked point to the owner's right or left (as seen from the owner's seat). */
  queenStart: 'right' | 'left';
  /** Zero-based index (counted from the end of the row) of the queens' marked points. 3 = "4th line". */
  queenMarkIndex: number;

  // --- dice ---
  diceCount: number;
  /** The four faces of every die; each is assumed equally likely (25%). */
  faces: Face[];
  /** What a blank face is worth. 0 means "no move". */
  blankValue: 0 | 4;
  /** Explicit: every die is applied as its own move (dice are never added together). */
  diceApplication: 'separate';
  diceOrder: 'fixed' | 'free';
  fixedOrder: OrderKey[];
  /** none | single: re-throw one X die until non-X | triple: re-throw all dice when all show X. */
  rethrow: 'none' | 'single' | 'triple';
  startRule: 'first-x' | 'most-x';

  // --- movement ---
  /** loop: home row once, then middle/enemy loop. loop-from-middle: no home row. figure-eight: Lágesvuotna. */
  track: 'loop' | 'loop-from-middle' | 'figure-eight';
  /** step: activated soldier steps along its track. up: it moves straight up onto the middle row. */
  activation: 'step' | 'up' | 'first-middle';
  activationOrder: 'front-first' | 'free';
  /** Whether the non-starting player may choose to mirror the track (mieđut). */
  allowMiedut: boolean;
  capturesInactive: boolean;
  stacking: 'allowed' | 'single';
  jumpOwnSoldiers: boolean;

  // --- king ---
  /** recruit: landing on the king takes control of it. push: landing pushes it one line forward. */
  kingMode: 'recruit' | 'push';
  kingMovement: 'figure-eight' | 'track';
  /** King and queen may share a line with their own army's pieces. */
  royalsShareWithOwn: boolean;
  /** When landing on the king the lander may instead remove it from the game. */
  kingKnockOut: boolean;
  /** landing: the king is taken only by landing on it. unjarga-*: it is dormant until a soldier reaches the far row. */
  kingAcquire: 'landing' | 'unjarga-first' | 'unjarga-every';
  kingAloneLoses: boolean;
  /** King/queen may also cross rows in a straight line at any column (1 row per step, at most 2 rows). */
  royalVerticalCrossing: boolean;
}

export interface RuleSet {
  id: string;
  name: string;
  region: string;
  status: 'documented' | 'experimental' | 'custom';
  reconstructionNote: string;
  credit: string;
  /** option key -> why this option is uncertain / disputed. */
  uncertain: Partial<Record<keyof RuleOptions, string>>;
  options: RuleOptions;
}

export interface Piece {
  id: number;
  kind: PieceKind;
  /** null = neutral king */
  side: Side | null;
  active: boolean;
  /** point index = row * cols + col. Row 0 is side 0's home row, row 2 is side 1's home row. */
  pt: number;
  /** Track index for active soldiers; home slot for inactive soldiers; -1 otherwise. */
  pi: number;
}

export interface Die {
  face: Face;
  used: boolean;
}

export interface Track {
  points: number[];
  loopStart: number;
}

export type Transform = 'id' | 'rot' | 'rowflip' | 'colflip';

export interface GameState {
  options: RuleOptions;
  tracks: [Track, Track];
  homeSlots: [number[], number[]];
  transforms: [Transform, Transform];
  pieces: Piece[];
  current: Side;
  phase: 'throw' | 'move' | 'over';
  dice: Die[];
  winner: Side | null;
  winReason: 'no-soldiers' | 'queen-captured' | null;
  rng: number;
  turnNumber: number;
  miedut: boolean;
  equalOdds: boolean;
  startLog: { side: Side; faces: Face[] }[];
  /** Events produced by the most recent action. */
  events: GameEvent[];
}

export type GameEvent =
  | { type: 'start'; starter: Side; log: { side: Side; faces: Face[] }[] }
  | { type: 'throw'; side: Side; faces: Face[] }
  | { type: 'rethrow'; side: Side; faces: Face[]; all: boolean }
  | {
      type: 'move';
      side: Side;
      piece: PieceKind;
      pieceId: number;
      from: number;
      to: number;
      face: Face;
      activated: boolean;
      captured: PieceKind[];
      king?: 'taken' | 'pushed' | 'removed';
    }
  | { type: 'turn-lost'; side: Side; reason: 'no-legal-move' | 'fixed-order-blocked' }
  | { type: 'turn-end'; side: Side }
  | { type: 'win'; winner: Side; reason: 'no-soldiers' | 'queen-captured' };

export type Action =
  | { type: 'throw' }
  | { type: 'move'; die: number; pieceId: number; to: number; fate?: 'take' | 'remove' }
  | { type: 'rethrow'; die: number }
  | { type: 'rethrowAll' };

export interface NewGameOptions {
  seed: number;
  /** The player who does not start plays the mirrored track (only if the ruleset allows it). */
  miedut?: boolean;
  /** Add-on: each side starts with three soldiers already active. */
  equalOdds?: boolean;
}
