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

for (const hold of [0, 5, 10, 60]) {
  test(`점프 곡선 hold=${hold}: vy·이동 y·높이 비트 일치`, () => {
    const w = makeWorld();
    const p = w.shared.get("player");
    // 서 있는 상태로 몇 프레임
    for (let i = 0; i < 10; i++) w.step(pad(0));
    assert.equal(p.pos[1], 0);
    assert.equal(p.onGround, true);
    const rows = fixture.runs[String(hold)];
    let jumped = 0;
    for (let n = 0; n < rows.length; n++) {
      const held = n === 0 || n < hold;
      w.step(pad(held ? Btn.Jump : 0, n === 0 ? Btn.Jump : 0));
      if (n === 0) jumped = w.events.list.filter((e) => e.type === "Jump").length;
      const r = rows[n];
      if (r.y <= 0) break; // 원본 실행도 y ≤ 0 에서 멈춘다(착지 처리는 대체)
      assert.equal(p.vy, Math.fround(r.vy), `frame ${r.frame} vy`);
      assert.equal(p.vel[1], Math.fround(r.my), `frame ${r.frame} 이동 y`);
      assert.equal(p.pos[1], Math.fround(r.y), `frame ${r.frame} y`);
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
