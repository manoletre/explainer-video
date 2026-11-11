// The building blocks of an explainer in Remotion. Positions are pixels on a 1920x1080 frame, x/y are
// an element's center; times are seconds from the start of the video, taken from the narration:
// at('bi1', 2) is when the words in the third [bracket] of line bi1 start being spoken.
// This file is copied from the skill's templates/remotion/ by `remotion.py new`; write the video
// in Video.tsx.
import React, {createContext, useContext, useEffect, useRef} from 'react';
import {
  AbsoluteFill, Easing, Html5Audio, Img, continueRender, delayRender, getInputProps, interpolate, spring,
  staticFile, useCurrentFrame, useVideoConfig,
} from 'remotion';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import '@fontsource/pt-serif/400.css';
import '@fontsource/pt-serif/700.css';
import '@fontsource/pt-serif/400-italic.css';
import '@fontsource/jetbrains-mono/400.css';
import data from './timeline.json';

export type Span = {i: number; text: string; start: number; end: number};
export type Word = {w: string; start: number; end: number; span: number | null};
export type Line = {key: string; start: number; end: number; text: string; spans: Span[]; words: Word[]};
export type Sect = {title: string; first: string; start: number; end: number};
export type Cue = {start: number; end: number; text: string};
export type Theme = {
  name: string; bg: string; fg: string; dim: string; accent: string; on_accent: string; ink: string;
  good: string; bad: string; blue: string; panel: string; line: string; pointer: string;
};
export type Timeline = {
  fps: number; width: number; height: number; duration: number; captions: boolean; theme: Theme;
  lines: Line[]; sections: Sect[]; cues: Cue[];
};
export const TL = data as Timeline;

// the theme (scripts/style.py): accent is gold for fills, with on_accent text on it; ink is the accent
// as text or a thin line on the background
export const C = {
  ...TL.theme,
  font: '"PT Serif", Georgia, "DejaVu Serif", serif',
  mono: '"JetBrains Mono", Menlo, "DejaVu Sans Mono", monospace',
};
/** A color with an alpha from 0 to 1. */
export const alpha = (hex: string, a: number) =>
  hex.slice(0, 7) + Math.round(Math.max(0, Math.min(1, a)) * 255).toString(16).padStart(2, '0');

const props = getInputProps() as {check?: boolean; captions?: boolean};
const LINES = new Map(TL.lines.map(l => [l.key, l]));
const used = new Set<string>();

// ---------- time ----------
export function line(key: string): Line {
  const l = LINES.get(key);
  if (!l) throw new Error(`no line "${key}" in narration.py (or the timeline is stale: remotion.py timeline)`);
  return l;
}
/** When the words of bracket i of line `key` start being spoken. */
export function at(key: string, i = 0): number {
  const l = line(key);
  const s = l.spans[i];
  if (!s) throw new Error(`line "${key}" has ${l.spans.length} brackets, so there is no bracket ${i}`);
  used.add(`${key}:${i}`);
  return s.start;
}
/** When the words of bracket i of line `key` have been spoken. */
export function done(key: string, i = 0): number {
  at(key, i);
  return line(key).spans[i].end;
}
export const starts = (key: string) => line(key).start;
export const ends = (key: string) => line(key).end;

export function useTime(): number {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return frame / fps;
}
/** 0 before t, 1 after t + dur, eased between. */
export function ramp(now: number, t: number, dur = 0.5): number {
  return interpolate(now, [t, t + dur], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic),
  });
}
/** A bump 0 -> 1 -> 0 starting at t, for emphasis. */
export function bump(now: number, t: number, dur = 0.9): number {
  return now < t || now > t + dur ? 0 : Math.sin((Math.PI * (now - t)) / dur);
}

const SectionCtx = createContext<{start: number; end: number}>({start: 0, end: Infinity});

/** Timing every element takes: appear at `at` (default: when its section starts), fade at `out`,
 *  drop to 35% at `dim`, pulse with an accent glow at each time in `hot`. */
export type Timed = {at?: number; out?: number; dim?: number; hot?: number[]; label?: string};

