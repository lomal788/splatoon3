// [physics] 벽 차기·오징어 롤·차지 벽 점프·덮어쓰기 스틱 흐름 (movement_physics.md §6.4.1~§6.4.3, §6.8, 판독식 대조).
// 비트 대조가 필요한 산술(감쇠 반복곱·0x7102458a18·데드존·벽 입력 계수)은 player_move_native.test.mjs 에서 원본 실행과 비교한다.
import { test } from "node:test";
import assert from "node:assert/strict";
import { createPlayerState } from "../core/player/state.ts";
import { inputStick, launchPre, pushHistory, inputPost } from "../core/player/move.ts";
import { tryJump, wallChargeStage, launch } from "../core/player/vertical.ts";
import * as C from "../core/player/consts.ts";

const f = Math.fround;
const ctx = (aim) => ({ aim, frame: 100, shooting: false });

function squidOnInk(state = 0x87) {
  const p = createPlayerState(1, 0);
  p.state = state;
  p.step.cls = 0;
  p.ceilTimer = 0;
  return p;
}

test("오징어 롤: 이력의 첫 유효 후보와 60° 이상 꺾인 스틱이면 발사(속력 = 후보, 점프 0.1705, 상태 0x8d)", () => {
  const p = squidOnInk();
  p.vel[0] = f(0.19);
  for (let i = 0; i < 6; i++) pushHistory(p);
  p.vel.fill(0);
  p.jumpHeld = p.jumpPressed = true;
  p.squidButton = true; p.squidHoldFrames = C.ROLL_SQUID_HOLD;
  p.stick[0] = 1; p.stick[1] = 0;
  const r = tryJump(p, ctx([0, 0, 1]));
  assert.equal(r.roll, true);
  assert.equal(r.kind, "jump");
  assert.equal(p.launch.active && p.launch.apply && !p.launch.wallJump, true);
  assert.deepEqual([...p.launch.vel], [f(-0.19), 0, 0]);
  assert.equal(p.vy, C.ROLL_JUMP);
  assert.equal(p.state, 0x8d);
  assert.equal(p.launch.count, 1);
});

test("오징어 롤 gate: 같은 방향(60° 안)이거나 오징어 버튼 6프레임 미만이면 롤 없음", () => {
  for (const [sx, hold] of [[-1, 6], [1, 5]]) {
    const p = squidOnInk();
    p.vel[0] = f(0.19);
    for (let i = 0; i < 6; i++) pushHistory(p);
    p.jumpHeld = p.jumpPressed = true;
    p.squidButton = true; p.squidHoldFrames = hold;
    p.stick[0] = sx; p.stick[1] = 0;
    assert.equal(tryJump(p, ctx([0, 0, 1])).roll, false, `${sx} ${hold}`);
  }
});

test("벽 차기: 최근 6개 이력에 벽+잠복, 스틱이 벽 바깥 60° 안이면 발사 0.192·법선, vs 0.23, 덮어쓰기 스틱 15", () => {
  const p = squidOnInk();
  p.floorN.set([0, 0, 1]);
  for (let i = 0; i < 3; i++) pushHistory(p);
  p.jumpHeld = p.jumpPressed = true;
  p.sinceJump = 0; // 벽 차기는 재점프 대기를 건너뛴다
  p.stickSrc[0] = 0; p.stickSrc[1] = -1;
  p.stick[0] = 0; p.stick[1] = -1;
  const r = tryJump(p, ctx([0, 0, -1]));
  assert.equal(r.kind, "wall");
  assert.deepEqual([...p.launch.vel], [0, 0, C.WALLKICK_H]);
  assert.equal(p.vy, C.WALLKICK_V);
  assert.equal(p.launch.lock, C.STICK_LOCK_WALLJUMP);
  assert.deepEqual(p.launch.lockStick, [0, -1]);
  assert.equal(p.sinceJump, 0);
  assert.equal(p.state, 0x8d);
});

