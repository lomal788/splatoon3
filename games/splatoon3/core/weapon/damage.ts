// 탄 데미지·충돌 반경·수신 배율·넉백. 근거: docs/combat/damage_hit.md §6.1(0x71017506d0), §6.2(0x71018a6b68/0x71018a6fe4),
// §6.4(0x7101a86ec0 배율 곱 fcvtzs((rate+1e-5)*dmg)), §6.5(0x7101e66c4c).
import { f32 } from "../fmath.ts";
import type { V3 } from "./move.ts";
import type { CollisionParam, DamageParam } from "./params.ts";

export function shooterDamage(age: number, p: DamageParam): number {
  let denom = (p.ReduceEndFrame - p.ReduceStartFrame) | 0;
  if (denom === 0) denom = 1;
  const t = f32(f32((age - p.ReduceStartFrame + 1) | 0) / f32(denom));
  let t1 = Math.min(t, 1);
  if (t < 0) t1 = 0;
  const mx = f32(p.ValueMax);
  const d = f32(f32(f32(f32(p.ValueMin) - mx) * t1) + mx);
  return Math.trunc(d) | 0;
}

export function bulletRadius(age: number, init: number, end: number, changeFrame: number): number {
  if (changeFrame === 0) return f32(end);
  let t = Math.min(f32(f32(age) / f32(changeFrame)), 1);
  if (t < 0) t = 0;
  const r = f32(f32(init) + f32(t * f32(f32(end) - f32(init))));
  const lo = f32(0.02);
  return r > lo ? r : lo;
}

export function fieldRadius(age: number, p: CollisionParam): number {
  return bulletRadius(age, p.InitRadiusForField, p.EndRadiusForField, p.ChangeFrameForField);
}

export function playerRadius(age: number, p: CollisionParam): number {
  return bulletRadius(age, p.InitRadiusForPlayer, p.EndRadiusForPlayer, p.ChangeFrameForPlayer);
}

/** DamageRateInfo 셀 조회(0x7101a856e8): 표·셀·DamageRate 가 없으면 1.0, 빈 이름은 "Default". */
export function damageRate(tables: Record<string, unknown> | undefined, row: string, col: string): number {
  const r = row || "Default", cl = col || "Default";
  const info = tables?.["damage_rate_info"] as { default?: number; rows?: Record<string, Record<string, number>> } | undefined;
  if (info && info.rows) {
    const v = info.rows[r]?.[cl];
    return typeof v === "number" ? v : typeof info.default === "number" ? info.default : 1;
  }
  const key = `${r}___${cl}`;
  const t = (tables?.["damage_rate"] ?? tables?.["DamageRateInfoConfig"]) as Record<string, unknown> | undefined;
  if (!t) return 1;
  const cells = ("CellList" in t ? t.CellList : t) as Record<string, unknown>;
  const c = cells[key];
  if (typeof c === "number") return c;
  if (c && typeof c === "object" && typeof (c as Record<string, unknown>).DamageRate === "number") return (c as { DamageRate: number }).DamageRate;
  return 1;
}

/** 수신 배율 적용: fcvtzs((rate + 1e-5) × f32(dmg)), 99999 초과면 99998. */
export function applyRate(dmg: number, rate: number): number {
  let v = Math.trunc(f32(f32(f32(rate) + f32(1e-5)) * f32(dmg))) | 0;
  if (v > 99999) v = 99998;
  return v;
}

/** 0x7101e66c4c 슈터 인자 {95.0, 300, 280.0, 2000, 0.0}, up = (0,1,0). */
const KB = { lo: 95, a: 300, hi: 280, b: 2000 };

export function knockback(dmg: number, vel: V3, out: V3): V3 {
  const { lo, a, hi, b } = KB;
  const l = f32(Math.sqrt(f32(f32(f32(vel[0] * vel[0]) + f32(vel[1] * vel[1])) + f32(vel[2] * vel[2]))));
  let dx = vel[0], dy = vel[1], dz = vel[2];
  if (l > 0) {
    const inv = f32(1 / l);
    dx = f32(dx * inv);
    dy = f32(dy * inv);
    dz = f32(dz * inv);
  }
  let t = b === a ? 1 : f32(f32(dmg - a) / f32(b - a));
  t = t < 0 ? 0 : t > 1 ? 1 : t;
  const mag = f32(lo + f32(f32(hi - lo) * t));
  out[0] = f32(dx * mag);
  out[1] = f32(dy * mag);
  out[2] = f32(dz * mag);
  if (out[1] !== 0) out[1] = f32(out[1] - out[1]);
  return out;
}
