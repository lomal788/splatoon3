// 담당: [physics] — 수직 속도 0x71024a7d00, 점프 판정·대입(메인 계산 0x7102475a54 점프부), 점프 버튼 유지 가산
// 0x7102482df8, 벽 점프 0x7102459630, 최종 속도 합성 0x710245aed8.
// 근거: docs/player/movement_physics.md §6.4·§6.7·§6.8, docs/physics/phive_controller.md §4.2,
// 디컴파일 analysis/decomp/physics/phive_batch3.c, analysis/decomp/physplayer/wallkick.c(0x71024593e8).
import { f32 } from "../fmath.ts";
import { Btn } from "../input.ts";
import * as C from "./consts.ts";
import { historyAt, rising, squidInk } from "./move.ts";
import { requestJumpState, requestState } from "./sm.ts";
import type { MoveHistoryEntry, PlayerState } from "./state.ts";

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

/** 0x71024593e8 — 스틱이 벽 반대쪽(조준 기준 2D)으로 0.4 이상, 60° 안이면 참. 본체+0xaec > 0 이면 컨트롤러 원값을 읽는다. acosf 는 libm(Math.acos + f32). */
export function wallKickStick(p: PlayerState, aim: ArrayLike<number>): boolean {
  let sx = p.stick[0], sy = p.stick[1];
  if (0 < p.stickLock) { sx = p.stickSrc[0]; sy = p.stickSrc[1]; }
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
  if (d < -0.99999) d = Math.fround(-0.99999);
  const ang = d > 1 ? 0 : f32(Math.acos(d));
  return ang <= f32(C.WALLKICK_ANGLE * f32(0.017453292));
}

export interface JumpCtx {
  /** 조준 수평 방향(본체+0x538 = PlayerCamera+0x1a4) */
  aim: ArrayLike<number>;
  /** 게임 프레임([*0x710580e758]+0x148) */
  frame: number;
  shooting: boolean;
}

/** 점프 시작 0x71024a8000(…, a, b): a·b 가 모두 0 일 때만 상태 요청, +0x734 = 0, +0x77c = 0. */
export function jumpStart(p: PlayerState, shooting: boolean, request: boolean): void {
  if (request) requestJumpState(p, shooting);
  p.sinceJump = 0;
  p.jumpKeep = 0;
}

/** 0x7102459b44~0x7102459bb8: PlayerParam+0x140 을 max(0, min(n, 10))번 연속 곱한 배율(f = kd·f, powf 아님). */
export function launchDamping(n: number, kd: number): number {
  let f = 1;
  if (0 < n) {
    const k = n < C.LAUNCH_KD_MAX ? n : C.LAUNCH_KD_MAX;
    for (let i = 0; i < k; i++) f = f32(kd * f);
  }
  return f;
}

