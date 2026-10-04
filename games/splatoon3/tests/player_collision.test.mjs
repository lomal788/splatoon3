// [physics] 충돌 세계(collision.json + bin 읽기, 레이·구 쓸어 넘기기·동적 충돌체·레이어 필터)와
// 캐릭터 컨트롤러 근사(벽 막힘·미끄러짐·경사·낙하·물 리스폰).
import { test } from "node:test";
import assert from "node:assert/strict";
import { World } from "../core/world.ts";
import { ParamStore } from "../core/params.ts";
import { emptyPad, Btn } from "../core/input.ts";
import { Layer } from "../core/types.ts";
import { v3 } from "../core/fmath.ts";
import { createCollisionSystem, loadCollision } from "../core/collision/index.ts";
import { createPlayerSystem } from "../core/player/index.ts";

/** 사각형(4점, 반시계) 목록 → { meta, bin } (형식: positions f32 | indices u32 | triMaterial u16). */
function buildMesh(quads, materials) {
  const pos = [], idx = [], mat = [];
  for (const { pts, m } of quads) {
    const b = pos.length / 3;
    for (const p of pts) pos.push(...p);
    idx.push(b, b + 1, b + 2, b, b + 2, b + 3);
    mat.push(m, m);
  }
  const pb = pos.length * 4, ib = idx.length * 4, mb = mat.length * 2;
  const bin = new ArrayBuffer(pb + ib + mb + 4);
  new Float32Array(bin, 0, pos.length).set(pos);
  new Uint32Array(bin, pb, idx.length).set(idx);
  new Uint16Array(bin, pb + ib, mat.length).set(mat);
  const meta = {
    layout: {
      positions: { offset: 0, count: pos.length / 3 },
      indices: { offset: pb, count: idx.length },
      triMaterial: { offset: pb + ib, count: mat.length },
    },
    materials,
  };
  return { meta, bin };
}

const floor = (y, x0, x1, z0, z1, m = 0) => ({ pts: [[x0, y, z0], [x0, y, z1], [x1, y, z1], [x1, y, z0]], m });
// 벽·경사 면은 −z(플레이어 쪽)를 향하도록 감는다: 원본 접지 판정의 얼굴 법선 0x7103c4988c(flag1)는 삼각형 (b−a)×(c−a)를
// winding 그대로 쓰고(player_state.md §7.3.4 [판독]+[실행]), 몸 뒤쪽을 향한 면의 접촉은 분류에서 버린다(0x7102c5dd20 첫 검사).
// 실제 Lby_Lobby00 충돌 메시도 바깥쪽 winding 이다(법선 위 1500 / 아래 737 / 옆 4092 삼각형). 이전 판은 반대로 감겨 있었다(2026-10-04 정정).
const wallZ = (z, x0, x1, y0, y1, m = 0) => ({ pts: [[x0, y0, z], [x0, y1, z], [x1, y1, z], [x1, y0, z]], m });

const MATS = [
  { name: "Stone", layer: "SplSolidGround", paintable: true },
  { name: "Water", filter: { layerHitMask: "SplWater", subLayerHitMask: "SplWater" }, paintable: false },
  { name: "Fence", filter: { layerHitMask: "SplInkThrough", subLayerHitMask: "SquidThrough" }, paintable: false },
  { name: "KeepOut", filter: { layerHitMask: "SplKeepOutPlayer", subLayerHitMask: "HitAll" }, paintable: false },
];

function makeWorld(collision, placement = null) {
  const w = new World({
    map: "test", placement, collision, params: new ParamStore({}, {}), tables: {},
    players: [{ character: "Player00", weapon: "Shooter_Normal_00", team: 0 }],
  });
  w.add(createCollisionSystem());
  w.add(createPlayerSystem());
  w.init();
  return w;
}

function pad(moveX, moveY, hold = 0, trigger = 0) {
  const p = emptyPad();
  p.moveX = moveX; p.moveY = moveY; p.hold = hold; p.trigger = trigger;
  return p;
}

