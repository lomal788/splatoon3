// 발사 속도·생성 정보. 근거: docs/weapon/shooter_bullet.md §5.5, 초기 속도 0x71026beed0(asm 연산 순서),
// 생성 정보 채우기 0x71025823b0, 분할 인덱스 순열 표 0x7104a9b0a1.
import { f32 } from "../fmath.ts";
import type { V3 } from "./move.ts";
import type { AdditionParam } from "./params.ts";
import { sinCos } from "./swerve.ts";

/** 0x71026beed0: d = 조준(흔들림 반영) 단위벡터, p = 플레이어 최종 속도(본체+0xe4), a = 조준 기준 축. */
export function initialVelocity(speed: number, d: V3, p: V3, a: V3, A: AdditionParam, guide: boolean, out: V3): V3 {
  const s = f32(speed);
  const t = f32(f32(f32(p[0] * a[0]) + f32(a[1] * 0)) + f32(p[2] * a[2]));
  let yr: number;
  if (p[1] > 0) yr = f32(A.YPlusRate);
  else if (guide && A.GuideYMinusZero) yr = 0;
  else yr = f32(A.YMinusRate);
  const xr = f32(A.XRate), zr = f32(A.ZRate);
  const pax = f32(a[0] * t), pay = f32(a[1] * t), paz = f32(a[2] * t);
  const vyRaw = f32(p[1] * yr);
  const yMax = f32(A.YMax);
  const vy = vyRaw > yMax ? yMax : vyRaw;
  out[0] = f32(f32(f32(d[0] * s) + f32(f32(p[0] - pax) * xr)) + f32(pax * zr));
  out[1] = f32(f32(f32(f32(d[1] * s) + f32(f32(0 - pay) * xr)) + f32(pay * zr)) + vy);
  out[2] = f32(f32(f32(d[2] * s) + f32(f32(p[2] - paz) * xr)) + f32(paz * zr));
  return out;
}

/** spl__BulletShotDirParam (SplPlayer spl__BulletShotDirAllInkActionParam 에 "Shooter" 항목이 없어 코드 기본값 [데이터]). */
export interface ShotDirParam {
  PitchDegMin: number;
  PitchDegHorizon: number;
  PitchDegMax: number;
  BezierKMin: number;
  BezierKHor: number;
  BezierKMax: number;
}

export const SHOT_DIR_DEFAULT: ShotDirParam = {
  PitchDegMin: -70, PitchDegHorizon: 5, PitchDegMax: 75, BezierKMin: 0.17800000309944153, BezierKHor: 0.17000000178813934, BezierKMax: 0.15199999511241913,
};

/** 0x71058bdeb8..+0xc0 총구 오프셋(옆, 위, 앞) [실행(정적 초기화 에뮬)]. */
export const MUZZLE_OFFSET: V3 = [f32(-0.24), 0, f32(0.18)];

/**
 * 생성 위치 0x7102552170 (S 는 0x7102583008 이 구성: P = 본체+0x58, L = 본체+0x54c, p = 본체+0x558, b40 = b41 = 1).
 * weapon_spawnpos_emu.py 와 17/17 비트 일치한 식을 연산 순서 그대로 옮김.
 */
export function spawnPosition(P: V3, L: V3, p: number, sd: ShotDirParam, off: V3, out: V3): V3 {
  const z = 0;
  const ox = off[0], oz = off[2];
  let oy = off[1];
  if (p < 0) oy = f32(oy - f32(f32(f32(0.6) - oy) * p));
  const t1 = f32(L[1] * z), t2 = f32(L[0] * z);
  let Rx = f32(L[2] - t1), Ry = f32(t2 - f32(L[2] * z)), Rz = f32(t1 - L[0]);
  const ln = f32(Math.sqrt(f32(f32(Rz * Rz) + f32(f32(Rx * Rx) + f32(Ry * Ry)))));
  if (ln > 0) {
    const inv = f32(1 / ln);
    Rx = f32(Rx * inv);
    Ry = f32(inv * Ry);
    Rz = f32(Rz * inv);
  }
  const a = f32(Rx * z), c = f32(Ry * z);
  const Fy = f32(f32(Rz * z) - a), Fx = f32(c - Rz), Fz = f32(Rx - c);
  const aMin = f32(sd.PitchDegMin), aHor = f32(sd.PitchDegHorizon), aMax = f32(sd.PitchDegMax);
  const kMin = f32(sd.BezierKMin), kHor = f32(sd.BezierKHor), kMax = f32(sd.BezierKMax);
  const b1k = f32(f32(aMax - aMin) * kHor);
  let c0: number, c1: number, c2: number, p3: number, B1: number, B2: number, end: number;
  if (p > 0) {
    const t = f32(1 - p);
    const m = f32(f32(p * 3) * t);
    const E = f32(f32(aMax - aHor) * kMax);
    B2 = f32(aMax - f32(E + E));
    B1 = f32(aHor + b1k);
    c0 = f32(t * f32(t * t));
    c1 = f32(t * m);
    c2 = f32(p * m);
    p3 = f32(p * f32(p * p));
    end = aMax;
  } else {
    const r = f32(p + 1);
    const m = f32(f32(p * -3) * r);
    const E = f32(f32(aHor - aMin) * kMin);
    B2 = f32(aMin + f32(E + E));
    B1 = f32(aHor - b1k);
    c0 = f32(r * f32(r * r));
    c1 = f32(r * m);
    c2 = f32(m * f32(-p));
    p3 = f32(f32(p * p) * f32(-p));
    end = aMin;
  }
  const deg = f32(f32(end * p3) + f32(f32(f32(aHor * c0) + f32(B1 * c1)) + f32(c2 * B2)));
  const th = f32(deg * f32(-0.017453292));
  const [sn, cs] = sinCos(th);
  const Ux = f32(f32(Fx * sn) + f32(cs * z)), Uy = f32(cs + f32(Fy * sn)), Uz = f32(f32(Fz * sn) + f32(cs * z));
  const Wx = f32(f32(Fx * cs) - f32(sn * z)), Wy = f32(f32(Fy * cs) - sn), Wz = f32(f32(Fz * cs) - f32(sn * z));
  const y0 = f32(P[1] + f32(1.1));
  out[0] = f32(P[0] + f32(f32(oz * Wx) + f32(f32(ox * Rx) + f32(oy * Ux))));
  out[1] = f32(y0 + f32(f32(oz * Wy) + f32(f32(ox * Ry) + f32(oy * Uy))));
  out[2] = f32(P[2] + f32(f32(oz * Wz) + f32(f32(ox * Rz) + f32(oy * Uz))));
  return out;
}

