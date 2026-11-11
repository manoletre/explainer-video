// Storyboard and checks: renders stills (default: just after every [bracket] starts) at half size into
// <out>/, and writes <out>/check.json with the brackets the scene uses and the layout problems seen
// in each still (overlapping boxes, boxes off the frame). Run by `remotion.py check`, or:
//   node tools/inspect.mjs storyboard            # the default moments
//   node tools/inspect.mjs storyboard 12.5,40    # these seconds
import fs from 'node:fs';
import path from 'node:path';
import {bundle} from '@remotion/bundler';
import {ensureBrowser, openBrowser, renderStill, selectComposition} from '@remotion/renderer';

const out = path.resolve(process.argv[2] || 'storyboard');
const tl = JSON.parse(fs.readFileSync('src/timeline.json', 'utf8'));
let times = process.argv[3] ? process.argv[3].split(',').map(Number) : [];
if (!times.length) {
  for (const s of tl.sections) times.push(s.start + 0.9);
  for (const l of tl.lines) {
    for (const s of l.spans) times.push(Math.min(s.start + 0.8, l.end));
    times.push(l.end - 0.05);
  }
}
times = [...new Set(times.map(t => Math.round(t * 4) / 4))].sort((a, b) => a - b);

fs.rmSync(out, {recursive: true, force: true});
fs.mkdirSync(out, {recursive: true});
await ensureBrowser();
const serveUrl = await bundle({entryPoint: path.resolve('src/index.tsx')});
const inputProps = {check: true};
const browser = await openBrowser('chrome');
const composition = await selectComposition({serveUrl, id: 'Explainer', inputProps, puppeteerInstance: browser});
const used = new Set();
const frames = [];
let i = 0;
for (const t of times) {
  const frame = Math.min(composition.durationInFrames - 1, Math.max(0, Math.round(t * composition.fps)));
  const logs = [];
  const file = path.join(out, `${String(i++).padStart(3, '0')}_${t.toFixed(2)}s.png`);
  await renderStill({
    composition, serveUrl, inputProps, frame, output: file, scale: 0.5, puppeteerInstance: browser,
    onBrowserLog: log => { if (log.text.startsWith('EXPLAINER_CHECK ')) logs.push(JSON.parse(log.text.slice(16))); },
  });
  const last = logs[logs.length - 1] || {used: [], problems: ['the layout check did not run']};
  last.used.forEach(u => used.add(u));
  frames.push({t, file: path.basename(file), problems: last.problems});
}
await browser.close({silent: true});
fs.writeFileSync(path.join(out, 'check.json'), JSON.stringify({used: [...used], frames}, null, 1));
console.log(`${frames.length} stills in ${out}`);
