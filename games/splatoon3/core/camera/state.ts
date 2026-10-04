// Explicit original camera inputs, not inferred from mouse/ordinary web flags.
// r10_state_producers §6.2/6.4/6.10, native 24c99f0 / 24da0b0.
import { F, add, sub, mul, div, length, directionSlerp } from "./native_math.ts";

export interface CameraControlState {
  beforeGame: number; gameEnd: number; demoCanControl: number;
  missionGate: number; sm: number; frames: ArrayLike<number>; frameIndex: number;
  missionPinch: number; coopGate: number; demoSeconds: number;
  dokan: number; directionActive: number; coop: number;
}

function earlyPitchReturn(i: CameraControlState): boolean {
  if (!(i.beforeGame || i.gameEnd || i.demoCanControl)) return true;
  if (i.missionGate !== 0 && i.missionGate !== 5) return true;
  const frame = F(i.frames[i.frameIndex === 0 || i.frameIndex === 1 ? i.frameIndex : 0]);
  if ((i.sm === 0xef || i.sm === 0xf0) && frame <= 95) return true;
  if (i.sm === 0xf1 || (i.sm === 0xf2 && frame <= 50)) return true;
  return i.missionPinch === 3 || i.missionPinch === 4 || (i.coopGate >= 5 && i.coopGate <= 8);
}

/** Entire 24c99f0 predicate. NaN does not take the original LS/GT branches. */
export function cameraInputBlocked(i: CameraControlState): boolean {
  if (earlyPitchReturn(i)) return true;
  if (!i.demoCanControl || F(i.demoSeconds) > 0) return true;
  if (i.dokan === 1 || i.dokan === 2 || i.directionActive !== 0) return true;
  const coop = i.coop >>> 0;
  return coop > 9 || ((0x1fc >>> coop) & 1) !== 0;
}

export interface CameraAutoPitchState {
  control: CameraControlState;
  /** Already-produced native s9. No guessed rate from blocked/mouse state. */
  returnRate: number;
  airRatio: number;
  versusScene: boolean; result: number; ready: number; coop1348: number;
  respawn: number; bodyF34: number; cameraMissionGate: number;
}

/** Separate 24e2d80/24e407c branch. null selects the normal target blend. */
export function cameraAutoPitch(p: number, i: CameraAutoPitchState): number | null {
  if (earlyPitchReturn(i.control)) return add(p, mul(i.returnRate, F(-p)));
  if (i.control.directionActive !== 0)
    return add(p, mul(sub(-.5, p), add(mul(i.airRatio, .09), .01)));
  const f34 = i.bodyF34 >>> 0;
  const ready = i.ready !== 0 || F(i.respawn) > 0 || f34 === 1 || f34 === 2 || f34 === 4;
  if (i.versusScene && (((!i.result && i.coop1348 !== 12) && ready) || i.control.beforeGame !== 0) && ((f34 - 2) >>> 0) > 2)
    return add(p, mul(.2, F(-p)));
  if (i.cameraMissionGate === 1 || i.cameraMissionGate === 2 || i.cameraMissionGate === 4)
    return add(p, mul(.1, F(-p)));
  return null;
}

/** B180 target + WaterFall Bdf0/Bdf4; C124 is the follow point, not camera Y. */
export function cameraNormalTarget(normal: ArrayLike<number>, waterFrames: number, waterHeight: number, followY: number): number[] {
  const n = [F(normal[0]), F(normal[1]), F(normal[2])];
  if ((waterFrames | 0) < 1) return n;
  n[1] = add(n[1], mul(Math.max(0, sub(waterHeight, followY)), .4));
  const l = length(n);
  if (l > 0) { const inv = div(1, l); for (let j = 0; j < 3; j++) n[j] = mul(n[j], inv); }
  if (l < F(.01)) return [F(normal[0]), F(normal[1]), F(normal[2])];
  return n;
}

/** 24da160 onward: native slerp, then conditional length correction. */
export function cameraFollowNormal(previous: ArrayLike<number>, target: ArrayLike<number>): number[] {
  const n = directionSlerp(F(.1), previous, target), l = length(n);
  if (l > F(.001) && Math.abs(sub(l, 1)) > F(.01)) {
    const inv = div(1, l); for (let j = 0; j < 3; j++) n[j] = mul(n[j], inv);
  }
  return n;
}

/** Query1 24dd8c0..dd8f8. This is separate from query2 normal FNEG. */
export function cameraFirstQueryPoint(point: ArrayLike<number>, normal: ArrayLike<number>, entryFlags?: number, separation?: number): number[] {
  if (entryFlags === undefined || separation === undefined || (entryFlags & 1) !== 0) return Array.from(point);
  return [0, 1, 2].map(j => add(point[j], mul(separation, normal[j])));
}
