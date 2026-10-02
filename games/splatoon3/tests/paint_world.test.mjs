// 도색 파이프라인(요청 → 패스 → 스텐실·색·카운트) 대조.
// 텍셀 판정 9경우의 기대값 = web/tools/paintgpu_frame_sim.py 출력(analysis/paintgpu/frame_sim_out.txt):
//   패스 순서 0x7102c14168 + 모드별 렌더 상태(원본 실행) + PaintOverpaint 셰이더 재구현.
// 스탬프 값을 정확히 주려고 균일 마스크(Shot00_k 를 상수로)와 변형 번호를 고르는 요청 번호(시드)를 쓴다.
import { test } from "node:test";
import assert from "node:assert/strict";
import { World } from "../core/world.ts";
import { ParamStore } from "../core/params.ts";
import { v3 } from "../core/fmath.ts";
import { createPaintSystem, playerPoint, teamPoint } from "../core/paint/index.ts";
import { paintSeed, patternVariant } from "../core/paint/inktex.ts";

const SINGLE = { Shot00: { TextureName: "", PatternNum: 12, AnimationFrame: 1, AnimationStep: 1, HeightRangeType: "MinEdge", HeightRangeRate: 1, StaticHeightRangeMin: -1, StaticHeightRangeMax: 1, DisableSlopeScale: false } };
const LEVELS = [255, 102, 74, 89, 51, 255, 255, 255, 255, 255, 255, 255]; // k → 상수 마스크 바이트
const INK = { "1.0": 0, "0.4": 1, "0.29": 2, "0.35": 3, "0.2": 4 };

function stamps(levels = LEVELS) {
  const t = {};
  levels.forEach((v, k) => (t[`Shot00_${k}`] = { w: 4, h: 4, data: new Array(16).fill(v) }));
  return t;
}

/** 원점 (0,0,0) 시드에서 변형 k 가 나오는 요청 번호 */
const seedFor = (() => {
  const m = new Map();
  for (let s = 0; m.size < 12 && s < 100000; s++) {
    const k = patternVariant(paintSeed([0, 0, 0], s), 12);
    if (!m.has(k)) m.set(k, s);
  }
  return (k) => m.get(k);
})();

function quad(x0, z0, x1, z1, y = 0) {
  return { positions: [x0, y, z0, x0, y, z1, x1, y, z1, x1, y, z0], indices: [0, 1, 2, 0, 2, 3] };
}

function mkWorld({ meta = quad(-2, -2, 2, 2), tables = { InkTexInfo: SINGLE, ink_stamps: stamps() } } = {}) {
  const w = new World({ map: "t", placement: null, collision: { meta, bin: null }, params: new ParamStore({}, {}), tables, players: [] });
  w.add(createPaintSystem());
  w.init();
  return w;
}

function req(team, inkKey, owner, kind = "Splash") {
  return { team, owner, pos: v3(0, 0, 0), normal: v3(0, 1, 0), dir: v3(1, 0, 0), widthHalf: 0.5, depthScale: 1, kind, seed: seedFor(INK[inkKey]) };
}

/** 월드 좌표에 가장 가까운 텍셀 */
function texelAt(w, x, y, z) {
  const s = w.paint.surf;
  for (const c of s.charts) {
    const d = [x - c.o[0], y - c.o[1], z - c.o[2]];
    const u = Math.floor((d[0] * c.e1[0] + d[1] * c.e1[1] + d[2] * c.e1[2]) * 8);
    const v = Math.floor((d[0] * c.e2[0] + d[1] * c.e2[1] + d[2] * c.e2[2]) * 8);
    const h = d[0] * c.n[0] + d[1] * c.n[1] + d[2] * c.n[2];
    if (Math.abs(h) < 1e-6 && u >= 0 && v >= 0 && u < c.w && v < c.h) {
      const pg = s.pages[c.page];
      return { pg, k: (c.y0 + v) * pg.w + c.x0 + u };
    }
  }
  throw new Error("텍셀 없음");
}

