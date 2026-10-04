// 담당: [physics] — native 강체 솔버의 플레이어(무회전·마찰0·반발0) 경로. 식은 원본 명령 순서 그대로 f32 로 반올림한다.
// 근거: docs/physics/phive_controller.md §6.10.1~6.10.5, analysis/completion/r8/contact_kernel_support.md §4~7.2,
// solver_info_support.md, contact_properties_support.md. 함수마다 원본 주소와 확정 수준을 적는다.
// 접촉 생성(실제 메시 manifold·TOI)은 여기 없다 — PHY05 [미확정], core/player/body.ts 의 근사가 행을 만든다.
import { f32 } from "../fmath.ts";

/** −2^-23. 침투 보정의 old 비교 임계 [실행]. */
export const BIAS_THRESHOLD = -(2 ** -23);
/** native 선속도 setter 의 축 허용차 2^-23 [실행]. */
export const VEL_EPS = 2 ** -23;
const VEL_FAC = f32(1 - f32(2 * VEL_EPS));

/** ARM FMIN/FMAX (유한 입력): 같은 0 이면 FMIN 은 −0, FMAX 는 +0 우선. */
export function fmin(a: number, b: number): number {
  if (a === 0 && b === 0) return Object.is(a, -0) || Object.is(b, -0) ? -0 : 0;
  return a < b ? a : b;
}
export function fmax(a: number, b: number): number {
  if (a === 0 && b === 0) return Object.is(a, -0) && Object.is(b, -0) ? -0 : 0;
  return a > b ? a : b;
}

// ---------------------------------------------------------------------------------------------
// solverInfo (World+0x530) — 0x7100a452fc(tau, damp) → 0x7100a4536c(dt, …, sub, micro) [실행 1,024사례]
// ---------------------------------------------------------------------------------------------

export interface SolverInfo {
  /** +0x10 dt */
  dt: number;
  /** +0x74 1/sub (carry·finalize) */
  invSub: number;
  /** +0xb0 tau/damp (carry·finalize) */
  tauDamp: number;
  /** +0xc0 damp/tau (finalize) */
  dampTau: number;
  /** +0xd0 gamma = (tau/damp)·(1/dt)·sub (침투 target) */
  gamma: number;
  /** +0x40 (1/dt)·sub */
  invSubDt: number;
  sub: number;
}

/** 게임 world 설명자: substep 8 / microstep 1 / tau 0.6 / damp 1 [판독+실행: phive_controller §6.10.1]. */
export const WORLD_SUBSTEPS = 8;
export const WORLD_MICROSTEPS = 1;
export const WORLD_TAU = f32(0.6000000238418579);
export const WORLD_DAMP = 1;
/** 월드 dt = f32(1/60) [판독: phive_controller §6.4]. */
export const WORLD_DT = f32(1 / 60);

export function makeSolverInfo(tau = WORLD_TAU, damp = WORLD_DAMP, dt = WORLD_DT, sub = WORLD_SUBSTEPS): SolverInfo {
  const ratio = f32(tau / damp);
  const inv = f32(1 / dt);
  const invSubDt = f32(inv * f32(sub));
  return {
    dt,
    invSub: f32(1 / f32(sub)),
    tauDamp: ratio,
    dampTau: f32(damp / tau),
    gamma: f32(ratio * invSubDt),
    invSubDt,
    sub,
  };
}

// ---------------------------------------------------------------------------------------------
// 접촉 cache 계수 0x7100a21ae4: quality+2c bit7 == 0 → C+C0 = 1, C+C8 = −0.05 [실행]
// ---------------------------------------------------------------------------------------------
export const CACHE_C0 = 1;
export const CACHE_C8 = f32(-0.05);

/** 압축 inverse mass: 원본 SHLL #16 으로 상위 16비트 복원. mass 100 → 0x3c24 → 0.010009765625 [실행]. */
export function decompressInvMass(bits16: number): number {
  const b = new DataView(new ArrayBuffer(4));
  b.setUint32(0, (bits16 & 0xffff) << 16, true);
  return b.getFloat32(0, true);
}
export const PLAYER_INV_MASS = decompressInvMass(0x3c24);

/** 단일 몸체 행 유효 질량 0a16cd8..0a16d14: wi = f32(invIi·f32(Ai²)), den = f32(f32(w0+w1)+f32(w2+invMass)), M = f32(damp/den) [실행]. */
export function effectiveMass(angJ: ArrayLike<number>, invI: ArrayLike<number>, invMass: number, damp = WORLD_DAMP): number {
  const w0 = f32(invI[0] * f32(angJ[0] * angJ[0]));
  const w1 = f32(invI[1] * f32(angJ[1] * angJ[1]));
  const w2 = f32(invI[2] * f32(angJ[2] * angJ[2]));
  const den = f32(f32(w0 + w1) + f32(w2 + invMass));
  return f32(damp / den);
}

