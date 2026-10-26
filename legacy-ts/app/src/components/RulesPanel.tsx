import { useState } from 'react';
import type { GameState, RuleSet } from '@engine';
import { useT } from '../i18n';
import { FIELDS, fieldValueString } from '../ruleSchema';
import { sideName } from '../format';
import { faceText } from '../format';

export function ruleValueText(t: ReturnType<typeof useT>, key: string, value: string): string {
  if (value === 'true') return t('common.yes');
  if (value === 'false') return t('common.no');
  const k = `val.${key}.${value}`;
  const s = t(k);
  return s === k ? value : s;
}

export function RulesPanel({
  rules,
  state,
  defaultOpen = false,
}: {
  rules: RuleSet;
  state?: GameState;
  defaultOpen?: boolean;
}) {
  const t = useT();
  const [open, setOpen] = useState(defaultOpen);
  const o = state?.options ?? rules.options;
  return (
    <section className="panel" aria-label={t('rules.title')}>
      <h2>
        <button
          type="button"
          className="disclosure"
          aria-expanded={open}
          onClick={() => setOpen(!open)}
        >
          {open ? '▾' : '▸'} {t('rules.title')}
        </button>
      </h2>
      <p>
        <span className="badge">{rules.name}</span>{' '}
        <span className={`badge status-${rules.status}`}>{t('status.' + rules.status)}</span>
      </p>
      {open && (
        <>
          <p className="small">{t('rules.unofficial')}</p>
          <p className="small">{rules.reconstructionNote}</p>
          <p className="small">
            <strong>{t('rules.credit')}:</strong> {rules.credit}
          </p>
          {state && (
            <p className="small">
              <strong>{t('rules.start')}:</strong>{' '}
              {sideName(
                t,
                state.startLog.length
                  ? state.startLog[state.startLog.length - 1].side
                  : state.current,
              )}{' '}
              (
              {state.startLog
                .map((l) => `${t('side.' + l.side)}: ${l.faces.map(faceText).join(' ')}`)
                .join(' · ')}
              )
            </p>
          )}
          <dl className="rules-list">
            {FIELDS.filter((f) => f.key !== 'extraMarks' && f.key !== 'boardStyle').map((f) => {
              const val = fieldValueString(o, f.key);
              const unc = rules.uncertain[f.key];
              const help = t('help.' + f.key);
              return (
                <div key={f.key} className="rule-row">
                  <dt>
                    {t('opt.' + f.key)}
                    {unc && (
                      <span className="badge warn" title={unc}>
                        {t('rules.uncertain')}
                      </span>
                    )}
                  </dt>
                  <dd>
                    {ruleValueText(t, f.key, val)}
                    {unc && <div className="small note">{unc}</div>}
                    {help !== 'help.' + f.key && <div className="small note">{help}</div>}
                  </dd>
                </div>
              );
            })}
          </dl>
          <p className="small">{t('help.diceApplication')}</p>
          <p className="small">{t('help.faces')}</p>
        </>
      )}
    </section>
  );
}
