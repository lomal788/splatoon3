// 카메라 공용 곡선. 근거: docs/camera/camera_feel.md §4.2(bias), player_camera.md §6.1(조각 3차 베지어).
import { f32 } from "../fmath.ts";

/** Perlin bias (원본 인라인 코드 0x7102583ad8 등). |u|^(-log2 b), 부호 유지. */
export function bias(u: number, b: number): number {
  const d = b - 0.5;
  if (!(d < -0.001 || d > 0.001)) return u;
  const a = Math.abs(u);
  if (a < 0.001) return 0;
  if (b < 0.001) return a < 0.999 ? 0 : 1;
  const p = f32(Math.exp(Math.log(a) * (Math.log(b) * -1.442695)));
  return u < 0 ? -p : p;
}

/** 3차 베지어 (1-t)^3 P0 + 3t(1-t)^2 P1 + 3t^2(1-t) P2 + t^3 P3. */
export function cubic(t: number, p0: number, p1: number, p2: number, p3: number): number {
  const u = 1 - t;
  return u * u * u * p0 + 3 * t * u * u * p1 + 3 * t * t * u * p2 + t * t * t * p3;
}

/**
 * 피치 정규값 p(-1..1)의 조각 3차 베지어. 0x71024d6e84·0x7102551780 이 같은 꼴을 쓴다.
 * p<=0: P0=mid, P1=mid-kMid(up-down), P2=down+2kDown(mid-down), P3=down, t=-p
 * p>0 : P0=mid, P1=mid+kMid(up-down), P2=up-2kUp(up-mid),       P3=up,   t=p
 * 리그는 kDown=kUp=0(끝 기울기 0), 조준 피치 곡선은 셋 다 쓴다.
 */
export function pieceBez(p: number, down: number, mid: number, up: number, kMid: number, kDown = 0, kUp = 0): number {
  const tan = (up - down) * kMid;
  if (p <= 0) return cubic(-p, mid, mid - tan, down + 2 * kDown * (mid - down), down);
  return cubic(p, mid, mid + tan, up - 2 * kUp * (up - mid), up);
}

/** 제어점을 직접 주는 조각 곡선(대체 리그의 상수 곡선). neg/pos = [P0, P1, P2, P3]. */
export function pieceCtrl(p: number, neg: readonly number[], pos: readonly number[]): number {
  const c = p <= 0 ? neg : pos;
  return cubic(Math.abs(p), c[0], c[1], c[2], c[3]);
}

/** invLerp + clamp01 (원본 여러 곳의 "a<=b 이면 (x-a)/(b-a), 아니면 1-(x-b)/(a-b)" 꼴). */
export function invLerp01(a: number, b: number, x: number): number {
  if (a <= b) {
    if (x <= a) return 0;
    if (x >= b) return 1;
    return b - a !== 0 ? (x - a) / (b - a) : 0;
  }
  if (x <= b) return 1;
  if (x >= a) return 0;
  return a - b !== 0 ? 1 - (x - b) / (a - b) : 1;
}

export function clamp01(x: number): number {
  return x < 0 ? 0 : x > 1 ? 1 : x;
}
