// Native ordinary B7a0 -> SM -> holder display leaves. Full input producers are
// separate: docs/graphics/character_display_r8.md §9/11, squid_ink_visibility_r2.md.
import { f32 } from "../fmath.ts";
import { FLOOR_NY } from "./consts.ts";

export interface PlayerDisplayState { hidden: boolean; delay: number; age: number }
/** 2457620 / 2354d90 native field-write blocks; not the whole constructors. */
export const createPlayerDisplayState = (): PlayerDisplayState => ({ hidden: false, delay: 0, age: 9999 });

export interface OrdinaryDisplayInput {
  state: number; paintClass: number; airFrames: number; ceilingTimer: number;
  chargeFrames: number; chargeMax: number;
  normal: ArrayLike<number>; rawNormal: ArrayLike<number>;
  /** B1b4 is the un-interpolated support normal Y, not B184 in the air. */
  supportNormalY?: number; verticalVelocity: number;
  /** Ba74 / Ba78. Optional only when no executed branch needs them. */
  edgeBlend?: number; edgeTarget?: number;
  b781: boolean; b7f4: boolean; b7f9: boolean; railLatch: boolean;
  forceByte: boolean; launchActive: boolean; wallChargeRelease: boolean; debugForce: boolean;
  /** Explicit scope witnesses, supplied by the adapter. No native default claim. */
  dokanKind: number; grindActive: boolean; warpActive: boolean; specialCandidate: boolean;
}

export type DisplayBinding =
  | { supported: true; hidden: boolean; candidate: boolean; factor: number | null; threshold: number; state: PlayerDisplayState }
  | { supported: false; reason: string; state: PlayerDisplayState };

export const isNativeSquidState = (state: number): boolean =>
  (state >= 0x82 && state <= 0x90) || (state >= 0xaa && state <= 0xac) || state === 0xed || state === 0xee || state === 0x10c;

/** ARM FCVTZS Wd: saturate signed i32 and return zero for NaN. */
function truncI32(x: number): number {
  if (Number.isNaN(x)) return 0;
  if (x >= 2147483647) return 2147483647;
  if (x <= -2147483648) return -2147483648;
  return Math.trunc(x) | 0;
}

/** 248c250..c2e4: each f32 difference must be inclusively within ±2^-23. */
export function nativeDisplayNormalMatch(a: ArrayLike<number>, b: ArrayLike<number>): boolean {
  for (let j = 0; j < 3; j++) {
    const d = f32(f32(a[j]) - f32(b[j]));
    if (!(-(2 ** -23) <= d && d <= 2 ** -23)) return false;
  }
  return true;
}

/** 248c2f0..c418; reversed ranges follow the original, no generic clamp. */
export function nativeWallChargeRatio(chargeFrames: number, chargeMax: number): number {
  const x = f32(((chargeFrames | 0) - 10) | 0), hi = f32(chargeMax);
  if (hi >= 0) {
    if (!(x > 0)) return 0;
    if (hi <= x) return 1;
    return hi === 0 ? 0 : f32(x / hi);
  }
  let q = 0;
  if (hi < x) q = 0 <= x ? 1 : hi === 0 ? 0 : f32(f32(x - hi) / f32(-hi));
  return f32(1 - q);
}

/** 248c5c0..c7dc. Only the upper bound 1 exists in the original factor. */
export function nativeDisplayFactor(match: boolean, y: number, a: number, b: number): number {
  if (!match) return 1;
  a = f32(a); b = f32(b);
  const edge = a > b ? a : b;
  const f = f32(f32(1 - f32(y)) + edge);
  return f > 1 ? 1 : f;
}

