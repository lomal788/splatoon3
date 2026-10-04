// [physics] 몸체 전체 경로(컨트롤러 → native 솔버 → SplResultPlayer → write-back) 시나리오. 원본 실행 대조가 아니라
// 원본 식으로 이은 경로의 성질(침투 보정 5%/프레임, 떨림 없음, 계단·경사 분류, write-back 관계)을 확인한다.
import { test } from "node:test";
import assert from "node:assert/strict";
import { World } from "../core/world.ts";
import { ParamStore } from "../core/params.ts";
import { emptyPad } from "../core/input.ts";
import { createCollisionSystem } from "../core/collision/index.ts";
import { createPlayerSystem } from "../core/player/index.ts";
import { bodyOf, CAPSULE_RADIUS } from "../core/player/body.ts";

function buildMesh(quads) {
  const pos = [], idx = [], mat = [];
  for (const pts of quads) {
    const b = pos.length / 3;
    for (const p of pts) pos.push(...p);
    idx.push(b, b + 1, b + 2, b, b + 2, b + 3);
    mat.push(0, 0);
  }
  const pb = pos.length * 4, ib = idx.length * 4, mb = mat.length * 2;
  const bin = new ArrayBuffer(pb + ib + mb + 4);
  new Float32Array(bin, 0, pos.length).set(pos);
  new Uint32Array(bin, pb, idx.length).set(idx);
  new Uint16Array(bin, pb + ib, mat.length).set(mat);
  return {
    meta: {
      layout: { positions: { offset: 0, count: pos.length / 3 }, indices: { offset: pb, count: idx.length }, triMaterial: { offset: pb + ib, count: mat.length } },
      materials: [{ name: "Stone", layer: "SplSolidGround", paintable: true }],
    },
    bin,
  };
}
// 바깥쪽(위·−z) winding
const floor = (y, x0, x1, z0, z1) => [[x0, y, z0], [x0, y, z1], [x1, y, z1], [x1, y, z0]];
const riser = (z, x0, x1, y0, y1) => [[x0, y0, z], [x0, y1, z], [x1, y1, z], [x1, y0, z]];

function makeWorld(quads, start = [0, 0, 0]) {
  const placement = { Actors: [{ Gyaml: "StartPos", Translate: start, TeamCmp: { Team: "Alpha" } }] };
  const w = new World({ map: "t", placement, collision: buildMesh(quads), params: new ParamStore({}, {}), tables: {}, players: [{ character: "Player00", weapon: "Shooter_Normal_00", team: 0 }] });
  w.add(createCollisionSystem());
  w.add(createPlayerSystem());
  const warn = console.warn;
  console.warn = () => {};
  w.init();
  console.warn = warn;
  return w;
}
function pad(x, y) {
  const p = emptyPad();
  p.moveX = x; p.moveY = y;
  return p;
}

test("write-back: 본체 위치 = 몸체 원점 − 0.6·up (매 프레임 비트)", () => {
  const w = makeWorld([floor(0, -20, 20, -20, 20)]);
  const p = w.shared.get("player");
  for (let i = 0; i < 90; i++) {
    w.step(pad(i < 60 ? 0.7 : 0, i < 60 ? 0.7 : 0));
    const o = bodyOf(p).motion.origin;
    for (let j = 0; j < 3; j++) assert.equal(p.pos[j], Math.fround(o[j] - Math.fround(CAPSULE_RADIUS * (j === 1 ? 1 : 0))), `f${i} ${j}`);
  }
});

test("평지: 서 있기·걷기에서 높이 떨림 없음, 멈추면 위치 고정", () => {
  const w = makeWorld([floor(0, -20, 20, -20, 20)]);
  const p = w.shared.get("player");
  for (let i = 0; i < 120; i++) {
    w.step(pad(0, i < 80 ? 1 : 0));
    assert.equal(p.pos[1], 0, `f${i} y`);
    assert.equal(p.onGround, true);
  }
  const z = p.pos[2];
  for (let i = 0; i < 30; i++) w.step(pad(0, 0));
  assert.equal(p.pos[2], z, "정지 후 수평 위치 고정");
});

test("침투 보정: 바닥에 0.15 묻힌 몸체는 첫 프레임 depth×0.05(0.0075)만큼 올라온다 (C+C8 −0.05, target·carry 식)", () => {
  const w = makeWorld([floor(0, -20, 20, -20, 20)], [0, -0.15, 0]);
  const p = w.shared.get("player");
  const y0 = p.pos[1];
  w.step(pad(0, 0));
  const dy = p.pos[1] - y0;
  assert.ok(Math.abs(dy - 0.0075) < 2e-5, `첫 프레임 ${dy}`);
  for (let i = 0; i < 200; i++) w.step(pad(0, 0));
  assert.ok(Math.abs(p.pos[1]) < 1e-3, `회복 ${p.pos[1]}`);
});

test("계단: 0.15 턱은 걸어서 오르고 0.5 턱은 막힘", () => {
  for (const [h, climbs] of [[0.15, true], [0.5, false]]) {
    const w = makeWorld([floor(0, -10, 10, -10, 2), riser(2, -10, 10, 0, h), floor(h, -10, 10, 2, 10)]);
    const p = w.shared.get("player");
    for (let i = 0; i < 60; i++) w.step(pad(0, 1));
    if (climbs) assert.ok(Math.abs(p.pos[1] - h) < 1e-3 && p.pos[2] > 2.6 && p.onGround, `${h}: ${[...p.pos]}`);
    else assert.ok(p.pos[2] < 2 - 0.5 && Math.abs(p.pos[1]) < 1e-3, `${h}: ${[...p.pos]}`);
  }
});

test("경사: 60° 면도 Phive 지지(θ < 75°)로 분류된다", () => {
  const t = Math.tan((60 * Math.PI) / 180);
  const w = makeWorld([floor(0, -10, 10, -10, 2), [[-5, 0, 2], [-5, 6 * t, 8], [5, 6 * t, 8], [5, 0, 2]]]);
  const p = w.shared.get("player");
  let steep = false;
  for (let i = 0; i < 60; i++) {
    w.step(pad(0, 1));
    const S = bodyOf(p).S;
    if (S.supported && Math.abs(S.face[1] - 0.5) < 1e-3) steep = true;
  }
  assert.ok(steep);
});
