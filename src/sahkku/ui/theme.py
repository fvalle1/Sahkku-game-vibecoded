"""Neutral, wood-toned theme. No Sámi flag colours, patterns or motifs; system fonts only."""

from __future__ import annotations

CSS = """
:root {
  --sk-bg: #f4efe6; --sk-panel: #fffdf8; --sk-ink: #2a2620; --sk-muted: #6b6358;
  --sk-line: #cfc3ae; --sk-accent: #35566b; --sk-accent-ink: #ffffff;
  --sk-row-home: #e6d9c0; --sk-row-mid: #efe4cd; --sk-cell: #8b7a5e;
  --sk-men: #3b2f24; --sk-men-ink: #f4efe6; --sk-women: #f6f0e4; --sk-women-stroke: #3b2f24;
  --sk-king: #9aa0a6; --sk-dest: #2f7d4f; --sk-capture: #b04a2e; --sk-track: #35566b;
  --sk-warn: #8a5a00; --sk-warn-bg: #fff1cf; --sk-focus: #1b66d1;
}
body.body--dark {
  --sk-bg: #1d1a16; --sk-panel: #26221d; --sk-ink: #eee7da; --sk-muted: #b1a897;
  --sk-line: #4a4237; --sk-accent: #8cb4cc; --sk-accent-ink: #10151a;
  --sk-row-home: #332c23; --sk-row-mid: #3a3228; --sk-cell: #b6a687;
  --sk-men: #e9dcc3; --sk-men-ink: #1d1a16; --sk-women: #26221d; --sk-women-stroke: #e9dcc3;
  --sk-king: #aab0b6; --sk-dest: #6cc08a; --sk-capture: #ec8f73; --sk-track: #8cb4cc;
  --sk-warn: #ffd88a; --sk-warn-bg: #46381a; --sk-focus: #7db2ff;
}
/* colour-blind-safe palette (Okabe-Ito) plus heavier strokes */
body.sk-cb {
  --sk-men: #0072b2; --sk-men-ink: #ffffff; --sk-women: #ffffff; --sk-women-stroke: #d55e00;
  --sk-dest: #009e73; --sk-capture: #d55e00;
}
body { background: var(--sk-bg); color: var(--sk-ink);
  font: 16px/1.5 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }
.q-page, .nicegui-content { background: var(--sk-bg); }
.nicegui-content { padding: 0; align-items: stretch; gap: 0; }
:focus-visible { outline: 3px solid var(--sk-focus); outline-offset: 2px; }
.sk-top { display: flex; flex-wrap: wrap; gap: 8px 24px; align-items: center;
  justify-content: space-between; padding: 8px 16px; border-bottom: 1px solid var(--sk-line);
  background: var(--sk-panel); }
.sk-main { width: 100%; max-width: 1180px; margin: 0 auto; padding: 12px 16px 32px; }
.sk-small { font-size: .86rem; color: var(--sk-muted); }
.sk-term { font-size: .8em; color: var(--sk-muted); }
.sk-panel { background: var(--sk-panel); border: 1px solid var(--sk-line); border-radius: 12px;
  padding: 10px 14px; margin-bottom: 12px; width: 100%; }
.sk-panel h2 { font-size: 1rem; margin: 0 0 6px; font-weight: 600; }
.sk-badge { display: inline-block; border: 1px solid var(--sk-line); border-radius: 999px;
  padding: 1px 10px; font-size: .8rem; background: var(--sk-panel); margin-right: 6px; }
.sk-badge.warn { background: var(--sk-warn-bg); color: var(--sk-warn); border-color: var(--sk-warn); }
.sk-game { display: grid; grid-template-columns: minmax(0, 1fr) 360px; gap: 16px; align-items: start; width: 100%; }
.sk-game.compact { grid-template-columns: minmax(0, 1fr) 280px; }
@media (max-width: 900px) { .sk-game, .sk-game.compact { grid-template-columns: 1fr; } }
.sk-controls { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 12px; }
.sk-guide { min-height: 3em; margin: 6px 0; }
.sk-loglist { max-height: 220px; overflow: auto; font-size: .9rem; margin: 0; padding-left: 20px; width: 100%; }
.sk-rule-row { display: grid; grid-template-columns: 1fr 1fr; gap: 4px 12px; padding: 4px 0;
  border-top: 1px solid var(--sk-line); font-size: .9rem; width: 100%; }
.sk-page { max-width: 820px; width: 100%; display: flex; flex-direction: column; gap: .55rem; }
.sk-page h1 { font-size: 1.8rem; font-weight: 600; line-height: 1.25; letter-spacing: normal; margin: .4rem 0 0; }
.sk-page h2 { font-size: 1.25rem; font-weight: 600; line-height: 1.3; letter-spacing: normal; margin: .8rem 0 0; }
.sk-page ul { margin: 0; padding-left: 1.3rem; }
.sk-page .q-btn { align-self: flex-start; }

/* board */
.sk-board-scroll { overflow-x: auto; border-radius: 14px; width: 100%; }
.sk-board { width: 100%; height: auto; display: block; background: var(--sk-panel);
  border: 1px solid var(--sk-line); border-radius: 14px; }
.sk-row-home { fill: var(--sk-row-home); } .sk-row-mid { fill: var(--sk-row-mid); }
.sk-side-label { font-size: 12px; fill: var(--sk-muted); }
.sk-cell-line { stroke: var(--sk-cell); stroke-width: 3; stroke-linecap: round; }
.sk-cell { fill: none; stroke: var(--sk-cell); stroke-width: 2.5; }
.sk-castle { fill: none; stroke: var(--sk-cell); stroke-width: 2; }
.sk-mark { fill: var(--sk-cell); }
.sk-pt .sk-hit { fill: transparent; cursor: pointer; }
.sk-pt:focus-visible .sk-hit, .sk-pt:focus .sk-hit { stroke: var(--sk-focus); stroke-width: 3;
  fill: color-mix(in srgb, var(--sk-focus) 12%, transparent); }
.sk-pt:focus { outline: none; }
.sk-ring circle { fill: none; stroke: var(--sk-dest); stroke-width: 3; stroke-dasharray: 5 4; }
.sk-ring.capture circle { stroke: var(--sk-capture); stroke-dasharray: none; stroke-width: 4; }
.sk-ring.no circle { stroke: var(--sk-muted); stroke-width: 2; stroke-dasharray: 2 4; }
.sk-ring text { font-size: 16px; font-weight: 700; fill: var(--sk-capture); }
.sk-ring.no text { fill: var(--sk-muted); }
.sk-count { font-size: 12px; font-weight: 700; fill: var(--sk-ink); }
.sk-piece path, .sk-piece circle { stroke-width: 2.5; }
.sk-piece.side0 > circle, .sk-piece.side0 > path { stroke: var(--sk-men); fill: var(--sk-men); }
.sk-piece.side1 > path, .sk-piece.side1 > circle { stroke: var(--sk-women-stroke); fill: var(--sk-women); }
.sk-piece.neutral > path { stroke: var(--sk-ink); fill: var(--sk-king); }
.sk-piece .inner { fill: none; stroke: var(--sk-ink); stroke-width: 2.5; }
.sk-piece.side0 .inner { stroke: var(--sk-men-ink); } .sk-piece.side1 .inner { stroke: var(--sk-women-stroke); }
.sk-piece.king .inner.own0 { fill: var(--sk-men); stroke: var(--sk-men); }
.sk-piece.king .inner.own1 { fill: var(--sk-women); stroke: var(--sk-women-stroke); }
.sk-piece.asleep.side0 > *, .sk-piece.asleep.side1 > * { fill: var(--sk-panel); stroke-dasharray: 4 3; }
.sk-piece.asleep.side0 > * { stroke: var(--sk-men); }
.sk-piece.glow { filter: drop-shadow(0 0 5px var(--sk-focus)); }
.sk-piece.selected > path:first-child, .sk-piece.selected > circle:first-child { stroke-width: 5; stroke: var(--sk-focus); }
.sk-track polyline { stroke: var(--sk-track); stroke-width: 3; opacity: .55; stroke-linejoin: round; fill: none; }
.sk-track circle { fill: var(--sk-track); }

/* dice */
.sk-dice { display: flex; gap: 12px; flex-wrap: wrap; margin: 8px 0; }
.sk-die-wrap { display: flex; flex-direction: column; align-items: flex-start; gap: 2px; max-width: 110px; }
.sk-die { width: 64px; height: 64px; border-radius: 12px; font-size: 1.5rem; font-weight: 700;
  border: 2px solid var(--sk-line); background: var(--sk-panel); color: var(--sk-ink); cursor: pointer;
  display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 0; }
.sk-die .val { font-size: .7rem; font-weight: 400; color: var(--sk-muted); min-height: 1em; }
.sk-die.sel { outline: 3px solid var(--sk-focus); outline-offset: 1px; }
.sk-die.used, .sk-die.no-move, .sk-die.out-of-order { opacity: .5; border-style: dashed; cursor: default; }
.sk-die.roll { animation: sk-roll .5s ease-out; }
@keyframes sk-roll { from { transform: rotate(-200deg) scale(.6); opacity: 0; } to { transform: none; opacity: 1; } }
body.sk-noanim .sk-die.roll { animation: none; }
@media (prefers-reduced-motion: reduce) { .sk-die.roll { animation: none; } }
.sk-link { background: none; border: none; color: var(--sk-accent); text-decoration: underline;
  cursor: pointer; padding: 2px 4px; font: inherit; }
.sk-glossary { border-collapse: collapse; width: 100%; }
.sk-glossary th, .sk-glossary td { text-align: left; border-bottom: 1px solid var(--sk-line); padding: 4px 8px; }
.sk-skip { position: absolute; left: -999px; } .sk-skip:focus { left: 8px; top: 8px; background: var(--sk-panel); padding: 6px 10px; z-index: 10; }
"""
