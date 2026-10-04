// [physics] 이동 계산 원본 대조: fixtures/player_move_native.json(web/tools/r7_player_move_fixture.py) — 모두 원본 실행 결과.
// acos 0x7101252780·방향 보간 0x7101252ff0(sead 표), 스틱 데드존 구간, 벽 입력 계수 0x71024a7100, 발사 감쇠 반복곱·n/프레임 쓰기,
// 오징어 목표 속도 k 0x710266c6e4, 차지 벽 점프 해제 0x7102458a18(원본 연결 실행).
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { acosTable } from "../core/camera/native_math.ts";
import { createPlayerState } from "../core/player/state.ts";
import { inputStick, slerpDir, wallInputUpdate, pushHistory, historyAt, launchPre } from "../core/player/move.ts";
import { launch, launchDamping, wallLatch } from "../core/player/vertical.ts";
import { makePlayerParam, squidSpeedK } from "../core/player/gear.ts";

const fx = JSON.parse(readFileSync(new URL("./fixtures/player_move_native.json", import.meta.url), "utf8"));
const u32 = new Uint32Array(1), f32v = new Float32Array(u32.buffer);
const fb = (h) => { u32[0] = parseInt(h, 16) >>> 0; return f32v[0]; };
const bits = (x) => { f32v[0] = x; return u32[0].toString(16).padStart(8, "0"); };

test("acos 0x7101252780: sead 아탄 표 재구현이 원본 실행과 비트 일치", () => {
  assert.ok(fx.acos.length > 2000);
  for (const [x, got] of fx.acos) assert.equal(bits(acosTable(fb(x))), got, `x ${x}`);
});

test("방향 보간 0x7101252ff0 (axis null): slerpDir 이 원본 실행과 비트 일치", () => {
  assert.ok(fx.slerp.length > 2000);
  const out = new Float32Array(3);
  for (const r of fx.slerp) {
    slerpDir(fb(r.t), out, r.a.map(fb), r.b.map(fb));
    assert.deepEqual([...out].map(bits), r.got, JSON.stringify(r));
  }
});

test("스틱 기록·데드존·+0x480 (0x71024a0850~0x71024a0940) 원본 실행과 비트 일치", () => {
  for (const r of fx.deadzone) {
    const p = createPlayerState(1, 0);
    p.stickMagSmooth = fb(r.prev);
    inputStick(p, fb(r.stick[0]), fb(r.stick[1]));
    assert.deepEqual([p.stick[0], p.stick[1], p.stickMag01, p.stickMagSmooth].map(bits), r.got, JSON.stringify(r));
  }
});

test("벽 입력 계수 0x71024a7100 (+0x484/+0x488) 원본 실행과 비트 일치", () => {
  for (const r of fx.wall_input) {
    const p = createPlayerState(1, 0);
    p.floorN.set(r.n.map(fb)); p.fwdAxis.set(r.d.map(fb));
    p.stick[0] = fb(r.stick[0]); p.stick[1] = fb(r.stick[1]);
    p.wallInputDir = fb(r.prev[0]); p.wallInput = fb(r.prev[1]);
    wallInputUpdate(p, r.c.map(fb));
    assert.deepEqual([p.wallInputDir, p.wallInput].map(bits), r.got, JSON.stringify(r));
  }
});

test("발사 감쇠 PlayerParam+0x140 반복곱 0x7102459b44 원본 실행과 비트 일치", () => {
  for (const [n, ratio, got] of fx.damping) assert.equal(bits(launchDamping(n, fb(ratio))), got, `n ${n} r ${ratio}`);
});

test("발사 꼬리: n 정수 +1, 마지막 프레임 max(frame, 0) (0x7102459eec~) 원본 실행과 일치", () => {
  for (const [n, frame, n1, f1] of fx.launch_writes) {
    const p = createPlayerState(1, 0);
    p.launch.count = n;
    launch(p, { aim: [0, 0, 1], frame, shooting: false }, true);
    assert.equal(p.launch.count, n1 | 0, `n ${n}`); // fixture 는 u32 로 읽은 값
    assert.equal(p.launch.frame, f1, `frame ${frame}`);
  }
});

test("오징어 목표 속도 k 0x710266c6e4: 원본 실행 1088건과 비트 일치 (기본 장비 1, 징어닌자 0.9)", () => {
  assert.equal(fx.squid_k.length, 1088);
  for (const r of fx.squid_k) {
    const pp = { ...makePlayerParam(), abilityBits: r.flags };
    assert.equal(bits(squidSpeedK(pp, r.arg, r.table)), r.got, JSON.stringify(r));
  }
  assert.equal(squidSpeedK(makePlayerParam(), 0), 1);
  assert.equal(bits(squidSpeedK(makePlayerParam({ ninja: true }), 0)), "3f666666");
  assert.equal(squidSpeedK(makePlayerParam({ ninja: true }), 1), 1);
});

test("차지 벽 점프 해제 0x7102458a18: 3D 점프 y·+0x780/+0x782 원본 연결 실행과 비트 일치", () => {
  assert.ok(fx.walljump.length >= 90);
  for (const r of fx.walljump) {
    const p = createPlayerState(1, 0);
    p.gear.wallJumpChargeFrames = fb(r.F);
    p.wallJumpCharge = r.c774;
    p.jump3d[1] = fb(r.y754_before);
    wallLatch(p, { aim: [0, 0, 1], frame: 0, shooting: false });
    assert.equal(bits(p.jump3d[1]), r.y754, JSON.stringify(r));
    assert.equal(p.jump3dHold, r.b780 === 1);
    assert.equal(p.holdBlock, r.b782 === 1);
    assert.equal(p.wallJumpCharge, 0);
    assert.equal(p.sinceJump, 0);
  }
});

test("이동 이력: capacity 24 링, 최신부터 읽기, 항목 = 수평 방향·속력·잠복·벽 (§6.4.2)", () => {
  const p = createPlayerState(1, 0);
  for (let i = 0; i < 30; i++) {
    p.vel[0] = i; p.vel[2] = 0;
    pushHistory(p);
  }
  assert.equal(p.history.count, 24);
  assert.equal(historyAt(p, 0).speed, 29);
  assert.equal(historyAt(p, 23).speed, 6);
  assert.deepEqual([...historyAt(p, 0).dir], [1, 0, 0]);
  assert.equal(historyAt(p, 0).wall, false);
});

test("발사 활성 해제 0x7102477780: 접지·vs ≤ 0.001 이면 +0x3c/+0x3d 해제, 오징어 집합 밖이면 +0x3c 만", () => {
  const p = createPlayerState(1, 0);
  p.state = 0x87;
  launch(p, { aim: [0, 0, 1], frame: 5, shooting: false }, false);
  assert.equal(p.launch.lock, 15);
  p.launch.apply = false;
  p.groundFrames = 0; p.vy = 0.2;
  launchPre(p);
  assert.equal(p.launch.active, true);
  assert.equal(p.launch.lock, 14);
  p.groundFrames = 1; p.vy = 0;
  launchPre(p);
  assert.equal(p.launch.active, false);
  assert.equal(p.launch.active2, false);
  p.launch.active = p.launch.active2 = true; p.state = 0x56; p.groundFrames = 0;
  launchPre(p);
  assert.equal(p.launch.active, false);
  assert.equal(p.launch.active2, true);
});
