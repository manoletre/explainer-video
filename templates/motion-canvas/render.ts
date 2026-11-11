// Headless render page: tools/render.mjs opens it in Chrome; frames go to output/<name>/ as PNGs.
import '@fontsource/pt-serif/400.css';
import '@fontsource/pt-serif/700.css';
import '@fontsource/jetbrains-mono/400.css';
import project from './src/project?project';
import {Renderer, Vector2} from '@motion-canvas/core';
import timeline from './src/timeline.json';

const params = new URLSearchParams(location.search);
const w = window as any;
await Promise.all(['400 48px "PT Serif"', '700 48px "PT Serif"', '48px "JetBrains Mono"'].map(f => document.fonts.load(f)));
const renderer = new Renderer(project as any);
const settings: any = {
  name: params.get('name') ?? 'video', range: [0, Infinity], fps: Number(params.get('fps') ?? timeline.fps),
  size: new Vector2(timeline.width, timeline.height), resolutionScale: Number(params.get('scale') ?? '1'),
  colorSpace: 'srgb', background: timeline.theme.bg,
  exporter: {name: '@motion-canvas/core/image-sequence', options: {fileType: 'image/png', quality: 100, groupByScene: false}},
};
w.__frames = 0;
renderer.onFrameChanged.subscribe((f: number) => { w.__frames = f; });
renderer.onFinished.subscribe((r: number) => { w.__done = r; });
w.__start = () => renderer.render(settings);
w.__ready = true;