/** Ordinary inactive-special path. Returns unsupported without mutating latches. */
export function stepPlayerDisplay(old: PlayerDisplayState, i: OrdinaryDisplayInput): DisplayBinding {
  if (i.dokanKind === 3 || i.warpActive || i.specialCandidate || i.debugForce)
    return { supported: false, reason: "valid warp/special/debug producer is outside the ordinary fixture", state: old };
  if (!Number.isFinite(f32(i.chargeMax)))
    return { supported: false, reason: "non-finite PlayerParam+13c has no supported ordinary gear fixture", state: old };
  let upward = false;
  if ((i.airFrames | 0) >= 1 && f32(i.verticalVelocity) > f32(.05)) {
    if (i.supportNormalY === undefined)
      return { supported: false, reason: "B1b4 support normal Y is missing", state: old };
    // 248c1d4 B.PL rejects unordered too, unlike an inverted >= test.
    upward = f32(i.supportNormalY) < FLOOR_NY;
  }
  const threshold = i.b781 ? 2 : (i.b7f4 && i.b7f9) || i.railLatch ? 1 : upward ? 2 : 4;
  const candidate = isNativeSquidState(i.state) && i.state !== 0x88 && (i.ceilingTimer | 0) <= 0 &&
    (i.paintClass >>> 0) < 2 && i.dokanKind !== 1 && i.dokanKind !== 2 && !i.grindActive &&
    (i.airFrames | 0) < threshold && !(nativeWallChargeRatio(i.chargeFrames, i.chargeMax) >= f32(.25));
  const match = nativeDisplayNormalMatch(i.normal, i.rawNormal);
  // Factor matters only for stable true or a false -> true exchange this frame.
  let delay = old.delay | 0, age = old.age | 0, hidden = old.hidden;
  const factorNeeded = (candidate && hidden) || (candidate && delay <= 1);
  const readFactor = (): number | undefined => {
    if (!match) return 1;
    if (i.edgeBlend === undefined || i.edgeTarget === undefined) return undefined;
    return nativeDisplayFactor(true, i.normal[1], i.edgeBlend, i.edgeTarget);
  };
  let factor: number | null = null;
  if (candidate === hidden) {
    if (factorNeeded) {
      const f = readFactor();
      if (f === undefined) return { supported: false, reason: "matching normals require native Ba74/Ba78 or a verified zero witness", state: old };
      factor = f;
    }
    delay = Math.max((delay - 1) | 0, hidden ? truncI32(f32(f32((factor as number) * 4) + 1)) : 5);
    age = (age + 1) | 0;
  } else {
    if (!isNativeSquidState(i.state)) delay = truncI32(Math.min(f32(delay), 3));
    if (i.forceByte || i.launchActive || (i.wallChargeRelease && i.state === 0x87) || i.railLatch || (upward && !candidate))
      delay = truncI32(Math.min(f32(delay), 1));
    // SUBS/CSEL GT uses signed subtraction flags, including INT_MIN overflow.
    delay = delay > 1 ? (delay - 1) | 0 : 0;
    if (delay > 0) age = (age + 1) | 0;
    else {
      if (candidate) {
        const f = readFactor();
        if (f === undefined) return { supported: false, reason: "entering hidden requires native Ba74/Ba78 or a verified zero witness", state: old };
        factor = f;
      }
      hidden = candidate; delay = hidden ? truncI32(f32(f32((factor as number) * 7) + 3)) : 10; age = 0;
    }
  }
  old.hidden = hidden; old.delay = delay; old.age = age;
  return { supported: true, hidden, candidate, factor, threshold, state: old };
}

export interface DisplayFlags { body: boolean; hlf: boolean; squid: boolean; rail: boolean }
export interface SmDisplayInput {
  hidden: boolean; humanCommand: boolean; squidCommand: boolean; formCounter: number;
  modelKind: number; dead: boolean; state: number; old: DisplayFlags;
}
export type DisplayResetTarget = "body" | "hlf" | "commonHuman" | "squid";
/** Whole 243e2dc ordinary/invalidrail display flags; wrappers keep ticking. */
export function nativeSmDisplay(i: SmDisplayInput): { flags: DisplayFlags; formCounter: number; reset: DisplayResetTarget[] } {
  const hlf = !i.hidden && i.humanCommand && i.formCounter >= 61 && i.modelKind !== 4;
  const body = !i.hidden && i.humanCommand && !hlf, squid = !i.hidden && i.squidCommand;
  const flags = { body, hlf, squid, rail: false }, reset: DisplayResetTarget[] = [];
  if (i.old.body && !body) reset.push("body");
  if (i.old.hlf && !hlf) reset.push("hlf");
  if (i.old.squid && !squid) reset.push("squid");
  if ((i.old.body || i.old.hlf) && !body && !hlf) reset.push("commonHuman");
  return { flags, formCounter: !i.dead && !body && !hlf ? i.state === 0x96 ? 140 : 90 : i.formCounter, reset };
}

