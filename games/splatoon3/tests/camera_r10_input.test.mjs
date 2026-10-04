import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  nativeAxisSnap, nativeLengthBias, nativeYawInput, nativePitchInput,
  nativePitchFollow, nativeVerticalDeadzone, WEB_INPUT_LIBM,
} from "../core/camera/stick.ts";
import { pitchAngleToP } from "../core/camera/pitch.ts";
import { floatBits } from "../core/camera/native_math.ts";

const fixture = JSON.parse(readFileSync(new URL("./fixtures/camera_r10_input_native.json", import.meta.url)));
const bits = values => Array.from(new Uint32Array(Float32Array.from(values).buffer));

// Captured SDK argument/result boundary; production does not use this replay.
function nativeLibmTrace(rows) {
  let at = 0;
  const invoke = (name, ...args) => {
    const row = rows[at++];
    assert.ok(row, `unexpected ${name} call ${at}`);
    assert.equal(name, row.name);
    assert.deepEqual(bits(args), row.argBits, `${name} original f32 arguments`);
    return floatBits(row.resultBits);
  };
  return {
    math: { powf: (x, p) => invoke("powf", x, p), logf: x => invoke("logf", x), expf: x => invoke("expf", x) },
    done: () => assert.equal(at, rows.length, "all original SDK calls consumed"),
  };
}

test("r10 fixture is native capture with no null/unknown PLT/automatic mapping", () => {
  assert.equal(fixture.meta.new_analysis_credit, false);
  assert.equal(fixture.meta.whole_input_or_scene, false);
  assert.deepEqual(fixture.meta.null, {});
  assert.deepEqual(fixture.meta.auto, []);
  assert.deepEqual(fixture.meta.fault, []);
  assert.deepEqual(fixture.meta.plt, {});
  assert.equal(Object.values(fixture.meta.cases).reduce((a, b) => a + b), 1280);
});

test("native axis C180/184/188, two -1 floors, pow exponent0 and restored length: 256 bit fixtures", () => {
  for (const [i, row] of fixture.axis.entries()) {
    const state = { ...row.state }, trace = nativeLibmTrace(row.mathTrace);
    const out = nativeAxisSnap(state, row.input, trace.math);
    assert.deepEqual(bits([state.deltaX, state.deltaY, state.accumulator, out.yaw, out.pitch]), row.outputBits, `axis ${i}`);
    trace.done();
  }
  assert.ok(fixture.axis.some(row => floatBits(row.outputBits[2]) < 0), "negative accumulator remains stored");
});

test("axis consecutive native state chain preserves gyro enter/exit and delta history: 64 steps", () => {
  let state = { ...fixture.axis[192].state };
  for (const row of fixture.axis.slice(192)) {
    assert.deepEqual(bits(Object.values(state)), bits(Object.values(row.state)));
    const trace = nativeLibmTrace(row.mathTrace), out = nativeAxisSnap(state, row.input, trace.math);
    assert.deepEqual(bits([state.deltaX, state.deltaY, state.accumulator, out.yaw, out.pitch]), row.outputBits);
    trace.done();
  }
});

test("native length bias raw SDK boundary: 128 bit fixtures", () => {
  for (const [i, row] of fixture.bias.entries()) {
    const trace = nativeLibmTrace(row.mathTrace), { x, y, gyro } = row.input;
    assert.deepEqual(bits([nativeLengthBias(x, y, gyro, trace.math)]), row.outputBits, `bias ${i}`);
    trace.done();
  }
});

test("yaw native constants, state/cap/tilt branches and multiply order: 256 complete bit fixtures", () => {
  for (const [i, row] of fixture.yaw.entries()) {
    const out = nativeYawInput(row.input);
    assert.deepEqual(bits([out.maximum, out.velocity]), row.outputBits, `yaw ${i}`);
  }
});

test("pitch maximum/velocity/angle, controller exactly1, gyro slots: 256 bit fixtures", () => {
  for (const [i, row] of fixture.pitch.entries()) {
    const trace = nativeLibmTrace(row.mathTrace), out = nativePitchInput(row.input, trace.math);
    assert.deepEqual(bits([out.maximum, out.velocity, out.angle]), row.outputBits, `pitch ${i}`);
    trace.done();
  }
});

test("whole original pitch-angle-to-p/out f32 Bezier and correction: 256 bit fixtures", () => {
  for (const [i, row] of fixture.pitchMap.entries()) {
    const v = row.input;
    const out = pitchAngleToP(v.angle, v.gyroK, v.handheldFlag, v.offA, v.offB, v.stick);
    assert.deepEqual(bits(out), row.outputBits, `pitchMap ${i}`);
  }
});

test("p follow uses remapped y before deadzone, native grouping: 128 bit fixtures", () => {
  for (const [i, row] of fixture.pitchFollow.entries()) {
    assert.deepEqual(bits([nativePitchFollow(row.previous, row.remappedY)]), row.outputBits, `pFollow ${i}`);
  }
  assert.equal(nativeVerticalDeadzone(.1, false, false, false), 0);
  assert.equal(nativeVerticalDeadzone(.1, true, false, false), Math.fround(.1));
  assert.equal(nativeVerticalDeadzone(.8, true, true, false), 0);
  assert.equal(nativeVerticalDeadzone(.8, true, true, true), Math.fround(.8));
});

test("web-libm changes do not alter exact yaw or pitch speed arithmetic", () => {
  assert.equal(WEB_INPUT_LIBM.powf(0, 0), 1);
  for (const row of fixture.pitch) {
    const out = nativePitchInput(row.input);
    assert.deepEqual(bits([out.maximum, out.velocity]), row.outputBits.slice(0, 2));
  }
});

test("production JS-libm path matches all 1280 native fixtures / 3328 fields in this corpus", () => {
  const consume = {
    axis: row => { const state = { ...row.state }, out = nativeAxisSnap(state, row.input); return [state.deltaX, state.deltaY, state.accumulator, out.yaw, out.pitch]; },
    bias: row => [nativeLengthBias(row.input.x, row.input.y, row.input.gyro)],
    yaw: row => { const out = nativeYawInput(row.input); return [out.maximum, out.velocity]; },
    pitch: row => { const out = nativePitchInput(row.input); return [out.maximum, out.velocity, out.angle]; },
    pitchMap: row => { const v = row.input; return pitchAngleToP(v.angle, v.gyroK, v.handheldFlag, v.offA, v.offB, v.stick); },
    pitchFollow: row => [nativePitchFollow(row.previous, row.remappedY)],
  };
  for (const [name, run] of Object.entries(consume)) {
    for (const [i, row] of fixture[name].entries()) assert.deepEqual(bits(run(row)), row.outputBits, `${name} production ${i}`);
  }
});
