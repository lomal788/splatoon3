import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { cameraInputBlocked, cameraAutoPitch, cameraNormalTarget, cameraFirstQueryPoint, cameraFollowNormal } from "../core/camera/state.ts";
import { readPlayer } from "../core/camera/index.ts";
import { PlayerCamera } from "../core/camera/camera.ts";
import { emptyPad } from "../core/input.ts";

const fixture = JSON.parse(readFileSync(new URL('./fixtures/camera_r10_state.json', import.meta.url)));
const u = new Uint32Array(1), f = new Float32Array(u.buffer);
const number = b => { u[0] = b; return f[0]; };
const bits = x => { f[0] = x; return u[0]; };
const decode = v => ({ beforeGame: v.p9210, gameEnd: v.p9212, demoCanControl: v.control34,
  missionGate: v.mission, sm: v.sm, frames: v.frames.map(number), frameIndex: v.index,
  missionPinch: v.a860, coopGate: v.coop_gate, demoSeconds: number(v.controlbf4),
  dokan: v.dokan, directionActive: v.active, coop: v.coop });
const ordinary = () => decode(fixture.blocked[0].input);

test('r10 entire native input-blocked predicate: 2175 captured returns including NaN/unsigned', () => {
  assert.equal(fixture.blocked.length, 2175);
  for (const [j, c] of fixture.blocked.entries()) assert.equal(+cameraInputBlocked(decode(c.input)), c.actual, `native case ${j}`);
});
test('r10 WaterFall normal: 512 captured native f32 triples', () => {
  assert.equal(fixture.normal.length, 512);
  for (const [j, c] of fixture.normal.entries())
    assert.deepEqual(cameraNormalTarget(c.normal.map(number), c.active, number(c.water), number(c.follow)).map(bits), c.actual, `native case ${j}`);
});
test('Demo timed input block does not become an automatic zero-pitch gate', () => {
  const control = { ...ordinary(), demoSeconds: 1 };
  const i = { control, returnRate: .2, airRatio: 0, versusScene: false, result: 0,
    ready: 0, coop1348: 0, respawn: 0, bodyF34: 0, cameraMissionGate: 0 };
  assert.equal(cameraInputBlocked(control), true);
  assert.equal(cameraAutoPitch(.5, i), null);
  control.directionActive = 1;
  assert.equal(cameraAutoPitch(.5, i), Math.fround(.5 + Math.fround(-1 * Math.fround(.01))));
});
test('camera adapter consumes only a supported B7a0 display producer, not wallCling', () => {
  const player = { pos: [0,0,0], display: { hidden: true }, displayBinding: { supported: true }, wallCling: false };
  const w = { shared: new Map([['player', player]]) };
  assert.equal(readPlayer(w).native.wall7a0, true);
  player.displayBinding.supported = false; player.wallCling = true;
  assert.equal(readPlayer(w).native, undefined);
  player.cameraNative = { wall7a0: false }; player.displayBinding.supported = true;
  assert.equal(readPlayer(w).native.wall7a0, false);
});
test('standing mouse input is discarded when explicit native control is blocked', () => {
  const c = new PlayerCamera(), control = { ...ordinary(), demoSeconds: 1 };
  const pl = { pos: [0,0,0], floorNormal: [0,1,0], native: { control } };
  const p = { ...emptyPad(), lookMode: 'mouse', lookYaw: .5, lookPitch: .2 };
  c.step(pl, p, null);
  assert.deepEqual([...c.out.aimForward], [0,0,1]); assert.equal(c.out.pitchAngleDeg, 0);
  control.demoSeconds = 0; c.step(pl, p, null);
  assert.ok(c.out.aimForward[0] > 0); assert.ok(c.out.pitchAngleDeg > 0);
});

test('query1 separation corrects the raw point only; query2 sign is independent', () => {
  assert.deepEqual(cameraFirstQueryPoint([0,0,-3], [0,0,1], 0, .3), [0,0,Math.fround(-3 + Math.fround(.3))]);
  assert.deepEqual(cameraFirstQueryPoint([0,0,-3], [0,0,1], 1, .3), [0,0,-3]);
  assert.deepEqual(cameraFirstQueryPoint([0,0,-3], [0,0,1]), [0,0,-3]);
});
test('native normal follow conditionally corrects non-unit lengths', () => {
  assert.deepEqual(cameraFollowNormal([0,2,0], [0,2,0]), [0,1,0]);
  assert.deepEqual(cameraFollowNormal([0,0,0], [0,0,0]), [0,0,0]);
});

test('explicit right-stick frames use snap/velocity and reset their accumulated state', () => {
  const c = new PlayerCamera(), pl = { pos: [0,0,0], floorNormal: [0,1,0] };
  const pad = { ...emptyPad(), cameraStick: { axis: { x: .7, y: .8, deltaX: .7, deltaY: .8 },
    sensitivity: 0, gyroSensitivity: 0, controllerMode: 0, pitchLimitBlend: 0,
    yaw: { slowBlendDisabled: true, movementBlend: 0, postureState: 0, capDeg: 4, capBlend: 0, tilt: 0 } } };
  c.step(pl, pad, null);
  const first = [...c.out.aimForward, c.out.pitchAngleDeg, c.out.pitchNorm];
  assert.ok(first[0] < 0); assert.ok(first[3] > 0); assert.equal(c.out.mouseLook, false);
  for (let n = 0; n < 8; n++) c.step(pl, pad, null);
  c.reset(pl, false); c.step(pl, pad, null);
  assert.deepEqual([...c.out.aimForward, c.out.pitchAngleDeg, c.out.pitchNorm], first);
  const mouse = { ...emptyPad(), lookMode: 'mouse', lookYaw: .1 };
  c.reset(pl, false); c.step(pl, mouse, null);
  assert.equal(c.out.mouseLook, true); assert.ok(c.out.aimForward[0] > 0);
});
