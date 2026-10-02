// Headless screenshots of web/tools/graphics_verify/view.html.
// usage: node web/tools/graphics_verify/shot.mjs "<query>" [...]   e.g. "scene=assembled&clip=Wait&frame=0"
// -> analysis/graphics/shots/<query>.png + <query>.json (page report)
// three / playwright-core are used read-only from c:/dev/mpj/web/node_modules (nothing installed here).
import fs from 'node:fs';
import http from 'node:http';
import os from 'node:os';
import path from 'node:path';
import { createRequire } from 'node:module';

const ROOT = 'C:/dev/splatoon3';
const MPJ_MODULES = 'C:/dev/mpj/web/node_modules';
const { chromium } = createRequire(path.join(MPJ_MODULES, 'x.js'))('playwright-core');
const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.png': 'image/png', '.glb': 'model/gltf-binary', '.json': 'application/json' };

function findChromium() {
  const root = path.join(process.env.LOCALAPPDATA ?? path.join(os.homedir(), 'AppData', 'Local'), 'ms-playwright');
  const dirs = fs.readdirSync(root).filter((d) => /^chromium-\d+$/.test(d)).sort((a, b) => +b.split('-')[1] - +a.split('-')[1]);
  for (const d of dirs) for (const sub of ['chrome-win64', 'chrome-win']) {
    const p = path.join(root, d, sub, 'chrome.exe');
    if (fs.existsSync(p)) return p;
  }
  throw new Error('chromium not found');
}

const server = http.createServer((req, res) => {
  const u = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  const f = u.startsWith('/three/') ? path.join(MPJ_MODULES, 'three', u.slice(7)) : path.join(ROOT, u);
  if (!fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.statusCode = 404; res.end(); return; }
  res.setHeader('content-type', MIME[path.extname(f)] ?? 'application/octet-stream');
  fs.createReadStream(f).pipe(res);
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const port = server.address().port;
const browser = await chromium.launch({ executablePath: findChromium(), args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
const page = await browser.newPage({ viewport: { width: 960, height: 720 } });
const errors = [];
page.on('console', (m) => { if (m.type() === 'error' || m.type() === 'warning') errors.push(m.text()); });
page.on('pageerror', (e) => errors.push(String(e)));
page.on('response', (r) => { if (r.status() >= 400) errors.push(r.status() + ' ' + r.url()); });
const outDir = path.join(ROOT, 'analysis/graphics/shots');
fs.mkdirSync(outDir, { recursive: true });
for (const q of process.argv.slice(2)) {
  await page.goto(`http://127.0.0.1:${port}/web/tools/graphics_verify/view.html?${q}`);
  await page.waitForFunction(() => window.__done === true, null, { timeout: 180000 });
  const name = q.replace(/[=&]/g, '_');
  await page.locator('canvas').screenshot({ path: path.join(outDir, name + '.png') });
  const rep = await page.evaluate(() => window.__report);
  fs.writeFileSync(path.join(outDir, name + '.json'), JSON.stringify(rep, null, 1));
  console.log('shot', name, JSON.stringify(rep.bbox), Object.keys(rep.parts || {}).length, 'parts', rep.warnings.join(';'));
}
console.log('console errors/warnings:', errors.length ? errors.slice(0, 10) : 'none');
await browser.close();
server.close();
