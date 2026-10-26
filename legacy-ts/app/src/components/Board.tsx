import { useMemo } from 'react';
import { colOf, ptOf, rowOf } from '@engine';
import type { GameState, Piece, Track } from '@engine';
import { useT } from '../i18n';
import { TERMS } from '../glossary';

export interface DestInfo {
  ok: boolean;
  capture: boolean;
}

interface Props {
  state: GameState;
  dests: Map<number, DestInfo>;
  movable: Set<number>;
  selectedPieceId: number | null;
  onPoint: (pt: number) => void;
  track?: Track | null;
  large?: boolean;
  interactive?: boolean;
}

const PAD_X = 34;
const PAD_Y = 30;
const ROW_H = 92;

export function Board({
  state,
  dests,
  movable,
  selectedPieceId,
  onPoint,
  track,
  large,
  interactive = true,
}: Props) {
  const t = useT();
  const o = state.options;
  const n = o.cols;
  const cw = large ? 58 : 48;
  const width = PAD_X * 2 + n * cw;
  const height = PAD_Y * 2 + 3 * ROW_H;
  const cx = (col: number) => PAD_X + (col + 0.5) * cw;
  const cy = (row: number) => PAD_Y + (2 - row + 0.5) * ROW_H;
  const mid = Math.floor(n / 2);
  const marks = useMemo(() => {
    const m = new Set<number>();
    if (o.extraMarks) {
      m.add(o.queenMarkIndex);
      m.add(n - 1 - o.queenMarkIndex);
    }
    return m;
  }, [o.extraMarks, o.queenMarkIndex, n]);

  const byPt = useMemo(() => {
    const map = new Map<number, Piece[]>();
    for (const p of state.pieces) map.set(p.pt, [...(map.get(p.pt) ?? []), p]);
    return map;
  }, [state.pieces]);

  const rowName = (r: number) => t(r === 0 ? 'row.near' : r === 1 ? 'row.middle' : 'row.far');
  const unit = t(o.boardStyle === 'squares' ? 'unit.squares' : 'unit.lines');

  const label = (pt: number) => {
    const r = rowOf(n, pt);
    const c = colOf(n, pt);
    const parts = [`${rowName(r)}, ${unit} ${c + 1} / ${n}`];
    if (r === 1 && c === mid) parts.push(t('pt.castle'));
    const here = byPt.get(pt) ?? [];
    for (const p of here) {
      const who =
        p.side === null ? t('piece.neutralKing') : `${t('side.' + p.side)} ${t('piece.' + p.kind)}`;
      parts.push(
        p.kind === 'king' ? who : `${who}, ${t(p.active ? 'piece.awake' : 'piece.asleep')}`,
      );
    }
    const d = dests.get(pt);
    if (d)
      parts.push(
        d.ok
          ? d.capture
            ? 'legal destination, captures'
            : 'legal destination'
          : 'blocked destination',
      );
    return parts.join('; ');
  };

  const focusNeighbour = (pt: number, dr: number, dc: number) => {
    const r = rowOf(n, pt) + dr;
    const c = colOf(n, pt) + dc;
    if (r < 0 || r > 2 || c < 0 || c >= n) return;
    document.getElementById(`pt-${ptOf(n, r, c)}`)?.focus();
  };

  const trackPath = useMemo(() => {
    if (!track) return null;
    const seen = new Map<number, number>();
    const pts = track.points.map((p) => {
      const k = seen.get(p) ?? 0;
      seen.set(p, k + 1);
      return { x: cx(colOf(n, p)) + k * 7, y: cy(rowOf(n, p)) + k * 7 };
    });
    return pts;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [track, n, cw]);

  return (
    <div className="board-scroll">
      <svg
        className="board"
        style={large ? { minWidth: width } : undefined}
        viewBox={`0 0 ${width} ${height}`}
        role="group"
        aria-label={t('app.title') + ' ' + TERMS.board}
      >
        <defs>
          <marker
            id="arrow"
            viewBox="0 0 10 10"
            refX="6"
            refY="5"
            markerWidth="5"
            markerHeight="5"
            orient="auto-start-reverse"
          >
            <path d="M0,0 L10,5 L0,10 z" fill="var(--track)" />
          </marker>
        </defs>
        {[0, 1, 2].map((r) => (
          <rect
            key={r}
            x={PAD_X - 8}
            y={cy(r) - ROW_H / 2 + 4}
            width={n * cw + 16}
            height={ROW_H - 8}
            rx={10}
            className={r === 1 ? 'row-mid' : 'row-home'}
          />
        ))}
        <text x={PAD_X - 8} y={PAD_Y - 10} className="side-label">
          {t('side.1')} · {TERMS.women}
        </text>
        <text x={PAD_X - 8} y={height - 8} className="side-label">
          {t('side.0')} · {TERMS.men}
        </text>

        {[0, 1, 2].flatMap((r) =>
          Array.from({ length: n }, (_, c) => {
            const pt = ptOf(n, r, c);
            const x = cx(c);
            const y = cy(r);
            const castle = r === 1 && c === mid;
            const d = dests.get(pt);
            const here = byPt.get(pt) ?? [];
            return (
              <g
                key={pt}
                id={`pt-${pt}`}
                role={interactive ? 'button' : 'img'}
                tabIndex={interactive ? 0 : -1}
                aria-label={label(pt)}
                className={'pt' + (d ? (d.ok ? ' dest' : ' blocked') : '')}
                onClick={interactive ? () => onPoint(pt) : undefined}
                onKeyDown={
                  interactive
                    ? (e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault();
                          onPoint(pt);
                        } else if (e.key === 'ArrowLeft') focusNeighbour(pt, 0, -1);
                        else if (e.key === 'ArrowRight') focusNeighbour(pt, 0, 1);
                        else if (e.key === 'ArrowUp') focusNeighbour(pt, 1, 0);
                        else if (e.key === 'ArrowDown') focusNeighbour(pt, -1, 0);
                      }
                    : undefined
                }
              >
                <rect
                  x={x - cw / 2}
                  y={y - ROW_H / 2 + 4}
                  width={cw}
                  height={ROW_H - 8}
                  className="hit"
                />
                {castle && <circle cx={x} cy={y} r={cw * 0.42} className="castle" />}
                {!castle && r === 1 && marks.has(c) && (
                  <circle cx={x} cy={y - 34} r={3.5} className="mark" />
                )}
                {o.boardStyle === 'squares' ? (
                  <rect
                    x={x - cw / 2 + 5}
                    y={y - cw / 2 + 5}
                    width={cw - 10}
                    height={cw - 10}
                    rx={4}
                    className="cell"
                  />
                ) : (
                  <line x1={x} x2={x} y1={y - 38} y2={y + 38} className="cell-line" />
                )}
                {d && (
                  <g className={d.ok ? (d.capture ? 'ring capture' : 'ring') : 'ring no'}>
                    <circle cx={x} cy={y} r={cw * 0.46} />
                    {d.ok && d.capture && (
                      <text x={x + cw * 0.3} y={y - cw * 0.3}>
                        ×
                      </text>
                    )}
                    {!d.ok && (
                      <text x={x + cw * 0.3} y={y - cw * 0.3}>
                        ⊘
                      </text>
                    )}
                  </g>
                )}
                {here.map((p, i) => (
                  <PieceGlyph
                    key={p.id}
                    piece={p}
                    x={x}
                    y={y - Math.min(i, 3) * 7 + Math.min(here.length - 1, 3) * 3.5}
                    glow={movable.has(p.id)}
                    selected={selectedPieceId === p.id}
                    small={cw < 50}
                  />
                ))}
                {here.length > 1 && (
                  <text x={x + 12} y={y + 26} className="count">
                    {here.length}
                  </text>
                )}
              </g>
            );
          }),
        )}

        {trackPath && (
          <g className="track-overlay" aria-hidden="true">
            <polyline
              points={trackPath.map((p) => `${p.x},${p.y}`).join(' ')}
              fill="none"
              markerMid="url(#arrow)"
              markerEnd="url(#arrow)"
            />
            <circle cx={trackPath[0].x} cy={trackPath[0].y} r={5} />
          </g>
        )}
      </svg>
    </div>
  );
}