const CASES = [
  // [이름, 프레임별 요청 [팀, ink, 플레이어(null=지우기)], 프레임별 카운터 {플레이어: 수}, 색 [R,G], 스텐실]
  ["빈 텍셀 팀0 ink1.0", [[[0, "1.0", 0]]], [{ 0: 1 }], [255, 0], 1],
  ["같은 팀 다시 칠함(자기 땅)", [[[0, "1.0", 0]], [[0, "1.0", 1]]], [{ 0: 1 }, { 1: 0 }], [255, 0], 1],
  ["팀0 위 팀1 ink1.0", [[[0, "1.0", 0]], [[1, "1.0", 4]]], [{ 0: 1 }, { 4: 1 }], [0, 255], 2],
  ["팀0 위 팀1 ink0.4(못 뺏음)", [[[0, "1.0", 0]], [[1, "0.4", 4]]], [{ 0: 1 }, { 4: 0 }], [153, 102], 1],
  ["빈 텍셀 ink0.29(문턱 미달)", [[[0, "0.29", 0]]], [{ 0: 0 }], [74, 0], 0],
  ["같은 프레임 같은 팀 2명 겹침", [[[0, "1.0", 0], [0, "1.0", 1]]], [{ 0: 1, 1: 0 }], [255, 0], 1],
  ["같은 프레임 두 팀 겹침", [[[0, "1.0", 0], [1, "1.0", 4]]], [{ 0: 1, 4: 1 }], [0, 255], 2],
  ["팀0 0.35 위 팀1 ink0.2(약한 덧칠)", [[[0, "0.35", 0]], [[1, "0.2", 4]]], [{ 0: 1 }, { 4: 0 }], [89, 51], 1],
  ["팀0 칠한 뒤 지우기 1.0", [[[0, "1.0", 0]], [[0, "1.0", null]]], [{ 0: 1 }, {}], [0, 0], 0],
];

for (const [name, frames, counters, color, stencil] of CASES) {
  test(`텍셀 판정 = paintgpu_frame_sim: ${name}`, () => {
    const w = mkWorld();
    const pw = w.paint;
    const STAMP = 64; // 균일 1×1 스탬프 = 8×8 텍셀, 모두 같은 판정
    frames.forEach((reqs, fi) => {
      const before = new Map();
      for (const [team, ink, pl] of reqs) {
        if (pl === null) pw.request(req(team, ink, -1, "Erase"));
        else {
          before.set(pl, pw.playerPaintTexels(100 + pl));
          pw.request(req(team, ink, 100 + pl));
        }
      }
      w.step({ moveX: 0, moveY: 0, lookYaw: 0, lookPitch: 0, hold: 0, trigger: 0, release: 0 });
      for (const [pl, n] of Object.entries(counters[fi])) {
        const got = pw.playerPaintTexels(100 + Number(pl)) - before.get(Number(pl));
        assert.equal(got, n * STAMP, `프레임 ${fi} 플레이어 ${pl} 카운터`);
      }
    });
    const { pg, k } = texelAt(w, 0.0625, 0, 0.0625);
    assert.deepEqual([pg.color[k * 4], pg.color[k * 4 + 1]], color, "색");
    assert.equal(pg.stencil[k], stencil, "스텐실");
    const owner = { 1: 0, 2: 1, 4: 2 }[stencil] ?? -1;
    const c = pw.counts();
    for (let t = 0; t < 3; t++) assert.equal(c.team[t], t === owner ? STAMP : 0, `팀 ${t} 면적`);
  });
}

const PAD = { moveX: 0, moveY: 0, lookYaw: 0, lookPitch: 0, hold: 0, trigger: 0, release: 0 };

test("애니 프레임: Shot00 AF 3·AS 3 → 0,3,6 프레임에 다시 그림, 매번 카운트, 7 프레임에 제거 (0x7102c13750/0x7102c1461c)", () => {
  const w = mkWorld({ tables: { ink_stamps: stamps() } }); // InkTexInfo 없음 → 원본 값 대체 행(AF 3, AS 3)
  const pw = w.paint;
  pw.request(req(0, "0.2", 7));
  const seen = [];
  for (let f = 0; f < 10; f++) {
    w.step(PAD);
    const { pg, k } = texelAt(w, 0.0625, 0, 0.0625);
    seen.push([pg.color[k * 4], pg.stencil[k], pw.playerPaintTexels(7)]);
  }
  // 0.2 → 0.36(소유 성립) → 0.488 (8비트 저장 후 다시 읽음)
  assert.deepEqual(seen.map((s) => s[0]), [51, 51, 51, 92, 92, 92, 125, 125, 125, 125]);
  assert.deepEqual(seen.map((s) => s[1]), [0, 0, 0, 1, 1, 1, 1, 1, 1, 1]);
  assert.deepEqual(seen.map((s) => s[2]), [0, 0, 0, 64, 64, 64, 64, 64, 64, 64]);
});

