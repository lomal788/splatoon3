// 탄 도색 모양: 반폭 w·깊이 비율 ds → 사각형 (W, L)·패턴·중심 이동.
// 근거: docs/paint/paint_shape.md §4~§7 (0x7101751c08 슈터, 0x7101811b44 스플래시, 0x71018ae054 벽 낙하,
// 0x7101765fd8 크기, 0x7101765ad8 패턴, 0x7101765b50 중심 이동). 재구현 대조: web/tools/paint_shape.py.
// 원본은 f32 연산이라 연산마다 f32 로 맞춘다.
import { f32 } from "../fmath.ts";

/** spl::BulletShooterPaintParam (무기 표 키 "PaintParam"). 기본값 = 생성자 기본값(paint_shape.md §3.1). */
export interface ShooterPaintParam {
  DistanceNear: number;
  DistanceMiddle: number;
  DistanceFar: number;
  WidthHalfNear: number;
  WidthHalfMiddle: number;
  WidthHalfFar: number;
  DegreeUseDepthScaleMin: number;
  DegreeUseDepthScaleMax: number;
  DepthScaleMin: number;
  DepthScaleMax: number;
  HeightUseDepthScaleMinBreakFree: number;
  HeightUseDepthScaleMaxBreakFree: number;
  DepthScaleMinBreakFree: number;
  DepthScaleMaxBreakFree: number;
}

export const SHOOTER_PAINT_DEFAULTS: ShooterPaintParam = {
  DistanceNear: 2.0,
  DistanceMiddle: 20.0,
  DistanceFar: 20.0,
  WidthHalfNear: 1.4,
  WidthHalfMiddle: 1.4,
  WidthHalfFar: 1.4,
  DegreeUseDepthScaleMin: 35.0,
  DegreeUseDepthScaleMax: 10.0,
  DepthScaleMin: 1.4,
  DepthScaleMax: 2.4,
  HeightUseDepthScaleMinBreakFree: 10.0,
  HeightUseDepthScaleMaxBreakFree: 1.5,
  DepthScaleMinBreakFree: 1.2,
  DepthScaleMaxBreakFree: 2.4,
};

/** spl::BulletSplashShooterPaintParam (키 "SplashPaintParam"), paint_shape.md §3.2. */
export interface SplashPaintParam {
  WidthHalf: number;
  WidthHalfNearest: number;
  DepthScaleMin: number;
  DepthScaleMax: number;
  DepthMinDropHeight: number;
  DepthMaxDropHeight: number;
}

export const SPLASH_PAINT_DEFAULTS: SplashPaintParam = {
  WidthHalf: 1.28,
  WidthHalfNearest: 1.792,
  DepthScaleMin: 1.0,
  DepthScaleMax: 1.2,
  DepthMinDropHeight: 10.0,
  DepthMaxDropHeight: 3.0,
};

/** spl::BulletWallDropCollisionPaintParam (키 "WallDropCollisionPaintParam"), paint_shape.md §3.3. */
export interface WallDropPaintParam {
  PaintRadiusShock: number;
  PaintRadiusFall: number;
  PaintRadiusGround: number;
}

export const WALLDROP_PAINT_DEFAULTS: WallDropPaintParam = {
  PaintRadiusShock: 1.3,
  PaintRadiusFall: 0.65,
  PaintRadiusGround: 0.6,
};

/** 0x7101751c08 안의 두 점 보간. 두 점 순서가 뒤집혀도 정렬해서 같은 식(원본 동작 그대로). */
export function clampLerp(x: number, x0: number, y0: number, x1: number, y1: number): number {
  if (x1 < x0) {
    const tx = x0, ty = y0;
    x0 = x1;
    y0 = y1;
    x1 = tx;
    y1 = ty;
  }
  if (x <= x0) return f32(y0);
  if (x >= x1) return f32(y1);
  const d = f32(x1 - x0);
  const t = d === 0 ? 0 : f32(f32(x - x0) / d);
  return f32(y0 + f32(f32(y1 - y0) * t));
}

