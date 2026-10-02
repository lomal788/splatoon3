// 담당: [physics] — 슬롯19 접촉 정리 0x71024abcf0(물리 뒤): 공중/접지 카운터, 착지 감속, 접지 중 수직 속도·벽 수영,
// 측면 접촉, 천장, 경사·벽 미끄럼(a38/a2c), 바닥 평면 투영, 발밑 잉크 PlayerStepPaint 0x710268b3b8.
// 근거: docs/player/player_state.md §7.3·§8, docs/player/movement_physics.md §3.3, 디컴파일 analysis/decomp/move/move_air.c
// (0x710246b32c / 0x710246b574). 판독식은 그대로, 의미 미확정 필드는 0 으로 두었다(docs/impl/physics.md).
import { f32 } from "../fmath.ts";
import type { PaintWorld, Team } from "../types.ts";
import type { BodyStepResult } from "./body.ts";
import * as C from "./consts.ts";
import { slerpDir } from "./move.ts";
import type { PlayerState } from "./state.ts";
import { isSquidMove } from "./states.ts";

const UP = [0, 1, 0];

/** 0x710246b32c — 접지(또는 점프 프레임) 카운터 리셋. flag = 접지 플래그 인자. */
export function groundReset(p: PlayerState, flag: boolean): void {
  p.groundFrames = Math.min(p.groundFrames, C.COUNTER_MAX - 1) + 1;
  p.ground26c = Math.min(p.ground26c, C.COUNTER_MAX - 1) + 1;
  if (!flag || p.surfN[1] < C.FLOOR_NY) p.offFlatFrames++;
  else p.offFlatFrames = 0;
  const s = p.airStep < 2 ? 1 : p.airStep;
  p.airFrames = 0;
  p.airC8 = 0;
  p.airRatio = 0;
  p.airStep = s - 1;
  p.airStepRatio = f32(f32(s - 1) / f32(C.AIR_RATIO_DIV));
  if (flag) p.airFrames2 = 0;
  p.airDampAlt = false;
}

/** 0x710246b574 — 공중 카운터 증가, 바닥 법선을 위쪽으로 되돌림. */
export function airAdvance(p: PlayerState, flag: boolean): void {
  const a = Math.min(p.airFrames, C.COUNTER_MAX);
  const a2 = Math.min(p.airFrames2, C.COUNTER_MAX);
  p.airFrames = a + 1;
  p.airFrames2 = a2 + 1;
  let r = f32(f32(a + 1) / f32(C.AIR_RATIO_DIV));
  if (r > 1) r = 1;
  p.airRatio = r;
  let st = p.airStep + C.AIR_D4_INC;
  if (C.AIR_RATIO_DIV <= st) st = C.AIR_RATIO_DIV;
  p.airStep = st;
  p.airStepRatio = f32(f32(st) / f32(C.AIR_RATIO_DIV));
  p.groundFrames = 0;
  if (C.AIR_DAMP_START <= p.airFrames) {
    p.ground26c = 0;
    p.offFlatFrames++;
  }
  if (!flag) p.airC8 = 0;
  if (0 < p.airFrames) {
    const t = f32(p.launch.active ? C.AIR_NORMAL_SLERP_LAUNCH : f32(C.AIR_NORMAL_SLERP * p.airRatio));
    const n = p.floorN;
    slerpDir(t, n, n, UP);
    const l = f32(Math.sqrt(f32(f32(f32(n[0] * n[0]) + f32(n[1] * n[1])) + f32(n[2] * n[2]))));
    if (0 < l) {
      const i = f32(1 / l);
      n[0] = f32(i * n[0]); n[1] = f32(i * n[1]); n[2] = f32(i * n[2]);
    }
  }
}

function clamp01(x: number): number {
  return x < 0 ? 0 : x > 1 ? 1 : x;
}

export interface ContactOut {
  landed: boolean;
  /** 착지 직전 공중 프레임(착지 상태 요청용) */
  landedAir: number;
  /** 천장 접촉 */
  ceiling: boolean;
  /** 이번 스텝에 닿은 삼각형들 */
  tris: number[];
}

/**
 * 접촉 정리. res = 캐릭터 몸 스텝 결과, forceAir = 이번 프레임 게임이 공중 상태를 강제했는지.
 * 순서(0x71024abcf0 행 순서): ①② 접지 중 침투·수직 속도 → ③ 측면 접촉 → (c) 착지·카운터 → (d) 천장 → ④⑤ 미끄럼 → ⑥ 바닥 투영.
 */
