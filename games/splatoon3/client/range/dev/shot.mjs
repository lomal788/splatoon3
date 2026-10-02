// [range] 헤드리스 확인: 개발 서버를 띄우고 사격장 표적을 맞혀 스크린샷과 상태를 남긴다.
// 사용: node games/splatoon3/client/range/dev/shot.mjs   (출력 test/out/range_*.png, test/out/range_shots.json)
// 다른 뷰(소리·이펙트 등)의 상태와 분리하려고 앱 루프를 멈추고 월드 스텝 + 사격장 뷰 + 렌더만 직접 돌린다.
// 카메라는 표적 앞 고정 위치(카메라 영역 구현과 무관).
import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright-core";

const here = path.dirname(fileURLToPath(import.meta.url));
const web = path.resolve(here, "../../../../..");
const out = path.join(web, "test/out");
fs.mkdirSync(out, { recursive: true });
const PORT = 5297;
const server = spawn(process.execPath, ["tools/serve.mjs"], { cwd: web, env: { ...process.env, PORT: String(PORT) }, stdio: "pipe" });
await new Promise((r) => setTimeout(r, 2500));

const exe = ["C:/Program Files/Google/Chrome/Application/chrome.exe", "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"].find((p) => fs.existsSync(p));
const browser = await chromium.launch({ executablePath: exe, headless: true, args: ["--enable-unsafe-swiftshader", "--use-angle=swiftshader", "--ignore-gpu-blocklist"] });
const page = await browser.newPage({ viewport: { width: 960, height: 600 } });
const logs = [];
page.on("console", (m) => logs.push(`[${m.type()}] ${m.text()}`));
page.on("pageerror", (e) => logs.push(`[pageerror] ${e.message}`));
// 앱의 rAF 루프를 멈춘다(로드 뒤 첫 프레임부터 직접 구동)
await page.addInitScript(() => {
  const raf = window.requestAnimationFrame.bind(window);
  window.requestAnimationFrame = (cb) => (globalThis.__rangeHold ? 0 : raf(cb));
});
const result = { shots: [], logs };
try {
  await page.goto(`http://localhost:${PORT}/game/splatoon3/`);
  await page.waitForFunction(() => globalThis.__splatoon3?.world?.shared?.get("range") && globalThis.__splatoon3_rangeView, null, { timeout: 120000 });
  await page.evaluate(() => (globalThis.__rangeHold = true));
  await page.waitForTimeout(300);
  // 표적 모델(맵 번들 parts) 로드 대기
  await page.waitForTimeout(1500);
  const run = (frames, hits = 0) =>
    page.evaluate(
      ({ frames, hits }) => {
        const s = globalThis.__splatoon3;
        const v = globalThis.__splatoon3_rangeView;
        const w = s.world;
        const r = w.shared.get("range");
        const t = r.targets.find((x) => Math.abs(x.pos[0] - 24) < 0.01 && Math.abs(x.pos[2] - 22.9) < 0.01);
        for (let i = 0; i < hits; i++)
          w.hittables.get(t.id).onDamage({ attacker: 1, team: 0, value: 360, pos: new Float32Array([24.2, 1, 22.5]), dir: new Float32Array([0, 0, 1]), vel: new Float32Array([0, 0, 2]), rateRow: "Shooter", critical: false });
        const pad = { moveX: 0, moveY: 0, lookYaw: 0, lookPitch: 0, hold: 0, trigger: 0, release: 0 };
        for (let i = 0; i < frames; i++) w.step(pad);
        s.camera.position.set(24, 2.2, 16.5);
        s.camera.lookAt(24, 1.3, 22.9);
        s.camera.updateMatrixWorld();
        v.update(w, 1);
        s.renderer.render(s.scene, s.camera);
        const tt = w.shared.get("range").targets.find((x) => x.id === t.id);
        return { frame: w.frame, count: r.targets.length, kinds: [...new Set(r.targets.map((x) => x.kind))], target: tt };
      },
      { frames, hits },
    );
  const snap = async (name, frames, hits = 0) => {
    const st = await run(frames, hits);
    await page.screenshot({ path: path.join(out, `range_${name}.png`) });
    result.shots.push({ name, ...st });
  };
  await snap("idle", 1);
  await snap("hit1", 6, 1);
  await snap("break", 2, 2);
  await snap("burstwait", 90);
  await snap("expand", 50);
  await snap("wait", 30);
} catch (e) {
  result.error = String(e);
} finally {
  fs.writeFileSync(path.join(out, "range_shots.json"), JSON.stringify(result, null, 1));
  await browser.close();
  server.kill();
}
console.log(JSON.stringify(result.shots.map((s) => ({ name: s.name, frame: s.frame, n: s.count, state: s.target?.stateName, anim: `${s.target?.anim}:${s.target?.animFrame}`, hp: s.target?.hp, bend: s.target?.bend, dmg: s.target?.damageInfo?.value, active: s.target?.damageInfo?.active }))));
if (result.error) console.log("ERROR", result.error);
console.log(logs.filter((l) => /error|range/i.test(l)).slice(0, 10).join("\n"));
