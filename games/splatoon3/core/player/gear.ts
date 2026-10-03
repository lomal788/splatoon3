// 담당: [physics] — 기어 능력 AP → 수치(spl::PlayerParam 캐시). 근거: docs/player/gear_skills.md §4.3·§5
// (원본 함수 0x710265df40/0x710265fd48/0x7102665ee4 를 에뮬로 실행해 재구현과 731값 비트 일치한 식).
import { f32 } from "../fmath.ts";
import { fb } from "./consts.ts";

const C_0001 = fb(0x3a83126f); // 0.001
const C_0999 = fb(0x3f7fbe77); // 0.999
const C_NLOG2E = fb(0xbfb8aa3b); // −1.442695

/** AP(메인+서브 합) → 비율 p (gear_skills.md §5.1). */
export function apRate(ap: number, ninja = false): number {
  let a = f32(ap);
  if (a > 57) a = 57;
  let p = f32(f32(a * f32(f32(a * f32(-0.027)) + f32(3.3))) / f32(100));
  p = p > 1 ? 1 : p < 0 ? 0 : p;
  if (ninja) {
    p = f32(p * f32(0.8));
    p = p > 1 ? 1 : p < 0 ? 0 : p;
  }
  return p;
}

/** Low/Mid/High 비선형 보간 (§5.2). logf/expf 는 Math.log/exp + f32 반올림(원본 SDK 와 1ulp 차이 가능성은 §5.2 참고). */
export function gearLerp(low: number, mid: number, high: number, rate: number): number {
  low = f32(low); mid = f32(mid); high = f32(high);
  const range = f32(high - low);
  let s: number;
  if (low <= high) {
    s = !(low < mid) ? 0 : !(mid < high) ? 1 : range === 0 ? 0 : f32((mid - low) / range);
  } else {
    let t = 0;
    if (high < mid) {
      if (low <= mid) t = 1;
      else if (f32(low - high) !== 0) t = f32((mid - high) / f32(low - high));
    }
    s = f32(1 - t);
  }
  let k = rate;
  const d = f32(s - 0.5);
  if (d > C_0001 || d < -C_0001) {
    const a = Math.abs(rate);
    if (a < C_0001) k = 0;
    else if (s < C_0001) k = a >= C_0999 ? 1 : 0;
    else {
      const ls = f32(Math.log(s));
      const la = f32(Math.log(a));
      k = f32(Math.exp(f32(la * f32(ls * C_NLOG2E))));
    }
  }
  return f32(low + f32(range * k));
}

/** 같은 b(x, s) 곡선(가속량 식에 인라인된 형태, 부호 보존). movement_physics.md §6.3.1 */
export function curve(x: number, s: number): number {
  const d = f32(s - 0.5);
  if (!(d < -C_0001 || C_0001 < d)) return x;
  const a = x < 0 ? -x : x;
  if (!(C_0001 <= a)) return 0;
  if (!(C_0001 <= s)) return C_0999 <= a ? 1 : 0;
  const v = f32(Math.exp(f32(f32(f32(Math.log(a)) * f32(Math.log(s))) * C_NLOG2E)));
  return x < 0 ? -v : v;
}

/** 생성자 기본값 (gear_skills.md §4.3 표, (Low, Mid, High)) [판독]. */
export const GEAR = {
  HumanMid: [0.096, 0.12, 0.144],
  HumanSlow: [0.088, 0.116, 0.144],
  HumanFast: [0.104, 0.124, 0.144],
  ShotRate: [1.0, 1.125, 1.25],
  SquidMid: [0.192, 0.216, 0.24],
  SquidSlow: [0.1728, 0.216, 0.24],
  SquidFast: [0.2016, 0.2208, 0.24],
  OpJump: [0.08, 0.098, 0.11],
  OpMove: [0.024, 0.05568, 0.0768],
  OpMoveShot: [0.012, 0.033, 0.042],
  SomersaultKd: [0.85, 0.925, 1.0],
  WallJumpChargeFrames: [45, 18, 5], // actual ActionSpecUp_Squid data overrides constructor 60/40/20
} as const;

/** spl::PlayerParam 이동 관련 캐시(+0xb0..+0x140). */
export interface PlayerParam {
  /** +0xb4/+0xb0/+0xb8 (WeaponSpeedType 0 Slow, 1 Mid, 2 Fast) */
  human: [number, number, number];
  /** +0xbc MoveVelRt_Shot */
  shotRate: number;
  /** +0xc4/+0xc0/+0xc8 */
  squid: [number, number, number];
  /** +0x100 적 잉크 위 점프 속도 */
  opJump: number;
  /** +0x104 적 잉크 위 이동 속도 */
  opMove: number;
  /** +0x108 적 잉크 위 사격 중 이동 속도 */
  opMoveShot: number;
  /** +0x140 Somersault_MoveVelKd */
  somersaultKd: number;
  /** +0x13c WallJumpChargeFrm, actual 45/18/5, same AP interpolation. */
  wallJumpChargeFrames: number;
  /** MainWeaponSetting WeaponSpeedType(0/1/2), WeaponAccType(0/1/2) */
  speedType: number;
  accType: number;
}

export interface GearAP {
  humanMove?: number;
  squidMove?: number;
  opInk?: number;
  actionUp?: number;
  ninja?: boolean;
}

const L = (t: readonly number[], p: number) => gearLerp(t[0], t[1], t[2], p);

/** 기어 AP(기본 0AP)와 무기 설정으로 캐시를 만든다. MoveVelRt_Shot 덮어쓰기(Overwrite_*)는 무기 설정에 값이 있을 때만. */
export function makePlayerParam(ap: GearAP = {}, weapon: { speedType?: number; accType?: number; shotRateOverwrite?: [number, number, number] } = {}): PlayerParam {
  const ph = apRate(ap.humanMove ?? 0);
  const ps = apRate(ap.squidMove ?? 0, ap.ninja ?? false);
  const po = apRate(ap.opInk ?? 0);
  const pa = apRate(ap.actionUp ?? 0);
  const shot = GEAR.ShotRate.map((v, i) => {
    const o = weapon.shotRateOverwrite?.[i];
    return o !== undefined && o >= 0 ? o : v;
  });
  return {
    human: [L(GEAR.HumanSlow, ph), L(GEAR.HumanMid, ph), L(GEAR.HumanFast, ph)],
    shotRate: L(shot, ph),
    squid: [L(GEAR.SquidSlow, ps), L(GEAR.SquidMid, ps), L(GEAR.SquidFast, ps)],
    opJump: L(GEAR.OpJump, po),
    opMove: L(GEAR.OpMove, po),
    opMoveShot: L(GEAR.OpMoveShot, po),
    somersaultKd: L(GEAR.SomersaultKd, pa),
    wallJumpChargeFrames: L(GEAR.WallJumpChargeFrames, pa),
    speedType: weapon.speedType ?? 1,
    accType: weapon.accType ?? 1,
  };
}
