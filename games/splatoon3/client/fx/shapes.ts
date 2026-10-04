// nn::vfx emitter volume shapes (jump table 0x710540fea8), ported from the original functions.
//   0 point 0x710081fa94, 1 circle 0x710081facc, 2 circle (divided) 0x710081fcac,
//   12 line 0x7100821c28, 13 line (divided) 0x7100821cb0, 14 rectangle perimeter 0x7100821dec.
// Verified against unicorn runs of the originals: tests/fixtures/r11_fx_shapes.json (web/tools/r11_gfx_fx_shape_emu.py).
// Other numbers are [미확정] and fall back to the point shape.
import { VFX_DIR_TABLE } from "./vfx_random_table.ts";

type V3 = [number, number, number];
const f32 = Math.fround;
const TWO_PI = f32(Math.PI * 2);

/** Per-emitter random state: E+0xB8 seed split (0x7100828004): counter = seed>>16 (E+0xBA), lcg = seed (E+0xBC). */
export interface ShapeState {
  lcg: number;
  counter: number;
  seq: number;
}

export function shapeState(seed: number): ShapeState {
  return { lcg: seed >>> 0, counter: (seed >>> 16) & 0xffff, seq: 0 };
}

/** LCG 0x41c64e6d/0x3039: returns current/2^32 and advances (E+0xBC). */
export function lcgNext(s: ShapeState): number {
  const u = s.lcg;
  s.lcg = (Math.imul(u, 0x41c64e6d) + 0x3039) >>> 0;
  return f32(f32(u) * 2.3283064e-10);
}

/** DAT_71057d52f8[E+0xBA++ & 0x1ff] */
export function dirTable(s: ShapeState): V3 {
  const k = s.counter & 0x1ff;
  s.counter = (s.counter + 1) & 0xffff;
  return [VFX_DIR_TABLE[k * 3], VFX_DIR_TABLE[k * 3 + 1], VFX_DIR_TABLE[k * 3 + 2]];
}

/** Original shape inputs (ResEmitter bytes). */
export interface ShapeRes {
  volumeType: number;
  sweepStartRandom: number; // +0xB81
  sweepLongitude: number; // +0xB88
  sweepStart: number; // +0xB90
  sweepRandom: number; // +0xB94
  lineCenter: number; // +0xB9C
  lineLength: number; // +0xBA0
  volumeRadius: V3; // +0xBA4
  divisionMode: number; // +0xBBC (0 by-count, 1 random, 2 sequential)
  divisionCount: number; // +0xBC8
  divisionRandom: number; // +0xBCC (%)
  lineDivisionCount: number; // +0xBD0
  lineDivisionRandom: number; // +0xBD4 (u32 %)
}

/**
 * Emission count multiplier of 0x710081e070 for division shapes (2 and 13, mode 0): (n − int(u·pct·0.01·n))·count.
 * `u` is the per-emission LCG draw of 0x710081e070 (also passed to each particle as s0).
 */
export function divisionCount(r: ShapeRes, u: number, count: number): number {
  if (r.divisionMode !== 0) return count;
  if (r.volumeType === 2) return (r.divisionCount - Math.trunc(f32(f32(f32(u * f32(r.divisionRandom >>> 0)) * f32(0.01)) * r.divisionCount))) * count;
  if (r.volumeType === 13) return (r.lineDivisionCount - Math.trunc(f32(f32(f32(u * f32(r.lineDivisionRandom >>> 0)) * f32(0.01)) * r.lineDivisionCount))) * count;
  return count;
}

