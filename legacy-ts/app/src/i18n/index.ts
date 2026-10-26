import { createContext, useContext } from 'react';
import { en } from './en';
import { rulesEn } from './rulesText';
import type { MessageKey } from './en';

export const LANGUAGES: Record<string, Record<string, string>> = { en: { ...en, ...rulesEn } };

export type TFn = (
  key: MessageKey | (string & {}),
  vars?: Record<string, string | number>,
) => string;

export function makeT(lang: string): TFn {
  const dict = LANGUAGES[lang] ?? LANGUAGES.en;
  return (key, vars) => {
    let s = dict[key] ?? LANGUAGES.en[key] ?? key;
    if (vars) for (const [k, v] of Object.entries(vars)) s = s.replaceAll(`{${k}}`, String(v));
    return s;
  };
}

export const I18nContext = createContext<TFn>(makeT('en'));
export const useT = () => useContext(I18nContext);