function useLook(t: Timed, dur = 0.45) {
  const now = useTime();
  const {fps} = useVideoConfig();
  const sec = useContext(SectionCtx);
  const a = t.at ?? sec.start;
  const shown = Math.min(ramp(now, a, dur), t.out === undefined ? 1 : 1 - ramp(now, t.out, 0.35));
  const dimmed = t.dim === undefined ? 1 : 1 - 0.65 * ramp(now, t.dim, 0.4);
  const pop = spring({frame: Math.max(0, (now - a) * fps), fps, config: {damping: 15, mass: 0.6}});
  const glow = Math.max(0, ...(t.hot ?? []).map(h => bump(now, h)));
  return {now, a, opacity: shown * dimmed, pop, glow, visible: shown > 0.001};
}

const label = (t: Timed, fallback: React.ReactNode) =>
  t.label ?? (typeof fallback === 'string' || typeof fallback === 'number' ? String(fallback) : 'element');

// ---------- layout ----------
/** One section: its title in the corner, and its content, shown from its first line to the next section. */
export const Section: React.FC<{id: string; header?: boolean; children?: React.ReactNode}> = ({id, header = true, children}) => {
  const now = useTime();
  const s = TL.sections.find(x => x.first === id);
  if (!s) throw new Error(`no section starts at line "${id}": add it to SECTIONS in narration.py`);
  if (now < s.start || now >= s.end) return null;
  return (
    <SectionCtx.Provider value={s}>
      <AbsoluteFill style={{opacity: 1 - ramp(now, s.end - 0.45, 0.45)}}>
        {header && <Header title={s.title}/>}
        {children}
      </AbsoluteFill>
    </SectionCtx.Provider>
  );
};

export const Header: React.FC<{title: string}> = ({title}) => {
  const {opacity} = useLook({});
  const [num, ...rest] = title.split(' · ');
  return (
    <div data-box="header" style={{position: 'absolute', left: 80, top: 52, fontSize: 40, fontWeight: 700, opacity}}>
      {rest.length ? <><span style={{color: C.ink}}>{num}</span><span style={{color: C.dim}}> · </span>{rest.join(' · ')}</> : title}
    </div>
  );
};

/** A card: a rounded panel with a title and an optional dim subtitle. */
export const Box: React.FC<Timed & {
  x: number; y: number; w?: number; h?: number; title?: React.ReactNode; sub?: React.ReactNode;
  color?: string; fill?: string; size?: number; children?: React.ReactNode;
}> = ({x, y, w = 320, h = 120, title, sub, color = C.line, fill = C.panel, size = 34, children, ...t}) => {
  const {opacity, pop, glow, visible} = useLook(t);
  if (!visible) return null;
  return (
    <div data-box={label(t, title)} style={{
      position: 'absolute', left: x - w / 2, top: y - h / 2, width: w, height: h, boxSizing: 'border-box',
      opacity, transform: `scale(${(0.92 + 0.08 * pop) * (1 + 0.04 * glow)})`,
      background: glow > 0.05 ? alpha(C.accent, glow) : fill,
      border: `3px solid ${glow > 0.05 ? C.accent : color}`, borderRadius: 16,
      boxShadow: glow > 0.05 ? `0 0 ${36 * glow}px ${C.accent}88` : undefined,
      display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      textAlign: 'center', padding: 14, color: glow > 0.4 ? C.on_accent : C.fg,
    }}>
      {title !== undefined && <div style={{fontSize: size, fontWeight: 700, lineHeight: 1.15}}>{title}</div>}
      {sub !== undefined && <div style={{fontSize: size * 0.62, color: glow > 0.4 ? C.on_accent : C.dim, marginTop: 8,
        lineHeight: 1.2}}>{sub}</div>}
      {children}
    </div>
  );
};

