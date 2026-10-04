// PlayerCamera24e0178 scalar input blocks. Native r10_input_response.md §3~6.
// Raw producer inputs are explicit; a mouse displacement is not a stick sample.
import { F, add, sub, mul, div, floatBits as bits } from "./native_math.ts";
import { pitchMaxDeg, yawMaxDeg } from "./pitch.ts";

export const INPUT_DEG_TO_RAD = bits(0x3c8efa35);
export const INPUT_RAD_TO_DEG = bits(0x42652ee0);
const SMALL = bits(0x3a83126f);

/** SDK powf/logf/expf consumer. JS Math is the web libm adapter, not SDK proof. */
export interface InputLibm {
  powf(x: number, exponent: number): number;
  logf(x: number): number;
  expf(x: number): number;
}
export const WEB_INPUT_LIBM: InputLibm = {
  powf: (x, exponent) => F(Math.pow(F(x), F(exponent))),
  logf: x => F(Math.log(F(x))),
  expf: x => F(Math.exp(F(x))),
};

/** C180/C184 filtered raw-minus-previous-inverted delta, C188 stored accumulator. */
export interface NativeAxisState { deltaX: number; deltaY: number; accumulator: number }
export interface NativeAxisInput {
  /** Signed, post-deadzone/remap inputs B a9c/aa0. */
  x: number; y: number;
  /** B aa4/aa8; do not substitute delta of an already-inverted pair. */
  deltaX: number; deltaY: number;
  gyro: boolean;
}
export interface NativeAxisOutput { yaw: number; pitch: number }

/** 0bbc..0d78. Returns native signed (-x,y), preserving the original length. */
export function nativeAxisSnap(state: NativeAxisState, input: NativeAxisInput, libm: InputLibm = WEB_INPUT_LIBM): NativeAxisOutput {
  const x = F(input.x), y = F(input.y), ax = Math.abs(x), ay = Math.abs(y);
  if (input.gyro) state.accumulator = 0;
  else {
    state.deltaX = add(state.deltaX, mul(sub(input.deltaX, state.deltaX), bits(0x3e4ccccd)));
    state.deltaY = add(state.deltaY, mul(sub(input.deltaY, state.deltaY), bits(0x3e4ccccd)));
    let diagonal = mul(ax, ay);
    if (diagonal > SMALL) diagonal = mul(diagonal, sub(1, div(Math.abs(sub(ax, ay)), add(ax, ay))));
    let e = add(state.accumulator, mul(sub(3, state.accumulator), bits(0x3dcccccd)));
    e = Math.max(add(e, mul(F(Math.sqrt(Math.abs(mul(state.deltaY, F(-state.deltaX))))), -3)), -1);
    state.accumulator = Math.max(add(e, mul(F(Math.sqrt(diagonal)), bits(0xbf333333))), -1);
  }
  const exponent = Math.max(state.accumulator, 0);
  const before = F(Math.sqrt(add(mul(ax, ax), mul(ay, ay))));
  let yaw = F(-x), pitch = y;
  if (ax > ay) pitch = mul(F(libm.powf(sub(1, div(sub(ax, ay), ax)), exponent)), pitch);
  else if (ay > 0) yaw = mul(F(libm.powf(sub(1, div(sub(ay, ax), ay)), exponent)), yaw);
  const after = F(Math.sqrt(add(mul(pitch, pitch), mul(yaw, yaw))));
  if (after > 0) {
    const scale = div(before, after);
    pitch = mul(pitch, scale); yaw = mul(scale, yaw);
  }
  return { yaw, pitch };
}

/** 09e0..0a18, before vertical deadzone. Input is already gyro-remapped y. */
export function nativePitchFollow(previous: number, remappedY: number): number {
  return add(previous, mul(sub(1, previous), mul(Math.abs(F(remappedY)), bits(0x3e4ccccd))));
}

/** Ordinary 0b8c..0bb8 deadzone; current gyro-enable byte is not a transition. */
export function nativeVerticalDeadzone(y: number, gyro: boolean, bodyIsEnableGyro: boolean, globalGyroYEnabled: boolean): number {
  y = F(y);
  return Math.abs(y) < (gyro ? 0 : F(.15)) || (bodyIsEnableGyro && !globalGyroYEnabled) ? 0 : y;
}

function inputBias(x: number, shape: number, libm: InputLibm): number {
  x = F(x);
  if (Math.abs(x) < SMALL) return 0;
  const exponent = mul(F(libm.logf(shape)), bits(0xbfb8aa3b));
  const result = F(libm.expf(mul(F(libm.logf(Math.abs(x))), exponent)));
  return x < 0 ? F(-result) : result;
}

/** 0f38..1008; snap preserves length, then bias shapes that length. */
export function nativeLengthBias(x: number, y: number, gyro: boolean, libm: InputLibm = WEB_INPUT_LIBM): number {
  const length = F(Math.sqrt(add(mul(x, x), mul(y, y))));
  return inputBias(length, gyro ? bits(0x3ecccccd) : bits(0x3f4ccccd), libm);
}

