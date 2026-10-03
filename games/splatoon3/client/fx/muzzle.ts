import type { EmitMatrix } from "./particles.ts";

/** The local render pose supplies this visual attachment, independently of bullet spawn position. */
export interface MuzzlePose {
  owner: unknown;
  frame: number;
  source: "Weapon_R/Root/Muzzle";
  matrix: number[];
}

/** three column-major -> native emitter basis columns. Preserve bone scale and roll. */
export function muzzlePoseMatrix(pose: unknown, owner: unknown): EmitMatrix | null {
  if (!pose || typeof pose !== "object") return null;
  const p = pose as Partial<MuzzlePose>;
  if (p.source !== "Weapon_R/Root/Muzzle" || p.owner !== owner || !Array.isArray(p.matrix) || p.matrix.length !== 16 || !p.matrix.every(Number.isFinite)) return null;
  const e = p.matrix;
  return { o: [e[12], e[13], e[14]], x: [e[0], e[1], e[2]], y: [e[4], e[5], e[6]], z: [e[8], e[9], e[10]] };
}

/** Original 2579244..25792c8 reader; caller must supply its actual selected bone, not infer its name. */
export function nativeHeadingDotReader(columnX: ArrayLike<number>, rigForward: ArrayLike<number>): number {
  const f = Math.fround, x = f(columnX[0]), z = f(columnX[2]);
  const length = f(Math.sqrt(f(f(f(x*x) + 0) + f(z*z))));
  let vx = f(-x), vy = 0, vz = f(-z);
  if (length > 0) {
    const k = f(1 / length);
    vx = f(k * vx); vy = f(k * 0); vz = f(k * vz);
  }
  return f(f(f(vx * f(rigForward[0])) + f(vy * f(rigForward[1]))) + f(vz * f(rigForward[2])));
}
