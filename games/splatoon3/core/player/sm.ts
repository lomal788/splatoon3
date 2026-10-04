// 담당: [physics] — 상태기계(본체+0xa8c8): 인간↔오징어 판정·전환 단계 0x710243e7d0, 형태 안 상태 결정 0x7102442354(부분).
// 근거: docs/player/player_state.md §5·§6. 애니 진행 프레임(cur/end)은 원본 ASB 대신 클립 길이 표로 근사한다.
// 구현 범위·생략: docs/impl/physics.md "상태기계".
import { f32 } from "../fmath.ts";
import type { PlayerState } from "./state.ts";
import { isSquidMove, isSquidSM, STATE_TABLE } from "./states.ts";

/**
 * 상태 → 클립 끝 프레임(FSKA FrameCount)·반복. 값은 analysis/graphics/dump/samples.json.gz [데이터].
 * 커맨드 → 클립 대응은 ASB 가 정하므로(JumpVarID 무작위 변형 등) 대표 클립(…00)으로 근사 [추정].
 */
const CLIP: Record<number, [number, boolean]> = {
  0x82: [6, false], // ToSquid
  0x83: [6, false],
  0x84: [13, false], // Sqd_ToSquid
  0x85: [120, true], // Sqd_Wait
  0x86: [120, true],
  0x87: [100, true], // Sqd_Walk
  0x88: [30, false], // Sqd_Surprise
  0x89: [15, false], // Sqd_Jump_St
  0x8a: [30, true], // Sqd_Jump
  0x8b: [30, true],
  0x8c: [15, false], // Sqd_Jump_Ed
  0x8f: [120, true], // Sqd_WallJumpCharge
  0x90: [35, false], // Sqd_WallJump
  0x91: [3, false], // Sqd_ToHuman
  0x92: [30, false], // ToHuman
  0x93: [24, false], // ToHuman_Chariot
  0x94: [30, false],
  0x95: [30, false],
  0x99: [5, false], // Jump00_St
  0x9a: [5, false], // JumpShoot_Shtr00_St
  0x9b: [20, false], // Jump00
  0x9f: [20, false], // JumpShoot_Shtr00
  0xa0: [20, false],
  0xa4: [20, false],
  0xa6: [19, false], // Jump00_Ed
  0xa7: [19, false], // JumpShoot_Shtr00_Ed
  0x56: [135, true], // Wait
  0x59: [135, true],
  0x5f: [40, true], // Walk
  0x60: [40, true],
  0x69: [40, true],
  0x72: [40, true],
  0x7b: [40, true],
};

function clipOf(s: number): [number, boolean] {
  return CLIP[s] ?? [1, true];
}

/** 상태 적용 0x710244128c (블렌드·레이어는 표시 쪽). 진행 프레임 0 으로 진입. */
export function applyState(p: PlayerState, s: number, rate = 1): void {
  if (p.state !== s) {
    p.prevState = p.state;
    p.state = s;
  }
  const [end] = clipOf(s);
  p.stateFrame = 0;
  p.stateEnd = end;
  p.stateRate = rate;
  p.stateChanged = true;
  p.squid = isSquidMove(s);
  p.squidModel = STATE_TABLE[s]?.[1] === 1;
}

/** 요청 0x7102447bfc 의 모델 검사: 다른 모델 상태로는 전환 상태를 거쳐야 한다. */
export function requestState(p: PlayerState, s: number, rate = 1, force = false): boolean {
  if (s === p.state && !force) return false;
  const modelNow = STATE_TABLE[p.state]?.[1] ?? 0;
  const modelNew = STATE_TABLE[s]?.[1] ?? 0;
  const free = (s >= 0x91 && s <= 0x98) || s === 0xad || s === 0xae || (s >= 0x82 && s <= 0x84) || s === 0xf1 || s === 0xf2 || (s >= 0xe6 && s <= 0x11d);
  if (modelNow !== modelNew && !free && !force) return false;
  applyState(p, s, rate);
  return true;
}