/** Text centered on (x, y), or starting at x with align="left". */
export const Text: React.FC<Timed & {
  x: number; y: number; children: React.ReactNode; size?: number; color?: string; weight?: number;
  align?: 'center' | 'left'; w?: number; mono?: boolean;
}> = ({x, y, children, size = 36, color = C.fg, weight = 400, align = 'center', w, mono, ...t}) => {
  const {opacity, pop, glow, visible} = useLook(t);
  if (!visible) return null;
  return (
    <div data-box={label(t, children)} style={{
      position: 'absolute', left: x, top: y, width: w, opacity, fontSize: size, fontWeight: weight,
      color: glow > 0.4 ? C.on_accent : color, fontFamily: mono ? C.mono : C.font, lineHeight: 1.25,
      background: glow > 0.02 ? alpha(C.accent, glow) : undefined, padding: '0 0.18em', borderRadius: 6,
      textAlign: align, whiteSpace: w ? 'normal' : 'nowrap',
      transform: `translate(${align === 'center' ? '-50%' : '0'}, -50%) translateY(${(1 - pop) * 18}px) scale(${1 + 0.06 * glow})`,
    }}>{children}</div>
  );
};

/** A formula, typeset by KaTeX (LaTeX math syntax). */
export const Formula: React.FC<Timed & {x: number; y: number; tex: string; size?: number; color?: string}> =
  ({x, y, tex, size = 52, color = C.fg, ...t}) => {
    const {opacity, pop, glow, visible} = useLook(t);
    if (!visible) return null;
    const html = katex.renderToString(tex, {throwOnError: true, output: 'html'});
    return (
      <div data-box={t.label ?? tex} style={{
        position: 'absolute', left: x, top: y, fontSize: size, opacity, color: glow > 0.05 ? C.ink : color,
        whiteSpace: 'nowrap', transform: `translate(-50%, -50%) translateY(${(1 - pop) * 18}px) scale(${1 + 0.05 * glow})`,
      }} dangerouslySetInnerHTML={{__html: html}}/>
    );
  };

/** An arrow drawn from `from` to `to` (bend > 0 curves it), its head appearing as it arrives. */
export const Arrow: React.FC<Timed & {
  from: [number, number]; to: [number, number]; color?: string; width?: number; bend?: number; dur?: number;
}> = ({from, to, color = C.fg, width = 4, bend = 0, dur = 0.6, ...t}) => {
  const {now, a, opacity, visible} = useLook(t, 0.01);
  if (!visible) return null;
  const p = ramp(now, a, dur);
  const [x1, y1] = from, [x2, y2] = to;
  const mx = (x1 + x2) / 2 - (y2 - y1) * bend, my = (y1 + y2) / 2 + (x2 - x1) * bend;
  const ang = Math.atan2(y2 - my, x2 - mx), L = 18;
  const head = [[x2, y2], [x2 - L * Math.cos(ang - 0.45), y2 - L * Math.sin(ang - 0.45)],
    [x2 - L * Math.cos(ang + 0.45), y2 - L * Math.sin(ang + 0.45)]].map(q => q.join(',')).join(' ');
  return (
    <svg style={{position: 'absolute', left: 0, top: 0, opacity}} width={1920} height={1080}>
      <path d={`M ${x1} ${y1} Q ${mx} ${my} ${x2} ${y2}`} fill="none" stroke={color} strokeWidth={width}
        strokeLinecap="round" pathLength={1} strokeDasharray="1" strokeDashoffset={1 - p}/>
      <polygon points={head} fill={color} opacity={ramp(now, a + dur * 0.8, 0.15)}/>
    </svg>
  );
};

/** A bar chart in the box centered on (x, y); bars grow one after another from `at` (or each bar's own at). */
export const Bars: React.FC<Timed & {
  x: number; y: number; w: number; h: number; data: {label: string; value: number; color?: string; at?: number}[];
  max?: number; format?: (v: number) => string; stagger?: number;
}> = ({x, y, w, h, data: bars, max, format = v => String(v), stagger = 0.25, ...t}) => {
  const {now, a, opacity, visible} = useLook(t);
  if (!visible) return null;
  const top = max ?? Math.max(...bars.map(b => b.value));
  const slot = w / bars.length, bw = slot * 0.62, base = h - 50;
  return (
    <div data-box={t.label ?? 'bar chart'} style={{position: 'absolute', left: x - w / 2, top: y - h / 2, width: w, height: h, opacity}}>
      <svg width={w} height={h} style={{overflow: 'visible'}}>
        <line x1={0} y1={base} x2={w} y2={base} stroke={C.line} strokeWidth={3}/>
        {bars.map((b, i) => {
          const g = ramp(now, b.at ?? a + i * stagger, 0.7);
          const bh = (base - 50) * (b.value / top) * g;
          const cx = slot * i + slot / 2;
          return (
            <g key={i}>
              <rect x={cx - bw / 2} y={base - bh} width={bw} height={bh} rx={6} fill={b.color ?? C.accent}/>
              <text x={cx} y={base - bh - 14} textAnchor="middle" fill={C.fg} fontSize={30} opacity={g > 0.95 ? 1 : 0}
                fontFamily={C.font}>{format(b.value)}</text>
              <text x={cx} y={base + 38} textAnchor="middle" fill={C.dim} fontSize={28} fontFamily={C.font}>{b.label}</text>
            </g>
          );
        })}
      </svg>
    </div>
  );
};

