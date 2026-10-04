// 담당: [physics] — 슬롯19 접촉 정리 0x71024abcf0(물리 뒤): 공중/접지 카운터, 착지 감속, 접지 중 수직 속도·벽 수영,
// 측면 접촉, 천장, 경사·벽 미끄럼(a38/a2c), 바닥 평면 투영, 발밑 잉크 PlayerStepPaint 0x710268b3b8.
// 근거: docs/player/player_state.md §7.3·§8, docs/player/movement_physics.md §3.3, 디컴파일 analysis/decomp/move/move_air.c
// (0x710246b32c / 0x710246b574). 판독식은 그대로, 의미 미확정 필드는 0 으로 두었다(docs/impl/physics.md).
import { f32 } from "../fmath.ts";
import type { Team } from "../types.ts";
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
  // PC+0xd0 = Phive 이동 상태 OnGround && S+0x20 (0x71024f7410). 게임 공중 강제는 몸체 단계에서 InAir 로 이미 반영됨.
  const onGround = res.onGround && !forceAir;
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
  // ③ 측면 접촉 PC+0xec: Result 벽 후보 평균 법선 S+0xb4 (0x7102c5a3c8 2280~2311). (공중 < 4 && vs ≤ 0.001 && S.y ≥ 0) 이면 S.y = 0 후 정규화.
  p.sideContact = false;
  if (res.wall) {
    let sx = res.wallN[0], sy = res.wallN[1], sz = res.wallN[2];
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
    // +0x1c8 표면 법선 = PC+0xb8(0 이 아닐 때만, Result+0x13f8) [판독: player_state §7.3.1]
    if (res.surfN[0] !== 0 || res.surfN[1] !== 0 || res.surfN[2] !== 0) { p.surfN[0] = res.surfN[0]; p.surfN[1] = res.surfN[1]; p.surfN[2] = res.surfN[2]; }
    groundReset(p, true);
  } else {
    p.landStiff = Math.max(p.landStiff - 1, 0);
    airAdvance(p, true);
  }
  // (d) 천장 (player_state.md §7.3.2 (d)): ny = PC+0xec ? 벽 법선 y : 접지 ? 지지 법선 y : 1
  //   ceiling = (본체+0x184 < 0.6414 && ny < −0.572 && KebaInk 벽 없음) || (PC+0xd3 && 상태 ∈ S && 최종 vy > 0)
  const nyC = res.wall ? res.wallN[1] : onGround ? res.gn[1] : 1;
  const ceiling = (p.floorN[1] < C.FLOOR_NY && nyC < C.CEIL_NY && !res.flags.kebaWall) || (res.flags.guard16c9 && sq && p.final[1] > 0);
  const up = f32(f32(f32(v[1] + p.vy) + p.jump3d[1]) + 0);
  if (ceiling) {
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
  // x = 본체+0x488 벽 입력 계수(입력 구조체 +0x14, writer 0x71024a7100 [실행: movement_physics §6.3.2], move.ts wallInputUpdate).
  const x = p.wallInput;
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
    // 0x710249bb60: s = min(a38, 1 − own²·x) 는 본체+0x790 > 0 && x > 0 일 때 (player_state §7.3.2 ⑤)
    if (s > 0 && p.squidInkFrames > 0 && x > 0) {
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

// ---- MOV04 발밑 잉크 모니터 (SplResultPlayer+0x1368, paint_and_score.md §7 [r6 paint]) -----------------

/** 모니터 GPU 카운트 공급: 접점·법선의 1×1 Disk 스탬프 안 팀0/1/2 소유 텍셀 수와 전체 수. */
export type MonitorCounts = (pos: ArrayLike<number>, n: ArrayLike<number>) => [number, number, number, number];

/** 모니터 배열 항목(0x50 B). */
export interface MonitorEntry {
  /** +0x28.. 대상 식별(웹: 삼각형 번호; 원본 (종류, id, 패널) 0x7102c71e50 미판독 [근사]) */
  key: number;
  /** +0x8..+0x14 캐시 카운트 */
  cache: number[];
  /** +0x38 이번에 배치, +0x3c 프레임 수, +0x40 가중치, +0x44 id, +0x48 id 유효, +0x4c 등록 */
  act: boolean;
  cnt: number;
  w: number;
  id: number;
  valid: boolean;
  reg: boolean;
  /** 모니터 객체 쪽: 칠 요청 위치·법선, GPU 카운트 +0x3c.. 와 유효 바이트 +0x40.. */
  pos: number[];
  n: number[];
  monC: number[];
  monV: boolean[];
  /** 모니터 객체 +8/+0x10 (해제 알림 조건) */
  monHas: boolean;
}

/** Result 쪽 슬롯(0x13c0+8k id, +4 유효, 캐시 0x1370+0x14k = 카운트 4 + 가중치). */
export interface MonitorSlots {
  valid: boolean[];
  id: number[];
  cache: number[][];
}

function u32(x: number): number {
  return x >>> 0;
}
/** ARM FCVTZU Wd */
function fcvtzu(x: number): number {
  if (!(x > 0)) return 0;
  return x >= 4294967295 ? 4294967295 : Math.floor(x);
}

/**
 * 발밑 샘플 델리게이트 0x7102c5ec74 (+0x7102c71bc4, 모니터 vt+0x60 0x7102c260c8: 유효 바이트 0·1·3 만 확인) [실행 4000/4000].
 * 출력 u32 4개(팀0/1/2/전체)와 최대 가중치. 슬롯 유효·캐시·항목 캐시를 제자리 갱신한다.
 */
export function footDelegate(R: MonitorSlots, ents: MonitorEntry[]): { out: number[]; wmax: number } {
  let out = [0, 0, 0, 0];
  let wmax = 0, first = true;
  for (let k = 0; k < 4; k++) {
    if (!R.valid[k]) continue;
    const e = ents.find((x) => x.valid && x.id === R.id[k]);
    if (!e) { R.valid[k] = false; R.cache[k] = [0, 0, 0, 0, 0]; continue; }
    let c: number[];
    if (e.monV[0] && e.monV[1] && e.monV[3]) {
      c = R.cache[k].slice(0, 4);
      for (let i = 0; i < 4; i++) if (e.monV[i]) c[i] = e.monC[i];
    } else c = e.cache.slice(0, 4);
    e.cache = c.slice();
    const w = f32(e.w);
    R.cache[k] = [...c, w];
    if (!(w > 0)) { R.valid[k] = false; continue; }
    if (first) { wmax = f32(Math.max(w, 0)); first = false; }
    else wmax = wmax > w ? wmax : w;
    out = out.map((o, i) => fcvtzu(f32(f32(w * f32(u32(c[i]))) + f32(u32(o)))));
  }
  return { out, wmax };
}

/** 가중치 갱신 0x7102c71330(dt, 배열) [실행 4000/4000]: 배치 뒤 frames(2) 프레임에 1.0, 그 밖 dt/rate(1/6초) 씩 0 으로, 0 이면 해제. 해제 알림 수를 돌려준다. */
export function footWeight(rate: number, frames: number, ents: MonitorEntry[], dt: number): number {
  let rel = 0;
  const r = f32(rate);
  for (const e of ents) {
    if (e.act) {
      e.cnt = (e.cnt + 1) >>> 0;
      if ((e.cnt | 0) >= frames) { e.w = 1; e.act = false; }
      continue;
    }
    if (r === 0) e.w = 0;
    else {
      let v = f32(f32(e.w) - f32(f32(dt) / r));
      v = !(v > 0) ? 0 : v;
      e.w = v;
      if (v > 0) continue;
    }
    e.act = false;
    if (e.reg) {
      e.w = 0;
      if (e.monHas) rel++;
      e.reg = false;
    }
  }
  return rel;
}

/**
 * Result+0x1368 모니터 배열(생성 0x7102c70e80(arr, heap, 4): 항목 4, +0x14 = 1/6(0x3e2aaaab), +0x18 = 2, +0x10 = InkTexType 16 Disk)과
 * Result 쪽 4 슬롯·접지 정보 O(+8 지지 몸체, +0x48 델리게이트). 배치 0x7102c71650·슬롯 기록은 [판독], 가중치·델리게이트는 [실행].
 */
export class FootMonitors {
  readonly ents: MonitorEntry[] = [];
  readonly slots: MonitorSlots = { valid: [false, false, false, false], id: [0, 0, 0, 0], cache: [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0]] };
  readonly rate = fb32(0x3e2aaaab);
  readonly frames = 2;
  /** 배열+0x1c id 카운터, +0x20 id 발급 플래그 */
  private counter = 0;
  private readonly issueIds = true;
  /** O+8 ≠ 0 (지지 몸체 기록됨) / O+0x48 델리게이트 설치 */
  bodySet = false;

  constructor() {
    for (let i = 0; i < 4; i++) {
      this.ents.push({ key: -1, cache: [0, 0, 0, 0], act: false, cnt: 0, w: 0, id: 0, valid: false, reg: false, pos: [0, 0, 0], n: [0, 1, 0], monC: [0, 0, 0, 0], monV: [false, false, false, false], monHas: false });
    }
  }

  weightUpdate(dt: number): void {
    footWeight(this.rate, this.frames, this.ents, dt);
  }

  /** 배치 0x7102c71650: 같은 대상이면 다시 쓰고(이번에 배치 = 1, 미등록이면 프레임 수 0·등록), 없으면 가중치 ≤ 0 인 첫 칸에 새로. */
  private place(key: number, pos: ArrayLike<number>, n: ArrayLike<number>, counts: MonitorCounts | null): MonitorEntry | null {
    let e = this.ents.find((x) => x.key === key);
    if (!e) {
      e = this.ents.find((x) => x.w <= 0);
      if (!e) return null;
      e.key = key;
      if (!this.issueIds) e.valid = false;
      else { this.counter = (this.counter + 1) >>> 0; e.id = this.counter; e.valid = true; }
    }
    e.act = true;
    if (!e.reg) { e.cnt = 0; e.reg = true; e.monHas = true; e.monV = [false, false, false, false]; }
    else {
      // GPU 결과는 이전 프레임 패스에서 그린 것을 읽는다 [근사: 1 프레임, 원본 1~2 프레임 미확정]
      e.monV = [true, true, true, true];
    }
    e.pos = [pos[0], pos[1], pos[2]];
    e.n = [n[0], n[1], n[2]];
    e.monC = counts ? counts(e.pos, e.n).map(u32) : [0, 0, 0, 0];
    return e;
  }

  /** 접촉 잉크 질의 0x7102c71a00(미판독 — 배치 규칙으로 근사): 가중치와 카운트. */
  query(key: number, pos: ArrayLike<number>, n: ArrayLike<number>, counts: MonitorCounts | null): { w: number; c: number[] } | null {
    const e = this.place(key, pos, n, counts);
    if (!e) return null;
    return { w: e.w, c: e.monV[0] && e.monV[1] && e.monV[3] ? e.monC : e.cache };
  }

  /** 지지 접점 발밑 모니터 배치 + 슬롯 기록(0x7102c5d5bc~0x7102c5db48): 이미 슬롯에 있는 id 면 그대로, 아니면 첫 빈 슬롯, 없으면 버림. */
  placeFoot(key: number, pos: ArrayLike<number>, n: ArrayLike<number>, counts: MonitorCounts | null): void {
    this.bodySet = true;
    const e = this.place(key, pos, n, counts);
    const R = this.slots;
    const free = [0, 1, 2, 3].map((k) => {
      if (!R.valid[k]) return true;
      if (this.ents.some((x) => x.valid && x.id === R.id[k])) return false;
      R.valid[k] = false;
      return true;
    });
    if (!e || !e.valid) return;
    for (let k = 0; k < 4; k++) if (!free[k] && R.id[k] === e.id) return;
    const k = free.indexOf(true);
    if (k < 0) return;
    R.id[k] = e.id;
    R.valid[k] = true;
  }

  /** PlayerStepPaint 의 샘플(O+8 ≠ 0 일 때 O+0x48 델리게이트 slot0). */
  sample(): number[] | null {
    if (!this.bodySet) return null;
    return footDelegate(this.slots, this.ents).out;
  }
}

function fb32(bits: number): number {
  const d = new DataView(new ArrayBuffer(4));
  d.setUint32(0, bits >>> 0, true);
  return d.getFloat32(0, true);
}

/**
 * 발밑 잉크 갱신 0x710268b3b8 (player_state.md §8.2). 샘플 = O+0x48 델리게이트(팀0/1/2 개수·전체 N, Disk 1×1 모니터 4개 가중 합 [실행]).
 * k = min(N/15, 1), f_t = c_t/N·k. N == 0 이면 직전 값(S+0xa0/+0xa4)을 한 번 재사용(S+0xa8) 후 0.
 * 샘플이 없으면(O+8 == 0) 아군 목표 0(프레임당 1.0 감소), 적 목표 0(0.25 감소) [판독 요약].
 */
export function updateStepPaint(p: PlayerState, counts: number[] | null): void {
  const S = p.step;
  let own = 0, enemy = 0, team: Team = -1;
  if (counts) {
    const N = u32(counts[3]);
    if (N !== 0) {
      let k = f32(f32(N) / 15);
      if (k > 1) k = 1;
      let best = 0;
      for (let t = 0; t < 3; t++) {
        const r = f32(f32(f32(u32(counts[t])) / f32(N)) * k);
        if (t === p.team) own = f32(own + r);
        else enemy = f32(enemy + r);
        if (r > best) { best = r; team = t as Team; }
      }
      S.lastOwn = own;
      S.lastEnemy = enemy;
      S.reused = false;
    } else if (!S.reused) {
      own = S.lastOwn;
      enemy = S.lastEnemy;
      S.reused = true;
      team = S.team;
    }
  } else {
    own = f32(Math.max(f32(S.own - 1), 0));
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

