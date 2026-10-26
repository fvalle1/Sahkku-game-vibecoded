import { useEffect, useRef, useState } from 'react';
import { VARIANTS, getVariant, normalizeOptions } from '@engine';
import type { RuleOptions, RuleSet, Side } from '@engine';
import { useT } from '../i18n';
import { FIELDS, fieldValueString, setField } from '../ruleSchema';
import { ruleValueText } from './RulesPanel';
import type { Opponent } from './GameView';

export interface GameConfig {
  rules: RuleSet;
  opponent: Opponent;
  humanSide: Side;
  seed: number;
  equalOdds: boolean;
  miedut: boolean;
}

export function NewGameDialog({
  initial,
  onStart,
  onCancel,
}: {
  initial: { variantId: string; custom: RuleOptions; opponent: Opponent; equalOdds: boolean };
  onStart: (c: GameConfig, custom: RuleOptions) => void;
  onCancel: () => void;
}) {
  const t = useT();
  const [variantId, setVariantId] = useState(initial.variantId);
  const [custom, setCustom] = useState<RuleOptions>(initial.custom);
  const [opponent, setOpponent] = useState<Opponent>(initial.opponent);
  const [humanSide, setHumanSide] = useState<Side>(0);
  const [equalOdds, setEqualOdds] = useState(initial.equalOdds);
  const [miedut, setMiedut] = useState(false);
  const [seedText, setSeedText] = useState('');
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    ref.current?.querySelector<HTMLElement>('select, button')?.focus();
  }, []);

  const base = getVariant(variantId);
  const rules: RuleSet = variantId === 'custom' ? { ...base, options: custom } : base;
  const opts = rules.options;

  const start = () => {
    const seed = seedText.trim() ? Number(seedText) >>> 0 : (Math.random() * 2 ** 32) >>> 0;
    const { options } = normalizeOptions(rules.options);
    onStart(
      {
        rules: { ...rules, options },
        opponent,
        humanSide,
        seed,
        equalOdds,
        miedut: miedut && options.allowMiedut && !options.queens,
      },
      custom,
    );
  };

  return (
    <div className="overlay" onKeyDown={(e) => e.key === 'Escape' && onCancel()}>
      <div className="dialog" role="dialog" aria-modal="true" aria-labelledby="ng-title" ref={ref}>
        <h2 id="ng-title">{t('new.title')}</h2>

        <label className="field">
          <span>{t('new.variant')}</span>
          <select value={variantId} onChange={(e) => setVariantId(e.target.value)}>
            {VARIANTS.map((v) => (
              <option key={v.id} value={v.id}>
                {v.name}
              </option>
            ))}
          </select>
        </label>
        <div className="variant-card">
          <p>
            <strong>{rules.region}</strong>{' '}
            <span className={`badge status-${rules.status}`}>{t('status.' + rules.status)}</span>
          </p>
          <p className="small">{rules.reconstructionNote}</p>
          <p className="small">
            <strong>{t('rules.credit')}:</strong> {rules.credit}
          </p>
          <p className="small">{t('rules.unofficial')}</p>
        </div>

        {variantId === 'custom' && (
          <fieldset className="custom">
            <legend>{t('new.customEditor')}</legend>
            <label className="field">
              <span>{t('new.customBase')}</span>
              <select
                defaultValue=""
                onChange={(e) =>
                  e.target.value && setCustom({ ...getVariant(e.target.value).options })
                }
              >
                <option value="">–</option>
                {VARIANTS.filter((v) => v.id !== 'custom').map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.name}
                  </option>
                ))}
              </select>
            </label>
            {FIELDS.map((f) => {
              const val = fieldValueString(custom, f.key);
              const id = `cf-${f.key}`;
              return (
                <label className="field" key={f.key} htmlFor={id}>
                  <span>{t('opt.' + f.key)}</span>
                  {f.type === 'bool' ? (
                    <input
                      id={id}
                      type="checkbox"
                      checked={val === 'true'}
                      onChange={(e) => setCustom(setField(custom, f.key, e.target.checked))}
                    />
                  ) : f.type === 'number' ? (
                    <input
                      id={id}
                      type="number"
                      min={f.min}
                      max={f.max}
                      value={val}
                      onChange={(e) => setCustom(setField(custom, f.key, e.target.value))}
                    />
                  ) : (
                    <select
                      id={id}
                      value={val}
                      onChange={(e) => setCustom(setField(custom, f.key, e.target.value))}
                    >
                      {f.choices!.map((c) => (
                        <option key={c} value={c}>
                          {ruleValueText(t, f.key, c)}
                        </option>
                      ))}
                    </select>
                  )}
                </label>
              );
            })}
            <p className="small">{normalizeOptions(custom).notes.join(' ')}</p>
          </fieldset>
        )}

        <label className="field">
          <span>{t('new.opponent')}</span>
          <select value={opponent} onChange={(e) => setOpponent(e.target.value as Opponent)}>
            {(['human', 'easy', 'medium', 'hard'] as const).map((o) => (
              <option key={o} value={o}>
                {t('new.opp.' + o)}
              </option>
            ))}
          </select>
        </label>
        {opponent !== 'human' && (
          <label className="field">
            <span>{t('new.side')}</span>
            <select
              value={humanSide}
              onChange={(e) => setHumanSide(Number(e.target.value) as Side)}
            >
              <option value={0}>{t('side.0')}</option>
              <option value={1}>{t('side.1')}</option>
            </select>
          </label>
        )}
        <label className="check">
          <input
            type="checkbox"
            checked={equalOdds}
            onChange={(e) => setEqualOdds(e.target.checked)}
          />{' '}
          {t('new.equalOdds')}
        </label>
        {opts.allowMiedut && !opts.queens && (
          <label className="check">
            <input type="checkbox" checked={miedut} onChange={(e) => setMiedut(e.target.checked)} />{' '}
            {t('new.miedut')}
          </label>
        )}
        <label className="field">
          <span>{t('new.seed')}</span>
          <input
            type="text"
            inputMode="numeric"
            value={seedText}
            onChange={(e) => setSeedText(e.target.value.replace(/\D/g, ''))}
          />
        </label>

        <div className="actions">
          <button type="button" className="primary" onClick={start}>
            {t('new.start')}
          </button>
          <button type="button" onClick={onCancel}>
            {t('new.cancel')}
          </button>
        </div>
      </div>
    </div>
  );
}