test("덮어쓰기 스틱: 벽 점프 발사 뒤 15프레임 동안 스틱 = 발사 순간 스틱, 그 뒤 실제 스틱", () => {
  const p = squidOnInk();
  p.floorN.set([0, 0, 1]);
  p.stickSrc[0] = 0.6; p.stickSrc[1] = -0.8;
  launch(p, ctx([0, 0, -1]), false);
  let locked = 0;
  for (let i = 0; i < 20; i++) {
    inputStick(p, 0, 1);
    if (p.stick[0] === f(0.6) && p.stick[1] === f(-0.8)) locked++;
    launchPre(p);
  }
  assert.equal(locked, 15);
  assert.deepEqual(p.stick, [0, 1]);
});

test("차지 벽 점프: 벽에서 점프를 누른 프레임만큼 +0x774, 뗄 때 스틱이 벽 바깥이 아니면 0x7102458a18(래치 s ≥ 0.2)", () => {
  const p = squidOnInk();
  p.floorN.set([0, 0, 1]);
  p.groundFrames = 1;
  p.jumpHeld = true;
  for (let i = 0; i < 30; i++) assert.equal(wallChargeStage(p, ctx([0, 0, -1])), "none");
  assert.equal(p.wallJumpCharge, 30);
  p.jumpHeld = false;
  assert.equal(wallChargeStage(p, ctx([0, 0, -1])), "latch");
  const s = f(f(20) / p.gear.wallJumpChargeFrames);
  assert.equal(p.jump3d[1], f(C.WALLJUMP_LATCH_LO + f(s * f(C.WALLJUMP_LATCH_HI - C.WALLJUMP_LATCH_LO))));
  assert.equal(p.jump3dHold, true);
  assert.equal(p.holdBlock, true);
  assert.equal(p.wallJumpCharge, 0);
  // 래치 진행: 잠복·벽이면 점프 시작 반복, 스틱 잠금 15
  assert.equal(wallChargeStage(p, ctx([0, 0, -1])), "climb");
  assert.equal(p.stickLock, C.STICK_LOCK_RELEASE);
  // 스틱을 아래로(−0.1 미만) 당기면 해제
  p.stickSrc[1] = -0.5;
  wallChargeStage(p, ctx([0, 0, -1]));
  assert.equal(p.jump3dHold, false);
});

test("차지 벽 점프: 뗄 때 스틱이 벽 바깥 60° 안이면 0x7102459630 발사", () => {
  const p = squidOnInk();
  p.floorN.set([0, 0, 1]);
  p.groundFrames = 1;
  p.jumpHeld = true;
  for (let i = 0; i < 12; i++) wallChargeStage(p, ctx([0, 0, -1]));
  p.jumpHeld = false;
  p.stick[0] = 0; p.stick[1] = -1; p.stickSrc[0] = 0; p.stickSrc[1] = -1;
  assert.equal(wallChargeStage(p, ctx([0, 0, -1])), "wall");
  assert.equal(p.launch.wallJump, true);
  assert.equal(p.wallJumpCharge, 0);
  assert.equal(p.vy, C.WALLKICK_V);
});

test("연속 발사 횟수 n: 오징어 집합 밖이거나 마지막 발사 + 90 < 프레임이면 0, 90 차이까지 유지", () => {
  const p = squidOnInk();
  p.launch.count = 3; p.launch.frame = 10;
  inputPost(p, [0, 1, 0], 100, 0);
  assert.equal(p.launch.count, 3);
  inputPost(p, [0, 1, 0], 101, 0);
  assert.equal(p.launch.count, 0);
  p.launch.count = 2; p.state = 0x56;
  inputPost(p, [0, 1, 0], 0, 0);
  assert.equal(p.launch.count, 0);
});

test("+0x786: 직전 +0x785 가 참이면 min(+1, 100), 아니면 0 / +0x790 잠복 연속 프레임 부호", () => {
  const p = squidOnInk(0x85);
  p.squidInput = true;
  for (let i = 0; i < 120; i++) inputStick(p, 0, 0);
  assert.equal(p.squidHoldFrames, 100);
  p.squidInput = false;
  inputStick(p, 0, 0);
  assert.equal(p.squidHoldFrames, 0);
  inputPost(p, [0, 1, 0], 0, 0);
  inputPost(p, [0, 1, 0], 0, 0);
  assert.equal(p.squidInkFrames, 2);
  p.step.cls = 4;
  inputPost(p, [0, 1, 0], 0, 0);
  assert.equal(p.squidInkFrames, -1);
});
