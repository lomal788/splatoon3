// 독립 배포 빌드: dist/game/splatoon3/{index.html, app.js, app.css, assets/...}
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { SPLATOON3, bundleSplatoon3 } from "../games/splatoon3/bundle.mjs";
import { vendor } from "./vendor.mjs";

const web = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const out = path.join(web, "dist", SPLATOON3);
vendor();
fs.rmSync(path.join(web, "dist"), { recursive: true, force: true });
fs.mkdirSync(out, { recursive: true });
for (const [name, body] of Object.entries(await bundleSplatoon3())) fs.writeFileSync(path.join(out, name), body);
fs.copyFileSync(path.join(web, "scripts/app/games/splatoon3/index.html"), path.join(out, "index.html"));
fs.cpSync(path.join(web, "games/splatoon3/assets"), path.join(out, "assets"), {
  recursive: true,
  filter: (src) => !path.basename(src).startsWith("."),
});
console.log("build ->", out);