function lerpClamped(a: number, b: number, t: number): number {
  if (t <= 0) return f32(a);
  if (t >= 1) return f32(b);
  return f32(a + f32(t * f32(b - a)));
}

/** 슈터 반폭: dist = 탄+0x1200 누적 이동거리 (§4.1). */
export function shooterWidthHalf(p: ShooterPaintParam, dist: number): number {
  if (dist < p.DistanceMiddle) return clampLerp(dist, p.DistanceNear, p.WidthHalfNear, p.DistanceMiddle, p.WidthHalfMiddle);
  return clampLerp(dist, p.DistanceMiddle, p.WidthHalfMiddle, p.DistanceFar, p.WidthHalfFar);
}

/**
 * 슈터 깊이 비율 (§4.2 입사 각도, §4.3 Brake/Free 낙하 높이, 최종 [1,5] 클램프).
 * spawn = 생성정보+0x30, pos = 탄 물리 바디 위치, moveState = 탄+0x198, maxYInState = 탄+0x1204.
 */
export function shooterDepthScale(
  p: ShooterPaintParam,
  spawn: ArrayLike<number>,
  pos: ArrayLike<number>,
  moveState: number,
  maxYInState: number,
): number {
  const dx = f32(pos[0] - spawn[0]);
  const dz = f32(pos[2] - spawn[2]);
  const hd = f32(Math.sqrt(f32(f32(dx * dx) + f32(dz * dz))));
  let t: number;
  if (hd > 0) {
    const deg = f32(f32(Math.atan(f32(Math.abs(f32(pos[1] - spawn[1])) / hd))) * f32(57.295776));
    t = f32(f32(deg - p.DegreeUseDepthScaleMax) / f32(p.DegreeUseDepthScaleMin - p.DegreeUseDepthScaleMax));
  } else t = 1;
  let ds = lerpClamped(p.DepthScaleMax, p.DepthScaleMin, t);
  if (moveState !== 0) {
    const h = f32(maxYInState - pos[1]);
    const t2 = f32(
      f32(h - p.HeightUseDepthScaleMaxBreakFree) / f32(p.HeightUseDepthScaleMinBreakFree - p.HeightUseDepthScaleMaxBreakFree),
    );
    const dsBF = lerpClamped(p.DepthScaleMaxBreakFree, p.DepthScaleMinBreakFree, t2);
    ds = ds < dsBF ? ds : dsBF;
  }
  return ds < 1 ? 1 : Math.min(ds, 5);
}

/** 스플래시 (§5): nearest = 생성정보+0x90, drop = 생성y(+0x34) − 현재 y. 상한 5 클램프 없음. */
export function splashPaint(p: SplashPaintParam, nearest: boolean, spawnY: number, y: number): { w: number; ds: number } {
  const w = nearest ? p.WidthHalfNearest : p.WidthHalf;
  const drop = f32(spawnY - y);
  const t = f32(f32(drop - p.DepthMaxDropHeight) / f32(p.DepthMinDropHeight - p.DepthMaxDropHeight));
  const ds = lerpClamped(p.DepthScaleMax, p.DepthScaleMin, t);
  return { w, ds: ds < 1 ? 1 : ds };
}

/** 벽 낙하 방울의 바닥 도색 크기 (§6, paint_and_score.md §3.0): 0.05 단위 양자화 정수 × 0.05 × 2 = W = L. */
export function wallDropSize(radius: number): number {
  const q = Math.trunc(f32(f32(radius / f32(0.05)) + f32(0.001)));
  return f32(f32(q * f32(0.05)) * 2);
}

/** 0x7101765fd8: W = 2w·ds^-1/4 (진행 직교), L = 2w·ds^3/4 (진행 방향). */
export function rectSize(w: number, ds: number): { W: number; L: number } {
  const s = f32(Math.sqrt(ds));
  const q = f32(Math.sqrt(Math.abs(s)));
  const w2 = f32(w + w);
  return { W: f32(f32(w2 / s) * q), L: f32(f32(w2 * s) * q) };
}