/** 벽 점프·오징어 롤 발사 0x7102459630(…, roll) — movement_physics.md §6.8. */
export function launch(p: PlayerState, ctx: JumpCtx, roll: boolean): void {
  const L = p.launch;
  L.wasSquid = p.state >= 0x82 && p.state <= 0x90;
  L.active = true;
  L.active2 = true;
  L.apply = true;
  L.height = p.pos[1];
  L.wallJump = !roll;
  if (roll) {
    const sx = p.stick[0], sy = p.stick[1], a = ctx.aim;
    let x = f32(f32(sy * a[0]) + f32(f32(f32(a[1] * 0) - a[2]) * sx));
    let z = f32(f32(sy * a[2]) + f32(f32(a[0] - f32(a[1] * 0)) * sx));
    let y = f32(f32(sy * a[1]) + f32(sx * f32(f32(a[2] * 0) - f32(a[0] * 0))));
    const l = f32(Math.sqrt(f32(f32(f32(z * z) + f32(x * x)) + f32(y * y))));
    if (0 < l) {
      const i = f32(1 / l);
      x = f32(i * x); y = f32(i * y); z = f32(i * z);
    }
    const sp = L.speed;
    L.vel[0] = f32(f32(x * sp) * C.ROLL_SPEED_K);
    L.vel[1] = f32(f32(y * sp) * C.ROLL_SPEED_K);
    L.vel[2] = f32(f32(z * sp) * C.ROLL_SPEED_K);
    L.dir[0] = x; L.dir[1] = y; L.dir[2] = z;
  } else {
    const n = p.floorN;
    let hx = n[0], hy = 0, hz = n[2];
    const l = f32(Math.sqrt(f32(f32(f32(hx * hx) + 0) + f32(hz * hz))));
    if (0 < l) {
      const i = f32(1 / l);
      hx = f32(i * hx); hy = f32(i * hy); hz = f32(i * hz);
    }
    L.vel[0] = f32(C.WALLKICK_H * hx);
    L.vel[1] = f32(C.WALLKICK_H * hy);
    L.vel[2] = f32(C.WALLKICK_H * hz);
    L.dir[0] = -0; L.dir[1] = -1; L.dir[2] = -0;
    L.lock = C.STICK_LOCK_WALLJUMP;
    let sx = p.stickSrc[0], sy = p.stickSrc[1];
    const sl = f32(Math.sqrt(f32(f32(sx * sx) + f32(sy * sy))));
    if (0 < sl) {
      sx = f32(f32(1 / sl) * sx); sy = f32(f32(1 / sl) * sy);
    }
    L.lockStick[0] = sx; L.lockStick[1] = sy;
  }
  const kd = launchDamping(L.count, p.gear.somersaultKd);
  L.vel[0] = f32(kd * L.vel[0]);
  L.vel[1] = f32(kd * L.vel[1]);
  L.vel[2] = f32(kd * L.vel[2]);
  if (!roll) {
    p.slide[1] = 0;
    p.slideAmt = 0;
    let s = f32(p.vel[1] + p.jump3d[1]);
    if (s <= 0) s = 0;
    const v = f32(C.WALLKICK_V + f32(C.WALLKICK_VK * s));
    p.jump3d[0] = 0; p.jump3d[1] = 0; p.jump3d[2] = 0;
    p.vy = v <= C.WALLKICK_VMAX ? v : C.WALLKICK_VMAX;
    jumpStart(p, ctx.shooting, false);
  }
  L.count = (L.count + 1) | 0;
  L.frame = Math.max(ctx.frame | 0, 0);
  if (L.wasSquid && p.state !== 0x8d) requestState(p, 0x8d, 1, true);
  if (p.aimHold < 6) p.aimHold = 6;
}

function scanHistory(p: PlayerState, fn: (e: MoveHistoryEntry, k: number) => void): void {
  const n = Math.min(C.HISTORY_SCAN, p.history.count);
  for (let k = 0; k < n; k++) fn(historyAt(p, k), k);
}

/**
 * 점프 판정과 대입(§6.4): 벽 차기(§6.4.1)·오징어 롤(§6.4.3) 포함. 점프 시작(0x71024a8000)은 여기서 한다.
 * kind: "jump" 일반 대입, "wall" 벽 차기 발사. roll = 이번 프레임 롤 발사.
 */