test("collision: 읽기·레이·구 쓸어 넘기기·레이어 필터·동적 충돌체", () => {
  const { meta, bin } = buildMesh([floor(0, -10, 10, -10, 10, 0), floor(-1, -10, 10, -10, 10, 1), wallZ(5, -10, 10, 0, 5, 2), wallZ(7, -10, 10, 0, 5, 3)], MATS);
  const c = loadCollision(meta, bin);
  assert.equal(c.materials[0].layer, Layer.Ground);
  assert.equal(c.materials[1].layer, Layer.Water);
  assert.equal(c.materials[2].layer, Layer.KeepOut, "철망: 잉크탄 통과·플레이어 막힘");
  assert.equal(c.materials[3].layer, Layer.KeepOut);
  const h = c.raycast(v3(0, 2, 0), v3(0, -1, 0), 10, Layer.Ground);
  assert.ok(h && Math.abs(h.t - 2) < 1e-6 && h.normal[1] > 0.999 && h.material === 0 && h.actor === -1);
  const hw = c.raycast(v3(0, -0.5, 0), v3(0, -1, 0), 10, Layer.Water);
  assert.ok(hw && Math.abs(hw.t - 0.5) < 1e-6 && hw.layer === Layer.Water);
  // 잉크탄 마스크(Ground)는 철망·킵아웃을 통과
  const s = c.sweepSphere(v3(0, 1, 0), v3(0, 1, 10), 0.2, Layer.Ground | Layer.Object);
  assert.equal(s, null);
  const s2 = c.sweepSphere(v3(0, 1, 0), v3(0, 1, 10), 0.2, Layer.KeepOut);
  assert.ok(s2 && Math.abs(s2.t - (5 - 0.2) / 10) < 1e-4 && s2.normal[2] < -0.99);
  c.setDynamic(42, { kind: "sphere", center: v3(0, 1, 3), radius: 0.5, layer: Layer.Object });
  const s3 = c.sweepSphere(v3(0, 1, 0), v3(0, 1, 10), 0.2, Layer.Object);
  assert.ok(s3 && s3.actor === 42 && Math.abs(s3.t - (3 - 0.7) / 10) < 1e-6);
  c.setDynamic(42, null);
  assert.equal(c.sweepSphere(v3(0, 1, 0), v3(0, 1, 10), 0.2, Layer.Object), null);
  // 플레이어 몸 필터: 사람은 철망에 막히고 오징어는 통과(하위 레이어 SquidThrough)
  const human = c.bodyFilter({ layerIndex: 5, subIndex: 3, fallbackMask: 0 });
  const squid = c.bodyFilter({ layerIndex: 5, subIndex: 4, fallbackMask: 0 });
  const fenceTri = 4; // 세 번째 사각형의 첫 삼각형
  assert.equal(human(fenceTri), true);
  assert.equal(squid(fenceTri), false);
  assert.equal(human(2), false, "물은 플레이어를 막지 않음");
});

test("캐릭터: 벽에 막히고 비스듬히 밀면 벽을 따라 미끄러짐", () => {
  const col = buildMesh([floor(0, -20, 20, -20, 20), wallZ(5, -20, 20, 0, 5)], MATS.slice(0, 1));
  const w = makeWorld(col);
  const p = w.shared.get("player");
  for (let i = 0; i < 200; i++) w.step(pad(0, 1));
  assert.ok(p.pos[2] <= 5 - 0.6 + 1e-3 && p.pos[2] > 5 - 0.6 - 0.01, `z ${p.pos[2]}`);
  assert.ok(Math.abs(p.vel[2]) < 1e-6, "벽 쪽 속도 성분 제거");
  const x0 = p.pos[0];
  for (let i = 0; i < 60; i++) w.step(pad(-0.7071, 0.7071));
  assert.ok(p.pos[0] - x0 > 1, `x 이동 ${p.pos[0] - x0}`);
  assert.ok(p.pos[2] <= 5 - 0.6 + 1e-3);
  assert.equal(p.onGround, true);
});

// 최대 경사: CharacterControllerParam MaxSlopeAngle 75° → S+0x190 [데이터+판독], 지지 분류 0x7102c5dd20 은 θ < 75° 면 바닥이다.
// 이전 판의 "60° 못 오름"은 웹 근사(n.y < 0.6414 면 수직 벽 취급)였고 원본 분류로는 60° 도 지지된다(게임 쪽 a38/a2c 미끄럼이 별도로 끌어내림).
// 그래서 못 오르는 쪽 경사를 75° 를 넘는 80° 로 바꾼다 — 2026-10-04 정정.
test("캐릭터: 30° 경사는 오르고 80° 경사는 못 오름", () => {
  for (const [deg, climbs] of [[30, true], [80, false]]) {
    const t = Math.tan((deg * Math.PI) / 180);
    const ramp = { pts: [[-5, 0, 2], [-5, 6 * t, 8], [5, 6 * t, 8], [5, 0, 2]], m: 0 };
    const col = buildMesh([floor(0, -10, 10, -10, 2), ramp], MATS.slice(0, 1));
    const w = makeWorld(col);
    const p = w.shared.get("player");
    let maxY = 0, groundedOnRamp = 0;
    for (let i = 0; i < 90; i++) {
      w.step(pad(0, 1));
      maxY = Math.max(maxY, p.pos[1]);
      if (p.onGround && p.pos[1] > 0.5) groundedOnRamp++;
    }
    if (climbs) assert.ok(maxY > 2 && groundedOnRamp > 20, `${deg}° maxY ${maxY} grounded ${groundedOnRamp}`);
    else assert.ok(maxY < 0.6, `${deg}° maxY ${maxY}`);
  }
});

