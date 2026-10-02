// 착탄 이펙트 분류. 근거: docs/effect_sound/effect_sound.md §3.5, effect_resources.md §3.1.
//   분배 0x71027b877c · 바닥 분류 0x71018b4f74 · 벽 기준 bss 0x71058cc928 (정적 초기화 0x71027b42a0)
import type { EmitMatrix } from "./particles.ts";

type V3 = [number, number, number];
const f32 = Math.fround;

/** 법선 y ≤ 이 값이면 벽 (≈ 50.1°) */
export const WALL_NY = f32(0.64144969);
/** a < T0 → Floor, a ≥ T1 → Dist, 그 사이 Near (0x71018b2278) */
export const T0 = f32(0.5235988);
export const T1 = f32(1.0471976);
const HALF_PI = f32(1.5707964);

export const FLOOR_ESETS: [string, string][] = [
  // [p = 0 (칠 불가), p = 1]
  ["CmnNPFloorSplash1Emit", "CmnFloorSplash1Emit"],
  ["CmnNPFloorSplashNear1Emit", "CmnFloorSplashNear1Emit"],
  ["CmnNPFloorSplashDist1Emit", "CmnFloorSplashDist1Emit"],
];
export const WALL_ESETS: [string, string] = ["CmnNpWallSplash1Emit", "CmnWallSplash1Emit"];
/** E2 코드 파티클 Hit / SplashWater 슬롯 이미터셋 */
export const HIT_ESET = "WpCmnHit";
export const WATER_ESET = "WpCmnWaterSplash";

/** θ = atan2(|v̂ × n|, v̂ · n), 0..π (f32) */
export function hitTheta(v: V3, n: V3): number {
  const l = Math.hypot(v[0], v[1], v[2]);
  if (!(l > 0)) return 0;
  const x = v[0] / l, y = v[1] / l, z = v[2] / l;
  const cx = y * n[2] - z * n[1], cy = z * n[0] - x * n[2], cz = x * n[1] - y * n[0];
  return f32(Math.atan2(f32(Math.hypot(cx, cy, cz)), f32(x * n[0] + y * n[1] + z * n[2])));
}

/** 0x71018b4f74: a = π/2 − |π/2 − θ|, kind 0 Floor / 1 Near / 2 Dist */
export function splashKind(theta: number): 0 | 1 | 2 {
  const a = f32(HALF_PI - Math.abs(f32(HALF_PI - theta)));
  return a < T0 ? 0 : a >= T1 ? 2 : 1;
}

export function isWall(n: V3): boolean {
  return f32(n[1]) <= WALL_NY;
}

export interface SplashPick {
  eset: string;
  wall: boolean;
  kind: number;
  theta: number;
}

/** E2 Splash(0) 분기: 벽이면 벽 슬롯, 아니면 θ 로 바닥 3종. 속도 0 이면 θ = 0 → kind 0. */
export function pickSplash(n: V3, v: V3 | null, paintable: boolean): SplashPick {
  const p = paintable ? 1 : 0;
  if (isWall(n)) return { eset: WALL_ESETS[p], wall: true, kind: -1, theta: 0 };
  const theta = v && Math.hypot(v[0], v[1], v[2]) > 0 ? hitTheta(v, n) : 0;
  const kind = splashKind(theta);
  return { eset: FLOOR_ESETS[kind][p], wall: false, kind, theta };
}

function norm(a: V3): V3 {
  const l = Math.hypot(a[0], a[1], a[2]);
  return l > 0 ? [a[0] / l, a[1] / l, a[2] / l] : [0, 0, 0];
}
function cross(a: V3, b: V3): V3 {
  return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
}

/**
 * Y 축을 법선으로 두는 행렬. 진행 방향 v 가 있으면 면에 투영한 방향을 Z 로 둔다.
 * 원본 행렬 축 배치(0x71027b877c 본문)는 정리하지 않았다 [추정]: Hit/SplashWater 는 "Y축을 n으로 돌리는 회전" [판독],
 * 바닥은 v·n 회전, 벽은 pitch = asin(n.y)·yaw = n 의 XZ 방향.
 */
export function normalMatrix(pos: V3, n: V3, v: V3 | null): EmitMatrix {
  const y = norm(n);
  let z: V3 | null = null;
  if (v) {
    const d = v[0] * y[0] + v[1] * y[1] + v[2] * y[2];
    const t: V3 = [v[0] - d * y[0], v[1] - d * y[1], v[2] - d * y[2]];
    if (Math.hypot(t[0], t[1], t[2]) > 1e-6) z = norm(t);
  }
  if (!z) {
    const up: V3 = Math.abs(y[1]) < 0.99 ? [0, 1, 0] : [0, 0, 1];
    const x0 = norm(cross(up, y));
    z = norm(cross(x0, y));
  }
  const x = norm(cross(y, z));
  return { o: pos, x, y, z };
}

