import { colOf, rowOf } from '@engine';
import type { Face, GameEvent, GameState, RuleOptions, Side } from '@engine';
import type { TFn } from './i18n';
import { TERMS } from './glossary';

export const faceText = (f: Face) => (f === 'blank' ? '–' : f);

export function sideName(t: TFn, s: Side | null) {
  if (s === null) return t('king.owner.none');
  return `${t('side.' + s)} (${s === 0 ? TERMS.men : TERMS.women})`;
}

export function ptName(t: TFn, o: RuleOptions, pt: number) {
  const r = rowOf(o.cols, pt);
  const c = colOf(o.cols, pt);
  const row = t(r === 0 ? 'row.near' : r === 1 ? 'row.middle' : 'row.far');
  const unit = t(o.boardStyle === 'squares' ? 'unit.squares' : 'unit.lines');
  return `${row} ${unit} ${c + 1}`;
}

export function describeEvent(t: TFn, o: RuleOptions, e: GameEvent): string | null {
  switch (e.type) {
    case 'start':
      return t('log.start', { side: sideName(t, e.starter) });
    case 'throw':
      return t('log.throw', { side: t('side.' + e.side), faces: e.faces.map(faceText).join(' ') });
    case 'rethrow':
      return t('log.rethrow', {
        side: t('side.' + e.side),
        faces: e.faces.map(faceText).join(' '),
      });
    case 'move': {
      const base = t(e.activated ? 'log.activate' : 'log.move', {
        side: t('side.' + e.side),
        piece: t('piece.' + e.piece),
        from: ptName(t, o, e.from),
        to: ptName(t, o, e.to),
      });
      const extra: string[] = [];
      if (e.captured.length)
        extra.push(
          t('log.capture', {
            n: e.captured.length,
            what: [...new Set(e.captured.map((k) => t('piece.' + k)))].join(', '),
          }),
        );
      if (e.king) extra.push(t('log.king.' + e.king));
      return [base, ...extra].join(' · ');
    }
    case 'turn-lost':
      return t('log.turnLost.' + e.reason, { side: t('side.' + e.side) });
    case 'win':
      return t('log.win', { side: sideName(t, e.winner) });
    case 'turn-end':
      return null;
  }
}

export function winText(t: TFn, s: GameState): string {
  if (s.winner === null) return '';
  const loser = (s.winner === 0 ? 1 : 0) as Side;
  return `${t('game.over', { side: sideName(t, s.winner) })} ${t('game.overReason.' + s.winReason, { loser: t('side.' + loser) })}`;
}
