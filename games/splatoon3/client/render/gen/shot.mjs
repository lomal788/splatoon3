// render 헤드리스 확인: 개발 서버 페이지를 열고 플레이어 상태를 주입해 스크린샷을 찍는다.
// 사용: node games/splatoon3/client/render/gen/shot.mjs [--fake] [--map <glb>] [이름=상태,...]
//   --fake       : catalog.json 을 가로채 analysis/graphics/web 의 변환 GLB(몸·파츠·오징어·무기)로 번들을 만든다
//                  (에셋 담당 번들이 아직 없을 때 조립·애니 확인용. 실제 번들 형식과 다를 수 있음)
//   --map <glb>  : --fake 일 때 맵 visual.glb 로 쓸 파일
//   장면 목록    : 이름=상태16진[,squid][,speed=0.05][,frames=N][,yaw=deg][,cam=x/y/z/tx/ty/tz]  예) wait=56 squid=85,squid shoot=d
//                  상태 x = 상태 번호 없이(squid 플래그로 render 대체 전이), 이름 real* = 주입 없이 physics 상태 그대로
// 출력: test/out/render_<이름>.png, test/out/render_shots.json
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright-core";

const here = path.dirname(fileURLToPath(import.meta.url));
const web = path.resolve(here, "../../../../..");
const root = path.resolve(web, "..");
const out = path.join(web, "test/out");
fs.mkdirSync(out, { recursive: true });
const args = process.argv.slice(2);
const fake = args.includes("--fake");
const mapArg = args.includes("--map") ? args[args.indexOf("--map") + 1] : null;
const scenes = args.filter((a) => a.includes("=")).map((a) => {
  const name = a.slice(0, a.indexOf("=")), spec = a.slice(a.indexOf("=") + 1);
  const parts = spec.split(",");
  const o = { name, state: parseInt(parts[0], 16), squid: false, speed: 0, frames: 40, yaw: 0, cam: null };
  for (const p of parts.slice(1)) {
    if (p === "squid") o.squid = true;
    else if (p.startsWith("speed=")) o.speed = +p.slice(6);
    else if (p.startsWith("frames=")) o.frames = +p.slice(7);
    else if (p.startsWith("yaw=")) o.yaw = +p.slice(4);
    else if (p.startsWith("cam=")) o.cam = p.slice(4).split("/").map(Number);
  }
  return o;
});
if (!scenes.length) scenes.push({ name: "default", state: NaN, squid: false, speed: 0, frames: 30, yaw: 0, cam: null });

