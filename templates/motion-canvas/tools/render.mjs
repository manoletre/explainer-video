// node tools/render.mjs <name> [scale] [fps]: renders every frame into output/<name>/NNNNNN.png and prints
// a JSON line {frames, seconds, used} (used: the [brackets] the scene animated).
import {createServer} from 'vite';
import puppeteer from 'puppeteer';
const [name = 'video', scale = '1', fps = ''] = process.argv.slice(2);
const server = await createServer({configFile: 'vite.config.ts', server: {port: 0}, logLevel: 'error'});
await server.listen();
const port = server.httpServer.address().port;
const browser = await puppeteer.launch({headless: 'shell', args: ['--no-sandbox']});
const page = await browser.newPage();
page.on('pageerror', e => console.error('page error:', e.message));
page.on('console', m => { if (m.type() === 'error') console.error('page:', m.text()); });
await page.goto(`http://localhost:${port}/render.html?name=${name}&scale=${scale}${fps ? `&fps=${fps}` : ''}`);
await page.waitForFunction('window.__ready === true', {timeout: 120000});
const t = Date.now();
let last = 0;
const tick = setInterval(async () => {
  const f = await page.evaluate('window.__frames').catch(() => 0);
  if (Date.now() - last > 20000) { last = Date.now(); console.error(`render: frame ${f}, ${((Date.now() - t) / 60000).toFixed(1)} min in`); }
}, 2000);
await page.evaluate('window.__start()');
await page.waitForFunction('window.__done !== undefined', {timeout: 0, polling: 500});
clearInterval(tick);
const out = {result: await page.evaluate('window.__done'), frames: await page.evaluate('window.__frames'),
  seconds: (Date.now() - t) / 1000, used: await page.evaluate('window.__used || []')};
console.log(JSON.stringify(out));
await browser.close();
await server.close();
