// Hair: HairArrange bone apply 0x71026df700 and the confirmed hcl cloth pieces (damping 8A63E0/DC42A0,
// integrate EE41F0, Standard D47BD0 / Bend D1C354 links, CullFrame gate 0F73368).
// Not wired to the hair bones: LocalRange/Transition/Stretch, capsule collision, frameInfo dt producer
// and the particle→bone write-back are [미확정] (hair_cloth.md, cloth_*_runtime.md).
import { fma32 } from "./native_f32.ts";

const F = Math.fround;
const A = (a: number, b: number): number => F(F(a) + F(b));
const D = (a: number, b: number): number => F(F(a) - F(b));
const M = (a: number, b: number): number => F(F(a) * F(b));
const V = (a: number, b: number): number => F(F(a) / F(b));
const buf = new DataView(new ArrayBuffer(4));
export const f32bits = (x: number): number => { buf.setFloat32(0, x); return buf.getUint32(0); };
export const bitsf32 = (b: number): number => { buf.setUint32(0, b >>> 0); return buf.getFloat32(0); };

// ---------------------------------------------------------------- HairArrange
export interface HairArrangeParam {
  /** BoneParam +0x48..+0x50 radians. Data is degrees; 0x710124ea4c stores deg × 0.017453292. */
  rotation: [number, number, number];
  scale: [number, number, number];
  transform: [number, number, number];
  /** Skeletal animation weight for this bone (+0x38, default 1). */
  animReduceRt: number;
}
/** BoneParam data (degrees) → apply input. */
export function hairArrangeParam(p: { Rotation?: { X?: number; Y?: number; Z?: number }; Scale?: { X?: number; Y?: number; Z?: number }; Transform?: { X?: number; Y?: number; Z?: number }; AnimReduceRt?: number }): HairArrangeParam {
  const k = F(0.017453292);
  return {
    rotation: [p.Rotation?.X ?? 0, p.Rotation?.Y ?? 0, p.Rotation?.Z ?? 0].map(v => M(v, k)) as [number, number, number],
    scale: [p.Scale?.X ?? 1, p.Scale?.Y ?? 1, p.Scale?.Z ?? 1].map(F) as [number, number, number],
    transform: [p.Transform?.X ?? 0, p.Transform?.Y ?? 0, p.Transform?.Z ?? 0].map(F) as [number, number, number],
    animReduceRt: F(p.AnimReduceRt ?? 1),
  };
}
/** 0x71026df700 per BoneParam: bind local B (row-major 3×4) and bind scale → new local matrix and scale.
 * swapTransform = hair+0x338 && this bone is the +0x348 bone: t' = t + (Ty, Tz, Tx). sin/cos are SDK libm [근사: JS Math]. */
export function hairArrangeLocal(bind: readonly number[], bindScale: readonly number[], p: HairArrangeParam, swapTransform = false): { matrix: number[]; scale: number[] } {
  const [sx, sy, sz] = p.rotation.map(a => F(Math.sin(F(a))));
  const [cx, cy, cz] = p.rotation.map(a => F(Math.cos(F(a))));
  const v4 = [M(cy, cz), D(M(M(sx, sy), cz), M(sz, cx)), A(M(sx, sz), M(sy, M(cx, cz)))];
  const v6 = [M(sz, cy), A(M(M(sx, sy), sz), M(cx, cz)), D(M(sy, M(sz, cx)), M(sx, cz))];
  const v7 = [F(-sy), M(sx, cy), M(cx, cy)];
  const t = swapTransform ? [p.transform[1], p.transform[2], p.transform[0]] : p.transform;
  const matrix: number[] = [];
  for (let r = 0; r < 3; r++) {
    const b0 = F(bind[4 * r]), b1 = F(bind[4 * r + 1]), b2 = F(bind[4 * r + 2]);
    for (let c = 0; c < 3; c++) matrix.push(F(fma32(v7[c], b2, fma32(v6[c], b1, M(v4[c], b0))) + 0));
    matrix.push(A(A(bind[4 * r + 3], 0), t[r]));
  }
  const scale = [0, 1, 2].map(k => M(bindScale[k], p.scale[k] > F(0.01) ? p.scale[k] : F(0.01)));
  return { matrix, scale };
}