const G = path.join(root, "analysis/graphics/web");
const FAKE_CHAR = ["Player00", "Player_Squid", "Har_SQD000_F", "Eyb_SQD000_F", "Clt_SHT000", "Btm_000_F", "Shs_BOT000", "Tnk_Simple"];
const exe = ["C:/Program Files/Google/Chrome/Application/chrome.exe", "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"].find((p) => fs.existsSync(p));
const browser = await chromium.launch({ executablePath: exe, headless: true, args: ["--enable-unsafe-swiftshader", "--use-angle=swiftshader", "--ignore-gpu-blocklist"] });
const page = await browser.newPage({ viewport: { width: 960, height: 600 } });
const logs = [];
page.on("console", (m) => logs.push(`[${m.type()}] ${m.text()}`));
page.on("pageerror", (e) => logs.push(`[pageerror] ${e.message}`));
if (fake) {
  // 실제 카탈로그 위에 GLB 만 덧붙인다(data/params JSON 은 코어가 쓰므로 그대로)
  const catalog = JSON.parse(fs.readFileSync(path.join(web, "games/splatoon3/assets/catalog.json"), "utf8"));
  catalog.bundles ??= {};
  const add = (id, dir, files) => {
    const b = (catalog.bundles[id] ??= { dir, files: [] });
    b.files = [...b.files.filter((f) => !f.endsWith(".glb")), ...files];
  };
  add("common", "common/", []);
  add("map/Lby_Lobby00", "maps/Lby_Lobby00/", mapArg ? ["fakeglb_map/visual.glb"] : []);
  add("character/Player00", "characters/Player00/", FAKE_CHAR.map((n) => `fakeglb/${n}/${n}.glb`));
  add("weapon/Shooter_Normal_00", "weapons/Shooter_Normal_00/", ["fakeglb/Wmn_Shooter_NormalT/Wmn_Shooter_NormalT.glb"]);
  if (!mapArg) catalog.bundles["map/Lby_Lobby00"].files = catalog.bundles["map/Lby_Lobby00"].files.filter((f) => !f.endsWith(".glb"));
  await page.route("**/game/splatoon3/assets/catalog.json", (r) => r.fulfill({ contentType: "application/json", body: JSON.stringify(catalog) }));
  await page.route("**/fakeglb/**", (r) => {
    const rel = decodeURIComponent(new URL(r.request().url()).pathname).split("/fakeglb/")[1];
    const f = path.join(G, rel);
    if (!fs.existsSync(f)) return r.fulfill({ status: 404, body: "" });
    r.fulfill({ body: fs.readFileSync(f), contentType: f.endsWith(".png") ? "image/png" : "model/gltf-binary" });
  });
  await page.route("**/fakeglb_map/**", (r) => r.fulfill({ body: fs.readFileSync(mapArg), contentType: "model/gltf-binary" }));
}
await page.goto("http://127.0.0.1:5190/game/splatoon3/");
await page.waitForFunction(() => globalThis.__splatoon3_render && globalThis.__splatoon3, null, { timeout: 120000 });
await page.addStyleTag({ content: ".s3-overlay .s3-click{display:none !important}" });
await page.waitForTimeout(1500);
const result = [];
for (const s of scenes) {
  await page.evaluate((s) => {
    const g = globalThis.__splatoon3;
    const w = g.world;
    const fakeP = { pos: [0, 0, 0], yaw: (s.yaw * Math.PI) / 180, vel: [0, 0, s.speed], squid: s.squid, team: 0 };
    if (!Number.isNaN(s.state)) fakeP.state = s.state;
    // 이름이 real* 이면 주입하지 않고 physics 의 실제 player 를 쓴다
    globalThis.__fakePlayer = s.name.startsWith("real") ? null : fakeP;
    if (!w.__renderShotPatched) {
      const get = w.shared.get.bind(w.shared);
      w.shared.get = (k) => (k === "player" && globalThis.__fakePlayer ? globalThis.__fakePlayer : get(k));
      const r = g.renderer;
      const orig = r.render.bind(r);
      r.render = (sc, cam) => {
        const c = globalThis.__shotCam ?? [2.6, 1.5, 3.2, 0, 0.9, 0];
        cam.position.set(c[0], c[1], c[2]);
        cam.lookAt(c[3], c[4], c[5]);
        orig(sc, cam);
      };
      w.__renderShotPatched = true;
    }
    globalThis.__shotCam = s.cam;
  }, s);
  // 벽시계가 아니라 게임 프레임 수로 기다린다(swiftshader 는 느림)
  const f0 = await page.evaluate(() => globalThis.__splatoon3.world.frame);
  await page.waitForFunction((t) => globalThis.__splatoon3.world.frame >= t, f0 + s.frames, { timeout: 300000, polling: 50 });
  const file = path.join(out, `render_${s.name}.png`);
  await page.screenshot({ path: file });
  const info = await page.evaluate(() => {
    const r = globalThis.__splatoon3_render;
    const a = r.player.animator;
    return {
      state: a ? a.state.toString(16) : null, disp: a ? a.disp : null, f0: a ? a.f0 : null,
      humanLeaves: a ? a.humanLeaves(0).map((l) => `${l.clip}@${l.frame.toFixed(1)}x${l.weight.toFixed(2)}`) : [],
      squidLeaves: a ? a.squidLeaves(0).map((l) => `${l.clip}@${l.frame.toFixed(1)}x${l.weight.toFixed(2)}`) : [],
      player: r.player.info, map: r.map.stats, env: r.map.env.source,
      calls: globalThis.__splatoon3.renderer.info.render.calls, tris: globalThis.__splatoon3.renderer.info.render.triangles,
    };
  });
  result.push({ name: s.name, file, ...info });
  console.log(s.name, JSON.stringify(info));
}
fs.writeFileSync(path.join(out, "render_shots.json"), JSON.stringify({ result, logs }, null, 1));
console.log(logs.filter((l) => /error|warn|render/i.test(l)).slice(0, 30).join("\n"));
await browser.close();
