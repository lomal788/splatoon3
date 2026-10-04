// [physics] 기어 수치·이동 속도: 기어는 원본 실행으로 검증된 재구현(player_gear.py) 값과 비트 일치,
// 이동은 판독식(movement_physics.md §6.1~6.3)대로 상한 cap 수렴·정상 속도를 확인.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { World } from "../core/world.ts";
import { ParamStore } from "../core/params.ts";
import { emptyPad, Btn } from "../core/input.ts";
import { createCollisionSystem } from "../core/collision/index.ts";
import { createPlayerSystem, makePlayerParam, apRate, gearLerp } from "../core/player/index.ts";

const gear = JSON.parse(readFileSync(new URL("./player_fixture_gear.json", import.meta.url), "utf8"));
const f = Math.fround;

function makeWorld(extra = {}) {
  const w = new World({
    map: "test", placement: null, collision: null, params: new ParamStore({}, {}), tables: {},
    players: [{ character: "Player00", weapon: "Shooter_Normal_00", team: 0 }], ...extra,
  });
  w.add(createCollisionSystem());
  w.add(createPlayerSystem());
  const warn = console.warn;
  console.warn = () => {};
  w.init();
  console.warn = warn;
  return w;
}

function pad(moveY, hold = 0, trigger = 0) {
  const p = emptyPad();
  p.moveY = moveY;
  p.hold = hold;
  p.trigger = trigger;
  return p;
}

test("기어 AP → 수치: 재구현(원본 실행 일치) 표와 비트 일치", () => {
  for (const r of gear.rows) {
    assert.equal(apRate(r.ap), f(r.rate), `AP ${r.ap} rate`);
    const pp = makePlayerParam({ humanMove: r.ap, squidMove: r.ap, opInk: r.ap });
    assert.deepEqual(pp.human, r.human.map(f), `AP ${r.ap} human`);
    assert.deepEqual(pp.squid, r.squid.map(f), `AP ${r.ap} squid`);
    assert.equal(pp.shotRate, f(r.shotRate));
    assert.equal(pp.opJump, f(r.opJump));
    assert.equal(pp.opMove, f(r.opMove));
    assert.equal(pp.opMoveShot, f(r.opMoveShot));
  }
});

test("기어 0AP: Low 값 그대로 (인간 0.096 / 오징어 0.192 / 적잉크 0.024·점프 0.08)", () => {
  const pp = makePlayerParam();
  assert.deepEqual(pp.human, [f(0.088), f(0.096), f(0.104)]);
  assert.deepEqual(pp.squid, [f(0.1728), f(0.192), f(0.2016)]);
  assert.equal(pp.shotRate, 1);
  assert.equal(pp.opMove, f(0.024));
  assert.equal(pp.opJump, f(0.08));
  assert.equal(gearLerp(600, 410, 220, 0), 600);
});

test("인간 이동: cap 은 입력과 무관하게 목표로 수렴(정지 중 비율 0.1), 정상 속도 0.096(Mid, 0AP)", () => {
  const w = makeWorld();
  const p = w.shared.get("player");
  // 리스폰 cap 0 → 서 있는 동안 (t·m)² = 0 ≤ |v|² 이므로 비율 0.1([0x71058bbdd0])
  w.step(pad(0));
  assert.equal(p.cap, f(0 + f(f(0.1) * f(f(0.096) - 0))));
  for (let i = 0; i < 300; i++) w.step(pad(1));
  const speed = Math.hypot(p.vel[0], p.vel[2]);
  assert.ok(Math.abs(p.cap - f(0.096)) < 1e-7, `cap ${p.cap}`);
  assert.ok(Math.abs(speed - 0.096) < 1e-6, `speed ${speed}`);
  // 카메라 기본 정면 +Z 로 이동
  assert.ok(p.vel[2] > 0.095 && Math.abs(p.vel[0]) < 1e-7);
  assert.equal(p.vel[1], 0);
  assert.equal(p.onGround, true);
  const dz = p.pos[2];
  assert.ok(dz > 25 && dz < 30.1, `z ${dz}`);
});

test("가속량: 지상 스틱 끝까지 0.01/프레임, 손 떼면 0.008/프레임 감속", () => {
  const w = makeWorld();
  const p = w.shared.get("player");
  for (let i = 0; i < 3; i++) w.step(pad(0));
  const speeds = [];
  for (let i = 0; i < 4; i++) { w.step(pad(1)); speeds.push(Math.hypot(p.vel[0], p.vel[2])); }
  // 1프레임: desired = 0.0288 > accel 0.01 이므로 0.01
  assert.ok(Math.abs(speeds[0] - 0.01) < 1e-7, `${speeds}`);
  assert.ok(Math.abs(speeds[1] - 0.02) < 1e-7, `${speeds}`);
  for (let i = 0; i < 200; i++) w.step(pad(1));
  w.step(pad(0));
  const s1 = Math.hypot(p.vel[0], p.vel[2]);
  assert.ok(Math.abs(0.096 - s1 - 0.008) < 1e-6, `stop ${s1}`);
});