export function contactCleanup(p: PlayerState, res: BodyStepResult, forceAir: boolean): ContactOut {
  p.prevOnGround = p.onGround;
  const onGround = res.supported && !forceAir;
  p.onGround = onGround;
  const sq = isSquidMove(p.state);
  const v = p.vel;
  const out: ContactOut = { landed: false, landedAir: 0, ceiling: false, tris: res.contacts.map((c) => c.tri) };
  if (onGround) {
    p.groundN[0] = res.gn[0]; p.groundN[1] = res.gn[1]; p.groundN[2] = res.gn[2];
    p.groundP[0] = res.gp[0]; p.groundP[1] = res.gp[1]; p.groundP[2] = res.gp[2];
    // ① 표면 침투 제거(k = 1 근사)
    const n = p.groundN;
    const d = f32(f32(f32(n[0] * v[0]) + f32(n[1] * v[1])) + f32(n[2] * v[2]));
    if (d < 0) {
      v[0] = f32(v[0] - f32(n[0] * d));
      const ny = f32(v[1] - f32(n[1] * d));
      if (!(p.vy > 0 && ny > v[1])) v[1] = ny;
      v[2] = f32(v[2] - f32(n[2] * d));
    }
    // ② 수직 속도
    const ny = n[1];
    if (p.vy <= 0) {
      if (!sq) p.vy = 0;
      else {
        let vs = p.vy < C.SQUID_WALL_VS_MIN ? C.SQUID_WALL_VS_MIN : p.vy;
        const k = f32(C.SQUID_WALL_VS_K_WALL + f32(f32(C.SQUID_WALL_VS_K_FLOOR - C.SQUID_WALL_VS_K_WALL) * clamp01(ny)));
        vs = f32(vs * k);
        if (Math.abs(vs) < C.VY_EPS) vs = 0;
        p.vy = vs;
      }
    } else {
      if (p.airFrames < C.GRAVITY_START) {
        let vs = f32(p.vy - C.GRAVITY);
        if (vs <= 0) vs = 0;
        p.vy = vs;
      }
      if (ny < C.FLOOR_NY) {
        p.jump3d[1] = f32(p.jump3d[1] + p.vy);
        p.vy = 0;
      }
    }
  }
  // ③ 측면 접촉: 지면이 아닌 접촉 중 가장 수평인 것
  p.sideContact = false;
  const limit = p.wallCling ? C.OVERHANG_NY : C.FLOOR_NY;
  let best = -1, bestAbs = 2;
  for (let i = 0; i < res.contacts.length; i++) {
    const c = res.contacts[i];
    if (c.ny >= limit) continue;
    if (c.ny < C.CEIL_NY) continue;
    const a = Math.abs(c.ny);
    if (a < bestAbs) { bestAbs = a; best = i; }
  }
  if (best >= 0) {
    const c = res.contacts[best];
    let sx = c.nx, sy = c.ny, sz = c.nz;
    if (p.airFrames < C.AIR_DAMP_START && p.vy <= C.VY_EPS && sy >= 0) {
      sy = 0;
      const l = Math.hypot(sx, sz) || 1;
      sx /= l; sz /= l;
    }
    p.sideN[0] = f32(sx); p.sideN[1] = f32(sy); p.sideN[2] = f32(sz);
    p.sideContact = true;
    const S = p.sideN;
    const d = f32(f32(f32(v[0] * S[0]) + f32(v[1] * S[1])) + f32(v[2] * S[2]));
    if (d < 0) {
      v[0] = f32(v[0] - f32(S[0] * d));
      if (!(S[1] > 0)) v[1] = f32(v[1] - f32(S[1] * d));
      v[2] = f32(v[2] - f32(S[2] * d));
    }
  }
  // (c) 착지 판정·카운터
  if (onGround) {
    p.landStiff = Math.max(p.landStiff - 1, 0);
    if (p.airFrames > C.LANDING_AIR_MIN) {
      const t = clamp01(f32(f32(p.airFrames - C.LANDING_AIR_MIN) / f32(C.LANDING_AIR_SPAN)));
      out.landedAir = p.airFrames;
      const vl = f32(Math.sqrt(f32(f32(f32(v[0] * v[0]) + f32(v[1] * v[1])) + f32(v[2] * v[2]))));
      const tgt = f32(vl + f32(t * f32(C.LANDING_SPEED - vl)));
      if (vl > tgt && vl > 0) {
        const s = f32(tgt / vl);
        v[0] = f32(v[0] * s); v[1] = f32(v[1] * s); v[2] = f32(v[2] * s);
      }
      if (tgt < p.cap) p.cap = tgt;
      p.landStiff = Math.max(p.landStiff, Math.trunc(f32(30 * t)));
    }
    if (!p.prevOnGround) out.landed = true;
    // 바닥 법선 갱신
    p.floorN[0] = p.groundN[0]; p.floorN[1] = p.groundN[1]; p.floorN[2] = p.groundN[2];
    p.floorNRaw[0] = p.groundN[0]; p.floorNRaw[1] = p.groundN[1]; p.floorNRaw[2] = p.groundN[2];
    p.surfN[0] = p.groundN[0]; p.surfN[1] = p.groundN[1]; p.surfN[2] = p.groundN[2];
    groundReset(p, true);
  } else {
    p.landStiff = Math.max(p.landStiff - 1, 0);
    airAdvance(p, true);
  }
  // (d) 천장
  let ceiling = false;
  for (const c of res.contacts) if (c.ny < C.CEIL_NY) ceiling = true;
  const up = f32(f32(f32(v[1] + p.vy) + p.jump3d[1]) + 0);
  if (ceiling && up > 0) {
    out.ceiling = true;
    p.ceilTimer = 30; // [0x71058bbebc]
    if (p.slideAmt < 1) p.slideAmt = 1;
    let rem = up;
    const take = (x: number): number => {
      if (x <= 0 || rem <= 0) return x;
      const d = x < rem ? x : rem;
      rem = f32(rem - d);
      return f32(x - d);
    };
    p.vy = take(p.vy);
    p.jump3d[1] = take(p.jump3d[1]);
    v[1] = take(v[1]);
  } else {
    const dec = (sq) || C.AIR_DAMP_START <= p.airFrames || C.VY_EPS < p.vy || p.floorN[1] < C.FLOOR_NY ? 1 : 5;
    p.ceilTimer = Math.max(p.ceilTimer - dec, 0);
  }
  // ④ 미끄럼 양 a38, ⑤ 미끄럼 속도 a2c.
  // x = 본체+0x488(입력 구조체 본체+0x474 의 +0x14, writer 미확정) — 오징어 버튼을 누르는 동안 1 로 둔다 [추정]:
  // 0x710249bb60 이 s = min(a38, 1 − own²·x) 로 아군 잉크 벽에서 미끄럼을 없애는 항이라 누르는 동안 벽에 머무는 동작과 맞는다.
  const x = p.squidRequest ? 1 : 0;
  const cling = p.wallCling;
  const t90 = clamp01(f32(f32(p.offFlatFrames) / 90));
  const sy = p.surfN[1];
  let w = cling ? f32(1 - clamp01(f32(sy / C.FLOOR_NY))) : f32(1 - clamp01(f32(f32(sy - C.WALL_NY) / f32(C.FLOOR_NY - C.WALL_NY))));
  if (p.floorN[1] <= C.FLOOR_NY) {
    if (p.ceilTimer >= 1) w = 1;
    let tgt: number, r: number;
    if (cling) {
      tgt = f32(Math.pow(w, 1.737));
      r = f32(f32(f32(w * f32(-0.01)) + f32(0.03)) * f32(f32(x * f32(f32(f32(f32(Math.pow(w, 2.322)) * f32(0.4)) + f32(0.1)) - 1)) + 1));
    } else {
      tgt = 1;
      r = f32(f32(0.04) + f32(f32(0.16) * w));
    }
    p.slideAmt = Math.min(f32(p.slideAmt + r), tgt);
  } else if (p.ceilTimer < 1) {
    const N = p.floorN;
    let d = cling ? 0 : N[1] <= C.WALL_SAMPLE_NY ? f32(0.03) : f32(f32(0.03) + f32(f32(1 - 0.03) * f32(f32(N[1] - C.WALL_SAMPLE_NY) / f32(0.2929))));
    if (!onGround) d = f32(d * p.airRatio);
    p.slideAmt = Math.max(f32(p.slideAmt - d), 0);
  }
  {
    let s = p.slideAmt > 0 ? p.slideAmt : 0;
    if (s > 0 && x > 0) {
      const lim = f32(f32(f32(f32(p.step.own * p.step.own) * x) * -1) + 1);
      if (lim < s) s = lim;
    }
    let q = clamp01(f32(f32(p.vy + p.jump3d[1]) / C.JUMP_VEL));
    q = f32(Math.pow(q, 0.322));
    if (q < p.airRatio) q = p.airRatio;
    const acc = cling
      ? f32(f32(Math.pow(s, 1.737)) * f32(f32(0.005) - f32(x * f32(0.0019999999))))
      : f32(f32(s + f32(t90 * f32(1 - s))) * f32(f32(0.01) - f32(f32(0.002) * t90)));
    const a = p.slide, N = p.floorN;
    a[1] = f32(a[1] - f32(acc * f32(1 - q)));
    const dn = f32(f32(f32(a[0] * N[0]) + f32(a[1] * N[1])) + f32(a[2] * N[2]));
    a[0] = f32(a[0] - f32(N[0] * dn)); a[1] = f32(a[1] - f32(N[1] * dn)); a[2] = f32(a[2] - f32(N[2] * dn));
    const k = cling ? f32(f32(0.97) + f32(x * f32(-0.01000005))) : f32(f32(0.8) + f32(f32(0.18) * t90));
    a[0] = f32(a[0] * k); a[1] = f32(a[1] * k); a[2] = f32(a[2] * k);
    if (p.jump3dHold) {
      if (a[1] < 0) a[1] = 0;
    } else if (p.wallJumpCharge > 10) {
      const f = clamp01(f32(f32(p.wallJumpCharge - 10) / 30));
      const y2 = f32(a[1] * f32(1 - f32(0.5 * f)));
      if (y2 > a[1]) a[1] = y2;
    }
    const lim = cling ? f32(0.1) : f32(f32(0.15) + f32(f32(0.05) * t90));
    const al = f32(Math.sqrt(f32(f32(f32(a[0] * a[0]) + f32(a[1] * a[1])) + f32(a[2] * a[2]))));
    if (al > lim) {
      const s2 = f32(lim / al);
      a[0] = f32(a[0] * s2); a[1] = f32(a[1] * s2); a[2] = f32(a[2] * s2);
    }
  }
  // ⑥ 바닥 평면 투영(접지 중)
  if (onGround) {
    const N = p.floorN;
    const d = f32(f32(f32(v[0] * N[0]) + f32(v[1] * N[1])) + f32(v[2] * N[2]));
    v[0] = f32(v[0] - f32(N[0] * d));
    v[1] = f32(v[1] - f32(N[1] * d));
    v[2] = f32(v[2] - f32(N[2] * d));
  }
  return out;
}