/** Axes with curves: each series is a function f or a list of points, traced from its own at (or the plot's). */
export const Plot: React.FC<Timed & {
  x: number; y: number; w: number; h: number; xr: [number, number]; yr: [number, number];
  series: {f?: (v: number) => number; points?: [number, number][]; color?: string; at?: number; dur?: number; name?: string}[];
  xlabel?: string; ylabel?: string;
}> = ({x, y, w, h, xr, yr, series, xlabel, ylabel, ...t}) => {
  const {now, a, opacity, visible} = useLook(t);
  if (!visible) return null;
  const X = (v: number) => ((v - xr[0]) / (xr[1] - xr[0])) * w;
  const Y = (v: number) => h - ((v - yr[0]) / (yr[1] - yr[0])) * h;
  return (
    <div data-box={t.label ?? 'plot'} style={{position: 'absolute', left: x - w / 2, top: y - h / 2, width: w, height: h, opacity}}>
      <svg width={w} height={h} style={{overflow: 'visible'}}>
        <line x1={0} y1={h} x2={w} y2={h} stroke={C.fg} strokeWidth={3}/>
        <line x1={0} y1={0} x2={0} y2={h} stroke={C.fg} strokeWidth={3}/>
        {xlabel && <text x={w} y={h + 44} textAnchor="end" fill={C.dim} fontSize={28} fontFamily={C.font}>{xlabel}</text>}
        {ylabel && <text x={-16} y={-16} fill={C.dim} fontSize={28} fontFamily={C.font}>{ylabel}</text>}
        {series.map((s, i) => {
          const pts = s.points ?? Array.from({length: 201}, (_, k) => {
            const v = xr[0] + ((xr[1] - xr[0]) * k) / 200;
            return [v, s.f!(v)] as [number, number];
          });
          const d = pts.map(([u, v], k) => `${k ? 'L' : 'M'} ${X(u).toFixed(1)} ${Y(Math.max(yr[0], Math.min(yr[1], v))).toFixed(1)}`).join(' ');
          const p = ramp(now, s.at ?? a, s.dur ?? 1.2);
          const [lu, lv] = pts[pts.length - 1];
          return (
            <g key={i}>
              <path d={d} fill="none" stroke={s.color ?? C.ink} strokeWidth={5} pathLength={1}
                strokeDasharray="1" strokeDashoffset={1 - p} strokeLinejoin="round"/>
              {s.name && <text x={X(lu) + 12} y={Y(Math.min(yr[1], lv))} fill={s.color ?? C.ink} fontSize={28}
                opacity={p > 0.95 ? 1 : 0} fontFamily={C.font}>{s.name}</text>}
            </g>
          );
        })}
      </svg>
    </div>
  );
};

