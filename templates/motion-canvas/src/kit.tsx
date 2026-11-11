// The building blocks of a Motion Canvas explainer, timed to the narration. Copied from the skill's
// templates/motion-canvas/ by `motion_canvas.py new`; write the video in scenes/video.tsx.
// Coordinates: (0, 0) is the center of the 1920x1080 frame, y grows downwards.
import {Layout, Rect, Txt, Node} from '@motion-canvas/2d';
import {ThreadGenerator, all, useThread, waitFor} from '@motion-canvas/core';
import data from './timeline.json';

export const TL = data as any;
export const C = {...TL.theme, font: 'PT Serif', mono: 'JetBrains Mono'} as Record<string, string>;
const used = new Set<string>();
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
}
/** Clear the stage and show the title of the section starting at line `key`. */
export function* section(view: Node, key: string): ThreadGenerator {
  const sec = TL.sections.find((s: any) => s.first === key);
  if (!sec) throw new Error(`no section starts at line "${key}": add it to SECTIONS in narration.py`);
  const old = view.children();
  if (old.length) { yield* all(...old.map(n => n.opacity(0, 0.4))); old.forEach(n => n.remove()); }
  yield* until(sec.start);
  const [num, ...rest] = sec.title.split(' · ');
  const header = <Txt x={-960 + 80} y={-540 + 76} offset={[-1, 0]} fontFamily={C.font} fontWeight={700} fontSize={40}
    fill={C.fg} opacity={0} text={rest.length ? `${num} · ${rest.join(' · ')}` : sec.title}/>;
  view.add(header);
  yield* header.opacity(1, 0.5);
}
/** Hold the last picture until the narration ends. Call it at the end of the scene. */
export function* finish(): ThreadGenerator {
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
