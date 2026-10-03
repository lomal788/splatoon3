// ColPaint display-vertex leaves: docs/paint/colpaint_atlas.md §7.2,
// model_panel_mapping.md §4/7. These do not build/select the native lobby atlas.
import { f32 } from "../fmath.ts";

export type PaintVec2 = [number, number];
export type PaintVec3 = [number, number, number];
export type PaintBasis = readonly [ArrayLike<number>, ArrayLike<number>, ArrayLike<number>];
/** Row-major 2×3: [m0,m1,m2, m3,m4,m5]. */
export type PaintUvMatrix = ArrayLike<number>;

const mul = (a: number, b: number): number => f32(f32(a) * f32(b));
const add = (a: number, b: number): number => f32(f32(a) + f32(b));
const sub = (a: number, b: number): number => f32(f32(a) - f32(b));
const dot3 = (a: ArrayLike<number>, b: ArrayLike<number>): number =>
  add(add(mul(a[0], b[0]), mul(a[1], b[1])), mul(a[2], b[2]));

/** 0x7102bed910; basis comes from the caller's native mapping direction. */
export function nativeVisualUv(
  position: ArrayLike<number>, basis: PaintBasis,
  mappingMin: ArrayLike<number>, mappingMax: ArrayLike<number>, uv2x3: PaintUvMatrix | null,
): PaintVec2 {
  if (uv2x3 === null) return [0, 0];
  const u = sub(dot3(basis[0], position), mul(add(mappingMin[0], mappingMax[0]), 0.5));
  const v = sub(dot3(basis[1], position), mul(add(mappingMin[1], mappingMax[1]), 0.5));
  return [
    add(uv2x3[2], add(mul(u, uv2x3[0]), mul(v, uv2x3[1]))),
    add(uv2x3[5], add(mul(u, uv2x3[3]), mul(v, uv2x3[4]))),
  ];
}

/** 0x7102bedb98. det=0 reads prior native registers; no invented fallback. */
export function nativeVisualTangent(basis: PaintBasis, uv2x3: PaintUvMatrix | null): PaintVec3 | undefined {
  if (uv2x3 === null) return [0, 1, 0];
  const det = sub(mul(uv2x3[0], uv2x3[4]), mul(uv2x3[1], uv2x3[3]));
  if (det === 0 || !Number.isFinite(det)) return undefined;
  const inv = f32(1 / det);
  let x = mul(uv2x3[4], inv), y = mul(inv, -f32(uv2x3[3]));
  const length = f32(Math.sqrt(add(mul(x, x), mul(y, y))));
  // Non-finite sqrt's external SDK path is not covered by the finite fixtures.
  if (!Number.isFinite(length)) return undefined;
  if (length > 0) {
    const q = f32(1 / length);
    x = mul(x, q); y = mul(y, q);
  }
  return [0, 1, 2].map(j => add(add(mul(x, basis[0][j]), mul(y, basis[1][j])), mul(basis[2][j], 0))) as PaintVec3;
}

const transform3x4 = (p: ArrayLike<number>, matrix: ArrayLike<number>): PaintVec3 =>
  [0, 1, 2].map(row => {
    const k = row * 4;
    return add(matrix[k + 3], add(add(mul(p[0], matrix[k]), mul(p[1], matrix[k + 1])), mul(p[2], matrix[k + 2])));
  }) as PaintVec3;

/** 0x7102bd1298: sanitize decoded NaN, optional shape, then root; no FMA. */
export function nativeVisualWorld(position: ArrayLike<number>, root3x4: ArrayLike<number>, shape3x4?: ArrayLike<number>): PaintVec3 {
  const p: PaintVec3 = Number.isNaN(position[0]) || Number.isNaN(position[1]) || Number.isNaN(position[2])
    ? [0, 0, 0] : [f32(position[0]), f32(position[1]), f32(position[2])];
  return transform3x4(shape3x4 ? transform3x4(p, shape3x4) : p, root3x4);
}

/** AArch64 FCVTZS Wd,Sn: toward-zero with signed32 saturation; NaN becomes 0. */
function fcvtzs(value: number): number {
  return Number.isNaN(value) ? 0 : Math.max(-2147483648, Math.min(2147483647, Math.trunc(value)));
}

/** 0x7102be59f0 writes the low 16 bits of each signed32 conversion. */
export function nativePackPaintUv(uv4: ArrayLike<number>): Uint16Array {
  return new Uint16Array([0, 1, 2, 3].map(i => fcvtzs(mul(uv4[i], 32767)) & 0xffff));
}

/** 0x7102be5ae8 writes the low byte; negative values are not clamped away. */
export function nativePackPaintSwitch(value: number): number {
  return fcvtzs(mul(value, 127)) & 0xff;
}

/** 0x7102be5ba4. model3x3 is nine row-major floats, without translation. */
export function nativePackPaintTangent(tangent: ArrayLike<number>, model3x3: ArrayLike<number>): number {
  const packed = [0, 1, 2].map(row => {
    const k = row * 3;
    const d = add(add(mul(tangent[0], model3x3[k]), mul(tangent[1], model3x3[k + 1])), mul(tangent[2], model3x3[k + 2]));
    const scaled = mul(d, 511);
    const q = fcvtzs(add(scaled, scaled >= 0 ? 0.5 : -0.5)) >>> 0;
    return ((q >>> 6) & 0x200) | (q & 0x1ff);
  });
  return (packed[0] | (packed[1] << 10) | (packed[2] << 20)) >>> 0;
}

/** Shader's UV branch, offset then Y flip. Texture upload orientation is caller-owned. */
export function nativeChoosePaintUv(uv4: ArrayLike<number>, paintSwitch: number, offset: ArrayLike<number>): PaintVec2 {
  const k = paintSwitch < 0 ? 2 : 0;
  return [add(uv4[k], offset[0]), sub(1, add(uv4[k + 1], offset[1]))];
}

// WebGL SNORM adapters for the CPU bytes above. The original GPU enum names and
// live binding are still unconfirmed; these helpers do not assert native GPU equivalence.
const snorm = (signed: number, max: number): number => f32(Math.max(signed / max, -1));
export function webDecodePaintUv(packed: ArrayLike<number>): [number, number, number, number] {
  return [0, 1, 2, 3].map(i => snorm((packed[i] << 16) >> 16, 32767)) as [number, number, number, number];
}
export function webDecodePaintSwitch(packed: number): number {
  return snorm((packed << 24) >> 24, 127);
}
export function webDecodePaintTangent(packed: number): PaintVec3 {
  return [0, 1, 2].map(i => snorm(((packed >>> (i * 10)) << 22) >> 22, 511)) as PaintVec3;
}
