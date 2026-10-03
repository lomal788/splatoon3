// Native CC mode 0 packet and shader 41 equations, ink_lighting_r2 §4/6.
// CPU reconstruction is not an execution of the native GPU LUT bake.
import { F, add, sub, mul, div, clamp, curveSamples, type V3 } from "./graphics_math.ts";

export interface NativeColorGrading {
  Enable?: boolean;
  Hue?: number;
  Saturate?: number;
  Value?: number;
  CurveColorR?: { Type?: string; Data?: number[] };
  CurveColorG?: { Type?: string; Data?: number[] };
  CurveColorB?: { Type?: string; Data?: number[] };
}
export interface ColorCorrectionPacket {
  headers: number[][];
  params: number[][];
  count: number;
}
/** Explicit web policies; native NVN rounding/filter live binding is unverified. */
export const CC_WEB_POLICY = Object.freeze({
  storage: "RGB11/11/10 unsigned float widths; CPU nearest-even rounding",
  sampler: "linear min/mag, clamp-to-edge, level 0 only",
  source: "native default mode 0 shader equations, CPU f32 reconstruction",
});
const fma = (a: number, b: number, c: number): number => F(F(a) * F(b) + F(c));
const fract = (x: number): number => sub(x, Math.floor(x));

/** Reuses the native-executed Hermit2D reader; does not replace 8-point curves with per-pixel Hermite. */
export function colorCorrectionPacket(g: NativeColorGrading | undefined): ColorCorrectionPacket | null {
  if (!g || g.Enable !== true) return null;
  const curves = [g.CurveColorR, g.CurveColorG, g.CurveColorB];
  if (curves.some(c => c?.Type !== "Hermit2D" || !c.Data || c.Data.length < 6 || c.Data.length % 3 || c.Data.some(x => !Number.isFinite(x)))) return null;
  if (curves.some(c => c!.Data!.some((v, i, d) => i % 3 === 0 && i > 0 && v <= d[i - 3]))) return null;
  const hsv = [g.Hue ?? 0, g.Saturate ?? 1, g.Value ?? 1, 0].map(F);
  if (hsv.some(x => !Number.isFinite(x))) return null;
  const channels = curves.map(c => curveSamples(c!.Data!));
  const params = [hsv, ...Array.from({ length: 8 }, (_, i) => [channels[0][i], channels[1][i], channels[2][i], F(i / 7)])];
  params.push([...params[8]], [1, 1, 1, 1]);
  // A is not consumed by the RGB LUT; its values are not claimed native bit-exact.
  return { headers: [[0, 0, 0, 0], [6, 1, 0, 0], [1, 10, 0, 0]], params, count: 3 };
}