/** Code, with lines highlighted while they are talked about. */
export const Code: React.FC<Timed & {
  x: number; y: number; w: number; code: string; size?: number; marks?: {line: number; at: number; out?: number}[];
}> = ({x, y, w, code, size = 28, marks = [], ...t}) => {
  const {now, opacity, pop, visible} = useLook(t);
  if (!visible) return null;
  const rows = code.replace(/^\n+|\s+$/g, '').split('\n');
  return (
    <div data-box={t.label ?? 'code'} style={{
      position: 'absolute', left: x - w / 2, top: y, width: w, transform: `translateY(-50%) translateY(${(1 - pop) * 18}px)`,
      opacity, background: C.panel, borderRadius: 14, padding: '18px 0', fontFamily: C.mono, fontSize: size,
      border: `2px solid ${C.line}`,
    }}>
      {rows.map((r, i) => {
        const on = Math.max(0, ...marks.filter(mk => mk.line === i + 1)
          .map(mk => Math.min(ramp(now, mk.at, 0.3), mk.out === undefined ? 1 : 1 - ramp(now, mk.out, 0.3))));
        return (
          <div key={i} style={{padding: '2px 24px', whiteSpace: 'pre', background: alpha(C.accent, 0.9 * on),
            color: on > 0.5 ? C.on_accent : C.fg}}>{r || ' '}</div>
        );
      })}
    </div>
  );
};

/** An image from public/ (staticFile name), fitted into w x h around (x, y). */
export const Picture: React.FC<Timed & {x: number; y: number; w: number; h: number; src: string}> =
  ({x, y, w, h, src, ...t}) => {
    const {opacity, pop, visible} = useLook(t);
    if (!visible) return null;
    return (
      <Img data-box={t.label ?? src} src={staticFile(src)} style={{
        position: 'absolute', left: x - w / 2, top: y - h / 2, width: w, height: h, objectFit: 'contain', opacity,
        transform: `scale(${0.95 + 0.05 * pop})`, borderRadius: 12,
      }}/>
    );
  };

/** The laser pointer. Each move flies to (x, y) at `at` and pulses; `ring` circles a spot of that radius,
 *  `sweep` underlines a width as it is read, `hide` takes the pointer away. */
export type Move = {at: number; x?: number; y?: number; ring?: number; sweep?: number; hide?: boolean};
export const Pointer: React.FC<{moves: Move[]}> = ({moves}) => {
  const now = useTime();
  const ms = [...moves].sort((p, q) => p.at - q.at);
  const k = ms.reduce((acc, mv, i) => (mv.at <= now ? i : acc), -1);
  if (k < 0 || ms[k].hide) return null;
  const cur = ms[k], prev = k > 0 && !ms[k - 1].hide ? ms[k - 1] : null;
  // where a move lands, and where the pointer is once it has landed (a sweep then runs along its width)
  const land = (mv: Move): [number, number] => [mv.x! - (mv.sweep ?? 0) / 2, mv.y!];
  const rest = (mv: Move, t: number): [number, number] =>
    [mv.x! - (mv.sweep ?? 0) / 2 + (mv.sweep ?? 0) * ramp(t, mv.at + 0.5, 1.2), mv.y!];
  const fly = prev ? ramp(now, cur.at, 0.5) : 1;
  const [fx, fy] = prev ? rest(prev, cur.at) : land(cur);
  const [lx, ly] = land(cur);
  const [x, y] = fly < 1 ? [fx + (lx - fx) * fly, fy + (ly - fy) * fly] : rest(cur, now);
  const sweepP = cur.sweep ? ramp(now, cur.at + 0.5, 1.2) : 0;
  const arrive = bump(now, cur.at + 0.45, 0.6);
  const ringP = cur.ring ? ramp(now, cur.at + 0.45, 0.8) : 0;
  const appear = prev ? 1 : ramp(now, cur.at, 0.25);
  return (
    <svg style={{position: 'absolute', left: 0, top: 0, opacity: appear, pointerEvents: 'none'}} width={1920} height={1080}>
      <defs>
        <radialGradient id="laser"><stop offset="0%" stopColor="#FFFFFF"/><stop offset="35%" stopColor={C.pointer}/>
          <stop offset="100%" stopColor={alpha(C.pointer, 0)}/></radialGradient>
      </defs>
      {cur.sweep && <line x1={cur.x! - cur.sweep / 2} y1={cur.y! + 8} x2={cur.x! - cur.sweep / 2 + cur.sweep * sweepP}
        y2={cur.y! + 8} stroke={C.pointer} strokeWidth={5} strokeLinecap="round" opacity={0.85}/>}
      {cur.ring && <circle cx={cur.x} cy={cur.y} r={cur.ring} fill="none" stroke={C.pointer} strokeWidth={5}
        pathLength={1} strokeDasharray="1" strokeDashoffset={1 - ringP} opacity={0.9}/>}
      <circle cx={x} cy={y} r={22 + 16 * arrive} fill="url(#laser)" opacity={0.55 + 0.3 * arrive}/>
      <circle cx={x} cy={y} r={7} fill="#FFFFFF"/>
    </svg>
  );
};

