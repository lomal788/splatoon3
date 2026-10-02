// 슈터 조준 흔들림·연사 타이머. 근거: docs/camera/aim_swerve.md, 발사 처리 0x7102583008(asm 0x71025839a8~0x7102583c64),
// 흔들림 각 0x7102580f98, 연사 타이머 0x7102551530, 대기 0x710258295c.
import { f32 } from "../fmath.ts";
import type { V3 } from "./move.ts";
import type { WeaponShooterParam } from "./params.ts";
import { SINCOS_TABLE } from "./sincos_table.ts";

const U32 = new Uint32Array(1);
const F32 = new Float32Array(U32.buffer);

function bitsToF32(b: number): number {
  U32[0] = b >>> 0;
  return F32[0];
}

/** 매치 공용 시드(탄 관리자 +0x120 / +0x124..+0x130). 원천 객체가 없으면 a..d = 1,2,3,4, sum = 10 (0x71016e2fd4). */
export interface MatchSeeds {
  a: number;
  b: number;
  c: number;
  d: number;
  /** +0x120 = 13a + 59b + 71c + 97d (원천 객체가 없으면 10) */
  sum: number;
}

export const DEFAULT_SEEDS: MatchSeeds = { a: 1, b: 2, c: 3, d: 4, sum: 10 };

export function seedsFrom(a: number, b: number, c: number, d: number): MatchSeeds {
  return { a: a >>> 0, b: b >>> 0, c: c >>> 0, d: d >>> 0, sum: (Math.imul(13, a) + Math.imul(59, b) + Math.imul(71, c) + Math.imul(97, d)) >>> 0 };
}

/** 발사 흔들림·패턴 바이트 시드(0x7102583a00~0x7102583ab4, 리셋 0x7102582e3c)의 첫 u32. f = max(GameFrame, 0) (+ 플레이어 번호×100). */
export function shotSeedU32(f: number, s: MatchSeeds): number {
  const M = 0x6c078965;
  let x = (f + Math.imul((s.b + s.a) >>> 0, 0x89)) >>> 0;
  x = (Math.imul((x ^ (x >>> 30)) >>> 0, M) + 1) >>> 0;
  const y = (Math.imul((x ^ (x >>> 30)) >>> 0, M) + Math.imul((s.c + s.b) >>> 0, 0x1c1) + 2) >>> 0;
  const z = (Math.imul((y ^ (y >>> 30)) >>> 0, M) + Math.imul((s.d + s.c) >>> 0, 0x233) + 3) >>> 0;
  let w = (Math.imul((z ^ (z >>> 30)) >>> 0, M) + Math.imul((s.d + s.a) >>> 0, 0x3df) + 4) >>> 0;
  let x0 = x;
  if ((x | y | z | w) === 0) {
    x0 = 1;
    w = 0x48077044;
  }
  const t = (x0 ^ (x0 << 11)) >>> 0;
  return (t ^ (t >>> 8) ^ w ^ (w >>> 19)) >>> 0;
}

/** 발사 흔들림 난수의 첫 float01 (0x7102583a00~0x7102583ad4). frame = max(GameFrame, 0). */
export function shotRandom01(frame: number, s: MatchSeeds): number {
  const u = shotSeedU32(frame < 0 ? 0 : frame, s);
  return f32(bitsToF32(((u >>> 9) | 0x3f800000) >>> 0) + -1);
}

/** bias 곡선 (0x7102583ad8~0x7102583b80). logf/expf 는 f64 계산 후 f32 반올림. */
export function biasCurve(u: number, b: number): number {
  const d = f32(b + -0.5);
  if (!(d < f32(-0.001)) && !(d > f32(0.001))) return u;
  const au = u < 0 ? f32(-u) : u;
  if (!(au >= f32(0.001))) return 0;
  if (!(b >= f32(0.001))) return au < f32(0.999) ? 0 : 1;
  const s12 = f32(f32(Math.log(b)) * f32(-1.442695));
  const p = f32(Math.exp(f32(f32(Math.log(au)) * s12)));
  return u < 0 ? f32(-p) : p;
}