/** 조준 기준 축 a = −Z, Z = normalize(카메라 위치 − 주시점) (PlayerCamera+0x3c 기저, 0x71024df4e8). 거의 수직이면 null(이전 값 유지). */
export function cameraAxis(camPos: V3, at: V3, out: V3): V3 | null {
  const dx = f32(camPos[0] - at[0]), dy = f32(camPos[1] - at[1]), dz = f32(camPos[2] - at[2]);
  const ln = f32(Math.sqrt(f32(f32(f32(dx * dx) + f32(dy * dy)) + f32(dz * dz))));
  let zx = dx, zy = dy, zz = dz;
  if (ln > 0) {
    const inv = f32(1 / ln);
    zx = f32(dx * inv);
    zy = f32(dy * inv);
    zz = f32(dz * inv);
  }
  const d = f32(f32(zy + f32(zx * 0)) + f32(zz * 0));
  if (!(Math.abs(d) <= f32(0.99999988))) return null;
  out[0] = f32(-zx);
  out[1] = f32(-zy);
  out[2] = f32(-zz);
  return out;
}

/** 0x71025823b0 로컬 발사: dir = normalize(v), speed = |v| (len² = (x²+y²)+z²). */
export function dirSpeed(v: V3, dir: V3): number {
  const l2 = f32(f32(f32(v[0] * v[0]) + f32(v[1] * v[1])) + f32(v[2] * v[2]));
  const l = f32(Math.sqrt(l2));
  let x = v[0], y = v[1], z = v[2];
  if (l > 0) {
    const inv = f32(1 / l);
    x = f32(x * inv);
    y = f32(y * inv);
    z = f32(z * inv);
  }
  dir[0] = x;
  dir[1] = y;
  dir[2] = z;
  return l;
}

/** 표 0x7104a9b0a1: 분할 수 N(행)마다 16바이트, 앞 N바이트가 0..N-1 순열. N ≥ 16 이면 0행. */
const PERM_ROWS: number[][] = [
  [], [0], [1, 0], [2, 0, 1], [3, 1, 2, 0], [4, 2, 0, 3, 1], [5, 1, 4, 2, 0, 3], [6, 1, 4, 2, 5, 0, 3],
  [7, 4, 1, 6, 3, 0, 5, 2], [8, 5, 0, 3, 6, 2, 7, 4, 1], [9, 2, 5, 8, 1, 4, 7, 0, 3, 6], [10, 2, 5, 8, 0, 3, 6, 9, 1, 4, 7],
  [11, 2, 7, 10, 4, 1, 9, 6, 3, 0, 8, 5], [12, 4, 9, 1, 6, 11, 3, 8, 0, 5, 10, 2, 7], [13, 2, 7, 10, 0, 3, 6, 12, 9, 4, 1, 11, 8, 5],
  [14, 3, 8, 11, 4, 7, 12, 0, 5, 10, 1, 6, 13, 2, 9],
];

/** 표 값 그대로(행 밖·열 밖은 0) — 0x7102583008 의 주소 계산과 같은 범위 처리. */
export function permAt(n: number, i: number): number {
  const row = n >>> 0 < 16 ? PERM_ROWS[n] : PERM_ROWS[0];
  const col = i >>> 0 < 16 ? i : 0;
  return row[col] ?? 0;
}
