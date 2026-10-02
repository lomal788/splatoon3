// PaintOverpaint 픽셀 셰이더(Hoian_Proc.sharcb) 한 텍셀 재현. 근거: docs/graphics/shaders.md §4.4,
// CPU 상수 0x7102c188b4 (cTeamAlphaTestThreshold 0.3, cConvex 0.99, cColor = 팀 원-핫, cAlpha = 요청 바이트/255).
// 재구현 대조: web/tools/shader_paint_overpaint.py (같은 연산 순서).
import { f32 } from "../fmath.ts";

export const TH = f32(0.3);
const ONE_MINUS_CONVEX = f32(1 - f32(0.99));
const WEAK = f32(TH * f32(1.04999995));

/**
 * 일반 덧칠(ERASE=0, WRITE_NORMAL=0). d = 현재 텍셀 (R,G,B) 잉크량(0..1), out 에 새 값.
 * 반환: false = discard(쓰지 않음). alphaTest 면 결과 내 팀 채널이 0.3 이상이면서 최대일 때만 통과.
 */
export function overpaint(
  d0: number,
  d1: number,
  d2: number,
  inkRaw: number,
  cAlpha: number,
  team: number,
  alphaTest: boolean,
  out: Float32Array,
): boolean {
  const ink = f32(inkRaw * cAlpha);
  if (!(ink > 0)) return false;
  const n0 = mixCh(d0, team === 0 ? 1 : 0, ink);
  const n1 = mixCh(d1, team === 1 ? 1 : 0, ink);
  const n2 = mixCh(d2, team === 2 ? 1 : 0, ink);
  const weak = n0 < WEAK && n1 < WEAK && n2 < WEAK;
  out[0] = d0 > TH && weak ? d0 : n0;
  out[1] = d1 > TH && weak ? d1 : n1;
  out[2] = d2 > TH && weak ? d2 : n2;
  if (alphaTest && team >= 0 && team < 3) {
    const mine = out[team];
    const mx = Math.max(out[0], out[1], out[2]);
    if (mine < TH || mine < mx) return false;
  }
  return true;
}

function mixCh(d: number, c: number, ink: number): number {
  let s = f32(d - TH);
  s = s < 0 ? 0 : s > 1 ? 1 : s;
  const dec = f32(s * ONE_MINUS_CONVEX);
  const dd = f32(d * f32(1 - f32(dec * c)));
  return f32(dd + f32(ink * f32(c - dd)));
}

/** ERASE 변형(모드 10/11): N = clamp(D − ink, 0, 1), alphaTest 면 세 채널 모두 0.3 미만일 때만 통과. */
export function erasepaint(d0: number, d1: number, d2: number, inkRaw: number, cAlpha: number, alphaTest: boolean, out: Float32Array): boolean {
  const ink = f32(inkRaw * cAlpha);
  if (!(ink > 0)) return false;
  out[0] = clamp01(f32(d0 - ink));
  out[1] = clamp01(f32(d1 - ink));
  out[2] = clamp01(f32(d2 - ink));
  if (alphaTest && (out[0] >= TH || out[1] >= TH || out[2] >= TH)) return false;
  return true;
}

function clamp01(x: number): number {
  return x < 0 ? 0 : x > 1 ? 1 : x;
}

/** 8비트 UNORM 저장 [추정: RG8/RGBA8 UNORM]. */
export function toUnorm8(x: number): number {
  const v = Math.round(x * 255);
  return v < 0 ? 0 : v > 255 ? 255 : v;
}
