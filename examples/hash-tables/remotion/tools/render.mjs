// Render the video at the best size that finishes within a time budget, with progress.
//   node tools/render.mjs out/video.mp4 [--budget 10] [--plan] [--scale 1] [--concurrency N] [--captions]
// It bundles once, times a sample of the video's own frames at full size (then smaller, if needed),
// picks the first size whose estimate fits the budget, says so, and renders it.
import os from 'node:os';
import fs from 'node:fs';
import path from 'node:path';
import {bundle} from '@remotion/bundler';
import {ensureBrowser, openBrowser, renderMedia, selectComposition} from '@remotion/renderer';

const args = process.argv.slice(2);
const opt = (name, dflt) => { const i = args.indexOf(name); return i >= 0 ? args[i + 1] : dflt; };
const output = path.resolve(args[0] && !args[0].startsWith('--') ? args[0] : 'out/video.mp4');
const budget = Number(opt('--budget', 10));
const forced = opt('--scale', null);
const cores = os.availableParallelism ? os.availableParallelism() : os.cpus().length;
const ramGb = os.totalmem() / 2 ** 30;
const concurrency = Number(opt('--concurrency', Math.max(1, Math.min(cores, Math.floor(ramGb / 1.0)))));
const inputProps = {captions: args.includes('--captions')};
const LADDER = [1, 2 / 3, 1 / 2];
const say = s => console.log(s);

await ensureBrowser();
const t0 = Date.now();
const serveUrl = await bundle({entryPoint: path.resolve('src/index.tsx')});
const browser = await openBrowser('chrome');
const composition = await selectComposition({serveUrl, id: 'Explainer', inputProps, puppeteerInstance: browser});
const N = composition.durationInFrames;
const size = s => `${Math.round(composition.width * s)}x${Math.round(composition.height * s)}`;
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'explainer-'));

async function sample(scale) {
  const n = Math.min(N, Math.max(60, 4 * concurrency * 8));
  const a = Math.max(0, Math.floor(N / 2 - n / 2));
  const t = Date.now();
  await renderMedia({composition, serveUrl, inputProps, codec: 'h264', scale, concurrency, muted: true,
    frameRange: [a, a + n - 1], outputLocation: path.join(tmp, 'sample.mp4'), puppeteerInstance: browser});
  return (Date.now() - t) / 1000 / n;
}

let pick = forced ? Number(forced) : null;
const est = {};
if (!pick) {
  for (const s of LADDER) {
    est[s] = (await sample(s)) * N * 1.1 / 60;
    say(`measured ${size(s)} at ${composition.fps} fps: about ${est[s].toFixed(1)} min for ${N} frames (${concurrency} Chrome workers)`);
    if (est[s] <= budget) { pick = s; break; }
  }
  pick = pick || LADDER[LADDER.length - 1];
}
say(`plan: ${size(pick)} at ${composition.fps} fps` + (est[pick] ? `, about ${est[pick].toFixed(1)} min` : '') + ` (budget ${budget} min)`);
if (pick !== 1 && !forced) {
  say('limits:');
  for (const s of LADDER.filter(s => s > pick)) say(`  ${size(s)}: about ${est[s].toFixed(1)} min (--budget ${Math.ceil(est[s])} or --scale ${s.toFixed(3)})`);
  say('  more CPU cores render proportionally faster; Remotion needs no GPU');
}
if (args.includes('--plan')) { await browser.close({silent: true}); process.exit(0); }

fs.mkdirSync(path.dirname(output), {recursive: true});
const start = Date.now();
let lastPrint = 0;
await renderMedia({
  composition, serveUrl, inputProps, codec: 'h264', crf: 18, scale: pick, concurrency, outputLocation: output,
  puppeteerInstance: browser,
  onProgress: ({progress}) => {
    const now = (Date.now() - start) / 1000;
    if (now - lastPrint >= 20 && progress > 0) {
      lastPrint = now;
      const left = now / progress - now;
      say(`render: ${Math.round(progress * 100)}%, ${(now / 60).toFixed(1)} min in, about ${(left / 60).toFixed(1)} min left`);
    }
  },
});
await browser.close({silent: true});
fs.rmSync(tmp, {recursive: true, force: true});
const mb = fs.statSync(output).size / 1e6;
say(`${output}  ${size(pick)} at ${composition.fps} fps, ${mb.toFixed(1)} MB (rendered in ${((Date.now() - start) / 60000).toFixed(1)} min, ${((Date.now() - t0) / 60000).toFixed(1)} min with planning)`);