export interface BiasOut {
  old: number;
  carry: number;
  target: number;
}

/**
 * 침투 보정 target 0x7100a15b70 의 0a16d78..0a16e24 (단일 몸체), 같은 식 0a16670..0a17548 (두 몸체) [실행 4,097사례].
 * old = cache 저장 depth, carry = 보정 누적, d = 현재 depth(native contact+30), v·pred = 예측 항(flag==0 일 때만),
 * flag = nativeManifold+92 바이트(이름·producer [미확정]).
 */
export function contactBias(old: number, carry: number, d: number, v: number, flag: number, pred: number,
  dt: number, c0: number, k: number, gamma: number, ratio = 2): BiasOut {
  let p = flag !== 0 ? carry : f32(carry + f32(v * pred));
  const cap = f32(dt * c0);
  const ng = f32(-gamma);
  if (old >= BIAS_THRESHOLD && d > f32(p - cap)) return { old, carry: d, target: f32(d * ng) };
  const t = fmax(0, fmin(f32(d * k), cap));
  const b = flag !== 0 ? t : fmin(f32(old * k), cap);
  const diff = f32(d - old);
  p = f32(fmin(p, 0) - diff);
  const limit = f32(cap + f32(ratio * b));
  const select = p > limit ? p : 0;
  const nextOld = f32(f32(old + b) - select);
  const nextCarry = f32(f32(diff - b) + select);
  return { old: fmin(fmax(nextOld, f32(d - b)), BIAS_THRESHOLD), carry: nextCarry, target: f32(nextCarry * ng) };
}

export interface NormalRowOut {
  lambda: number;
  delta: number;
  skip: boolean;
}

/**
 * 단일 몸체 법선 충격량 0a1a98c..0a1abd0 [실행 4,097사례]. L(선속도)·W(각속도)를 제자리에서 갱신한다.
 * invI[0..2] = inverse inertia, invI[3] = 압축 inverse mass.
 */
export function normalRow(L: number[] | Float32Array, W: number[] | Float32Array, N: ArrayLike<number>, A: ArrayLike<number>,
  M: number, invI: ArrayLike<number>, lam: number, target: number): NormalRowOut {
  const r0 = f32(f32(L[0] * N[0]) + f32(W[0] * A[0]));
  const r1 = f32(f32(L[1] * N[1]) + f32(W[1] * A[1]));
  const r2 = f32(f32(L[2] * N[2]) + f32(W[2] * A[2]));
  const dot = f32(f32(r0 + r1) + r2);
  if (dot >= target && lam === 0) return { lambda: lam, delta: 0, skip: true };
  const d = fmax(f32(-lam), f32(f32(target - dot) * M));
  const dlm = f32(d * invI[3]);
  for (let i = 0; i < 3; i++) {
    L[i] = f32(L[i] + f32(N[i] * dlm));
    W[i] = f32(W[i] + f32(A[i] * f32(d * invI[i])));
  }
  return { lambda: f32(lam + d), delta: d, skip: false };
}

export interface TwoBodyRow {
  /** 행 +0..+0xf: JA xyz, 유효 질량 */
  ja: ArrayLike<number>;
  /** 행 +0x10..+0x1f: JB xyz, target */
  jb: ArrayLike<number>;
}

/**
 * 같은 manifold 의 여러 행 순차 반복 0a18d8c..0a1911c (두 몸체 경로) [실행 1,025사례/3,074행].
 * 앞 행이 바꾼 속도로 다음 행을 계산한다. lam 배열을 제자리 갱신하고 누적 delta 를 돌려준다.
 */
export function normalRowsTwoBody(LA: number[], LB: number[], WA: number[], WB: number[], N: ArrayLike<number>,
  rows: TwoBodyRow[], lam: number[], IA: ArrayLike<number>, IB: ArrayLike<number>): number {
  let acc = 0;
  for (let k = 0; k < rows.length; k++) {
    const JA = rows[k].ja, JB = rows[k].jb, L0 = lam[k];
    let dot = 0;
    const r: number[] = [0, 0, 0];
    for (let i = 0; i < 3; i++) r[i] = f32(f32(f32(LA[i] - LB[i]) * N[i]) + f32(f32(WA[i] * JA[i]) + f32(WB[i] * JB[i])));
    dot = f32(f32(r[0] + r[1]) + r[2]);
    const skip = dot >= JB[3] && L0 === 0;
    const d = skip ? 0 : fmax(f32(-L0), f32(f32(JB[3] - dot) * JA[3]));
    lam[k] = f32(L0 + d);
    if (!skip) {
      for (let i = 0; i < 4; i++) {
        const n = i < 3 ? N[i] : (N[3] ?? 0);
        LA[i] = f32(LA[i] + f32(n * f32(d * IA[3])));
        LB[i] = f32(LB[i] - f32(n * f32(d * IB[3])));
        WA[i] = f32(WA[i] + f32(f32(d * IA[i]) * JA[i]));
        WB[i] = f32(WB[i] + f32(f32(d * IB[i]) * JB[i]));
      }
      acc = f32(acc + d);
    }
  }
  return acc;
}