test("슈터 요청은 다음 프레임에 칠함(슬롯55 지연, §7.7), 진행 방향으로 늘어나고 앞으로 이동", () => {
  const w = mkWorld({ meta: quad(-8, -8, 8, 8), tables: {} }); // 해석적 근사 마스크
  const pw = w.paint;
  const r = { team: 1, owner: 3, pos: v3(0.3, 0, -0.2), normal: v3(0, 1, 0), dir: v3(0, 0, 1), widthHalf: 1.5, depthScale: 2.5, kind: "Shooter", seed: 42 };
  pw.request(r);
  w.step(PAD);
  assert.equal(pw.counts().team[1], 0, "접촉 프레임에는 아직 칠하지 않음");
  w.step(PAD);
  assert.ok(pw.counts().team[1] > 0, "다음 프레임에 칠함");
  // 소유 텍셀 범위: W = 2w·ds^-1/4, L = 2w·ds^3/4, 중심 = 접촉 + (L−W)/2 전진
  const W = 3 * 2.5 ** -0.25, L = 3 * 2.5 ** 0.75;
  let x0 = Infinity, x1 = -Infinity, z0 = Infinity, z1 = -Infinity;
  const s = pw.surf;
  for (const c of s.charts) {
    const pg = s.pages[c.page];
    for (let j = 0; j < c.h; j++)
      for (let i = 0; i < c.w; i++) {
        if (pg.stencil[(c.y0 + j) * pg.w + c.x0 + i] !== 2) continue;
        const p = [0, 1, 2].map((a) => c.o[a] + ((i + 0.5) / 8) * c.e1[a] + ((j + 0.5) / 8) * c.e2[a]);
        x0 = Math.min(x0, p[0]); x1 = Math.max(x1, p[0]); z0 = Math.min(z0, p[2]); z1 = Math.max(z1, p[2]);
      }
  }
  assert.ok(x0 >= 0.3 - W / 2 - 0.07 && x1 <= 0.3 + W / 2 + 0.07, `x 범위 ${x0}..${x1}`);
  assert.ok(z0 >= -0.2 - W / 2 - 0.07 && z1 <= -0.2 + L - W / 2 + 0.07, `z 범위 ${z0}..${z1}`);
  assert.ok(z1 - z0 > x1 - x0, "진행 방향(z)으로 길쭉");
  assert.equal(w.events.list.filter((e) => e.type === "Paint").length, 1, "Paint 이벤트");
});

test("바닥 스탬프는 붙은 수직 벽을 칠하지 않고, 벽 스탬프는 벽만 칠함", () => {
  // 바닥 [-2,2]² + x=1 벽(법선 −x, 원점 쪽)
  const meta = {
    positions: [-2, 0, -2, -2, 0, 2, 2, 0, 2, 2, 0, -2, 1, 0, -2, 1, 0, 2, 1, 2, 2, 1, 2, -2],
    indices: [0, 1, 2, 0, 2, 3, 4, 5, 6, 4, 6, 7],
  };
  const w = mkWorld({ meta, tables: { InkTexInfo: SINGLE, ink_stamps: stamps(new Array(12).fill(255)) } });
  const pw = w.paint;
  assert.equal(pw.surf.charts.length, 2);
  const wall = pw.surf.charts.find((c) => Math.abs(c.n[0]) > 0.9);
  const floor = pw.surf.charts.find((c) => Math.abs(c.n[1]) > 0.9);
  assert.ok(wall.n[0] < 0, "벽 법선이 원점 쪽(−x)");
  const owned = (c) => {
    const pg = pw.surf.pages[c.page];
    let n = 0;
    for (let j = 0; j < c.h; j++) for (let i = 0; i < c.w; i++) if (pg.stencil[(c.y0 + j) * pg.w + c.x0 + i]) n++;
    return n;
  };
  pw.request({ ...req(0, "1.0", 1), pos: v3(0.8, 0, 0), kind: "ShooterDeferred" });
  w.step(PAD);
  assert.ok(owned(floor) > 0);
  assert.equal(owned(wall), 0);
  pw.request({ ...req(1, "1.0", 2), pos: v3(1, 1, 0), normal: v3(-1, 0, 0), dir: v3(1, 0, 0), kind: "ShooterDeferred" });
  w.step(PAD);
  assert.ok(owned(wall) > 0, "벽 칠함(진행 방향이 면에 수직이면 대체 축)");
});