function PieceGlyph({
  piece,
  x,
  y,
  glow,
  selected,
  small,
}: {
  piece: Piece;
  x: number;
  y: number;
  glow: boolean;
  selected: boolean;
  small: boolean;
}) {
  const k = piece.kind;
  const r = (k === 'soldier' ? 13 : 16) * (small ? 0.92 : 1);
  const side = piece.side;
  const cls =
    'piece ' +
    (side === null ? 'neutral' : `side${side}`) +
    ` ${k}` +
    (piece.active ? ' active' : ' asleep') +
    (glow ? ' glow' : '') +
    (selected ? ' selected' : '');
  let shape;
  if (k === 'king') {
    shape = (
      <path
        d={`M ${x} ${y - r - 2} L ${x + r + 2} ${y} L ${x} ${y + r + 2} L ${x - r - 2} ${y} Z`}
      />
    );
  } else if (side === 1) {
    shape = <path d={`M ${x} ${y - r} L ${x + r} ${y + r * 0.85} L ${x - r} ${y + r * 0.85} Z`} />;
  } else {
    shape = <circle cx={x} cy={y} r={r} />;
  }
  return (
    <g className={cls}>
      {shape}
      {k === 'queen' && (
        <circle cx={x} cy={y + (side === 1 ? 2 : 0)} r={r * 0.45} className="inner" />
      )}
      {k === 'king' && side !== null && (
        <circle cx={x} cy={y} r={r * 0.4} className={`inner own${side}`} />
      )}
    </g>
  );
}