/** 0x7101765ad8 (슈터 슬롯102): L/W 로 InkTexType Shot00..Shot04. 스플래시·벽 낙하는 0. */
export function shooterPattern(W: number, L: number): number {
  const r = f32(L / W);
  if (r < f32(1.3)) return 0;
  if (r < f32(1.6)) return 1;
  if (r < f32(2.2)) return 2;
  if (r < f32(2.85)) return 3;
  return 4;
}

/** 0x7101765b50: 패턴 1..7 이면 중심 이동 길이 L·((L/W − 1)/(2·L/W)) = (L − W)/2. */
export function centerShiftLength(W: number, L: number, pattern: number): number {
  if (pattern < 1 || pattern > 7) return 0;
  const r = f32(L / W);
  return f32(L * f32(f32(r - 1) / f32(r + r)));
}

/**
 * 0x7101765b50 중심 이동 벡터. n = 접촉 법선, d = 진행 방향(xz만 쓰임).
 * a = normalize(X × n) (|X × n| < 0.1 이면 b = normalize(n × Z), a = b × n), v = a·d.z + (n × a)·d.x.
 */
export function centerShift(out: Float32Array, n: ArrayLike<number>, d: ArrayLike<number>, W: number, L: number, pattern: number): Float32Array {
  out[0] = out[1] = out[2] = 0;
  if (pattern < 1 || pattern > 7) return out;
  const nx = n[0], ny = n[1], nz = n[2];
  let ax = 0, ay = f32(-nz), az = f32(ny);
  const la = f32(Math.sqrt(f32(f32(az * az) + f32(ay * ay))));
  if (la > 0) {
    const inv = f32(1 / la);
    ay = f32(ay * inv);
    az = f32(az * inv);
  }
  if (la < 0.1) {
    let bx = f32(ny), by = f32(-nx);
    const lb = f32(Math.sqrt(f32(f32(bx * bx) + f32(by * by))));
    if (lb > 0) {
      const inv = f32(1 / lb);
      bx = f32(bx * inv);
      by = f32(by * inv);
    }
    ax = f32(f32(nz * by));
    ay = f32(-f32(nz * bx));
    az = f32(f32(ny * bx) - f32(nx * by));
  }
  let dx = d[0], dz = d[2];
  const ld = f32(Math.sqrt(f32(f32(f32(dx * dx) + f32(d[1] * d[1])) + f32(dz * dz))));
  if (ld > 0) {
    const inv = f32(1 / ld);
    dx = f32(dx * inv);
    dz = f32(dz * inv);
  }
  const cx = f32(f32(ny * az) - f32(nz * ay));
  const cy = f32(f32(nz * ax) - f32(nx * az));
  const cz = f32(f32(nx * ay) - f32(ny * ax));
  const vx = f32(f32(ax * dz) + f32(cx * dx));
  const vy = f32(f32(ay * dz) + f32(cy * dx));
  const vz = f32(f32(az * dz) + f32(cz * dx));
  const lv = f32(Math.sqrt(f32(f32(f32(vz * vz) + f32(vx * vx)) + f32(vy * vy))));
  if (lv > 0) {
    const k = f32(centerShiftLength(W, L, pattern) / lv);
    out[0] = f32(vx * k);
    out[1] = f32(vy * k);
    out[2] = f32(vz * k);
  }
  return out;
}

/** §4.4: 수평 진행 방향 = (v.x, 0, v.z) 정규화, 길이 < 1e-5 이면 (1,0,0). */
export function horizontalDir(out: Float32Array, v: ArrayLike<number>): Float32Array {
  const x = v[0], z = v[2];
  const l = f32(Math.sqrt(f32(f32(x * x) + f32(z * z))));
  if (l < 1e-5) {
    out[0] = 1;
    out[1] = 0;
    out[2] = 0;
  } else {
    const inv = f32(1 / l);
    out[0] = f32(x * inv);
    out[1] = 0;
    out[2] = f32(z * inv);
  }
  return out;
}