function responseAlpha(k: number, gyro: boolean, magnitude: number): number {
  k = F(k);
  const a0 = gyro ? add(mul(k, k < 0 ? bits(0x3ca3d70c) : bits(0x3ca3d708)), bits(0x3dcccccd)) : F(.8);
  const a1 = gyro ? F(.2) : F(.3);
  return add(a0, mul(magnitude, sub(a1, a0)));
}

export interface NativeYawInput {
  k: number; gyro: boolean; velocity: number; yaw: number; magnitude: number; fovRatio: number;
  /** C15d9, stack38 horizontal movement blend w, B f34. */
  slowBlendDisabled: boolean; movementBlend: number; postureState: number;
  /** C156c / C1550 / C1764 / C14d4. Explicit raw inputs, no missing producer defaults. */
  capDeg: number; capBlend: number; squidBlend: number; tilt: number;
}
export interface NativeVelocityOutput { maximum: number; velocity: number }

/** 10bc..12a8, original degrees/radian constants and multiply grouping. */
export function nativeYawInput(input: NativeYawInput): NativeVelocityOutput {
  const k = F(input.k);
  let base = yawMaxDeg(k);
  const slow = add(mul(k, k < 0 ? bits(0x3f75c290) : bits(0x3fe66664)), bits(0x4019999a));
  if (!input.slowBlendDisabled) base = add(base, mul(input.movementBlend, sub(slow, base)));
  if (base > F(input.capDeg)) base = add(base, mul(sub(input.capDeg, base), mul(input.capBlend, input.squidBlend)));
  const state = input.postureState >>> 0;
  const maximum = mul(state >= 2 && state <= 4 ? slow : base, INPUT_DEG_TO_RAD);
  let term = mul(input.yaw, input.fovRatio);
  if (mul(term, input.tilt) < 0) term = mul(term, sub(1, Math.abs(F(input.tilt))));
  const target = mul(maximum, mul(input.magnitude, term));
  return { maximum, velocity: add(input.velocity, mul(responseAlpha(k, input.gyro, input.magnitude), sub(target, input.velocity))) };
}

export interface NativePitchInput {
  k: number; gyroK: number; gyro: boolean; velocity: number; angle: number;
  pitch: number; magnitude: number; fovRatio: number; limitBlend: number;
  /** Controller17d: exactly1 adjusts by10; C15f0 unsigned slot fallback. */
  controllerMode: number; slot: number;
  /** C15f4/f8 then C15fc/1600; ordinary nongyro does not consume offsets. */
  offsets: readonly [number, number, number, number];
}
export interface NativePitchOutput extends NativeVelocityOutput { angle: number }

/** 1674..1c30. Absolute gyro/device posture and final p follow are separate. */
export function nativePitchInput(input: NativePitchInput, libm: InputLibm = WEB_INPUT_LIBM): NativePitchOutput {
  const maximum = mul(pitchMaxDeg(input.k), INPUT_DEG_TO_RAD);
  const target = mul(mul(input.magnitude, mul(input.pitch, input.fovRatio)), maximum);
  const velocity = add(input.velocity, mul(responseAlpha(input.k, input.gyro, input.magnitude), sub(target, input.velocity)));
  const gk = F(input.gyroK), adjust = input.controllerMode === 1 ? 10 : 0;
  const base = add(-75, adjust);
  let lo = add(add(mul(gk, gk < 0 ? 11 : 3), -103), adjust);
  let hi = add(add(mul(gk, gk < 0 ? -18 : -6), -31), adjust);
  if (input.gyro) {
    const slot = (input.slot >>> 0) < 2 ? input.slot >>> 0 : 0;
    lo = sub(add(lo, input.offsets[slot]), input.offsets[slot + 2]);
    hi = sub(add(hi, input.offsets[slot]), input.offsets[slot + 2]);
  }
  const relative = add(input.angle, base);
  let t: number;
  if (lo <= hi) t = relative <= lo ? 0 : hi <= relative ? 1 : div(sub(relative, lo), sub(hi, lo));
  else t = relative <= hi ? 1 : lo <= relative ? 0 : sub(1, div(sub(relative, hi), sub(lo, hi)));
  const shape = bits(0x3ee66666);
  const slope = div(sub(inputBias(add(t, SMALL), shape, libm), inputBias(t, shape, libm)), SMALL);
  const angle = add(input.angle, mul(mul(velocity, INPUT_RAD_TO_DEG), slope));
  const limit = add(mul(input.limitBlend, -75), 90);
  // Original FCSEL upper first, lower second; do not clamp before accumulation.
  let clamped = angle > limit ? limit : angle;
  if (angle < F(-limit)) clamped = F(-limit);
  return { maximum, velocity, angle: clamped };
}
