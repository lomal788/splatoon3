// 탄 바디(phive 탄 바디 0x7105749990) 적분·충돌 응답. 근거: docs/physics/phive_controller.md §6.2~6.4.
// setVelocity 0x71016cb0a0: body+0xc4 = fmul(v, 60), 스텝 0x7103b0a2bc: p1 = fadd(fmul(dt, v60), p0), dt = 0x3c888889.
import { f32 } from "../fmath.ts";
import type { V3 } from "./move.ts";

export const DT = f32(1 / 60);
export const SIXTY = 60;
export const INV60 = f32(0.016666668);
/** [0x7105858358] 접촉 법선 y 임계값(바닥/벽 구분). */
export const FLOOR_NY = f32(0.64144969);

export class BulletBody {
  pos: V3 = [0, 0, 0];
  /** body+0xc4 (유닛/초) */
  velSec: V3 = [0, 0, 0];
  /** body+0xdc 이번 스텝에 쓴 속도 */
  stepVelSec: V3 = [0, 0, 0];
  /** body+0x90 bit1 충돌 끔 */
  collisionOff = false;

  setVelocity(v: V3): void {
    for (let i = 0; i < 3; i++) {
      const s = f32(v[i] * SIXTY);
      this.velSec[i] = s;
      this.stepVelSec[i] = s;
    }
  }

  /** 래퍼 slot10 0x71016cb174: body+0xc4 × 0.016666668 */
  velocity(out: V3): V3 {
    for (let i = 0; i < 3; i++) out[i] = f32(this.velSec[i] * INV60);
    return out;
  }

  /** 스텝 앞부분: +0xdc = +0xc4, p1 = dt·v + p0. 충돌 판정은 호출자가 p0→p1 구간으로 한다. */
  begin(p0: V3, p1: V3): void {
    for (let i = 0; i < 3; i++) {
      this.stepVelSec[i] = this.velSec[i];
      p0[i] = this.pos[i];
      p1[i] = f32(f32(DT * this.velSec[i]) + this.pos[i]);
    }
  }

  /** 막는 접촉이 없을 때: pos = p1 */
  commit(p1: V3): void {
    this.pos[0] = p1[0];
    this.pos[1] = p1[1];
    this.pos[2] = p1[2];
  }

  /** 막는 접촉 최소 비율 f: pos = p0 + f·(p1 − p0) (fsub→fmul→fadd 0x7103b0a90c), +0xc4 = 0 */
  stopAt(p0: V3, p1: V3, f: number): void {
    const t = f32(f);
    for (let i = 0; i < 3; i++) {
      this.pos[i] = f32(p0[i] + f32(t * f32(p1[i] - p0[i])));
      this.velSec[i] = 0;
    }
  }
}
