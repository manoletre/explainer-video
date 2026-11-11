// The building blocks of a Motion Canvas explainer, timed to the narration. Copied from the skill's
// templates/motion-canvas/ by `motion_canvas.py new`; write the video in scenes/video.tsx.
// Coordinates: (0, 0) is the center of the 1920x1080 frame, y grows downwards.
import {Layout, Line, Rect, Txt, Node} from '@motion-canvas/2d';
import {BBox, ThreadGenerator, all, useThread, waitFor} from '@motion-canvas/core';
import data from './timeline.json';

export const TL = data as any;
export const C = {...TL.theme, font: 'PT Serif', mono: 'JetBrains Mono'} as Record<string, string>;
const used = new Set<string>();
const problems = new Set<string>();
let stage: Node | null = null;
let sectionHeader: Node | null = null;
const LINES = new Map<string, any>(TL.lines.map((l: any) => [l.key, l]));

function line(key: string) {
  const l = LINES.get(key);
  if (!l) throw new Error(`no line "${key}" in narration.py (or the timeline is stale)`);
  return l;
}
/** When bracket i of line `key` starts being spoken, in seconds. */
export function at(key: string, i = 0): number {
  const s = line(key).spans[i];
  if (!s) throw new Error(`line "${key}" has no bracket ${i}`);
  used.add(`${key}:${i}`);
  (window as any).__used = [...used];
  return s.start;
}
/** How long bracket i of line `key` is spoken. */
export const span = (key: string, i = 0) => line(key).spans[i].end - line(key).spans[i].start;

/** Wait until t seconds from the start of the video. */
export function* until(t: number): ThreadGenerator {
  const now = useThread().time();
  if (t > now + 1e-3) yield* waitFor(t - now);
}
/** Run the animations when bracket i of line `key` starts. */
export function* beat(key: string, i: number, ...anims: ThreadGenerator[]): ThreadGenerator {
  yield* until(at(key, i));
  if (anims.length) yield* all(...anims);
  checkLayout();
}
const label = (n: Node) => {
  const txt = n instanceof Txt ? n : n.findFirst(c => c instanceof Txt) as Txt | null;
  return `${n.constructor.name.replace(/\d+$/, "")}${txt ? ` "${txt.text().slice(0, 30)}"` : ''}`;
};
/** Report shapes that leave the frame or overlap, at the current time (window.__layout, for the layout report). */
function checkLayout() {
  if (!stage) return;
  const t = useThread().time().toFixed(2).padStart(7);
  const boxes: [Node, BBox][] = [];
  for (const n of stage.children()) {
    if (n === sectionHeader || n.opacity() < 0.3) continue;
    const b = BBox.fromPoints(...n.cacheBBox().transformCorners(n.localToWorld()));
    if (b.width * b.height < 1) continue;
    if (b.left < -962 || b.right > 962 || b.top < -542 || b.bottom > 542) problems.add(`${t}s  off frame: ${label(n)}`);
    // lines and arrows are meant to touch what they connect
    if (!(n instanceof Line)) boxes.push([n, b]);
  }
  for (let a = 0; a < boxes.length; a++) for (let c = a + 1; c < boxes.length; c++) {
    const [[p, P], [q, Q]] = [boxes[a], boxes[c]];
    const w = Math.min(P.right, Q.right) - Math.max(P.left, Q.left);
    const h = Math.min(P.bottom, Q.bottom) - Math.max(P.top, Q.top);
    if (w <= 0 || h <= 0) continue;
    const inside = (A: BBox, B: BBox) => A.left >= B.left && A.right <= B.right && A.top >= B.top && A.bottom <= B.bottom;
    const small = Math.min(P.width * P.height, Q.width * Q.height);
    if (!inside(P, Q) && !inside(Q, P) && w * h > 0.03 * small)
      problems.add(`${t}s  overlap: ${label(p)} and ${label(q)} (${Math.round(100 * w * h / small)}%)`);
  }
  (window as any).__layout = [...problems];
}
/** Clear the stage and show the title of the section starting at line `key`. */
export function* section(view: Node, key: string): ThreadGenerator {
  const sec = TL.sections.find((s: any) => s.first === key);
  if (!sec) throw new Error(`no section starts at line "${key}": add it to SECTIONS in narration.py`);
  stage = view;
  const old = view.children();
  if (old.length) {
    yield* until(sec.start - 0.4);
    yield* all(...old.map(n => n.opacity(0, 0.4)));
    old.forEach(n => n.remove());
  }
  yield* until(sec.start);
  const [num, ...rest] = sec.title.split(' · ');
  const header = <Txt x={-960 + 80} y={-540 + 76} offset={[-1, 0]} fontFamily={C.font} fontWeight={700} fontSize={40}
    fill={C.fg} opacity={0} text={rest.length ? `${num} · ${rest.join(' · ')}` : sec.title}/>;
  view.add(header);
  sectionHeader = header;
  yield* header.opacity(1, 0.5);
  checkLayout();
}
/** Hold the last picture until the narration ends. Call it at the end of the scene. */
export function* finish(): ThreadGenerator {
  checkLayout();
  yield* until(TL.duration);
}
/** A card: rounded panel with a title and optional dim subtitle. */
export const card = (props: {x?: number; y?: number; w?: number; h?: number; title: string; sub?: string; size?: number}) =>
  <Rect x={props.x ?? 0} y={props.y ?? 0} width={props.w ?? 320} height={props.h ?? 120} radius={16} fill={C.panel}
    stroke={C.line} lineWidth={3} layout direction="column" alignItems="center" justifyContent="center" gap={6}>
    <Txt fontFamily={C.font} fontWeight={700} fontSize={props.size ?? 34} fill={C.fg} text={props.title}/>
    {props.sub ? <Txt fontFamily={C.font} fontSize={(props.size ?? 34) * 0.62} fill={C.dim} text={props.sub}/> : null}
  </Rect>;
export {Layout};
