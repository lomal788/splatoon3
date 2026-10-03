// CPU f32 consumers from stage_rendering §2.2.1/§5.6 and light_rig_runtime §6.
// GPU equations retain GPU ordering; JS libm is not claimed bit-identical to SDK.
export const F = Math.fround;
export const add = (a: number, b: number): number => F(F(a) + F(b));
export const sub = (a: number, b: number): number => F(F(a) - F(b));
export const mul = (a: number, b: number): number => F(F(a) * F(b));
export const div = (a: number, b: number): number => F(F(a) / F(b));
export const clamp = (x: number): number => Math.max(0, Math.min(1, x));
export type V3 = [number, number, number];
export const dot = (a: V3, b: V3): number => add(add(mul(a[0], b[0]), mul(a[1], b[1])), mul(a[2], b[2]));
export function norm(v: V3): V3 {
  const n = F(Math.sqrt(dot(v, v)));
  return n > 0 ? v.map(x => mul(x, div(1, n))) as V3 : v;
}

export function hermit2D(data: number[], t: number): number {
  t = F(t);
  const d = data.map(F), n = Math.floor(d.length / 3);
  if (n < 2) throw new Error("Hermit2D needs two increasing keys");
  if (t <= d[0]) return d[1];
  if (t >= d[(n - 1) * 3]) return d[(n - 1) * 3 + 1];
  for (let j = 1; j < n; j++) if (d[j * 3] > t) {
    const [x0, y0, m0, x1, y1, m1] = d.slice((j - 1) * 3, j * 3 + 3);
    const u = div(sub(t, x0), sub(x1, x0));
    const twoSq = mul(u, add(u, u)), twoCube = mul(u, twoSq), threeSq = mul(u, mul(u, 3));
    const sq = mul(u, u), cube = mul(u, sq);
    return add(mul(m1, sub(cube, sq)), add(mul(m0, add(u, sub(cube, twoSq))),
      add(mul(y1, sub(threeSq, twoCube)), mul(y0, add(sub(twoCube, threeSq), 1)))));
  }
  throw new Error("Invalid Hermit2D keys");
}

/** 1033b78: original startup fallback, not the final scene SH. */
export function directionalSH(d: V3, color: V3, samples = 1): number[] {
  d = d.map(F) as V3; color = color.map(F) as V3;
  const [x, y, z] = d, k = div(12.566371, samples);
  const a = mul(k, 0.488603), b = mul(k, 1.092548);
  const x1 = mul(a, x), y1 = mul(a, y), z1 = mul(a, z);
  const c0 = mul(k, 0.282095);
  const c6 = mul(mul(k, 0.315392), add(mul(z, mul(z, 3)), -1));
  const c8 = mul(mul(k, 0.546274), sub(mul(x, x), mul(y, y)));
  const xy = mul(x, mul(b, y)), yz = mul(mul(b, y), z), xz = mul(x, mul(b, z));
  const o = Array<number>(28).fill(0);
  for (let ch = 0; ch < 3; ch++) {
    const c = color[ch], a0 = ch * 4, b0 = 12 + ch * 4;
    o[a0] = mul(mul(x1, c), .32534343); o[a0 + 1] = mul(mul(y1, c), .32534343);
    o[a0 + 2] = mul(mul(z1, c), .32534343);
    o[a0 + 3] = sub(mul(mul(c0, c), .28175688), mul(mul(c, c6), .07875311));
    o[b0] = mul(mul(c, xy), .27280876); o[b0 + 1] = mul(mul(c, yz), .27280876);
    o[b0 + 2] = mul(mul(c, c6), .23625931); o[b0 + 3] = mul(mul(c, xz), .27280876);
    o[24 + ch] = mul(mul(c, c8), .13640438);
  }
  o[27] = 1;
  return o;
}
export function evalSH(d: V3, sh: number[]): V3 {
  const [x, y, z] = d.map(F);
  const xy = mul(x, y), yz = mul(y, z), zz = mul(z, z), xz = mul(x, z), q = sub(mul(x, x), mul(y, y));
  return [0, 1, 2].map(c => {
    const a = c * 4, b = 12 + a;
    const l = add(sh[a + 3], add(add(mul(x, sh[a]), mul(y, sh[a + 1])), mul(z, sh[a + 2])));
    const r = add(add(add(mul(xy, sh[b]), mul(yz, sh[b + 1])), mul(zz, sh[b + 2])), mul(xz, sh[b + 3]));
    return Math.max(0, add(add(l, r), mul(q, sh[24 + c])));
  }) as V3;
}

/** Final LUT generation remains unknown. These are the native 8 curve samples only. */
export function curveSamples(data: number[]): number[] {
  return Array.from({ length: 8 }, (_, i) => hermit2D(data, div(i, 7)));
}
