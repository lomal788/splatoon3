import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { PerspectiveCamera, Vector2, Vector3 } from "three";
import { logicalProjection, CameraProjectionState, projectionFovRadians } from "../core/camera/projection.ts";
import { createCameraView } from "../client/camera/index.ts";
import { PlayerCamera } from "../core/camera/camera.ts";
import { emptyPad } from "../core/input.ts";
import { shadowSliceCorners } from "../client/render/shadows.ts";

const fixture = JSON.parse(readFileSync(new URL("./fixtures/camera_r10_projection.json", import.meta.url)));
const bits = a => Array.from(new Uint32Array(Float32Array.from(a).buffer));
const fromBits = b => new Float32Array(Uint32Array.from([b]).buffer)[0];
const pose = { near: .2, far: 2000, fovRadians: projectionFovRadians(55) };
const viewport = (width, height) => ({ left: 0, top: 0, right: width, bottom: height });

test("r10 logical projection: saved original bytes match every f32 with captured SDK tanf input", () => {
  const out = new Float32Array(16);
  assert.equal(fixture.cases, 421);
  for (const d of fixture.rows) {
    logicalProjection(out, { ...d, tanHalfFov: fromBits(d.tanHalfFovBits) });
    assert.deepEqual(bits(out), d.projectionBits, "original case " + d.i);
  }
});

test("JS tanf adapter is isolated from exact native depth terms and reported separately", t => {
  const out = new Float32Array(16);
  let exact = 0, mismatchFields = 0, maxUlp = 0;
  for (const d of fixture.rows) {
    logicalProjection(out, d);
    const got = bits(out);
    assert.equal(got[10], d.projectionBits[10]);
    assert.equal(got[11], d.projectionBits[11]);
    assert.ok(out.every(Number.isFinite));
    if (got.every((v, i) => v === d.projectionBits[i])) exact++;
    got.forEach((v, i) => { if (v !== d.projectionBits[i]) { mismatchFields++; maxUlp = Math.max(maxUlp, Math.abs(v - d.projectionBits[i])); } });
  }
  t.diagnostic(JSON.stringify({ adapter: "Math.fround(Math.tan(f32 halfFov))", exact, cases: fixture.cases, mismatchFields, maxUlp,
    scope: "finite fixture measurement; not a claim about every SDK tanf input" }));
});

test("viewport supplies next projection aspect; valid latch survives missing viewport", () => {
  const p = new CameraProjectionState();
  p.update(pose, viewport(1920, 1080));
  assert.equal(p.matrixAspect, Math.fround(4 / 3));
  assert.equal(p.aspect, Math.fround(1920 / 1080));
  assert.equal(p.viewportValid, true);
  const first = bits(p.logical);
  p.update(pose, viewport(1200, 1200));
  assert.equal(p.matrixAspect, Math.fround(16 / 9));
  assert.equal(p.aspect, 1);
  assert.notDeepEqual(bits(p.logical), first);
  p.update(pose);
  assert.equal(p.matrixAspect, 1);
  assert.equal(p.logicalDirty, false);
  assert.equal(p.viewportValid, true);
  const stable = bits(p.logical);
  p.update(pose);
  assert.deepEqual(bits(p.logical), stable);
});

test("draw context follows viewport, preserves u16/type3 zero-height and does not set valid latch", () => {
  const p = new CameraProjectionState();
  p.update(pose, viewport(1600, 900), { width: 0, height: 0, type: 0 });
  assert.equal(p.aspect, 1);
  assert.equal(p.matrixAspect, Math.fround(4 / 3));
  const other = new CameraProjectionState();
  other.update(pose, null, { width: 640, height: 0, type: 3 });
  assert.equal(other.aspect, Infinity);
  assert.equal(other.viewportValid, false);
  assert.equal(other.matrixAspect, Math.fround(4 / 3));
  // The original fixture likewise stops before another matrix consumes +Inf.
});