function animEnded(p: PlayerState): boolean {
  const [end, loop] = clipOf(p.state);
  return !loop && p.stateFrame >= end;
}

/** 점프 시작 0x7102448ee4: 오징어 → 0x89, 사람 → 사격 ? 0x9a : 0x99 (슈터 K 는 마스크 밖). */
export function requestJumpState(p: PlayerState, shoot: boolean): void {
  requestState(p, isSquidMove(p.state) ? 0x89 : shoot ? 0x9a : 0x99, 1, true);
}

/** 착지 0x710244905c: 오징어 0x8c, 사람 사격 ? 0xa7 : 0xa6, 재생 속도 사람 0.7 · 오징어 1.0. */
export function requestLandState(p: PlayerState, shoot: boolean): void {
  if (isSquidMove(p.state)) requestState(p, 0x8c, 1, true);
  else requestState(p, shoot ? 0xa7 : 0xa6, f32(0.7), true);
}

export interface SmInput {
  want: boolean;
  shoot: boolean;
  /** 이동 애니 속도값 SM+0xd4 (0x710246d060 미판독 → 수평 이동 속력으로 근사) */
  animSpeed: number;
  /** 조준 수평 방향(본체+0x538) */
  aim: ArrayLike<number>;
  frame: number;
}

export interface SmEvents {
  toSquid: boolean;
  toHuman: boolean;
}

/** 슬롯19 상태기계 갱신(0x710243e7d0 → 0x7102442354) 후 애니 진행. */
export function updateStateMachine(p: PlayerState, inp: SmInput): SmEvents {
  const ev: SmEvents = { toSquid: false, toHuman: false };
  const cur = p.state;
  const inSquid = isSquidSM(cur);
  if (!inSquid && inp.want) {
    if (requestState(p, 0x82, 1, true)) ev.toSquid = true;
    if (p.transform < 30) p.transform = 30;
  } else if (inSquid && !inp.want && !(cur >= 0x91 && cur <= 0x98)) {
    if (cur === 0x86) {
      requestState(p, 0x96);
      p.transform = 0x8c;
    } else {
      applyState(p, 0x91);
      p.transform = 0x5a;
      if (p.holdBlock && p.airFrames < 4) p.toHumanFrame = inp.frame;
    }
    ev.toHuman = true;
  }
  // 전환 단계 진행 (end < cur + 3)
  const s0 = p.state;
  if (s0 === 0x82 || s0 === 0x83 || s0 === 0x91 || s0 === 0x96 || s0 === 0xad || s0 === 0xf1) {
    if (p.stateEnd < f32(p.stateFrame + 3)) {
      if (s0 === 0x82 || s0 === 0x83) applyState(p, 0x84, p.stateRate);
      else if (s0 === 0x91) {
        const wj = p.toHumanFrame > 0 && p.toHumanFrame + 30 > inp.frame;
        applyState(p, wj ? 0x95 : 0x92);
      } else applyState(p, s0 + 1);
    }
  }
  // 변신 과도기 카운터 SM+0xf0
  if (p.state >= 0x82 && p.state <= 0x84) p.transform += 10;
  else if (p.transform > 0) p.transform--;
  formState(p, inp);
  // 애니 진행(래퍼 틱)
  const [end, loop] = clipOf(p.state);
  p.stateEnd = end;
  let f = f32(p.stateFrame + p.stateRate);
  if (loop) {
    if (f >= end) f = f32(f - end);
  } else if (f > end) f = end;
  p.stateFrame = f;
  return ev;
}

