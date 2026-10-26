import { createContext, useContext } from 'react';

export interface Settings {
  diceAnim: boolean;
  sound: boolean;
  colorblind: boolean;
  largeTouch: boolean;
  explain: boolean;
}

export const DEFAULT_SETTINGS: Settings = {
  diceAnim: true,
  sound: false,
  colorblind: false,
  largeTouch: false,
  explain: true,
};

const KEY = 'sahkku.settings.v1';

export function loadSettings(): Settings {
  try {
    const raw = localStorage.getItem(KEY);
    if (raw) return { ...DEFAULT_SETTINGS, ...JSON.parse(raw) };
  } catch {
    /* storage can be unavailable; fall back to defaults */
  }
  // First visit: phones and tablets get large touch targets by default.
  const coarse = typeof matchMedia !== 'undefined' && matchMedia('(pointer: coarse)').matches;
  return { ...DEFAULT_SETTINGS, largeTouch: coarse };
}

export function saveSettings(s: Settings) {
  try {
    localStorage.setItem(KEY, JSON.stringify(s));
  } catch {
    /* ignore */
  }
}

export function getFlag(name: string): boolean {
  try {
    return localStorage.getItem('sahkku.' + name) === '1';
  } catch {
    return false;
  }
}
export function setFlag(name: string) {
  try {
    localStorage.setItem('sahkku.' + name, '1');
  } catch {
    /* ignore */
  }
}

export const SettingsContext = createContext<Settings>(DEFAULT_SETTINGS);
export const useSettings = () => useContext(SettingsContext);

export function prefersReducedMotion(): boolean {
  return (
    typeof matchMedia !== 'undefined' && matchMedia('(prefers-reduced-motion: reduce)').matches
  );
}

let audio: AudioContext | null = null;
export function beep(freq = 440, ms = 80) {
  try {
    audio ??= new AudioContext();
    const o = audio.createOscillator();
    const g = audio.createGain();
    o.frequency.value = freq;
    g.gain.value = 0.04;
    o.connect(g);
    g.connect(audio.destination);
    o.start();
    o.stop(audio.currentTime + ms / 1000);
  } catch {
    /* ignore */
  }
}