/** 발밑 잉크 갱신 0x710268b3b8 (§8.2). sample 이 없으면(도색 영역 없음) 무도색. */
export function updateStepPaint(p: PlayerState, paint: PaintWorld | null, samplePos: ArrayLike<number>): void {
  const S = p.step;
  let own = 0, enemy = 0, team: Team = -1;
  if (paint) {
    const s = paint.sample(samplePos as Float32Array, SAMPLE_RADIUS);
    team = s.team;
    for (let t = 0; t < 3; t++) {
      const r = s.ratio[t as 0 | 1 | 2] ?? 0;
      if (t === p.team) own = f32(own + r);
      else enemy = f32(enemy + r);
    }
    S.lastOwn = own;
    S.lastEnemy = enemy;
    S.reused = false;
  }
  // 아군: 실질적으로 즉시 반영
  S.own = own;
  // 적: 오를 때 목표/3, 내릴 때 0.25 씩
  if (enemy > S.enemy) {
    const step = f32(enemy / C.STEP_ENEMY_UP_DIV);
    S.enemy = f32(S.enemy + Math.min(f32(enemy - S.enemy), step));
  } else {
    S.enemy = f32(S.enemy - Math.min(f32(S.enemy - enemy), C.STEP_ENEMY_DOWN));
  }
  S.ownRaw = own;
  S.enemyRaw = enemy;
  S.enemySlow = enemy;
  // 이동용 적 비율
  const now = S.enemy;
  if (now > S.enemyMove) S.enemyMove = f32(S.enemyMove + f32(f32(now - S.enemyMove) * S.enemyMoveRate));
  else S.enemyMove = now;
  S.enemyMoveRate = S.enemy > 0
    ? f32(S.enemyMoveRate + f32(f32(C.STEP_MOVE_RATE_MAX - S.enemyMoveRate) * C.STEP_MOVE_RATE_K))
    : f32(S.enemyMoveRate * C.STEP_MOVE_RATE_DECAY);
  // 분류: 벽 정도 w(바닥 법선 y 0.6414 → 0, 0.0854 → 1)
  const ny = p.floorN[1];
  const w = ny >= C.FLOOR_NY ? 0 : ny <= C.WALL_NY ? 1 : f32(f32(C.FLOOR_NY - ny) / f32(C.FLOOR_NY - C.WALL_NY));
  S.ownThr = f32(C.STEP_OWN_THR_BASE - f32(C.STEP_THR_W * w));
  S.enemyThr = f32(C.STEP_ENEMY_THR_BASE + f32(C.STEP_THR_W * w));
  const a = f32(S.own - S.ownThr);
  const e = f32(S.enemy - S.enemyThr);
  S.cls = e > 0 && e > a ? 2 : a > 0 ? 0 : 4;
  S.team = S.cls === 4 ? -1 : team;
}

/** 발밑 모니터 원 반경(GroundPaintMonitorRadius) — 원본 값 미확정. 캡슐 반경으로 둔다. */
export const SAMPLE_RADIUS = 0.6;