/** Returns local position and direction (already × allDirectionVel·set scale = `adv`), or null when the shape rejects. */
export function nativeShape(r: ShapeRes, st: ShapeState, s0: number, index: number, adv: number, formScale: V3): { pos: V3; dir: V3 } | null {
  const sx = f32(formScale[0]), sz = f32(formScale[2]);
  switch (r.volumeType) {
    case 1: {
      let th = r.sweepStartRandom ? f32(f32(Math.PI * s0) * 2) : f32(r.sweepStart);
      const u = lcgNext(st);
      th = f32(f32(th + f32(r.sweepLongitude * u)) - f32(r.sweepLongitude * 0.5));
      const s = Math.sin(th), c = Math.cos(th);
      return { pos: [s * r.volumeRadius[0] * sx, 0, c * r.volumeRadius[2] * sz], dir: [s * adv, 0, c * adv] };
    }
    case 2: {
      let th = r.sweepStartRandom ? f32(f32(f32(Math.PI) * s0) + f32(f32(Math.PI) * s0)) : f32(r.sweepStart);
      const full = f32(r.sweepLongitude) === f32(TWO_PI);
      let n = r.divisionCount | 0, i6: number, idx: number;
      if (r.divisionMode === 0) {
        n = n - Math.trunc(f32(f32(f32(f32(r.divisionRandom >>> 0) * s0) * f32(0.01)) * n));
        i6 = n - (!full && n > 1 ? 1 : 0);
        const div = i6 + 1;
        idx = div !== 0 ? index - Math.trunc(index / div) * div : index;
      } else {
        i6 = n - (n > 1 && !full ? 1 : 0);
        if (r.divisionMode === 2) {
          const cur = st.seq;
          idx = n !== 0 ? cur - Math.trunc(cur / n) * n : cur;
          st.seq = cur + 1 < n ? cur + 1 : 0;
        } else {
          idx = Math.trunc(f32(lcgNext(st) * n));
        }
      }
      const u = f32(lcgNext(st) - 0.5);
      th = f32(f32(f32(th + f32(f32(r.sweepLongitude / i6) * idx)) + f32(r.sweepLongitude * -0.5)) + f32(r.sweepRandom * f32(u + u)));
      const s = Math.sin(th), c = Math.cos(th);
      return { pos: [s * r.volumeRadius[0] * sx, 0, r.volumeRadius[2] * sz * c], dir: [s * adv, 0, adv * c] };
    }
    case 12: {
      const L = f32(r.lineLength * sz), c = r.lineCenter;
      const u = lcgNext(st);
      return { pos: [0, 0, f32(L * u) - f32(f32(L + f32(L * c)) * 0.5)], dir: [0, 0, adv] };
    }
    case 13: {
      const L = f32(r.lineLength * sz), c = r.lineCenter;
      let n = r.lineDivisionCount | 0, i: number;
      if (r.divisionMode === 2) {
        i = n !== 0 ? st.seq % n : 0;
        st.seq = st.seq + 1 < n ? st.seq + 1 : 0;
      } else if (r.divisionMode === 1) {
        i = Math.trunc(f32(lcgNext(st) * n));
      } else {
        i = n !== 0 ? index - Math.trunc(index / n) * n : index;
        if (r.divisionMode === 0) n = n - Math.trunc(f32(f32(f32(f32(r.lineDivisionRandom >>> 0) * s0) * f32(0.01)) * n));
      }
      const t = n - 1 !== 0 ? f32(f32(1 / (n - 1)) * i) : 0.5;
      return { pos: [0, 0, f32(L * t) - f32(f32(L + f32(L * c)) * 0.5)], dir: [0, 0, adv] };
    }
    case 14: {
      const X = f32(r.volumeRadius[0] * sx), Z = f32(r.volumeRadius[2] * sz);
      const raw = (): number => { const u = st.lcg; st.lcg = (Math.imul(u, 0x41c64e6d) + 0x3039) >>> 0; return u; };
      const s0r = raw(), s1 = raw(), s2 = raw(), s3 = raw();
      let x: number, z: number;
      if (s0r < 0x7fffffff) { x = f32(X * f32(f32(f32(s2) * 2.3283064e-10) * 2 - 1)); z = s1 > 0x7ffffffe ? -Z : Z; }
      else { x = s1 > 0x7ffffffe ? -X : X; z = f32(Z * f32(f32(f32(s3) * 2.3283064e-10) * 2 - 1)); }
      const l = Math.hypot(x, z);
      return { pos: [x, 0, z], dir: l > 0 ? [x / l * adv, 0, z / l * adv] : [0, 0, 0] };
    }
    default: {
      const d = dirTable(st);
      return { pos: [0, 0, 0], dir: [d[0] * adv, d[1] * adv, d[2] * adv] };
    }
  }
}