test("사격 중 이동: 무기 MoveSpeed 0.072 로 상한", () => {
  const w = makeWorld();
  const p = w.shared.get("player");
  for (let i = 0; i < 300; i++) w.step(pad(1, Btn.Fire, i === 0 ? Btn.Fire : 0));
  const speed = Math.hypot(p.vel[0], p.vel[2]);
  assert.ok(Math.abs(speed - 0.072) < 1e-6, `speed ${speed}`);
  assert.equal(p.state, 0x60); // WalkShoot
});

test("오징어: 무도색 0.072, 아군 잉크 0.192, 적 잉크 0.012 (발밑 샘플 주입)", () => {
  for (const [ratio, want] of [[[0, 0, 0], 0.072], [[1, 0, 0], 0.192], [[0, 1, 0], 0.012]]) {
    const w = makeWorld();
    w.paint = {
      request() {},
      sample() { return { team: ratio[0] ? 0 : ratio[1] ? 1 : -1, ratio }; },
      counts() { return { team: [0, 0, 0], total: 0 }; },
    };
    const p = w.shared.get("player");
    for (let i = 0; i < 600; i++) w.step(pad(1, Btn.Squid, i === 0 ? Btn.Squid : 0));
    assert.equal(p.squid, true);
    const speed = Math.hypot(p.vel[0], p.vel[2]);
    assert.ok(Math.abs(speed - want) < 2e-5, `${ratio} speed ${speed}`);
  }
});

test("인간↔오징어 전환: 0x82 → 0x84 → 0x87, 해제 0x91 → 0x92, 이벤트", () => {
  const w = makeWorld();
  const p = w.shared.get("player");
  w.step(pad(0));
  w.step(pad(0, Btn.Squid, Btn.Squid));
  assert.equal(p.state, 0x82);
  assert.ok(w.events.list.some((e) => e.type === "ToSquid"));
  const seen = [p.state];
  for (let i = 0; i < 30; i++) {
    w.step(pad(1, Btn.Squid));
    if (seen.at(-1) !== p.state) seen.push(p.state);
  }
  assert.deepEqual(seen.slice(0, 2), [0x82, 0x84]);
  assert.equal(p.state, 0x87);
  w.step(pad(0));
  assert.equal(p.state, 0x91);
  assert.ok(w.events.list.some((e) => e.type === "ToHuman"));
  const after = [];
  for (let i = 0; i < 40; i++) {
    w.step(pad(0));
    if (after.at(-1) !== p.state) after.push(p.state);
  }
  // 오징어 ToHuman(3프레임 클립) 끝 3프레임 전 규칙으로 다음 프레임 0x92, 아직 움직이면 걷기로 끊기고 멈추면 WaitHold
  assert.equal(after[0], 0x92);
  assert.equal(p.state, 0x56);
});

test("리셋 버튼: 시작 위치로", () => {
  const w = makeWorld();
  const p = w.shared.get("player");
  for (let i = 0; i < 60; i++) w.step(pad(1));
  assert.ok(p.pos[2] > 1);
  w.step(pad(0, Btn.Reset, Btn.Reset));
  assert.ok(Math.abs(p.pos[2]) < 0.02);
});

test("StartPos: 이름 없는 팀 StartPos 를 고름", () => {
  const placement = { Actors: [
    { Gyaml: "StartPos", Translate: [4, 0, 5], TeamCmp: { Team: "Neutral" }, spl__StartPosParam: { Name: "ResultPlayer5" } },
    { Gyaml: "StartPos", Translate: [-0.149, 0.01, -11.96], Rotate: [0, -0.38, 0], TeamCmp: { Team: "Alpha" }, spl__StartPosParam: {} },
  ] };
  const w = makeWorld({ placement });
  const p = w.shared.get("player");
  assert.equal(p.spawnPos[2], f(-11.96));
  assert.equal(p.spawnYaw, -0.38);
  // 0.01 떠 있던 시작 위치가 바닥에 내려앉음. 원본 경로에는 지지 없는 첫 프레임에 바닥으로 붙이는 단계가 없고(SplAlongGnd 는 S+0x20 == 1 필요),
  // GameOnGround 중력 법선 성분(0.48 유닛/초 = 0.008/프레임)과 native 접촉(target −d·288)으로 2 프레임에 붙는다(body.ts). 이전 판의 1 프레임은
  // 웹 근사(지지 탐색 쓸어 넘기기로 즉시 붙임)였다 — 2026-10-04 정정.
  w.step(pad(0));
  w.step(pad(0));
  assert.ok(Math.abs(p.pos[1]) < 1e-3, `y ${p.pos[1]}`);
});
