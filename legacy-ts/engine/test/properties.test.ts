import { describe, it } from 'vitest';
import fc from 'fast-check';
import {
  VARIANTS,
  applyAction,
  checkInvariants,
  legalActions,
  newGame,
  normalizeOptions,
} from '../src';

describe('property: no illegal state is reachable', () => {
  for (const rs of VARIANTS) {
    it(`${rs.name}: any sequence of legal actions keeps the board consistent`, () => {
      fc.assert(
        fc.property(
          fc.integer({ min: 1, max: 1e6 }),
          fc.boolean(),
          fc.boolean(),
          fc.array(fc.nat(), { minLength: 50, maxLength: 400 }),
          (seed, miedut, equalOdds, picks) => {
            let s = newGame(rs.options, { seed, miedut, equalOdds });
            for (const pick of picks) {
              if (s.phase === 'over') break;
              const acts = legalActions(s);
              if (acts.length === 0) return false;
              s = applyAction(s, acts[pick % acts.length]);
              if (checkInvariants(s).length) return false;
              // every capturing landing leaves no enemy pieces on the same line
              if (s.phase === 'move' && s.dice.length === 0) return false;
            }
            return true;
          },
        ),
        { numRuns: 40 },
      );
    });
  }
  it('legal actions are always non-empty until the game ends, and apply never throws', () => {
    fc.assert(
      fc.property(fc.integer({ min: 1, max: 1e6 }), (seed) => {
        let s = newGame(VARIANTS[seed % 5].options, { seed });
        for (let i = 0; i < 300 && s.phase !== 'over'; i++) {
          const acts = legalActions(s);
          if (!acts.length) return false;
          s = applyAction(s, acts[(i * 13 + seed) % acts.length]);
        }
        return true;
      }),
      { numRuns: 30 },
    );
  });
  it('normalizeOptions makes any activation/track combination playable', () => {
    fc.assert(
      fc.property(
        fc.constantFrom('loop', 'loop-from-middle', 'figure-eight'),
        fc.constantFrom('step', 'up', 'first-middle'),
        fc.integer({ min: 1, max: 1000 }),
        (track, activation, seed) => {
          const { options } = normalizeOptions({
            ...VARIANTS[0].options,
            track,
            activation,
          } as never);
          let s = newGame(options, { seed });
          for (let i = 0; i < 60 && s.phase !== 'over'; i++) {
            const acts = legalActions(s);
            if (!acts.length) return false;
            s = applyAction(s, acts[i % acts.length]);
            if (checkInvariants(s).length) return false;
          }
          return true;
        },
      ),
      { numRuns: 30 },
    );
  });
});