/** sead 사인표 조회 (0x7102583bac~0x7102583bf8). */
export function sinCos(rad: number): [number, number] {
  const v = f32(f32(rad) * f32(6.8356525e8));
  const lo32 = Math.trunc(v) | 0;
  const idx = (lo32 >>> 24) & 0xff;
  const lo = lo32 & 0xffffff;
  const fr = f32(f32(lo) * f32(5.9604645e-8));
  const k = idx * 4;
  const s = f32(SINCOS_TABLE[k] + f32(SINCOS_TABLE[k + 1] * fr));
  const c = f32(SINCOS_TABLE[k + 2] + f32(fr * SINCOS_TABLE[k + 3]));
  return [s, c];
}

/** 월드 Y축 회전 (0x7102583bfc~0x7102583c64, 축 (0,1,0) 로드리게스 식 그대로). */
export function rotateY(aim: V3, rad: number, out: V3): V3 {
  const [sn, cs] = sinCos(rad);
  const x = aim[0], y = aim[1], z = aim[2];
  const s6 = f32(x * 0);
  const s7a = f32(y + s6);
  const s16 = f32(z * 0);
  const dot = f32(s16 + s7a);
  const s17 = f32(dot * 0);
  const s18 = f32(x - s17);
  const s19 = f32(y - dot);
  const s20 = f32(z - s17);
  const s1 = f32(y * 0);
  const c19 = f32(cs * s19);
  const s2 = f32(z - s1);
  const s5 = f32(s6 - s16);
  const s0 = f32(s1 - x);
  const c18 = f32(s17 + f32(cs * s18));
  const c7 = f32(dot + c19);
  const c3 = f32(s17 + f32(cs * s20));
  out[0] = f32(f32(s2 * sn) + c18);
  out[1] = f32(f32(s5 * sn) + c7);
  out[2] = f32(f32(s0 * sn) + c3);
  return out;
}

/** 흔들림 상태: bias(+0x8c), 점프 카운터(+0x88). */
export class Swerve {
  bias = 0;
  jumpFrames = 0;

  reset(): void {
    this.bias = 0;
    this.jumpFrames = 0;
  }

  /** vt40 0x7102580c4c 점프 시작 */
  onJump(p: WeaponShooterParam): void {
    this.jumpFrames = p.Jump_DegBiasEndFrame | 0;
  }

  /** 0x7102580f98 → [흔들림 각(도), 점프 bias]. gearRate = ReduceJumpSwerveRate 결과(기어 0 이면 0). */
  swerveAndJumpBias(p: WeaponShooterParam, gearRate = 0): [number, number] {
    const stand = f32(p.Stand_DegSwerve);
    const jumpRaw = f32(p.Jump_DegSwerve);
    const jump = f32(jumpRaw + f32(f32(stand - jumpRaw) * f32(gearRate)));
    if (this.jumpFrames < 1) return [stand, 0];
    const t = Math.min(f32(f32(this.jumpFrames) / f32((p.Jump_DegBiasEndFrame - p.Jump_DegBiasDecreaseStartFrame) | 0)), 1);
    const sw = f32(stand + f32(t * f32(jump - stand)));
    const mn = f32(p.Stand_DegBiasMin);
    const jb = f32(mn + f32(t * f32(f32(p.Jump_DegBiasMax) - mn)));
    return [sw, jb];
  }

