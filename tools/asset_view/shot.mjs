// 에셋 검증 렌더 스크린샷: node web/tools/asset_view/shot.mjs [view=range|top ...] → analysis/assets_work/shots/*.png
import fs from "node:fs";
import http from "node:http";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright-core";
const WEB = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const OUT = path.resolve(WEB, "../analysis/assets_work/shots");
const MIME = { ".html": "text/html", ".js": "text/javascript", ".mjs": "text/javascript", ".json": "application/json", ".wasm": "application/wasm", ".glb": "model/gltf-binary" };
function findChromium() {
  const root = path.join(process.env.LOCALAPPDATA ?? path.join(os.homedir(), "AppData", "Local"), "ms-playwright");
  for (const d of fs.readdirSync(root).filter((d) => /^chromium-\d+$/.test(d)).sort((a, b) => +b.split("-")[1] - +a.split("-")[1]))
    for (const sub of ["chrome-win64", "chrome-win"]) { const p = path.join(root, d, sub, "chrome.exe"); if (fs.existsSync(p)) return p; }
  throw new Error("chromium not found");
}
const server = http.createServer((req, res) => {
  const u = decodeURIComponent(new URL(req.url, "http://x").pathname);
  const f = path.join(WEB, u);
  if (!fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.statusCode = 404; res.end(); return; }
  res.setHeader("content-type", MIME[path.extname(f)] ?? "application/octet-stream");
  fs.createReadStream(f).pipe(res);
});
await new Promise((r) => server.listen(0, "127.0.0.1", r));
const browser = await chromium.launch({ executablePath: findChromium(), args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"] });
const page = await browser.newPage({ viewport: { width: 960, height: 600 } });
const errors = [];
page.on("console", (m) => { if (m.type() === "error" || m.type() === "warning") errors.push(m.text()); });
page.on("pageerror", (e) => errors.push(String(e)));
fs.mkdirSync(OUT, { recursive: true });
for (const qs of process.argv.slice(2).length ? process.argv.slice(2) : ["view=range", "view=top"]) {
  await page.goto(`http://127.0.0.1:${server.address().port}/tools/asset_view/view.html?${qs}`);
  await page.waitForFunction(() => window.__done === true || window.__err, null, { timeout: 300000 });
  const name = qs.replace(/[=&]/g, "_");
  await page.locator("canvas").screenshot({ path: path.join(OUT, name + ".png") });
  console.log(name, JSON.stringify(await page.evaluate(() => window.__report)));
}
console.log("errors:", errors.slice(0, 10));
await browser.close();
server.close();
