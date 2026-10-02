// 담당: [physics] — 수직 속도 0x71024a7d00, 점프 판정·대입(메인 계산 0x7102475a54 점프부), 점프 버튼 유지 가산
// 0x7102482df8, 벽 점프 0x7102459630, 최종 속도 합성 0x710245aed8.
// 근거: docs/player/movement_physics.md §6.4·§6.7·§6.8, docs/physics/phive_controller.md §4.2,
// 디컴파일 analysis/decomp/physics/phive_batch3.c, analysis/decomp/physplayer/wallkick.c(0x71024593e8).
import { f32 } from "../fmath.ts";
import * as C from "./consts.ts";
import type { PlayerState } from "./state.ts";

/** 0x71024c9684 — 특수 상태가 없으면 항상 g. */
export function gravity(_p: PlayerState): number {
  return C.GRAVITY;
}

/** 0x71024a7d00 (bodyInAir = Phive 이동 상태가 InAir([1])). 다운 계열 카운터는 없음(0). */
export function verticalUpdate(p: PlayerState, bodyInAir: boolean): void {
  const g = gravity(p);
  const X = p.jump3d;
  let xy = X[1];
  if (C.VY_EPS < xy && bodyInAir) {
    p.vy = f32(xy + p.vy);
    xy = 0;
    X[1] = 0;
  }
  const k = C.JUMP3D_DAMP;
  if (!p.jump3dHold) {
    X[0] = f32(k * X[0]);
    X[1] = f32(k * xy);
    X[2] = f32(k * X[2]);
    if (p.airFrames < C.GRAVITY_START && C.GRAVITY_START <= p.sinceJump) {
      let y = f32(f32(k * xy) - g);
      if (y <= 0) y = 0;
      X[1] = y;
    }
  }
  let vy = f32(C.VY_DAMP * p.vy);
  if (C.GRAVITY_START <= p.airFrames) vy = f32(vy - g);
  p.vy = vy;
  const sum = f32(vy + X[1]);
  if (C.VY_EPS < sum || C.AIR_DAMP_START <= p.airFrames) p.vySum = sum;
  p.sinceJump++;
  if (sum < C.VY_EPS) p.jumpKeep = 0;
}

/** 점프 초기 속도(§6.4). 적 잉크 위면 기어 OpInk_JumpVel 쪽으로 보간. */
export function jumpSpeed(p: PlayerState): number {
  let jump = C.JUMP_VEL;
  const e = p.step.enemyMove;
  if (e > 0) {
    const op = p.gear.opJump;
    const j2 = f32(jump + f32(f32(op - jump) * e));
    if (j2 < jump) jump = j2;
  }
  return jump;
}

/** 0x71024593e8 — 스틱이 벽 반대쪽(조준 기준 2D)으로 0.4 이상, 60° 안이면 참. */
export function wallKickStick(p: PlayerState, aim: ArrayLike<number>): boolean {
  let sx = p.stick[0], sy = p.stick[1];
  const sl = f32(Math.sqrt(f32(f32(sx * sx) + f32(sy * sy))));
  if (0 < sl) {
    const i = f32(1 / sl);
    sx = f32(i * sx); sy = f32(i * sy);
  }
  if (!(C.WALLKICK_STICK_MIN <= sl)) return false;
  const N = p.floorN;
  const ax = aim[0], ay = aim[1], az = aim[2];
  let f6 = f32(f32(f32(ax * N[0]) + f32(ay * N[1])) + f32(az * N[2]));
  const a3 = f32(ay * 0);
  let f7 = f32(f32(f32(f32(ax - a3) * N[2]) + f32(N[0] * f32(a3 - az))) + f32(N[1] * f32(f32(az * 0) - f32(ax * 0))));
  const l = f32(Math.sqrt(f32(f32(f6 * f6) + f32(f7 * f7))));
  if (0 < l) {
    const i = f32(1 / l);
    f7 = f32(i * f7); f6 = f32(i * f6);
  }
  let d = f32(f32(f7 * sx) + f32(f6 * sy));
  if (d < -0.99999) d = -0.99999;
  const ang = d > 1 ? 0 : f32(Math.acos(d));
  return ang <= f32(C.WALLKICK_ANGLE * f32(0.017453292));
}

/**
 * 점프 판정과 대입(§6.4). 성공하면 true(점프 시작 처리는 호출자: 상태 요청·카운터 리셋).
 * wallKick 이 참이면 벽 점프 발사(§6.8)로 처리한다.
 */