export function tryJump(p: PlayerState, ctx: JumpCtx): { kind: "none" | "jump" | "wall"; roll: boolean } {
  const none = { kind: "none" as const, roll: false };
  if (!p.jumpHeld) return none;
  const L = p.launch;
  let ok = p.airFrames < C.JUMP_AIR_MAX;
  let wallKick = false;
  if (!L.active && p.floorN[1] < C.FLOOR_NY && p.jumpPressed && p.history.count > 0) {
    let recentWall = false;
    scanHistory(p, (e, k) => { if (e.wall && k < C.HISTORY_RECENT && !recentWall) recentWall = e.squidInk; });
    if (recentWall && wallKickStick(p, ctx.aim)) wallKick = true;
  }
  if (!wallKick) ok = ok && C.JUMP_REJUMP + 1 < p.sinceJump;
  const canJump = ok && (wallKick || !p.jump3dHold);
  if (!canJump || p.ceilTimer >= 1) return none;
  let jump = jumpSpeed(p);
  let roll = false;
  const rollInput = (p.squidButton && C.ROLL_SQUID_HOLD <= p.squidHoldFrames) || p.inputFirst === Btn.Fire || p.inputFirst === Btn.Sub;
  if (!L.active && C.FLOOR_NY <= p.floorN[1] && p.jumpPressed && rollInput && p.history.count > 0) {
    let cand: MoveHistoryEntry | null = null;
    let recentSquid = false;
    scanHistory(p, (e, k) => {
      if (e.wall) return;
      if (!cand && f32(C.SQUID_REF * C.ROLL_MIN_RATIO) <= e.speed) {
        const d = e.dir;
        if (C.ROLL_DIR_EPS < f32(f32(f32(d[0] * d[0]) + f32(d[1] * d[1])) + f32(d[2] * d[2]))) cand = e;
      }
      if (k < C.HISTORY_RECENT && !recentSquid) recentSquid = e.squidInk;
    });
    const c = cand as MoveHistoryEntry | null;
    if (c && recentSquid) {
      const sx = p.stick[0], sy = p.stick[1], a = ctx.aim;
      let x = f32(f32(sy * a[0]) + f32(f32(f32(a[1] * 0) - a[2]) * sx));
      let z = f32(f32(sy * a[2]) + f32(f32(a[0] - f32(a[1] * 0)) * sx));
      let y = f32(f32(sy * a[1]) + f32(sx * f32(f32(a[2] * 0) - f32(a[0] * 0))));
      const l = f32(Math.sqrt(f32(f32(f32(z * z) + f32(x * x)) + f32(y * y))));
      if (0 < l) {
        const i = f32(1 / l);
        x = f32(i * x); y = f32(i * y); z = f32(i * z);
      }
      const d = f32(f32(f32(c.dir[0] * x) + f32(c.dir[1] * y)) + f32(c.dir[2] * z));
      if (!(l <= C.ROLL_DIR_EPS) && !(C.ROLL_COS < d)) {
        L.speed = c.speed;
        launch(p, ctx, true);
        roll = true;
        if (L.wasSquid) jump = C.ROLL_JUMP;
      }
    }
  }
  if (wallKick) {
    launch(p, ctx, false);
    return { kind: "wall", roll };
  }
  if (!(p.vy < jump)) return { kind: "none", roll };
  const jump3d = p.floorN[1] < C.FLOOR_NY && p.wallCling;
  if (jump3d) {
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
  jumpStart(p, ctx.shooting, !jump3d && !roll);
  return { kind: "jump", roll };
}

/** 0x7102458a18 — 차지 벽 점프 해제(스틱이 벽 바깥이 아님): 3D 점프 y·래치 +0x780/+0x782, +0x774 = 0, 점프 시작. 원본 연결 실행 96건 대조식(§6.8.3). */
export function wallLatch(p: PlayerState, ctx: JumpCtx): number {
  const x = f32(p.wallJumpCharge - C.WALLJUMP_CHARGE_START);
  const F = p.gear.wallJumpChargeFrames, c0 = C.WALLJUMP_LATCH_C0;
  let s: number;
  if (F >= c0) {
    if (x <= c0) s = 0;
    else if (F <= x) s = 1;
    else if (f32(F - c0) === 0) s = 0;
    else s = f32(f32(x - c0) / f32(F - c0));
  } else {
    let s3 = 0;
    if (F >= x) s3 = 0;
    else if (c0 <= x) s3 = 1;
    else if (f32(c0 - F) !== 0) s3 = f32(f32(x - F) / f32(c0 - F));
    s = f32(1 - s3);
  }
  const y = f32(C.WALLJUMP_LATCH_LO + f32(s * f32(C.WALLJUMP_LATCH_HI - C.WALLJUMP_LATCH_LO)));
  if (!(p.jump3d[1] >= y)) p.jump3d[1] = y;
  p.jump3dLatch[0] = p.jump3d[0]; p.jump3dLatch[1] = p.jump3d[1]; p.jump3dLatch[2] = p.jump3d[2];
  if (!(s < C.WALLJUMP_LATCH_MIN)) {
    p.jump3dHold = true;
    p.holdBlock = true;
  }
  p.wallJumpCharge = 0;
  jumpStart(p, ctx.shooting, false);
  return s;
}

/**
 * 벽 점프 차지·래치(메인 계산 0x7102482980~0x7102482fbc, §6.8.2). 행동 불가·Chariot 없음, 세션 조건은 로컬 조작 플레이어로 참.
 * wallFall = 본체+0xa4c(벽 낙하, 미구현 → 거짓). 반환: "wall" 차지 벽 점프 발사, "latch" 래치 시작, "climb" 래치 진행.
 */
export function wallChargeStage(p: PlayerState, ctx: JumpCtx, wallFall = false): "none" | "wall" | "latch" | "climb" {
  const ink = squidInk(p), up = rising(p);
  if (p.wallJumpCharge === 0 || ink || up) p.wallJumpOff = 0;
  else p.wallJumpOff++;
  const onWall = p.wallJumpOff < C.WALLJUMP_OFFWALL_MAX && p.floorN[1] < C.FLOOR_NY && 0 < p.groundFrames;
  let ev: "none" | "wall" | "latch" | "climb" = "none";
  if (!p.jump3dHold) {
    if (C.WALLJUMP_CHARGE_START <= p.wallJumpCharge && onWall && !p.jumpHeld) {
      if (wallKickStick(p, ctx.aim)) {
        launch(p, ctx, false);
        p.wallJumpCharge = 0;
        jumpStart(p, ctx.shooting, false);
        ev = "wall";
      } else {
        wallLatch(p, ctx);
        ev = "latch";
      }
    }
  } else if ((!ink && !up) || C.FLOOR_NY <= p.floorN[1] || p.stickSrc[1] < -0.1) {
    p.jump3dHold = false;
    if (!ink && !up && p.stickLock < C.STICK_LOCK_RELEASE) p.stickLock = C.STICK_LOCK_RELEASE;
  } else {
    jumpStart(p, ctx.shooting, false);
    if (p.stickLock < C.STICK_LOCK_RELEASE) p.stickLock = C.STICK_LOCK_RELEASE;
    if (p.onGround && p.jump3d[1] < p.jump3dLatch[1]) p.jump3d[1] = p.jump3dLatch[1];
    ev = "climb";
  }
  if (!p.jump3dHold) {
    if (!onWall || !p.jumpHeld || (p.wallJumpCharge < 1 && p.stick[1] < 0) || wallFall) p.wallJumpCharge = 0;
    else p.wallJumpCharge++;
  }
  return ev;
}

/** 점프 버튼 유지 가산 0x7102482df8. */
export function jumpHoldAdd(p: PlayerState): void {
  if (!(p.groundFrames < 1)) return;
  if (!(C.VY_EPS < f32(p.vy + p.jump3d[1]))) return;
  if (p.holdBlock) return;
  const L = p.launch;
  const squidLaunch = L.active2 && L.wasSquid;
  let add = 0;
  if (p.jumpHeld) {
    if (!squidLaunch) {
      // 0x710249bb60: 본체+0xa38 > 0 이고 본체+0x790 > 0 && x(본체+0x488) > 0 이면 min(a38, 1 − own²·x)
      let s = p.slideAmt > 0 ? p.slideAmt : 0;
      if (s > 0 && 0 < p.squidInkFrames && 0 < p.wallInput) {
        const lim = f32(f32(f32(f32(p.step.own * p.step.own) * p.wallInput) * -1) + 1);
        if (lim < s) s = lim;
      }
      add = f32(C.JUMP_HOLD_ADD * f32(1 - s));
    }
  } else if (!squidLaunch) return;
  if (C.VY_EPS < p.jump3d[1]) p.jump3d[1] = f32(add + p.jump3d[1]);
  else p.vy = f32(add + p.vy);
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