/** 이동 사분면 B+0x720 (0x71024a81a4): 0 앞, 1 뒤, 2 왼쪽, 3 오른쪽. 히스테리시스는 직전 값 기준. */
function moveQuadrant(p: PlayerState, aim: ArrayLike<number>): number {
  if (isSquidMove(p.state)) return (p.quadrant = 0);
  const v = p.vel;
  const l = Math.hypot(v[0], v[2]);
  if (l < 1e-6) return p.quadrant;
  const mx = v[0] / l, mz = v[2] / l;
  const d = aim[0] * mx + aim[2] * mz;
  const q = p.quadrant;
  const [f, b] = q === 0 ? [0.4, -0.6] : q === 1 ? [0.6, -0.4] : [0.6, -0.6];
  if (d > f) p.quadrant = 0;
  else if (d < b) p.quadrant = 1;
  else p.quadrant = aim[2] * mx - aim[0] * mz <= 0 ? 3 : 2;
  return p.quadrant;
}

/** 0x7102442354 중 점프·낙하(P15)·지상 공통(P16) — 슈터·특수 없음 경로. */
function formState(p: PlayerState, inp: SmInput): void {
  const cur = p.state;
  const sq = isSquidMove(cur);
  const air = p.airFrames;
  const idle = inp.animSpeed < (p.stickMag01 > 0 ? 0.001 : 0.003);
  const end = animEnded(p);
  if (cur === 0x88 && !end) return;
  if (cur >= 0x91 && cur <= 0x98 && !end) {
    // G: ToHuman 계열은 이동·공격 입력이 있으면 프레임 1부터 끊김
    if (p.stateFrame < 1) return;
    if (idle && !inp.shoot) return;
  }
  // P12 Somersault: B+0x7f4 && (B+0x784 && B+0xac4 < 1 || cur == 0x8d) && cur ∈ 0x82..0x90 → 0x8d (state_big_full.c 1492~1540행)
  if (p.launch.active && (inp.want || cur === 0x8d)) {
    if (cur === 0x8d || !(cur >= 0x82 && cur <= 0x90)) return;
    applyState(p, 0x8d);
    return;
  }
  // P13 WallJump: want && B+0x782 && B+0x780 && cur == 0x87 && !B+0x7a0 → 0x90, SM+0x1f4 = 게임 프레임 (SM+0xf6·[SM+0x10]+8 은 통과로 둠)
  if (inp.want && p.holdBlock && p.jump3dHold && cur === 0x87 && !p.display.hidden) {
    if (requestState(p, 0x90)) p.toHumanFrame = inp.frame;
    return;
  }
  if (cur === 0x90 && !end) return;
  const jumpSet = (cur >= 0x89 && cur <= 0x8c) || (cur >= 0x99 && cur <= 0xa9);
  if (jumpSet) {
    // [A] 사격 변형 교체(재생 위치 유지)
    const swap: Record<number, number> = { 0x99: 0x9a, 0x9a: 0x99, 0x9b: 0x9f, 0x9f: 0x9b, 0xa0: 0xa4, 0xa4: 0xa0, 0xa6: 0xa7, 0xa7: 0xa6 };
    const shootVar = cur === 0x9a || cur === 0x9f || cur === 0xa4 || cur === 0xa7;
    if (swap[cur] !== undefined && shootVar !== inp.shoot) {
      const fr = p.stateFrame, rt = p.stateRate;
      applyState(p, swap[cur], rt);
      p.stateFrame = fr;
    }
    const s = p.state;
    if (s === 0x89 || s === 0x99 || s === 0x9a) {
      if (air < 1) return ground(p, inp, idle);
      if (animEnded(p)) requestState(p, sq ? 0x8a : inp.shoot ? 0x9f : 0x9b, f32(0.6), true);
      return;
    }
    if (s === 0x8a || (s >= 0x9b && s <= 0x9f)) {
      if (s === 0x9b || s === 0x9f) {
        const t = clamp01(p.stateFrame / p.stateEnd);
        p.stateRate = f32(0.6 + (0.001 - 0.6) * Math.pow(t, 0.737));
      }
      if (air > 0) return;
      return ground(p, inp, idle);
    }
    if (s === 0x8b || (s >= 0xa0 && s <= 0xa5)) {
      if (s === 0xa0 || s === 0xa4) {
        const t = clamp01(p.stateFrame / p.stateEnd);
        p.stateRate = f32(0.2 + (0.001 - 0.2) * Math.pow(t, 6.644));
      }
      if (air < 1) return ground(p, inp, idle);
      return;
    }
    // [E] 착지
    const quick = false;
    const thr = quick ? 3 : idle ? p.stateEnd - 1 : 18 + (3 - 18) * clamp01((inp.animSpeed - 0.001) / (0.05 - 0.001));
    if (p.stateFrame < thr) return;
    return ground(p, inp, idle);
  }
  // [F] 그 밖 상태에서 낙하 시작
  if (air > 10) {
    if (cur >= 0x82 && cur <= 0x90) requestState(p, 0x8b, 1, true);
    else if (!sq) requestState(p, inp.shoot ? 0xa4 : 0xa0, f32(0.2), true);
    return;
  }
  ground(p, inp, idle);
}