// ---------- the frame ----------
const Captions: React.FC = () => {
  const now = useTime();
  const cue = TL.cues.find(c => now >= c.start && now < c.end);
  if (!cue) return null;
  return (
    <div style={{position: 'absolute', left: 0, right: 0, bottom: 44, display: 'flex', justifyContent: 'center'}}>
      <div style={{background: alpha(C.bg, 0.88), color: C.fg, border: `2px solid ${C.line}`, fontSize: 36, padding: '8px 22px', borderRadius: 10,
        maxWidth: 1500, textAlign: 'center', lineHeight: 1.3}}>{cue.text}</div>
    </div>
  );
};

function opacityOf(el: Element | null): number {
  let o = 1;
  for (let e: Element | null = el; e; e = e.parentElement) o *= parseFloat(getComputedStyle(e).opacity || '1');
  return o;
}

/** In check mode (remotion.py check): logs the brackets used and the layout problems of this frame. */
const Checker: React.FC = () => {
  const now = useTime();
  const frame = useCurrentFrame();
  const root = useRef<HTMLDivElement>(null);
  const key = TL.lines.find(l => now >= l.start && now < l.end + 0.6)?.key ?? '';
  useEffect(() => {
    const handle = delayRender('layout check');
    setTimeout(() => {
      const frameBox = root.current!.parentElement!.getBoundingClientRect();
      const sx = TL.width / frameBox.width;
      const boxes = Array.from(document.querySelectorAll<HTMLElement>('[data-box]'))
        .map(el => {
          const r = el.getBoundingClientRect();
          return {el, label: el.dataset.box ?? '?', o: opacityOf(el), x0: (r.left - frameBox.left) * sx,
            y0: (r.top - frameBox.top) * sx, x1: (r.right - frameBox.left) * sx, y1: (r.bottom - frameBox.top) * sx};
        })
        .filter(b => b.o > 0.3 && b.x1 > b.x0);
      const problems: string[] = [];
      for (const b of boxes) {
        if (b.x0 < -2 || b.y0 < -2 || b.x1 > TL.width + 2 || b.y1 > TL.height + 2) problems.push(`off frame: ${b.label}`);
      }
      for (let i = 0; i < boxes.length; i++) for (let j = i + 1; j < boxes.length; j++) {
        const p = boxes[i], q = boxes[j];
        if (p.el.contains(q.el) || q.el.contains(p.el)) continue;
        const w = Math.min(p.x1, q.x1) - Math.max(p.x0, q.x0), h = Math.min(p.y1, q.y1) - Math.max(p.y0, q.y0);
        if (w <= 0 || h <= 0) continue;
        const small = Math.min((p.x1 - p.x0) * (p.y1 - p.y0), (q.x1 - q.x0) * (q.y1 - q.y0));
        if (w * h > 0.03 * small) problems.push(`overlap: "${p.label}" and "${q.label}" (${Math.round((100 * w * h) / small)}%)`);
      }
      console.log('EXPLAINER_CHECK ' + JSON.stringify({t: now, used: [...used], problems}));
      continueRender(handle);
    }, 0);
  }, [frame, now]);
  return <div ref={root} style={{position: 'absolute', left: 14, top: 10, color: C.pointer, fontSize: 26,
    fontFamily: C.mono, zIndex: 99}}>{now.toFixed(2)}s {key}</div>;
};

/** The whole video: background, narration track, captions and (in check mode) the checker. */
export const Explainer: React.FC<{children?: React.ReactNode}> = ({children}) => (
  <AbsoluteFill style={{backgroundColor: C.bg, color: C.fg, fontFamily: C.font}}>
    <Html5Audio src={staticFile('narration.wav')}/>
    {children}
    {(TL.captions || props.captions) && <Captions/>}
    {props.check && <Checker/>}
  </AbsoluteFill>
);
