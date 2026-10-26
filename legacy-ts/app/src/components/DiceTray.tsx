import { dieStatus, faceValue } from '@engine';
import type { Action, GameState } from '@engine';
import { useT } from '../i18n';
import { useSettings } from '../settings';
import { TERMS } from '../glossary';
import { faceText } from '../format';

interface Props {
  state: GameState;
  actions: Action[];
  selected: number | null;
  onSelect: (i: number) => void;
  onAction: (a: Action) => void;
  disabled: boolean;
}

export function DiceTray({ state, actions, selected, onSelect, onAction, disabled }: Props) {
  const t = useT();
  const settings = useSettings();
  const o = state.options;
  const orderText =
    o.diceOrder === 'fixed'
      ? t('dice.order.fixed', {
          order: o.fixedOrder.map((k) => (k === 'X' ? 'X' : String(k))).join(' → '),
        })
      : t('dice.order.free');
  const rethrowAll = actions.some((a) => a.type === 'rethrowAll');
  return (
    <section aria-label={t('dice.title')} className="panel dice-panel">
      <h2>
        {t('dice.title')} <span className="term">{TERMS.dice}</span>
      </h2>
      <p className="small">{orderText}</p>
      <div className="dice" role="list">
        {state.dice.map((d, i) => {
          const status = dieStatus(state, i);
          const v = faceValue(o, d.face);
          const blankNote =
            d.face === 'blank' ? (o.blankValue === 0 ? t('die.blank0') : t('die.blank4')) : '';
          const reason =
            status === 'ready'
              ? d.face === 'X'
                ? t('die.x')
                : t('die.ready')
              : t('die.' + status);
          const canRethrow = actions.some((a) => a.type === 'rethrow' && a.die === i);
          return (
            <div role="listitem" key={`${state.turnNumber}-${i}-${d.face}`} className="die-wrap">
              <button
                type="button"
                className={`die ${status} ${selected === i ? 'sel' : ''} ${settings.diceAnim ? 'roll' : ''}`}
                disabled={disabled || status !== 'ready'}
                aria-pressed={selected === i}
                aria-label={`${d.face === 'blank' ? 'blank' : d.face}, ${blankNote || reason}`}
                title={blankNote || reason}
                onClick={() => onSelect(i)}
              >
                <span className="face">{faceText(d.face)}</span>
                <span className="val">{d.face === 'blank' ? v : d.face === 'X' ? '' : v}</span>
              </button>
              {canRethrow && !disabled && (
                <button
                  type="button"
                  className="link"
                  onClick={() => onAction({ type: 'rethrow', die: i })}
                >
                  {t('game.rethrow')}
                </button>
              )}
              <div className="small die-note">
                {d.face === 'blank' && o.blankValue === 0
                  ? t('die.blank0')
                  : status !== 'ready'
                    ? reason
                    : ''}
              </div>
            </div>
          );
        })}
      </div>
      {rethrowAll && !disabled && (
        <button type="button" onClick={() => onAction({ type: 'rethrowAll' })}>
          {t('game.rethrowAll')}
        </button>
      )}
    </section>
  );
}