// ---------------------------------------------------------------- damping / integrate
/** Havok f32 log/exp power helper 8A63E0 (every op f32, original constants). */
export function nativePow(base: number, exponent: number): number {
  const U = f32bits, B = bitsf32;
  let x = F(base);
  const sub = x < B(0x00800000);
  if (sub) x = M(x, B(0x4b000000));
  const zbits = ((U(x) + 0xc0cb0000) & 0xff800000) >>> 0;
  let k = M(F(zbits | 0), B(0x34000000));
  k = A(sub ? -23 : 0, k);
  const z = B((U(x) - zbits) >>> 0);
  const z1 = D(z, 1);
  const h = V(1, A(z, 1)), r = M(z1, h);
  const err = M(h, A(M(F(-z1), r), D(z1, A(r, r))));
  const r2 = M(r, r);
  let p = A(M(r2, B(0x3e049000)), B(0x3e1163fe));
  p = A(M(r2, p), B(0x3e4cd0bb));
  p = A(M(r2, p), B(0x3eaaaaa8));
  let t = A(M(r2, err), M(r, M(r, A(0, M(r, A(err, err))))));
  t = A(M(p, t), err);
  t = A(M(M(r, r2), p), t);
  const hi = M(k, B(0x3eb17218)), sumhi = A(hi, r), corr = D(r, D(sumhi, hi));
  t = A(corr, t);
  const low = A(t, M(k, B(0xb082e308)));
  const logx = A(A(sumhi, sumhi), A(low, low));
  const y = M(exponent, logx);
  const n = A(A(M(y, B(0x3fb8aa3b)), B(0x4b400000)), B(0xcb400000));
  const ni = Math.trunc(n);
  const rem = A(A(y, M(n, B(0xbf317200))), M(n, B(0xb5bfbe8e)));
  let pe = A(M(rem, B(0x3ab52000)), B(0x3c09383f));
  for (const c of [0x3d2aad87, 0x3e2aaa19, 0x3efffffa]) pe = A(M(rem, pe), B(c));
  pe = A(M(rem, pe), 1);
  pe = A(M(rem, pe), 1);
  const adjust = ni > 0 ? 0 : 0x83000000;
  let out = M(pe, B((adjust + 0x7f000000) >>> 0));
  out = M(out, B(((ni << 23) - adjust) >>> 0));
  if (y > B(0x42b170a4)) out = B(0x7f7fffee);
  if (y < B(0xc2aea8f6)) out = 0;
  return out;
}
/** DC42A0: effectiveDt = f32(inputDt / f32(scale · substeps)), scale = 1 for instance kind 1. */
export function clothEffectiveDt(inputDt: number, kind: number, timeScale: number, substeps: number): number {
  return V(inputDt, M(kind === 1 ? 1 : timeScale, substeps));
}
/** DC42A0 coefficient: damping ≥ 1 → 0, damping = 0 → 1, else (1 − damping)^effectiveDt. */
export function clothDampingCoefficient(damping: number, effectiveDt: number): number {
  const d = F(damping);
  return d >= 1 ? 0 : d === 0 ? 1 : nativePow(D(1, d), effectiveDt);
}
/** EE41F0 one vec4 lane, force 0: mass/invMass are not cancelled. */
export function clothIntegrateLane(current: number, previous: number, gravity: number, mass: number, invMass: number, coefficient: number, effectiveDt: number): number {
  const dt2 = M(effectiveDt, effectiveDt);
  const accel = M(A(0, M(gravity, mass)), invMass);
  const delta = M(coefficient, D(current, previous));
  return A(A(current, delta), M(dt2, accel));
}

// ---------------------------------------------------------------- links
/** ARM FRSQRTE estimate (independent integer form, r9 cloth_link_runtime.md §6). */
export function frsqrte(v: number): number {
  if (v === 0) return Infinity;
  const bits = f32bits(v), exp = (bits >>> 23) & 255;
  let a = exp & 1 ? ((bits >>> 16) & 127) | 128 : ((bits >>> 15) & 255) | 256;
  a = exp & 1 ? 2 * a + 1 : 4 * Math.floor(a / 2) + 2;
  let b = 512;
  while (a * (b + 1) * (b + 1) < 1 << 28) b++;
  const res = Math.floor((b + 1) / 2);
  return bitsf32((Math.floor((380 - exp) / 2) << 23) | ((res & 255) << 15));
}
function linkFrame(pa: readonly number[], pb: readonly number[]): { d: number[]; inv: number; length: number } {
  const d = [0, 1, 2, 3].map(k => D(pb[k], pa[k]));
  const sq = A(A(M(d[0], d[0]), M(d[1], d[1])), M(d[2], d[2]));
  const est = frsqrte(sq);
  const inv = sq <= 0 ? 0 : M(est, F((3 - sq * M(est, est)) * 0.5));
  return { d, inv, length: M(sq, inv) };
}
function applyLink(pa: number[], pb: number[], d: number[], inv: number, q: number, wa: number, wb: number): void {
  for (let k = 0; k < 4; k++) {
    const diff = M(M(d[k], inv), q);
    pa[k] = A(pa[k], M(diff, wa));
    pb[k] = D(pb[k], M(diff, wb));
  }
}
/** D47BD0 Standard link: stored stiffness × endpoint invMass, no re-division by their sum. */
export function standardLink(pa: number[], pb: number[], restLength: number, stiffness: number, invMassA: number, invMassB: number, scalar: number): void {
  if (!(F(scalar) > 0)) return;
  const { d, inv, length } = linkFrame(pa, pb);
  applyLink(pa, pb, d, inv, M(M(D(length, restLength), stiffness), scalar), invMassA, invMassB);
}
/** D1C354 Bend link: stretch above max, bend below min. */
export function bendLink(pa: number[], pb: number[], bendMinLength: number, stretchMaxLength: number, bendStiffness: number, stretchStiffness: number, invMassA: number, invMassB: number, scalar: number): void {
  if (!(F(scalar) > 0)) return;
  const { d, inv, length } = linkFrame(pa, pb);
  const stretch = M(Math.max(0, D(length, stretchMaxLength)), stretchStiffness);
  const bend = M(Math.max(0, D(bendMinLength, length)), bendStiffness);
  applyLink(pa, pb, d, inv, M(D(stretch, bend), scalar), invMassA, invMassB);
}

/** 0F73368 CullFrame gate: normal path steps on frame % period == phase with f32(period · dt). */
export function clothCullStep(period: number, phase: number, frame: number | null, bypass: boolean, dt: number): number | null {
  if (bypass || period < 2) return F(dt);
  if (frame === null) return M(period, dt);
  return frame % period === phase ? M(period, dt) : null;
}
