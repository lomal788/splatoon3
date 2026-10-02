// [range] 이동 표적 레일(game::RailMovableSequential) — 로비 Lby_Lobby00 의 실제 레일·파라미터 값으로 재구현 검사.
// 원본 실행 대조가 아니라 판독식(stage_misc.md §1.3, shooting_range.md §6.5) 재구현의 자기 일관성·경계 검사다.
import { test } from "node:test";
import assert from "node:assert/strict";
import { RailMover, RailPath, railMoveParam, quatToMat3 } from "../core/range/rail.ts";

const f = Math.fround;
// Banc Lby_Lobby00 Rails[0] (LiftRail 14877423949110540250): (40,0,18) → (40,0,3), 노드 Rotation Y -90°
const railA = {
  hash: "14877423949110540250",
  closed: false,
  rotation: [0, -0, 0],
  points: [
    { hash: "1280356437980484485", pos: [40, 0, 18], rotDeg: [0, -90, 0], breakTime: 0 },
    { hash: "7356806808280323317", pos: [40, 0, 3], rotDeg: [0, -90, 0], breakTime: 0 },
  ],
};
// SighterTarget_Move 15066127630233066301 의 game__RailMovableSequentialParam
const moveA = { InterpolationType: "cSin", MoveSpeed: 7, PatrolType: "cContinue", SpeedCalcType: "cSpeed" };

const close = (a, b, eps = 1e-4) => assert.ok(Math.abs(a - b) <= eps, `${a} != ${b}`);

test("레일 A 속도 7: 한 구간 15/7초, 왕복 주기 2구간, cSin 중간점", () => {
  const path = new RailPath(railA);
  assert.equal(path.total, 15);
  const m = new RailMover(path, railMoveParam(moveA), path.indexOf("1280356437980484485"));
  const D = f(15 / 7);
  assert.equal(m.period, f(D + D));
  assert.deepEqual(m.evaluate(0).pos, [40, 0, 18]);
  close(m.evaluate(f(D / 2)).pos[2], 10.5);
  close(m.evaluate(D).pos[2], 3);
  // 역방향 이동(cSpeed 는 rev 플래그로 양수 길이 — 0x710147b6dc)
  close(m.evaluate(f(D + D / 2)).pos[2], 10.5);
  close(m.evaluate(f(D + D * 0.999)).pos[2], 18, 1e-3);
  close(m.evaluate(f(m.period + D / 2)).pos[2], 10.5);
});

test("레일 A: sin 보간은 시작이 느리다(1/4 지점 < 선형)", () => {
  const path = new RailPath(railA);
  const m = new RailMover(path, railMoveParam(moveA), 0);
  const D = f(15 / 7);
  const z = m.evaluate(f(D / 4)).pos[2];
  // x = (sin(0.25π − π/2) + 1)/2 = 0.1464...
  close(18 - z, 15 * (Math.sin(0.25 * Math.PI - Math.PI / 2) + 1) / 2, 1e-3);
});

test("점 회전 Ry(-90°): X축 = (0,0,1), Z축 = (-1,0,0)", () => {
  const path = new RailPath(railA);
  const m = new RailMover(path, railMoveParam(moveA), 0);
  const r = quatToMat3(m.evaluate(0.5).rot);
  close(r[0], 0); close(r[1], 0); close(r[2], 1);
  close(r[6], -1); close(r[7], 0); close(r[8], 0);
});

test("advance: 프레임당 0.016666668초 누적, 리셋 0", () => {
  const path = new RailPath(railA);
  const m = new RailMover(path, railMoveParam(moveA), 0);
  for (let i = 0; i < 60; i++) m.advance(f(0.016666668));
  close(m.time, 1, 1e-5);
  m.reset();
  assert.equal(m.time, 0);
});

test("cStop·WaitTime·BreakTime: 대기 후 이동, 끝에서 멈춤", () => {
  const rail = { ...railA, points: railA.points.map((p, i) => ({ ...p, breakTime: i === 1 ? 2 : 0 })) };
  const path = new RailPath(rail);
  const m = new RailMover(path, railMoveParam({ PatrolType: "cStop", SpeedCalcType: "cTime", MoveTime: 3, WaitTime: 1 }), 0);
  assert.deepEqual(m.evaluate(0.5).pos, [40, 0, 18]);
  close(m.evaluate(2.5).pos[2], 10.5); // 선형, 1초 대기 뒤 1.5/3
  assert.deepEqual(m.evaluate(100).pos, [40, 0, 3]);
});

test("기본값: cStop·cTime·MoveTime 1·cLinear (생성자 판독값)", () => {
  const p = railMoveParam({});
  assert.deepEqual(p, { PatrolType: 0, SpeedCalcType: 0, InterpolationType: 0, MoveSpeed: 1, MoveTime: 1, WaitTime: 0 });
});
