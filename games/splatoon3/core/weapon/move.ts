// 탄 이동 상태 머신(spl::BulletMoveState GoStraight/Brake/Free). 근거: docs/weapon/shooter_bullet.md §5.1~5.2,
// GoStraight 0x71017657f4, Brake 0x71017683fc(asm 연산 순서), Free 0x71017659a4, 상태 머신 0x71017697f8.
import { f32 } from "../fmath.ts";
import type { MoveParam } from "./params.ts";

export const GO_STRAIGHT = 0;
export const BRAKE = 1;
export const FREE = 2;

export interface MoveSM {
  state: number;
  frame: number;
}

export type V3 = [number, number, number];

export function initialState(p: MoveParam): number {
  return p.GoStraightToBrakeStateFrame === 0 ? FREE : GO_STRAIGHT;
}

function stepGoStraight(p: MoveParam, v: V3, frame: number, out: V3): boolean {
  out[0] = v[0];
  out[1] = v[1];
  out[2] = v[2];
  return frame >= p.GoStraightToBrakeStateFrame - 1;
}

function stepBrake(p: MoveParam, v: V3, frame: number, out: V3): boolean {
  let x = v[0], y = v[1], z = v[2];
  if (frame === 0) {
    const mx = f32(p.GoStraightStateEndMaxSpeed);
    const l2 = f32(f32(f32(x * x) + f32(y * y)) + f32(z * z));
    if (l2 > f32(mx * mx)) {
      const l = f32(Math.sqrt(l2));
      if (l > 0) {
        const s = f32(mx / l);
        x = f32(x * s);
        y = f32(y * s);
        z = f32(z * s);
      }
    }
  }
  const r = f32(p.BrakeAirResist), g = f32(p.BrakeGravity);
  const bx = f32(x - f32(x * r));
  const by = f32(y + f32(f32(y * -r) - g));
  const bz = f32(z - f32(z * r));
  const vy = f32(p.BrakeToFreeVelocityY), vxz = f32(p.BrakeToFreeVelocityXZ), n = p.BrakeToFreeStateFrame;
  if (!(by < vy)) {
    out[0] = bx; out[1] = by; out[2] = bz;
    return false;
  }
  const h2 = f32(f32(bx * bx) + f32(bz * bz));
  if (!(h2 < f32(vxz * vxz)) && n > frame) {
    out[0] = bx; out[1] = by; out[2] = bz;
    return false;
  }
  const dy = f32(by - y);
  let t1 = 0;
  if (y >= vy) t1 = Math.min(f32(f32(vy - y) / dy), 1);
  const hp = f32(Math.sqrt(f32(f32(x * x) + f32(z * z))));
  let t2 = 0;
  if (!(hp < vxz)) {
    const hn = f32(Math.sqrt(h2));
    const dh = f32(hn - hp);
    if (dh !== 0) t2 = Math.min(f32(f32(vxz - hp) / dh), 1);
  }
  const t3 = n < frame ? 0 : 1;
  const m = t2 < t3 ? t2 : t3;
  const t = t1 > m ? t1 : m;
  const ix = f32(x + f32(f32(bx - x) * t));
  const iy = f32(y + f32(dy * t));
  const iz = f32(z + f32(f32(bz - z) * t));
  const fr = f32(p.FreeAirResist), fg = f32(p.FreeGravity);
  const s = f32(1 - t);
  out[0] = f32(ix + f32(s * f32(f32(ix - f32(ix * fr)) - ix)));
  out[1] = f32(iy + f32(s * f32(f32(iy + f32(f32(iy * -fr) - fg)) - iy)));
  out[2] = f32(iz + f32(s * f32(f32(iz - f32(iz * fr)) - iz)));
  return true;
}

function stepFree(p: MoveParam, v: V3, _frame: number, out: V3): boolean {
  const x = v[0], y = v[1], z = v[2];
  const fr = f32(p.FreeAirResist), fg = f32(p.FreeGravity);
  out[0] = f32(x - f32(x * fr));
  out[1] = f32(y + f32(f32(y * -fr) - fg));
  out[2] = f32(z - f32(z * fr));
  return false;
}

const STEPS = [stepGoStraight, stepBrake, stepFree];

/** 0x71017697f8: 현재 상태 스텝 → false 면 frame++, true 면 다음 상태·frame=0 (3 이상이면 표 0번). */
export function stepMoveSM(sm: MoveSM, p: MoveParam, v: V3, out: V3): void {
  const fn = STEPS[sm.state] ?? STEPS[0];
  if (fn(p, v, sm.frame, out)) {
    sm.state += 1;
    sm.frame = 0;
  } else sm.frame += 1;
}

/** BulletSimple 슬롯54(0x7101763a10) age==1 재정규화: len² = z² + (x² + y²), v *= speed/len. */
export function renormalize(v: V3, speed: number): void {
  const l2 = f32(f32(v[2] * v[2]) + f32(f32(v[0] * v[0]) + f32(v[1] * v[1])));
  const l = f32(Math.sqrt(l2));
  if (l > 0) {
    const s = f32(f32(speed) / l);
    v[0] = f32(v[0] * s);
    v[1] = f32(v[1] * s);
    v[2] = f32(v[2] * s);
  }
}