test("발밑 샘플: 팀 비율 × 덮임 min(N/15, 1) (PlayerStepPaint 0x710268b3b8)", () => {
  const w = mkWorld();
  const pw = w.paint;
  pw.request(req(0, "1.0", 0));
  w.step(PAD);
  const a = pw.sample(v3(0, 0, 0), 0.25); // 반경 0.25 안 텍셀 중심 12개 < 15
  assert.equal(a.texels, 12);
  assert.equal(a.team, 0);
  assert.ok(Math.abs(a.ratio[0] - 12 / 15) < 1e-9);
  const b = pw.sample(v3(0, 0.1, 0), 0.5);
  assert.equal(b.team, 0);
  assert.equal(b.ratio[0], 1);
  const c = pw.sample(v3(1.5, 0, 1.5), 0.4);
  assert.equal(c.team, -1);
  assert.deepEqual(c.ratio, [0, 0, 0]);
});

test("면적: 전체 텍셀 = 면적 × 64 (8 텍셀/단위), p 환산 = paint_score.py", () => {
  const w = mkWorld();
  assert.equal(w.paint.counts().total, 32 * 32);
  const big = mkWorld({ meta: null, tables: {} }); // 충돌 없음 → placeholder 160×160
  assert.equal(big.paint.counts().total, 1280 * 1280);
  for (const [n, p] of [[0, 0], [211, 0], [212, 1], [2112, 10], [42240, 200], [100000, 473]]) {
    assert.equal(teamPoint(n), p, `teamP ${n}`);
    assert.equal(playerPoint(n), p, `playerP ${n}`);
  }
});

test("충돌 입력: physics MeshCollisionWorld 형태 + 에셋 재질(paintable·태그) / 대체 평면이면 placeholder", async () => {
  const { readCollisionTriangles, isPaintableMaterial } = await import("../core/paint/surface.ts");
  const { InkTexTable } = await import("../core/paint/inktex.ts");
  const pos = new Float32Array([0, 0, 0, 0, 0, 1, 1, 0, 1, 5, 0, 0, 5, 0, 1, 6, 0, 1, 9, 0, 0, 9, 0, 1, 10, 0, 1]);
  const idx = new Uint32Array([0, 1, 2, 3, 4, 5, 6, 7, 8]);
  const mat = new Uint16Array([0, 1, 2]);
  const metaMats = [
    { name: "Stone", layer: "Ground", paintable: true, flags: { userShapeTags: [], layerHitMask: "SplSolidGround" } },
    { name: "Metal", layer: "KeepOut", paintable: false, flags: { userShapeTags: ["KeepOut"], layerHitMask: "SplKeepOutPlayer" } },
    { name: "Undefined", layer: "Ground", paintable: true, flags: { userShapeTags: ["KeepOut", "PlayerDead"], layerHitMask: "SplSolidGround" } },
  ];
  const w = { collision: { mesh: { pos, idx, mat }, materials: [] }, data: { collision: { meta: { materials: metaMats } } } };
  const raw = readCollisionTriangles(w);
  assert.equal(raw.source, "collision");
  assert.deepEqual([...raw.paintable], [1, 0, 0]);
  const fb = readCollisionTriangles({ collision: { fallback: true, mesh: { pos, idx, mat } }, data: { collision: null } });
  assert.equal(fb.source, "placeholder");
  assert.equal(isPaintableMaterial("Fence", ["Fence"]), false);
  assert.equal(isPaintableMaterial("Water", ["Water"]), false);
  assert.equal(isPaintableMaterial("Vinyl", ["ForceColPaintNotPaintable"]), false);
  assert.equal(isPaintableMaterial("Stone", ["ForceColPaintPaintable", "KeepOut"]), true);
  // 에셋 data/ink_tex_info.json 형식 { source, rows: [{..., name}] }
  const t = new InkTexTable({ source: "RSDB/InkTexInfo", rows: [{ name: "Shot02", TextureName: "", PatternNum: 6, AnimationFrame: 3, AnimationStep: 3, HeightRangeType: "MinEdge", HeightRangeRate: 1, StaticHeightRangeMin: -1, StaticHeightRangeMax: 1, DisableSlopeScale: false }] });
  assert.equal(t.source, "asset");
  assert.equal(t.get(2).PatternNum, 6);
  assert.equal(t.textureName(2, 4), "Shot02_4");
});
