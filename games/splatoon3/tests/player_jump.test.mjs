// [physics] 점프 곡선: 원본 함수 연결 실행 결과(analysis/move/jump_emu_hold*.json → player_fixture_jump.json)와 비트 일치.
// 평지(y = 0 평면), 0AP, 스틱 중립, 점프 버튼을 hold 프레임 동안 누름(0 = 점프 프레임만).
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { World } from "../core/world.ts";
import { ParamStore } from "../core/params.ts";
import { emptyPad, Btn } from "../core/input.ts";
import { createCollisionSystem } from "../core/collision/index.ts";
import { createPlayerSystem } from "../core/player/index.ts";
import { bodyOf, CAPSULE_RADIUS, NATIVE_MAX_LINEAR, setMoveVelocity } from "../core/player/body.ts";
import { makeSolverInfo, nativeSetLinear, PLAYER_INV_MASS, stepMotion } from "../core/collision/solver.ts";

const fixture = JSON.parse(readFileSync(new URL("./player_fixture_jump.json", import.meta.url), "utf8"));

export function makeWorld(extra = {}) {
  const w = new World({
    map: "test",
    placement: null,
    collision: null,
    params: new ParamStore({}, {}),
    tables: {},
    players: [{ character: "Player00", weapon: "Shooter_Normal_00", team: 0 }],
    ...extra,
  });
  w.add(createCollisionSystem());
  w.add(createPlayerSystem());
  const warn = console.warn;
  console.warn = () => {};
  w.init();
  console.warn = warn;
  return w;
}

function pad(hold, trigger = 0) {
  const p = emptyPad();
  p.hold = hold;
  p.trigger = trigger;
  return p;
}

/**
 * 높이 기대값: fixture 의 y 는 원본 실행 하네스(move_jump_emu.py)가 "Phive 스텝은 y += 최종 속도 y" 로 대신한 값이다(도구 머리말의 스텁·가정).
 * 원본 높이는 최종 속도 F → 0x71024f4f7c(F·60, 공중) → GameInAir(속력·방향) → native setter → 초기/carry7/finalize(double COM += f32(실효속도·dt))
 * → 몸체 원점(09d5b68) → write-back(원점 − r·up) 사슬이다(phive_controller.md §6.10.5, 사슬 함수는 physics_native_fixture.test.mjs 에서 원본 실행과 비트 대조).
 * 그래서 F(fixture vy + 이동 y, 원본 실행값)를 이 사슬에 넣은 값과 비교한다. setMoveVelocity 의 정규화 산술 순서는 [추정](body.ts). 2026-10-04 정정.
 */
function nativeAirStep(m, Fy) {
  const dir = new Float32Array(3);
  const speed = setMoveVelocity(dir, [0, Math.fround(Fy * 60), 0]);
  nativeSetLinear(m.vel, [Math.fround(speed * dir[0]), Math.fround(speed * dir[1]), Math.fround(speed * dir[2])], NATIVE_MAX_LINEAR);
  stepMotion(m, [], makeSolverInfo(), NATIVE_MAX_LINEAR, PLAYER_INV_MASS);
  return Math.fround(m.origin[1] - Math.fround(CAPSULE_RADIUS * 1));
}

for (const hold of [0, 5, 10, 60]) {
  test(`점프 곡선 hold=${hold}: vy·이동 y·높이 비트 일치`, () => {
    const w = makeWorld();
    const p = w.shared.get("player");
    // 서 있는 상태로 몇 프레임
    for (let i = 0; i < 10; i++) w.step(pad(0));
    assert.equal(p.pos[1], 0);
    assert.equal(p.onGround, true);
    const rows = fixture.runs[String(hold)];
    const b = bodyOf(p);
    const m = { com: Float64Array.from(b.motion.com), vel: Float32Array.from(b.motion.vel), origin: Float32Array.from(b.motion.origin),
      residual: Float32Array.from(b.motion.residual), center: Float32Array.from(b.motion.center) };
    let jumped = 0;
    for (let n = 0; n < rows.length; n++) {
      const held = n === 0 || n < hold;
      w.step(pad(held ? Btn.Jump : 0, n === 0 ? Btn.Jump : 0));
      if (n === 0) jumped = w.events.list.filter((e) => e.type === "Jump").length;
      const r = rows[n];
      if (r.y <= 0) break; // 원본 실행도 y ≤ 0 에서 멈춘다(착지 처리는 대체)
      // 착지 판정: 하네스는 y ≤ 0 스텁, 원본은 SplResultPlayer 지지(분리 < 0.02 또는 종류 2·≤ 0.2)다. 몸체가 지지를 받은
      // 프레임부터는 슬롯19 접지 처리(vy 0 등)가 들어가므로 비교를 멈춘다. 그 프레임의 스텁 높이는 등급 1 범위(≤ 0.2) 안이어야 한다.
      if (p.onGround) { assert.ok(r.y <= 0.2, `frame ${r.frame} 착지 높이 ${r.y}`); break; }
      assert.equal(p.vy, Math.fround(r.vy), `frame ${r.frame} vy`);
      assert.equal(p.vel[1], Math.fround(r.my), `frame ${r.frame} 이동 y`);
      const y = nativeAirStep(m, Math.fround(Math.fround(r.vy) + Math.fround(r.my)));
      assert.equal(p.pos[1], y, `frame ${r.frame} y`);
      assert.ok(Math.abs(p.pos[1] - r.y) < 1e-5, `frame ${r.frame} y ≈ 스텁 합 ${r.y}`);
      assert.equal(p.airFrames, r.air_after, `frame ${r.frame} 공중 프레임`);
    }
    assert.equal(jumped, 1);
  });
}

test("점프 최고점: 탭 0.84145(14프레임), 계속 유지 1.73148(30프레임)", () => {
  for (const [hold, apexF, apexY] of [[0, 14, 0.84145], [60, 30, 1.73148]]) {
    const w = makeWorld();
    const p = w.shared.get("player");
    for (let i = 0; i < 5; i++) w.step(pad(0));
    let best = 0, bestF = 0;
    for (let n = 0; n < 80; n++) {
      w.step(pad(n === 0 || n < hold ? Btn.Jump : 0, n === 0 ? Btn.Jump : 0));
      if (p.pos[1] > best) { best = p.pos[1]; bestF = n + 1; }
    }
    assert.equal(bestF, apexF);
    assert.ok(Math.abs(best - apexY) < 5e-6, `apex ${best}`);
    // 버튼을 누르고 있으면 착지 뒤 7프레임째부터 다시 뛴다(+0x72c 누름 조건). 손을 떼고 기다리면 착지 상태.
    for (let n = 0; n < 120; n++) w.step(pad(0));
    assert.equal(p.onGround, true, "착지");
    assert.equal(p.pos[1] < 1e-3, true);
  }
});
