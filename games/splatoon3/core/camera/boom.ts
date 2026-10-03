// Original instruction consumers: player_camera §6.8.1 and r9_collision_spring.
// Native input names remain explicit; missing producers are not inferred from unrelated fields.
import { F, add, sub, mul, div, mix, dot, length, normalized, cross, atan2Idx, floatBits, power0 } from "./native_math.ts";
import { clamp01, invLerp01 } from "./curves.ts";
type V = ArrayLike<number>;
export interface BoomState { target: number; ratio: number; rate: number; speed: number; angle: number; under: number }
export interface BoomInput {
  minimum: number; length: number; move: V; vy: number; dc: number; air: number;
  wall: boolean; normalY: number; basis: V; prevBasis: V; aim: V; dir: V;
  ad0: number; d9: boolean; d0: number; blend: number; hitN: V; hitDist: number;
  camDelta: V; atDelta: V; vel: V;
}
export function advanceBoom(s: BoomState, d: BoomInput): void {
  const q = invLerp01(div(d.minimum, d.length), 1, s.target);
  const mv = Array.from(d.move);
  if (d.air >= 4) mv[1] = sub(mv[1], d.vy);
  const dp = mul(dot(mv, d.dir), add(mul(d.dc, -.7), 1));
  const projection = mul(dp, dp < 0 ? -.5 : .5);
  const wallSpeed = d.wall && d.normalY < floatBits(0x3f24360c) ? mul(length(mv), .5) : 0;
  const ai = atan2Idx(length(cross(d.basis, d.prevBasis)), dot(d.basis, d.prevBasis));
  const aa = mul(F(ai), floatBits(0x30c90fdb));
  const wrap = aa > floatBits(0x40490fdb) ? Math.max(add(aa, floatBits(0xc0c90fdb)), floatBits(0xc0490fdb)) : aa;
  const angle = mix(s.angle, clamp01(div(wrap, .01)), .2);
  const z = mul(sub(1, mul(sub(1, d.d0), sub(1, d.d0))), 0);
  const k = add(z, .05);
  let speed = Math.max(wallSpeed, mul(angle, mix(k, .01, q)));
  if (d.ad0 > 0 && !d.d9) speed = Math.max(speed, mul(length(mv), add(mul(q, -.4), .5)));
  if (speed <= s.speed) speed = mix(s.speed, speed, .02);
  const pre = add(s.target, div(Math.max(speed, projection), Math.max(mul(d.length, s.target), d.minimum)));
  const limited = Math.min(pre, clamp01(div(d.hitDist, d.length)));
  let rate: number;
  if (s.ratio <= limited) {
    const delta = sub(limited, s.ratio);
    const base = delta <= 0 ? F(.1) : delta >= 1 ? F(.25) : add(mul(delta, .15), .1);
    rate = add(base, mul(limited, sub(1, base)));
    if (s.rate <= rate) rate = mix(s.rate, rate, .05);
  } else {
    const n = d.hitN, diff = [0, 1, 2].map(i => sub(d.camDelta[i], d.atDelta[i]));
    const nd = dot(n, diff), perp = [0, 1, 2].map(i => sub(diff[i], mul(n[i], nd)));
    const turn = dot([0, 1, 2].map(i => sub(d.aim[i], n[i])), perp);
    const approach = sub(mul(Math.max(turn, 0), mul(Math.max(dot(d.aim, d.vel), 0), .5)), dot(n, d.camDelta));
    const atApproach = dot(n, d.atDelta);
    const w0 = sub(div(add(s.ratio, -.5), -.45), Math.max(sub(s.ratio, limited), 0));
    const w1 = w0 < 0 ? 1 : sub(1, Math.min(w0, 1));
    const w = clamp01(mul(w1, clamp01(div(approach, .3))));
    const wa = clamp01(div(atApproach, -.2));
    const h = atApproach < F(-.001) ? sub(-1, div(approach, atApproach)) : 1;
    const cap = h < 0 ? F(.35) : add(mul(Math.min(h, 1), .35), .35);
    rate = Math.min(add(mul(power0(w, floatBits(0x3fc1dd88)), .9), .1), cap);
    const lower = Math.min(add(mul(power0(wa, floatBits(0x3fc1dd88)), .9), .1), F(.35));
    rate = mix(rate, .25, power0(Math.abs(dot(n, d.aim)), floatBits(0x3fde54e3)));
    if (rate > F(.25) && limited < pre) rate = mix(rate, .25, power0(sub(pre, limited), floatBits(0x3fde54e3)));
    rate = Math.max(rate, lower);
  }
  const blend = d.blend <= F(.1) ? 0 : d.blend >= 1 ? 1 : div(add(d.blend, -.1), .9);
  const target = Math.min(mix(pre, 1, blend), div(d.hitDist, d.length));
  rate = mix(rate, .25, blend);
  s.target = target; s.ratio = mix(s.ratio, target, rate); s.rate = rate;
  s.speed = speed; s.angle = angle; s.under = q;
}
/** C14ec. Keep the original negative h when speed is zero. */
export function forwardCoefficient(vel: V, aim: V, squid: boolean, old: number): number {
  const speed = length(vel), c = Math.max(-1, Math.min(1, dot(normalized(vel), aim)));
  const b = power0(Math.abs(c), floatBits(0x3ea4d3c1));
  const h = Math.min(div(add(mul(speed, b), floatBits(0xba83126e)), floatBits(0x3d48b43a)), F(2.5));
  let k = old;
  if (c <= 0) k = mul(k, add(1, mul(h, floatBits(0xbcf5c280))));
  else if (k < h && squid) k = mix(k, h, .2);
  return mul(k, .97);
}
/** C144/C120 consumer, 0x71024da320..24da5a4. bodyResidual is B210, not B1f8. */
export function collisionSpring(offset: Float32Array, track: Float32Array, input: V, bodyResidual: V, vel: V, aim: V, ratio: number, hold: number): void {
  const n = length(offset);
  const k = n <= 1 ? F(.25) : n >= F(2.5) ? 0 : add(add(mul(div(add(n, -1), -1.5), .25), .95), -.7);
  const damp = add(mul(k, ratio), .7);
  for (let i = 0; i < 3; i++) offset[i] = mul(offset[i], damp);
  if (hold > 0) return;
  const weight = ratio <= F(.4) ? 0 : ratio >= 1 ? 1 : add(div(add(ratio, -.4), .6), 0);
  const v = [0, 1, 2].map(i => add(input[i], mul(weight, bodyResidual[i])));
  const len = length(v), unit = normalized(v), projection = dot(unit, vel);
  const amount = sub(len, projection <= 0 ? Math.min(F(-projection), len) : 0);
  for (let i = 0; i < 3; i++) offset[i] = add(offset[i], mul(unit[i], amount));
  const a = dot(offset, aim);
  if (a > 0) {
    const t = mul(mul(sub(1, ratio), a), -.7);
    for (let i = 0; i < 3; i++) offset[i] = add(offset[i], mul(aim[i], t));
  }
  for (let i = 0; i < 3; i++) track[i] = sub(track[i], offset[i]);
}
/** Bde0 gate followed by C1760 postmix. Caller applies target correction before postmix. */
export function boomPosition(pos: Float32Array, pivot: V, dir: V, ratio: number, len: number, e: number, rigCam: V, gate: number): void {
  if (gate >= 1) return;
  const distance = mul(ratio, len);
  for (let i = 0; i < 3; i++) pos[i] = add(mul(dir[i], distance), pivot[i]);
  const dy = Math.abs(sub(rigCam[1], pivot[1]));
  const horizontal = (v: V) => F(Math.sqrt(add(mul(sub(pivot[0], v[0]), sub(pivot[0], v[0])), mul(sub(pivot[2], v[2]), sub(pivot[2], v[2])))));
  const dr = horizontal(rigCam), da = horizontal(pos);
  if (dr > 0) pos[1] = sub(pos[1], div(mul(sub(add(e, dy), dy), sub(dr, da)), dr));
}