export function tryJump(p: PlayerState, wallKick: boolean): "none" | "jump" | "wall" {
  if (!p.jumpHeld) return "none";
  let ok = p.airFrames < C.JUMP_AIR_MAX;
  if (!wallKick) ok = ok && C.JUMP_REJUMP + 1 < p.sinceJump;
  const canJump = ok && (wallKick || !p.jump3dHold);
  if (!canJump || p.ceilTimer >= 1) return "none";
  if (wallKick) {
    launchWallJump(p);
    return "wall";
  }
  const jump = jumpSpeed(p);
  if (!(p.vy < jump)) return "none";
  if (p.floorN[1] < C.FLOOR_NY && p.wallCling) {
    p.jump3d[0] = 0; p.jump3d[1] = jump; p.jump3d[2] = 0;
    p.jumpKeep = 0;
  } else {
    p.vy = jump;
  }
  if (p.floorN[1] < 1) {
    // 평지가 아니면 이동 속도를 바닥 기준으로 돌려 y 성분 0, 크기 유지 (raw 5600~5690행 요약)
    const v = p.vel;
    const l = f32(Math.sqrt(f32(f32(f32(v[0] * v[0]) + f32(v[1] * v[1])) + f32(v[2] * v[2]))));
    const h = f32(Math.sqrt(f32(f32(v[0] * v[0]) + f32(v[2] * v[2]))));
    if (h > 0) {
      const s = f32(l / h);
      v[0] = f32(v[0] * s); v[2] = f32(v[2] * s);
    }
    v[1] = 0;
  }
  return "jump";
}

/** 벽 점프 0x7102459630(벽 점프 쪽만; 오징어 롤은 미구현). */
function launchWallJump(p: PlayerState): void {
  const L = p.launch;
  L.wasSquid = p.state >= 0x82 && p.state <= 0x90;
  L.active = true;
  L.apply = true;
  L.wallJump = true;
  const n = p.floorN;
  let hx = n[0], hz = n[2];
  const hl = f32(Math.sqrt(f32(f32(hx * hx) + f32(hz * hz))));
  if (hl > 0) {
    const i = f32(1 / hl);
    hx = f32(hx * i); hz = f32(hz * i);
  }
  L.vel[0] = f32(hx * C.WALLKICK_H);
  L.vel[1] = 0;
  L.vel[2] = f32(hz * C.WALLKICK_H);
  const cnt = Math.min(L.count, 10);
  let kd = 1;
  for (let i = 0; i < cnt; i++) kd = f32(kd * p.gear.somersaultKd);
  L.vel[0] = f32(L.vel[0] * kd); L.vel[2] = f32(L.vel[2] * kd);
  p.slide[0] = 0; p.slide[1] = 0; p.slide[2] = 0;
  p.jump3d[0] = 0; p.jump3d[1] = 0; p.jump3d[2] = 0;
  let v = f32(C.WALLKICK_V + 0); // 0.23 + 0·max(0, 이동 y + 3D 점프 y)
  if (C.WALLKICK_VMAX < v) v = C.WALLKICK_VMAX;
  p.vy = v;
}

/** 점프 버튼 유지 가산 0x7102482df8. */
export function jumpHoldAdd(p: PlayerState): void {
  if (!(p.groundFrames < 1)) return;
  if (!(C.VY_EPS < f32(p.vy + p.jump3d[1]))) return;
  if (!p.jumpHeld) return;
  const L = p.launch;
  if (L.active && !L.wallJump && L.wasSquid) return; // 발사 +0x7f5 && 오징어 발사 +0x7f7 → 0
  // 0x710249bb60: 본체+0xa38 > 0 일 때만, min(a38, 1 − own²·x) (x 는 contact.ts 와 같은 추정)
  let s = p.slideAmt > 0 ? p.slideAmt : 0;
  if (s > 0 && p.squidRequest) {
    const lim = f32(f32(f32(p.step.own * p.step.own) * -1) + 1);
    if (lim < s) s = lim;
  }
  const add = f32(C.JUMP_HOLD_ADD * f32(1 - s));
  if (C.VY_EPS < p.jump3d[1]) p.jump3d[1] = f32(p.jump3d[1] + add);
  else p.vy = f32(p.vy + add);
}

/** 최종 속도 합성 0x710245aed8 (대시 패널·레일·특수 없음). */
export function composeFinal(p: PlayerState): void {
  const F = p.final, v = p.vel, X = p.jump3d, T = p.takeoff, S = p.slide;
  for (let i = 0; i < 3; i++) F[i] = f32(f32(f32(f32(0 + v[i]) + 0) + X[i]) + T[i]);
  F[1] = f32(F[1] + p.vy);
  // [0x71058bbb83] == 0 이므로 벽·경사 미끄럼 속도(본체+0xa2c)를 더한다
  F[0] = f32(F[0] + S[0]);
  F[1] = f32(F[1] + S[1]);
  F[2] = f32(F[2] + S[2]);
}
