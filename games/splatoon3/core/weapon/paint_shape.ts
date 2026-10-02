// 탄 쪽 도색 크기 입력(반폭 w·깊이 비율 ds·진행 방향). 근거: docs/paint/paint_shape.md §4(0x7101751c08), §5(0x7101811b44).
// 사각 크기·패턴·중심 이동(0x7101765fd8)은 paint 담당이 PaintRequest(widthHalf, depthScale)로 계산한다.
import { f32 } from "../fmath.ts";
import type { V3 } from "./move.ts";
import type { ShooterPaintParam, SplashPaintParam } from "./params.ts";

function clampLerp(x: number, x0: number, y0: number, x1: number, y1: number): number {
  if (x1 < x0) {
    const tx = x0, ty = y0;
    x0 = x1; y0 = y1; x1 = tx; y1 = ty;
  }
  if (!(x0 < x)) return f32(y0);
  if (!(x < x1)) return f32(y1);
  const d = f32(x1 - x0);
  const t = d === 0 ? 0 : f32(f32(x - x0) / d);
  return f32(f32(y0) + f32(f32(f32(y1) - f32(y0)) * t));
}

function lerpT(a: number, b: number, t: number): number {
  if (!(t > 0)) return f32(a);
  if (!(t < 1)) return f32(b);
  return f32(f32(a) + f32(t * f32(f32(b) - f32(a))));
}

/** 0x7101751c08 반폭: dist = 탄+0x1200 누적 이동 거리. */
export function shooterWidthHalf(p: ShooterPaintParam, dist: number): number {
  const mid = f32(p.DistanceMiddle);
  if (dist < mid) return clampLerp(dist, f32(p.DistanceNear), p.WidthHalfNear, mid, p.WidthHalfMiddle);
  return clampLerp(dist, mid, p.WidthHalfMiddle, f32(p.DistanceFar), p.WidthHalfFar);
}

/** 0x7101751c08 깊이 비율: 생성 위치 대비 각도 + (이동 상태≠0 이면) 상태 중 최고 높이에서의 낙하. 최종 [1, 5]. */
export function shooterDepthScale(p: ShooterPaintParam, spawnPos: V3, pos: V3, moveState: number, maxYInState: number): number {
  const dx = f32(pos[0] - spawnPos[0]);
  const dz = f32(pos[2] - spawnPos[2]);
  const hd = f32(Math.sqrt(f32(f32(dx * dx) + f32(dz * dz))));
  let t = 1;
  if (hd > 0) {
    let dy = f32(pos[1] - spawnPos[1]);
    if (dy < 0) dy = f32(-dy);
    const deg = f32(f32(Math.atan(f32(dy / hd))) * f32(57.295776));
    t = f32(f32(deg - f32(p.DegreeUseDepthScaleMax)) / f32(f32(p.DegreeUseDepthScaleMin) - f32(p.DegreeUseDepthScaleMax)));
  }
  let ds = lerpT(p.DepthScaleMax, p.DepthScaleMin, t);
  if (moveState !== 0) {
    const h = f32(maxYInState - pos[1]);
    const t2 = f32(f32(h - f32(p.HeightUseDepthScaleMaxBreakFree)) / f32(f32(p.HeightUseDepthScaleMinBreakFree) - f32(p.HeightUseDepthScaleMaxBreakFree)));
    const bf = lerpT(p.DepthScaleMaxBreakFree, p.DepthScaleMinBreakFree, t2);
    ds = ds < bf ? ds : bf;
  }
  return ds < 1 ? 1 : Math.min(ds, 5);
}

/** 0x7101751c08 끝: 속도의 수평 성분 정규화, 길이 < 1e-5 면 (1, 0, 0). */
export function horizontalDir(vel: V3, out: V3): V3 {
  let x = vel[0], z = vel[2];
  const l = f32(Math.sqrt(f32(f32(f32(z * z) + f32(x * x)) + 0)));
  let y = 0;
  if (l > 0) {
    const inv = f32(1 / l);
    x = f32(inv * x);
    y = f32(inv * 0);
    z = f32(inv * z);
  }
  if (l >= f32(1e-5)) {
    out[0] = x; out[1] = y; out[2] = z;
  } else {
    out[0] = 1; out[1] = 0; out[2] = 0;
  }
  return out;
}

/** 0x7101811b44 스플래시: 반폭(최근접 여부), 낙하 높이로 깊이 비율(하한 1, 상한 없음). */
export function splashPaintSize(p: SplashPaintParam, nearest: boolean, spawnY: number, y: number): [number, number] {
  const w = f32(nearest ? p.WidthHalfNearest : p.WidthHalf);
  const drop = f32(spawnY - y);
  const t = f32(f32(drop - f32(p.DepthMaxDropHeight)) / f32(f32(p.DepthMinDropHeight) - f32(p.DepthMaxDropHeight)));
  const ds = lerpT(p.DepthScaleMax, p.DepthScaleMin, t);
  return [w, ds < 1 ? 1 : ds];
}