export interface HolderDisplayInput {
  state: number; previousState: number; cur: number; old: DisplayFlags;
  de0: number; df0: number; e04: number; e0c: number; e1c: number; d60: number; d5c: number;
  life30: boolean; life31: boolean; life35: boolean; life38: number; debug: boolean;
  special: number; selected: boolean; specialDisabled: boolean;
}
/** Whole 14595b0 display consumer; timing/life fields are explicit inputs. */
export function nativeHolderDisplay(sm: DisplayFlags, i: HolderDisplayInput): DisplayFlags {
  const off = (): DisplayFlags => ({ body: false, hlf: false, squid: false, rail: false });
  if (i.de0 > 0 || (i.df0 >= 1 && i.e04 > 0) || (i.e0c >= 1 && i.e1c >= 1)) return off();
  if (i.d60 > 0) return { ...i.old, squid: false, rail: false };
  if (!(i.life35 && (!(i.life30 || i.life31) || i.life38 > 0)) || i.d5c > 0 || i.debug) return off();
  const f = { ...sm }, active = i.selected && !i.specialDisabled;
  if (active && i.special === 0x1a) f.squid = false;
  if (active && i.special === 0xf) {
    if (f.body) { f.body = false; f.hlf = true; }
    else if (!f.hlf) return f;
  } else if (!(f.body || f.hlf)) return f;
  if (f.squid) {
    const human = (i.state >= 0x91 && i.state <= 0x98) || [0xad, 0xae, 0xf1, 0xf2].includes(i.state);
    if (human && !(i.cur === 0 && i.previousState >= 0x82 && i.previousState <= 0x84)) f.squid = false;
    else { f.body = false; f.hlf = false; }
  }
  return f;
}

/** Native corner zero branch, conditional on raw query/probe inputs, not a Phive replacement. */
export function nativeCornerZeroWitness(a7cAfterProbe: number, lo: number, previousBlend: number, increase: number): { edgeBlend: 0; edgeTarget: 0 } | undefined {
  const a7c = f32(a7cAfterProbe), low = f32(lo), next = f32(f32(previousBlend) + f32(increase));
  if (!Number.isFinite(a7c) || !Number.isFinite(low) || !Number.isFinite(next) || !(a7c <= low) || next < 0) return undefined;
  return { edgeBlend: 0, edgeTarget: 0 };
}

export interface CornerProbeInput {
  contact: ArrayLike<number>; bodyPosition: ArrayLike<number>; platformVelocity: ArrayLike<number>;
  /** EntityWorld+21c: actual registered .01; absent singleton uses original .05. */
  worldTolerance?: number;
}
/** Native 24ac684..c780 geometry and 24f1358..140c radius leaf; no query execution. */
export function nativeCornerProbe(i: CornerProbeInput): { start: [number, number, number]; end: [number, number, number]; radius: number } | undefined {
  const dx = f32(f32(i.bodyPosition[0]) - f32(i.contact[0])), dz = f32(f32(i.bodyPosition[2]) - f32(i.contact[2]));
  const len = f32(Math.sqrt(f32(f32(f32(dx * dx) + 0) + f32(dz * dz))));
  if (!Number.isFinite(len)) return undefined; // external sqrtf/non-finite path not supplied
  let x = dx, z = dz;
  if (len > 0) { const inv = f32(1 / len); x = f32(x * inv); z = f32(z * inv); }
  const start = [0, 1, 2].map(j => f32(f32(f32(i.contact[j]) + f32(i.platformVelocity[j])) +
    (len < f32(.01) ? j === 1 ? f32(.05) : 0 : j === 0 ? f32(x * f32(.05)) : j === 2 ? f32(z * f32(.05)) : 0))) as [number, number, number];
  const end: [number, number, number] = [start[0], f32(start[1] + f32(-.059799324721097946)), start[2]];
  const tolerance = i.worldTolerance === undefined ? f32(.05) : f32(i.worldTolerance);
  const radius = Math.min(Number.isNaN(tolerance) ? f32(.01) : Math.max(tolerance, f32(.01)), 2000);
  return { start, end, radius };
}