/** Shader kind 0: min-channel sector/tie order, delta gate, f32 +1000 hue wrap. */
export function ccHSV(rgb: V3, parameter: number[]): V3 {
  const [r, g, b] = rgb.map(F), lo = Math.min(b, Math.min(r, g)), hi = Math.max(b, Math.max(r, g));
  const delta = sub(hi, lo);
  let hue = 0, saturation = 0;
  if (delta >= F(1e-5)) {
    const inv = div(1, delta);
    saturation = mul(delta, div(1, hi));
    const sector = b === lo ? fma(inv, sub(g, r), 1) : r === lo ? fma(inv, sub(b, g), 3) : fma(inv, sub(r, b), 5);
    hue = mul(sector, .166666672);
  }
  const s = mul(saturation, parameter[1]), v = mul(hi, parameter[2]);
  const h6 = mul(fract(add(fma(parameter[0], .0027777778, hue), 1000)), 6);
  const sector = Math.trunc(h6), w = fract(h6);
  const p = mul(v, sub(1, s)), q = mul(v, fma(s, -w, 1));
  const t = mul(v, sub(1, fma(s, -w, s)));
  switch (sector) {
    case 0: return [v, t, p];
    case 1: return [q, v, p];
    case 2: return [p, v, t];
    case 3: return [p, q, v];
    case 4: return [t, p, v];
    case 5: return [v, p, q];
    default: return [1, 0, 0]; // Native invalid-sector branch.
  }
}
export function ccPixel(rgb: V3, packet: ColorCorrectionPacket): V3 {
  let c = ccHSV(rgb, packet.params[0]);
  c = c.map((v, channel) => {
    const q = mul(clamp(v), 7), j = Math.floor(q), w = fract(q);
    const a = packet.params[j + 1][channel], b = packet.params[j + 2][channel];
    return fma(sub(b, a), w, a);
  }) as V3;
  const gamma = packet.params[10];
  return c.map((v, ch) => F(2 ** mul(div(1, mul(gamma[ch], gamma[3])), F(Math.log2(Math.abs(v)))))) as V3;
}
const roundEven = (x: number): number => {
  const floor = Math.floor(x), d = x - floor;
  return d > .5 || (d === .5 && floor % 2 !== 0) ? floor + 1 : floor;
};
/** 5 exponent bits, 6 mantissa bits for R/G, 5 for B. Rounding is a declared web policy. */
export function encodeUnsignedFloat(value: number, mantissaBits: 5 | 6): number {
  const m = 2 ** mantissaBits;
  value = F(value);
  if (Number.isNaN(value)) return 31 * m + 1;
  if (value <= 0) return 0;
  if (!Number.isFinite(value)) return 31 * m;
  if (value < 2 ** -14) return Math.min(m, roundEven(value / 2 ** (-14 - mantissaBits)));
  let exponent = Math.floor(Math.log2(value));
  let significand = roundEven(value / 2 ** (exponent - mantissaBits));
  if (significand === 2 * m) { exponent++; significand = m; }
  return exponent > 15 ? 31 * m : (exponent + 15) * m + significand - m;
}
export function decodeUnsignedFloat(code: number, mantissaBits: 5 | 6): number {
  const m = 2 ** mantissaBits, exponent = Math.floor(code / m), fraction = code % m;
  if (exponent === 31) return fraction ? NaN : Infinity;
  return exponent === 0 ? F(fraction * 2 ** (-14 - mantissaBits)) : F((m + fraction) * 2 ** (exponent - 15 - mantissaBits));
}
export function packRGB111110(rgb: V3): number {
  return (encodeUnsignedFloat(rgb[0], 6) | (encodeUnsignedFloat(rgb[1], 6) << 11) | (encodeUnsignedFloat(rgb[2], 5) << 22)) >>> 0;
}
export function unpackRGB111110(code: number): V3 {
  return [decodeUnsignedFloat(code & 2047, 6), decodeUnsignedFloat((code >>> 11) & 2047, 6), decodeUnsignedFloat(code >>> 22, 5)];
}
export interface ColorCorrectionLUT { size: 8; packed: Uint32Array; rgba: Float32Array }
/** RGB x/y/z, X fastest. Original map uses repeated slice addition, not z/7 per slice. */
export function colorCorrectionLUT(packet: ColorCorrectionPacket): ColorCorrectionLUT {
  const n = 8, inverse = div(1, 7), packed = new Uint32Array(n ** 3), rgba = new Float32Array(n ** 3 * 4);
  for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) {
    let zCoordinate = 0;
    for (let z = 0; z < n; z++) {
      const i = x + n * (y + n * z);
      packed[i] = packRGB111110(ccPixel([mul(x, inverse), mul(y, inverse), zCoordinate], packet));
      rgba.set([...unpackRGB111110(packed[i]), 1], i * 4);
      zCoordinate = add(zCoordinate, inverse);
    }
  }
  return { size: 8, packed, rgba };
}
/** GL linear/clamp reference for the explicit web sampler choice. */
export function sampleColorLUT(lut: ColorCorrectionLUT, rgb: V3): V3 {
  const p = rgb.map(v => clamp(v) * 7), a = p.map(Math.floor), w = p.map((v, i) => v - a[i]);
  const out: V3 = [0, 0, 0];
  for (let z = 0; z < 2; z++) for (let y = 0; y < 2; y++) for (let x = 0; x < 2; x++) {
    const i = Math.min(a[0] + x, 7) + 8 * (Math.min(a[1] + y, 7) + 8 * Math.min(a[2] + z, 7));
    const weight = (x ? w[0] : 1 - w[0]) * (y ? w[1] : 1 - w[1]) * (z ? w[2] : 1 - w[2]);
    for (let c = 0; c < 3; c++) out[c] += lut.rgba[i * 4 + c] * weight;
  }
  return out;
}