test("캐릭터: 턱에서 떨어지면 공중 → 아래 바닥에 착지(Land 이벤트)", () => {
  const col = buildMesh([floor(2, -10, 10, -10, 3), floor(0, -10, 10, 3, 20)], MATS.slice(0, 1));
  const w = makeWorld(col, { Actors: [{ Gyaml: "StartPos", Translate: [0, 2, 0], TeamCmp: { Team: "Alpha" } }] });
  const p = w.shared.get("player");
  w.step(pad(0, 0));
  assert.ok(Math.abs(p.pos[1] - 2) < 1e-3);
  let maxAir = 0, landed = false;
  for (let i = 0; i < 120; i++) {
    w.step(pad(0, 1));
    maxAir = Math.max(maxAir, p.airFrames);
    if (w.events.list.some((e) => e.type === "Land")) landed = true;
  }
  assert.ok(maxAir > 8, `air ${maxAir}`);
  assert.ok(landed);
  assert.ok(Math.abs(p.pos[1]) < 1e-3 && p.onGround);
});

test("물: 수면 아래로 떨어지면 시작 위치로", () => {
  const col = buildMesh([floor(0, -10, 10, -10, 2), floor(-1, -50, 50, -50, 50, 1)], MATS.slice(0, 2));
  const w = makeWorld(col);
  const p = w.shared.get("player");
  const r0 = p.respawns;
  for (let i = 0; i < 200; i++) w.step(pad(0, 1));
  assert.ok(p.respawns > r0, "리스폰");
});

test("에셋 없음: y=0 평면 대체", () => {
  const warn = console.warn;
  let warned = false;
  console.warn = () => { warned = true; };
  const w = makeWorld(null);
  console.warn = warn;
  assert.ok(warned);
  assert.ok(w.collision);
  const h = w.collision.raycast(v3(3, 5, -2), v3(0, -1, 0), 10, Layer.Ground);
  assert.ok(h && Math.abs(h.t - 5) < 1e-6);
  void Btn;
});

test("오징어 벽 수영: 아군 잉크 벽을 앞으로 밀면 오르고, 멈추면 머물고, 꼭대기를 넘어감", () => {
  const col = buildMesh([floor(0, -20, 20, -20, 20), wallZ(5, -20, 20, 0, 4), floor(4, -20, 20, 5, 20)], MATS.slice(0, 1));
  const w = makeWorld(col);
  w.paint = { request() {}, sample() { return { team: 0, ratio: [1, 0, 0] }; }, counts() { return { team: [0, 0, 0], total: 0 }; } };
  const p = w.shared.get("player");
  let clung = false;
  for (let i = 0; i < 55; i++) {
    w.step(pad(0, 1, Btn.Squid, i === 0 ? Btn.Squid : 0));
    if (p.wallCling) clung = true;
  }
  assert.ok(clung, "벽 붙기");
  assert.ok(p.pos[1] > 0.5 && p.floorN[2] < -0.9, `벽 위 y ${p.pos[1]} N ${[...p.floorN]}`);
  // 스틱을 놓으면 벽 입력 계수 x = 본체+0x488(0x71024a7100 [실행], move.ts) 가 0 이 되어 미끄럼 계수 s = min(a38, 1 − own²·x) = a38 이고
  // a38/a2c 벽 미끄럼(cling acc s^1.737·0.005, |a2c| ≤ 0.1)이 오징어를 끌어내린다(player_state.md §7.3.2 ④⑤ [판독]).
  // 이전 판의 "멈추면 머묾"은 x = 오징어 버튼 [추정]에 기댄 값이었다 — 2026-10-04 정정. 미끄러지는 동안 벽 지지는 유지된다.
  const y0 = p.pos[1];
  let clingWhileSliding = true;
  for (let i = 0; i < 40; i++) {
    w.step(pad(0, 0, Btn.Squid));
    if (p.pos[1] > 0.05 && !(p.onGround && p.wallCling)) clingWhileSliding = false;
  }
  for (let i = 0; i < 60; i++) w.step(pad(0, 0, Btn.Squid));
  assert.ok(clingWhileSliding && p.pos[1] < y0 && p.onGround, `미끄러져 내려옴 ${y0} → ${p.pos[1]}`);
  for (let i = 0; i < 80; i++) w.step(pad(0, 1, Btn.Squid));
  assert.ok(Math.abs(p.pos[1] - 4) < 1e-3 && p.pos[2] > 5.5 && p.onGround, `꼭대기 ${[...p.pos]}`);
});
