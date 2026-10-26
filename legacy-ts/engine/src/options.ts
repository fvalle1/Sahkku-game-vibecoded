import type { RuleOptions } from './types';

/** Fix up combinations of options that cannot work together. Returns the fixed options and notes. */
export function normalizeOptions(o: RuleOptions): { options: RuleOptions; notes: string[] } {
  const notes: string[] = [];
  const out = { ...o, faces: [...o.faces], fixedOrder: [...o.fixedOrder] };
  if (out.activation === 'step' && out.track === 'loop-from-middle') {
    out.activation = 'up';
    notes.push('A track without a home row needs "straight up" activation.');
  }
  if (out.activation === 'first-middle' && out.track !== 'loop-from-middle') {
    out.activation = out.track === 'loop' ? 'step' : 'up';
    notes.push('"First middle point" activation needs a track that starts on the middle row.');
  }
  if (out.soldiersPerSide > out.cols) {
    out.soldiersPerSide = out.cols;
    notes.push('Soldiers cannot outnumber the lines of the home row.');
  }
  if (out.queens && out.allowMiedut) {
    notes.push('Mieđut is ignored when queens are in play.');
  }
  if (out.queens && out.queenMarkIndex >= Math.floor(out.cols / 2)) {
    out.queenMarkIndex = Math.max(0, Math.floor(out.cols / 2) - 1);
    notes.push('Queen marks were moved to stay on their own side of the Castle.');
  }
  if (out.stacking === 'single') {
    // Fine as-is; nothing to adjust.
  }
  return { options: out, notes };
}