  /** 발사 1회: 흔들린 방향과 각(rad) 반환 후 bias 누적. */
  fire(p: WeaponShooterParam, aim: V3, frame: number, seeds: MatchSeeds, out: V3, noSwerve = false): number {
    const [sw, jb] = this.swerveAndJumpBias(p);
    const rad = noSwerve ? 0 : f32(sw * f32(0.017453292));
    const r = shotRandom01(frame, seeds);
    const b = this.bias > jb ? this.bias : jb;
    const u = f32(f32(r + r) + -1);
    const ub = biasCurve(u, b);
    const ang = f32(rad * ub);
    rotateY(aim, ang, out);
    const nb = f32(f32(p.Stand_DegBiasKf) + this.bias);
    const mx = f32(p.Stand_DegBiasMax);
    this.bias = nb <= mx ? nb : mx;
    return ang;
  }

  /** 매 프레임 끝 (0x71025830d0~0x71025835c4). airFramesGe4 = 본체+0xc0 >= 4. */
  endFrame(p: WeaponShooterParam, remFramesToReady: number, triggerHeld: boolean, airFramesGe4: boolean): void {
    const d = f32(remFramesToReady + -1);
    if (d >= -0.001 && d <= 0.001 && !triggerHeld) this.bias = f32(this.bias - f32(p.Stand_DegBiasDecrease));
    const mn = f32(p.Stand_DegBiasMin);
    this.bias = mn <= this.bias ? this.bias : mn;
    const n = this.jumpFrames + (airFramesGe4 ? -1 : -2);
    this.jumpFrames = n < 0 ? 0 : n;
  }
}

/** 연사 타이머 (PlayerInkActionShooter+0x68 구조체, 0x7102551530). */
export class RepeatTimer {
  phase = 0;
  rem = 0;
  count = 0;
  c0 = 0;
  c1 = 0;
  c2 = 0;
  limit = 0x7fffffff;
  flag = false;

  update(repeatFrame: number): boolean {
    const c1o = this.c1, c0o = this.c0, c2o = this.c2;
    const c1 = (c1o < 2 ? 1 : c1o) - 1;
    const c0 = (c0o < 2 ? 1 : c0o) - 1;
    this.c0 = c0;
    this.c1 = c1;
    this.c2 = (c2o < 2 ? 1 : c2o) - 1;
    if (c0 !== 0 && c0o > 0) return false;
    if (this.limit <= this.count) return false;
    let ph = this.phase;
    if (c1 === 0 || (this.flag && ph < 1)) {
      const inc = f32(1 / f32(repeatFrame));
      ph = f32(inc + ph);
      let rem = f32(f32(1 - ph) / f32(1 / f32(repeatFrame)));
      if (rem <= 0) rem = 0;
      this.phase = ph;
      this.rem = rem;
    }
    let fire = 1;
    if (1 <= ph || f32(ph + -1) < -1e-5 || 1e-5 < f32(ph + -1)) {
      fire = ph;
      if (ph < 1) return false;
    } else this.phase = 1;
    if (c1 !== 0 && this.flag) return false;
    this.phase = f32(fire + -1);
    return true;
  }

  /** 0x710258295c 앞부분(위상·남은 프레임). reset=true 는 리셋 경로(param_2=1). */
  idle(repeatFrame: number, reset: boolean, locked: boolean): void {
    const inc = f32(1 / f32(repeatFrame));
    let ph = this.phase;
    if (!locked) {
      ph = f32(1 - inc);
      if (!reset) {
        const n = f32(inc + this.phase);
        if (n <= ph) ph = n;
      }
    }
    let rem = f32(f32(1 - ph) / inc);
    if (rem <= 0) rem = 0;
    this.phase = ph;
    this.rem = rem;
    if (!locked) {
      if (!reset) {
        this.c0 = (this.c0 < 2 ? 1 : this.c0) - 1;
        const c1 = this.c1 - 1;
        this.c1 = c1 <= 0 ? 0 : c1;
        this.c2 = (this.c2 < 2 ? 1 : this.c2) - 1;
      } else {
        this.count = 0;
        this.c0 = 0;
        this.c1 = 0;
        this.c2 = 0;
      }
    }
  }
}

export function f32bits(x: number): number {
  F32[0] = x;
  return U32[0];
}
