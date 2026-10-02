// 독립 개발 서버. URL 레이아웃은 ddalkkakrider 포털과 같다:
//   /game/splatoon3/            -> scripts/app/games/splatoon3/index.html
//   /game/splatoon3/app.js|css  -> esbuild 메모리 번들(요청 시 재빌드)
//   /game/splatoon3/assets/*    -> games/splatoon3/assets/*
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { SPLATOON3, splatoon3Dev } from "../games/splatoon3/bundle.mjs";
import { vendor } from "./vendor.mjs";

const web = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const PORT = Number(process.env.PORT ?? 5190);
const page = path.join(web, "scripts/app/games/splatoon3/index.html");
const assets = path.join(web, "games/splatoon3/assets");
const bundle = splatoon3Dev();

export const MIME = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".glb": "model/gltf-binary",
  ".bin": "application/octet-stream",
  ".ktx2": "image/ktx2",
  ".png": "image/png",
  ".ogg": "audio/ogg",
  ".wasm": "application/wasm",
};

vendor();

http
  .createServer(async (req, res) => {
    try {
      const url = new URL(req.url ?? "/", "http://x");
      const p = decodeURIComponent(url.pathname);
      if (p === "/" || p === SPLATOON3.slice(0, -1)) return redirect(res, SPLATOON3);
      if (p === SPLATOON3) return send(res, ".html", fs.readFileSync(page));
      if (p === SPLATOON3 + "app.js" || p === SPLATOON3 + "app.css") {
        const files = await bundle();
        const name = p.slice(SPLATOON3.length);
        if (!files[name]) return notFound(res);
        return send(res, path.extname(name), Buffer.from(files[name]));
      }
      if (p.startsWith(SPLATOON3 + "assets/")) {
        const file = path.normalize(path.join(assets, p.slice((SPLATOON3 + "assets/").length)));
        if (!file.startsWith(assets) || !fs.existsSync(file) || !fs.statSync(file).isFile()) return notFound(res);
        return send(res, path.extname(file), fs.readFileSync(file));
      }
      notFound(res);
    } catch (e) {
      res.writeHead(500, { "content-type": "text/plain; charset=utf-8" });
      res.end(String(e?.errors?.map((x) => x.text).join("\n") ?? e?.stack ?? e));
    }
  })
  .listen(PORT, "127.0.0.1", () => console.log(`http://127.0.0.1:${PORT}${SPLATOON3}`));

function send(res, ext, body) {
  res.writeHead(200, { "content-type": MIME[ext] ?? "application/octet-stream", "cache-control": "no-cache" });
  res.end(body);
}
function redirect(res, to) {
  res.writeHead(302, { location: to });
  res.end();
}
function notFound(res) {
  res.writeHead(404);
  res.end("not found");
}