function clamp01(x: number): number {
  return x < 0 ? 0 : x > 1 ? 1 : x;
}

/** P16 지상 공통 */
function ground(p: PlayerState, inp: SmInput, idle: boolean): void {
  const cur = p.state;
  if (cur >= 0x91 && cur <= 0x98 && !animEnded(p)) {
    if (p.stateFrame < 1) return;
    if (idle && !inp.shoot) return;
  }
  if (cur >= 0x82 && cur <= 0x84 && !animEnded(p) && cur !== 0x84) return;
  if (cur === 0x84 && !animEnded(p)) return;
  // H: want && clamp((B+0x774 − 10 − 0)/(WallJumpChargeFrm − 0)) > 0 → 0x8f WallJumpCharge (state_big_full.c 2370~2422행)
  if (inp.want) {
    const x = f32(p.wallJumpCharge - 10);
    const F = p.gear.wallJumpChargeFrames;
    if (0 < x && 0 < F) {
      if (cur === 0x8f) return;
      const trans = (cur >= 0x91 && cur <= 0x98) || (cur >= 0x82 && cur <= 0x84) || cur === 0xf1 || cur === 0xf2 || cur === 0xad || cur === 0xae;
      if (trans && !animEnded(p)) return;
      requestState(p, 0x8f);
      return;
    }
  }
  const air = p.airFrames;
  if (air < 13 || inp.want) {
    if (!idle) {
      if (inp.want) {
        const v = inp.animSpeed;
        const rate = v <= 0.001 ? 0.05 : v >= 0.04 ? 1 : 0.05 + (0.95 * (v - 0.001)) / 0.039;
        if (cur !== 0x87) requestState(p, 0x87, f32(rate));
        else p.stateRate = f32(rate);
        return;
      }
      const q = moveQuadrant(p, inp.aim);
      // 슈터(K 1/2/8): 앞 shoot?0x60:0x5f, 뒤 0x69, 왼쪽 0x72, 오른쪽 0x7b (player_state.md §6.3 I2)
      const s = q === 0 ? (inp.shoot ? 0x60 : 0x5f) : q === 1 ? 0x69 : q === 2 ? 0x72 : 0x7b;
      if (cur !== s) {
        const fr = p.stateFrame;
        if (requestState(p, s)) {
          // 이전 슬롯 프레임을 새 애니에 이어 씀(0x7102450348) — 걷기 계열끼리만
          const walk = (x: number) => x === 0x5f || x === 0x60 || x === 0x69 || x === 0x72 || x === 0x7b;
          if (walk(p.prevState)) p.stateFrame = fr;
        }
      }
      return;
    }
    if (inp.want) {
      if (cur !== 0x85) requestState(p, 0x85);
      return;
    }
  }
  if (inp.want) return;
  if (air >= 13 && p.vy > 0 && !inp.shoot) return;
  // K: 사람 정지 0x710244187c — 슈터: shoot ? 0x59 : 0x56
  const s = inp.shoot ? 0x59 : 0x56;
  if (cur !== s) requestState(p, s);
}
