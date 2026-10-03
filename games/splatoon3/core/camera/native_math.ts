// Native arithmetic and sead direction tables. Sources: player_camera §6.7,
// movement_physics §6.3.3; r5_player_lerpdir_emu.py (original instruction fixtures).
import { ATAN_BASE, ATAN_SLOPE } from "./atan_table.ts";
import { SINCOS_TABLE } from "../weapon/sincos_table.ts";
export const F = Math.fround;
const ub = new Uint32Array(1), fb = new Float32Array(ub.buffer);
export function floatBits(b: number): number { ub[0] = b; return fb[0]; }
export const add = (a: number, b: number) => F(F(a) + F(b));
export const sub = (a: number, b: number) => F(F(a) - F(b));
export const mul = (a: number, b: number) => F(F(a) * F(b));
export const div = (a: number, b: number) => F(F(a) / F(b));
export const mix = (a: number, b: number, t: number) => add(a, mul(sub(b, a), t));
export function dot(a: ArrayLike<number>, b: ArrayLike<number>): number {
  return add(add(mul(a[0], b[0]), mul(a[1], b[1])), mul(a[2], b[2]));
}
export const length = (a: ArrayLike<number>) => F(Math.sqrt(dot(a, a)));
export function normalized(a: ArrayLike<number>): number[] {
  const n = length(a);
  return n > 0 ? [mul(a[0], div(1, n)), mul(a[1], div(1, n)), mul(a[2], div(1, n))] : Array.from(a);
}
export function cross(a: ArrayLike<number>, b: ArrayLike<number>): number[] {
  return [sub(mul(a[1], b[2]), mul(a[2], b[1])), sub(mul(a[2], b[0]), mul(a[0], b[2])), sub(mul(a[0], b[1]), mul(a[1], b[0]))];
}
const truncUnsigned = (n: number) => n > 0 ? Math.min(Math.trunc(n), 0xffffffff) : 0;
function atanLookup(r: number, exactIndex = Math.trunc(mul(r, 128))): number {
  return (ATAN_BASE[exactIndex] + truncUnsigned(mul(sub(mul(r, 128), exactIndex), ATAN_SLOPE[exactIndex]))) >>> 0;
}
export function atan2Idx(y: number, x: number): number {
  x = F(x); y = F(y);
  if (Number.isNaN(x) || Number.isNaN(y) || (x === 0 && y === 0)) return 0;
  if (Math.abs(y) === Infinity) {
    if (Math.abs(x) === Infinity) return x >= 0 ? (y < 0 ? 0xe0000000 : 0x20000000) : (y < 0 ? 0xa0000000 : 0x60000000);
    return y < 0 ? 0xc0000000 : 0x40000000;
  }
  if (Math.abs(x) === Infinity) return x < 0 ? 0x80000000 : 0;
  if (x >= 0) {
    if (y >= 0) return x >= y ? atanLookup(div(y, x)) : (0x40000000 - atanLookup(div(x, y))) >>> 0;
    const ny = F(-y);
    return ny >= x ? (0xc0000000 + atanLookup(div(x, ny))) >>> 0 : -atanLookup(div(ny, x)) >>> 0;
  }
  const nx = F(-x);
  if (y >= 0) return nx > y ? (0x80000000 - atanLookup(div(y, nx))) >>> 0 : (0x40000000 + atanLookup(div(nx, y))) >>> 0;
  const ny = F(-y);
  return nx > ny ? (0x80000000 + atanLookup(div(ny, nx))) >>> 0 : (0xc0000000 - atanLookup(div(nx, ny))) >>> 0;
}
export function acosTable(x: number): number {
  x = F(x);
  let a: number;
  const r2 = floatBits(0x3f3504f3);
  if (x < -1) a = 0x80000000;
  else if (x > 1) a = 0;
  else {
    const s = F(Math.sqrt(sub(1, mul(x, x))));
    if (x >= 0) {
      const r = x > r2 ? div(s, x) : div(x, s);
      const v = atanLookup(r, Math.trunc(r * 128));
      a = x > r2 ? v : (0x40000000 - v) >>> 0;
    } else if (x < -r2) {
      const r = mul(div(s, x), -128), i = Math.trunc(r);
      a = (0x80000000 - ((ATAN_BASE[i] + truncUnsigned(mul(ATAN_SLOPE[i], sub(r, i)))) >>> 0)) >>> 0;
    } else {
      const r = div(F(-x), s);
      a = (atanLookup(r, Math.trunc(r * 128)) + 0x40000000) >>> 0;
    }
  }
  return mul(F(a), floatBits(0x30c90fdb));
}
export function sinIndex(v: number): number {
  const n = Math.trunc(v), i = (n >> 24) & 255, fraction = F(n & 0xffffff);
  return add(SINCOS_TABLE[i * 4], mul(mul(SINCOS_TABLE[i * 4 + 1], fraction), floatBits(0x33800000)));
}
export function directionSlerp(t: number, a: ArrayLike<number>, b: ArrayLike<number>): number[] {
  t = F(t);
  if (t <= 0) return Array.from(a);
  if (t >= 1) return Array.from(b);
  const la = length(a), lb = length(b);
  const an = la === 0 ? [0, 0, 0] : normalized(a), bn = lb === 0 ? [0, 0, 0] : normalized(b), d = dot(an, bn);
  const omt = sub(1, t);
  let w0 = omt, w1 = t;
  // Native camera calls pass a null opposite-direction axis.
  if (d <= floatBits(0x3f7fffef) && d >= floatBits(0xbf7fffef)) {
    const th = acosTable(d), k = floatBits(0x4e22f983), st = sinIndex(mul(th, k));
    w0 = div(sinIndex(mul(mul(omt, th), k)), st);
    w1 = div(sinIndex(mul(mul(th, t), k)), st);
  }
  const n = add(mul(la, omt), mul(lb, t));
  return [0, 1, 2].map(i => mul(add(mul(bn[i], w1), mul(an[i], w0)), n));
}
/** X/Y/Z columns. Degenerate or near-vertical poses preserve all prior columns. */
export function updateBasis(pos: ArrayLike<number>, at: ArrayLike<number>, x: Float32Array, y: Float32Array, z: Float32Array): boolean {
  const raw = [sub(pos[0], at[0]), sub(pos[1], at[1]), sub(pos[2], at[2])], n = length(raw);
  const nz = normalized(raw);
  if (n === 0 || Math.abs(nz[1]) > floatBits(0x3f7ffffe)) return false;
  const nx = normalized(cross([0, 1, 0], nz));
  x.set(nx); y.set(cross(nz, nx)); z.set(nz);
  return true;
}
// SDK logf/expf are not JS Math. The remaining ULP difference is measured in fixtures.
export function power0(x: number, exponent: number): number {
  x = F(x);
  if (Math.abs(x) < F(.001)) return 0;
  const v = F(Math.exp(mul(F(Math.log(Math.abs(x))), exponent)));
  return x < 0 ? F(-v) : v;
}