// ---------------------------------------------------------------------------------------------
// motion 속도·적분
// ---------------------------------------------------------------------------------------------

function f32bits(x: number): number {
  const b = new DataView(new ArrayBuffer(4));
  b.setFloat32(0, x, true);
  return b.getUint32(0, true);
}
const QNAN = (() => { const b = new DataView(new ArrayBuffer(4)); b.setUint32(0, 0x7fc00000, true); return b.getFloat32(0, true); })();

/**
 * game stage 선속도 → native motion+60 setter (0x7103c50c7c → 0x71009d9e54) [실행 1,044사례].
 * 모든 축 차이가 2^-23 이하면 쓰지 않는다. 길이² > cap² 이면 cap·(1/√n)·(1−2·2^-23) 배.
 */
export function nativeSetLinear(old: Float32Array, v: ArrayLike<number>, cap: number): void {
  let same = true;
  for (let j = 0; j < 3; j++) if (!(Math.abs(f32(v[j] - old[j])) <= VEL_EPS)) same = false;
  if (same) return;
  const x = f32(v[0]), y = f32(v[1]), z = f32(v[2]);
  const n = f32(f32(f32(x * x) + f32(y * y)) + f32(z * z));
  if (n <= f32(cap * cap)) { old[0] = x; old[1] = y; old[2] = z; return; }
  if (((f32bits(n) ^ 0xffffffff) & 0x7fc00000) === 0) return;
  const inv = f32(1 / f32(Math.sqrt(n)));
  if (((f32bits(inv) ^ 0xffffffff) & 0x7fc00000) === 0) return;
  const k = f32(f32(cap * inv) * VEL_FAC);
  const o = [f32(x * k), f32(y * k), f32(z * k)];
  for (let j = 0; j < 3; j++) old[j] = Number.isNaN(o[j]) ? QNAN : o[j];
}

/**
 * 초기 current/baseline 0x71009d4ba8 [실행 1,024사례]: current = v + (압축 invMass ≠ 0 ? f32(subgravity·scale) : 0), baseline = 0.
 * 플레이어 특수 MotionProperties13 은 GravityScale 0 [실행: character_controller §4.2].
 */
export function initialCurrent(out: Float32Array, v: ArrayLike<number>, subGravity: ArrayLike<number>, scale: number, invMassBits: number): void {
  for (let j = 0; j < 3; j++) out[j] = f32(v[j] + (invMassBits ? f32(subGravity[j] * scale) : 0));
}

function capDelta(dx: number, dy: number, dz: number, cap: number, finalize: boolean): [number, number, number] {
  const n = f32(f32(f32(dx * dx) + f32(dy * dy)) + f32(dz * dz));
  if (n > f32(cap * cap)) {
    const s = f32(Math.sqrt(n));
    const k = finalize ? f32(f32(1 / s) * cap) : f32(cap / s);
    return [f32(dx * k), f32(dy * k), f32(dz * k)];
  }
  return [dx, dy, dz];
}

/**
 * carry 0x7100a4b514 (normal 단계 사이, 마지막 제외) [실행 2,048사례]:
 * delta = cap(current − baseline), baseline' = baseline + delta·(tau/damp), current' = (delta + baseline') + subgravity·propertyScale.
 * cap 은 cap/√n 순서.
 */
export function carryStep(cur: Float32Array, base: Float32Array, cap: number, tauDamp: number, g: ArrayLike<number>): void {
  const d = capDelta(f32(cur[0] - base[0]), f32(cur[1] - base[1]), f32(cur[2] - base[2]), cap, false);
  for (let j = 0; j < 3; j++) {
    const nb = f32(base[j] + f32(d[j] * tauDamp));
    base[j] = nb;
    cur[j] = f32(f32(d[j] + nb) + g[j]);
  }
}

