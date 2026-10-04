// Model LOD selector 0x7103788760, distance mode (lod_runtime.md §6). Not a Euclidean origin distance:
// bounding-sphere view-space Z, radius, global bias (25 when the type4 getter < 0.9), hysteresis 10.
const F = Math.fround;

export interface LodInput {
  /** Bounding sphere centre in view space (negative in front of the camera). */
  zView: number;
  radius: number;
  /** Threshold record [Start, 2·Start−End, 1/(End−Start)]: Start and inverse gap. */
  start: number;
  inverseGap: number;
  /** viewRecord+8, passed as the selector float. Its producer is [미확정]; never substitute a guessed value. */
  viewInput: number;
  /** Globals 0x7105999d5c / 0x7105999d60 (game init: hysteresis 10; bias 25 or 0 per frame). */
  bias: number;
  hysteresis: number;
  count: number;
  minimum: number;
  old: number;
}

const trunc = (x: number): number => Math.trunc(F(x));

export function lodStageDistance(i: LodInput): number {
  const T = F(F(F(F(i.zView) + F(i.start)) + F(i.radius)) + F(i.bias));
  if (i.count < 2 || !(F(i.viewInput) > T)) return i.minimum & 255;
  const inv = F(i.inverseGap);
  const q = F(F(F(i.viewInput) - T) * inv);
  const n2 = F(i.count - 2);
  if (F(i.hysteresis) <= 0) return (q <= 1 ? trunc(F(F(q * n2) + 1)) : i.count - 1) & 255;
  const lo = F(q - F(inv * F(i.hysteresis)));
  if (lo > 1) return (i.count - 1) & 255;
  const next = Math.max(i.minimum, trunc(F(F(lo * n2) + 1)));
  const hi = trunc(F(F(q * n2) + 1));
  return (next !== i.old && i.old !== hi ? next : i.old) & 255;
}

/** Player FMDL names (Player00, Player00_Hlf, Squid …) are not LODThreshold row keys → Default 20/50. */
export const LOD_DEFAULT = { start: 20, end: 50 } as const;