test("client supplies logical rows with no device reflection and keeps matrix inverse for depth/shadow unprojection", () => {
  const camera = new PerspectiveCamera(), c = new PlayerCamera();
  c.step({ pos: [0, 0, 0], forward: [0, 0, 1], floorNormal: [0, 1, 0] }, emptyPad(), null);
  const size = new Vector2(1920, 1080), renderer = { getSize: out => out.copy(size) };
  const view = createCameraView({ camera, renderer }), world = { shared: new Map([["camera", c.out]]) };
  view.update(world, 1);
  const state = camera.userData.nativeProjection.state;
  assert.equal(camera.userData.nativeProjection.source, "logical");
  assert.equal(camera.aspect, Math.fround(4 / 3));
  const rows = camera.projectionMatrix.clone().transpose().elements;
  assert.deepEqual(bits(rows), bits(state.logical));
  assert.ok(camera.projectionMatrix.elements[0] > 0);
  view.update(world, 1);
  assert.equal(camera.aspect, Math.fround(16 / 9));
  for (const z of [-1, 1]) for (const x of [-1, 0, 1]) for (const y of [-1, 1]) {
    const clip = new Vector3(x, y, z), eye = clip.clone().applyMatrix4(camera.projectionMatrixInverse);
    assert.ok(eye.clone().applyMatrix4(camera.projectionMatrix).distanceTo(clip) < 1e-9);
  }
  // Clip depth matches the OpenGL logical matrix; native depth is f32 rounded.
  assert.ok(Math.abs(new Vector3(0, 0, -camera.near).applyMatrix4(camera.projectionMatrix).z + 1) < 3e-7);
  assert.ok(Math.abs(new Vector3(0, 0, -camera.far).applyMatrix4(camera.projectionMatrix).z - 1) < 3e-7);
  assert.equal(camera.userData.nativeProjection.logicalView.length, 12);
});

test("render viewport cold start and resize lag are explicit web render-adapter frames", () => {
  const camera = new PerspectiveCamera(), c = new PlayerCamera();
  c.step({ pos: [0, 0, 0] }, emptyPad(), null);
  const size = new Vector2(1000, 500), view = createCameraView({ camera, renderer: { getSize: out => out.copy(size) } });
  const w = { shared: new Map([["camera", c.out]]) };
  view.update(w, .2); assert.equal(camera.aspect, Math.fround(4 / 3));
  view.update(w, .8); assert.equal(camera.aspect, 2);
  size.set(500, 1000);
  view.update(w, .1); assert.equal(camera.aspect, 2);
  view.update(w, .9); assert.equal(camera.aspect, .5);
  assert.equal(camera.userData.nativeProjection.cadence, "web-render-frame");
});

test("actual shadow slice consumer uses the new inverse without changing its own orthographic cameras", () => {
  const camera = new PerspectiveCamera(), c = new PlayerCamera();
  c.step({ pos: [2, 3, 4], floorNormal: [0, 1, 0] }, emptyPad(), null);
  const view = createCameraView({ camera, renderer: { getSize: out => out.set(1920, 1080) } });
  const w = { shared: new Map([["camera", c.out]]) };
  view.update(w, 1); view.update(w, 1);
  const corners = shadowSliceCorners(camera, 1, 30);
  assert.equal(corners.length, 8);
  for (let i = 0; i < corners.length; i++) {
    const eye = corners[i].clone().applyMatrix4(camera.matrixWorldInverse);
    assert.ok(Math.abs(eye.z + (i < 4 ? 1 : 30)) < 1e-10);
    const ndc = eye.clone().applyMatrix4(camera.projectionMatrix);
    assert.ok(Math.abs(Math.abs(ndc.x) - 1) < 1e-10);
    assert.ok(Math.abs(Math.abs(ndc.y) - 1) < 1e-10);
  }
});

test("View row layout preserves the native +Z-facing logical convention, world translation and one shake sum", () => {
  const camera = new PerspectiveCamera(), c = new PlayerCamera().out;
  c.right.set([-1, 0, 0]); c.prevRight.set(c.right);
  c.up.set([0, 1, 0]); c.prevUp.set(c.up);
  c.viewZ.set([0, 0, -1]); c.prevViewZ.set(c.viewZ);
  c.pos.set([3, 4, 5]); c.prevPos.set(c.pos);
  const view = createCameraView({ camera }), w = { shared: new Map([["camera", c]]) };
  camera.userData.shakeOffset = { x: .5, y: -.5, z: 1 };
  view.update(w, 1);
  const rows = Array.from(camera.userData.nativeProjection.logicalView);
  // Numeric row mapping only; Three inverse's signed-zero/FMA differences are
  // an explicit web View adapter boundary, not a whole SDK LookAt assertion.
  assert.deepEqual(rows.map(v => v === 0 ? 0 : v), [-1, 0, 0, 3.5, 0, 1, 0, -3.5, 0, 0, -1, 6]);
  const right = new Vector3(-1, 0, 0).add(camera.position).project(camera);
  assert.ok(right.x > 0);
});