/**
 * finalize 0x7100a4b8c8 [실행 2,048사례]: 저장 속도 = cap(current − baseline) (cap 은 (1/√n)·cap 순서),
 * 위치용 속도 = f32(f32(baseline + f32(delta·tau/damp))·f32(invSub·damp/tau)), COM64 += double(f32(위치용 속도·dt)).
 */
export function finalizeStep(cur: Float32Array, base: Float32Array, com: Float64Array, vel: Float32Array, info: SolverInfo, cap: number,
  comVel?: Float32Array): void {
  const d = capDelta(f32(cur[0] - base[0]), f32(cur[1] - base[1]), f32(cur[2] - base[2]), cap, true);
  const factor = f32(info.invSub * info.dampTau);
  for (let j = 0; j < 3; j++) {
    vel[j] = d[j];
    const e = f32(f32(base[j] + f32(d[j] * info.tauDamp)) * factor);
    if (comVel) comVel[j] = e;
    com[j] = com[j] + f32(e * info.dt);
  }
}

/** COM → 몸체 원점 0x71009d5b68 (회전 identity) [실행 1,024사례]: origin = f32(COM64 − center), 잔차 = f32(origin64 − origin32). */
export function poseFromCom(com: Float64Array, center: ArrayLike<number>, origin: Float32Array, residual: Float32Array): void {
  for (let j = 0; j < 3; j++) {
    const o = com[j] - f32(center[j]);
    const of = f32(o);
    origin[j] = of;
    residual[j] = f32(o - of);
  }
}

// ---------------------------------------------------------------------------------------------
// 한 물리 스텝: 초기 → normal8/carry7 → finalize → pose (단일 몸체, 정적 상대)
// ---------------------------------------------------------------------------------------------

export interface SolverRow {
  /** 접촉 법선(상대 → 몸체, 단위, f32) */
  n: Float32Array;
  /** 행 target 속도(유닛/초) */
  target: number;
  /** 유효 질량 */
  mass: number;
  /** 누적 lambda (프레임 시작 0) */
  lambda: number;
}

export interface MotionState {
  /** native motion+0x10 COM (double) */
  com: Float64Array;
  /** native motion+0x60 저장 선속도(유닛/초) */
  vel: Float32Array;
  /** nativeBody+0x30 원점 / +0x40 잔차 */
  origin: Float32Array;
  residual: Float32Array;
  /** nativeBody+0xc.. local COM offset */
  center: Float32Array;
}

const CUR = new Float32Array(3), BASE = new Float32Array(3), ANG = [0, 0, 0], ZERO_A = [0, 0, 0], ZERO_G = [0, 0, 0];
const GS = [0, 0, 0];

export interface StepMotionOpts {
  /** solverInfo+0x90 subgravity(= gravity·dt/sub). 플레이어 MotionProperties13 은 GravityScale 0 이라 기본 0 */
  subGravity?: ArrayLike<number>;
  gravityScale?: number;
  /** 위치용 실효 속도 출력(진단) */
  comVel?: Float32Array;
}

/**
 * 플레이어 몸체 1 스텝. 실제 MT 원본 graph: 한 프레임 normal kernel 8회, 그 사이 carry 7회, 마지막 finalize 1회 [실행].
 * 각속도·관성 0, 마찰·반발 0. invI = (0,0,0,invMass). 행은 한 프레임 동안 같은 target 을 쓴다(Jacobian 은 프레임마다 1회 생산).
 */
export function stepMotion(m: MotionState, rows: SolverRow[], info: SolverInfo, cap: number, invMass: number, opts: StepMotionOpts = {}): void {
  const invI = [0, 0, 0, invMass];
  const sg = opts.subGravity ?? ZERO_G, gs = opts.gravityScale ?? 0;
  for (let j = 0; j < 3; j++) GS[j] = f32(sg[j] * gs);
  initialCurrent(CUR, m.vel, sg, gs, 0x3c24);
  BASE[0] = 0; BASE[1] = 0; BASE[2] = 0;
  for (const r of rows) r.lambda = 0;
  for (let s = 0; s < info.sub; s++) {
    for (let micro = 0; micro < WORLD_MICROSTEPS; micro++) {
      for (const r of rows) {
        ANG[0] = 0; ANG[1] = 0; ANG[2] = 0;
        const o = normalRow(CUR, ANG, r.n, ZERO_A, r.mass, invI, r.lambda, r.target);
        r.lambda = o.lambda;
      }
    }
    if (s < info.sub - 1) carryStep(CUR, BASE, cap, info.tauDamp, GS);
  }
  finalizeStep(CUR, BASE, m.com, m.vel, info, cap, opts.comVel);
  poseFromCom(m.com, m.center, m.origin, m.residual);
}