/**
 * 벽 행렬 (0x71027b877c, 법선 y ≤ 0.64144969 분기) [판독]:
 *   A = asin(n.y), B = acos(−n.z/|n_xz|) (n.x ≥ 0 이면 −B), R = Ry(B)·Rx(A) (행 우선 3×4 에 위치)
 *   → 로컬 −Z = n, 로컬 Y = 벽면 위쪽. n = (0,0,−1) 이면 단위 행렬.
 * sin/cos 함수(0x7103e9be40/be30)의 구분은 n=(0,0,−1)→단위 행렬이 되는 쪽으로 정했다.
 */
export function wallMatrix(pos: V3, n: V3): EmitMatrix {
  const f = Math.fround;
  const ny = Math.max(-1, Math.min(1, n[1]));
  const A = f(Math.asin(ny));
  const l = Math.hypot(n[0], n[2]);
  let B = 0;
  if (l > 0) {
    B = Math.acos(Math.max(-1, Math.min(1, -n[2] / l)));
    if (-n[0] / l <= 0) B = -B;
  }
  const sA = Math.sin(A), cA = Math.cos(A), sB = Math.sin(B), cB = Math.cos(B);
  // 열 = 축
  return { o: pos, x: [cB, 0, -sB], y: [sA * sB, cA, sA * cB], z: [sB * cA, -sA, cA * cB] };
}

/**
 * 바닥 스플래시 행렬 (0x71027b877c, |v| > 0 분기 → 0x71018b4f74 의 info) [판독, 디컴파일 그대로 옮김]:
 *   a1 = asin(−n.x), a2 = ±acos(n.y/|n_yz|) (n.z ≤ 0 이면 −), 
 *   c = v × n (|v·n| ≤ 0.99999, v 는 정규화 전 속도) 아니면 (0,0,1), d = n × c, e = Ẑ × n, g = n × e,
 *   a3 = atan2(|d × g|, g·d) (e·d ≤ 0 이면 +, 아니면 −)
 *   축 X = (C3C1, C3S1C2+S3S2, C3S1S2−S3C2), Y = (−S1, C1C2, C1S2), Z = (S3C1, S3S1C2−C3S2, S3S1S2+C3C2)
 * n = (0,1,0) 이면 Y = n, Z = 면에 투영한 v 방향(Ry(a3)). 열/행 배치는 n = 위쪽일 때 회전 행렬이 되는 쪽으로 정했다.
 */
export function floorMatrix(pos: V3, n: V3, v: V3): EmitMatrix {
  const [nx, ny, nz] = n;
  const a1 = Math.asin(Math.max(-1, Math.min(1, -nx)));
  const lyz = Math.hypot(ny, nz);
  let a2 = 0;
  if (lyz > 0) {
    a2 = Math.acos(Math.max(-1, Math.min(1, ny / lyz)));
    if (nz / lyz <= 0) a2 = -a2;
  }
  let c: V3 = [0, 0, 1];
  if (Math.abs(v[0] * nx + v[1] * ny + v[2] * nz) <= 0.99999) c = cross(v, n);
  const d = cross(n, c);
  const e: V3 = [-ny, nx, 0];
  const g = cross(n, e);
  const dg = cross(d, g);
  let a3 = Math.atan2(Math.hypot(dg[0], dg[1], dg[2]), g[0] * d[0] + g[1] * d[1] + g[2] * d[2]);
  if (!(e[0] * d[0] + e[1] * d[1] + e[2] * d[2] <= 0)) a3 = -a3;
  const S1 = Math.sin(a1), C1 = Math.cos(a1), S2 = Math.sin(a2), C2 = Math.cos(a2), S3 = Math.sin(a3), C3 = Math.cos(a3);
  return {
    o: pos,
    x: [C3 * C1, C3 * S1 * C2 + S3 * S2, C3 * S1 * S2 - S3 * C2],
    y: [-S1, C1 * C2, C1 * S2],
    z: [S3 * C1, S3 * S1 * C2 - C3 * S2, S3 * S1 * S2 + C3 * C2],
  };
}

/** 속도 0 바닥: 고정 행렬(bss 0x71058237b0, 런타임 초기화 — 값 미확인) + 위치. 단위 회전으로 둔다 [추정]. */
export function identityFloor(pos: V3): EmitMatrix {
  return { o: pos, x: [1, 0, 0], y: [0, 1, 0], z: [0, 0, 1] };
}
