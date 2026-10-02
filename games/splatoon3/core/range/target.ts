// spl::SighterTarget (시험 사격장 표적) — vtable 0x7105615188, 객체 0x1e0 B.
// 근거: docs/range/shooting_range.md (§3 흐름, §5 상태, §6 식). 주소는 각 함수 주석.
import { f32 } from "../fmath.ts";
import type { DamageInfo, Team } from "../types.ts";
import { BEND_KIND_SCALE, SIGHTER_ANIM_FRAMES, type SighterParam } from "./data.ts";
import { quatToMat3, type Quat, type RailMover } from "./rail.ts";

/** spl::SighterTarget 상태 (등록 0x71021ee66c, 순서 = 번호) [판독] */
export const SighterState = { Wait: 0, DamageShot: 1, Burst: 2, BurstWait: 3, Expand: 4, Flick: 5 } as const;
export const SIGHTER_STATE_NAMES = ["Wait", "DamageShot", "Burst", "BurstWait", "Expand", "Flick"] as const;
/** 상태 → 애니 이름 (enter 함수들의 switch, 0x71021f10d8 등) [판독] */
const STATE_ANIM = ["", "DamageShot", "Brust", "", "Expand", "Flick"] as const;

/** game::DamageResultType [판독/추정 — combat/damage_hit.md §4.7] */
export const DamageResult = { Through: 0, Invincible: 4, Armored: 5, Damaged: 6, Cure: 7 } as const;

const EPS_RATE = f32(1e-5); // 0x3727c5ac
const INV60 = f32(0.016666668);

export interface SighterConfig {
  kind: string;
  model: string;
  elink: string;
  param: SighterParam;
  bend: { Kp: number; Kd: number };
  maxHitPoint: number;
  pos: [number, number, number];
  rot: Quat;
  team: Team;
  rail: RailMover | null;
}

/** HP 홀더(기준: 홀더 시작) — combat/player_life.md §4.1, §6.1. 비컨 등 DamageHelper 대상과 같은 홀더. */
export interface HpHolder {
  /** +0x00 비트0 음수 허용, 초기 6 */
  flags: number;
  /** +0x48 */
  max: number;
  /** +0x4c */
  hp: number;
  /** +0x50 이번 프레임 누적 */
  pending: number;
}

/** DamageReceiver 중 표적이 바꾸는 필드 (기준: 리시버 R) — combat/damage_hit.md §4.5 */
export interface ReceiverState {
  /** +0x1bc 소속 팀 (리셋 0x71021ef388 이 로컬 플레이어 팀 == 1 ? 0 : 1 로 씀) */
  team: number;
  /** +0x1cc 추가 배율 사용 */
  extraOn: boolean;
  /** +0x1c4 추가 배율 */
  extraRate: number;
  /** +0x1c8 추가 배율 결과 덮어쓰기(8 = 안 함) */
  extraResult: number;
}

export interface DamageOutcome {
  damage: number;
  result: number;
}

export type RateFn = (row: string, col: string) => number;

export class SighterTarget {
  readonly id: number;
  readonly cfg: SighterConfig;
  readonly team: Team;
  readonly rateCol = "Default";
  pos: [number, number, number];
  rot: Quat;
  /** 열 우선 3x3 (X, Y, Z 축) */
  axes: number[];
  /** spl__SighterTargetParam.Scale → 액터 스케일 (0x71021ef388, 0x71021f0a94) */
  scale: number;

  readonly holder: HpHolder;
  readonly recv: ReceiverState;
  /** +0x120 받은 데미지 누계(표시용) */
  accum = 0;
  /** 상태 기계 +0x128: +0x130 cur, +0x134 counter(f32 프레임), +0x138 prev, +0x149 changed */
  state: number = SighterState.Wait;
  counter = 0;
  prevState: number = SighterState.Wait;
  private changed = false;
  /** 스켈레탈 애니(+0x170) */
  anim = "";
  animFrame = 0;
  /** 몸(Main·ColBullet) 활성 — 0x7103ae4c48(body, 0|1) */
  bodiesEnabled = true;
  /** DamageShotBend 가산 애니가 살아 있는지(+0x188): Burst 진입에서 멈추고 Expand 진입에서 다시 건다 */
  bendAnimOn = true;
  bendAngleDeg = 0;
  bendWeight = 0;
  /** spl::BendCalculator(+0x180): +0x60 충격, +0x6c 휨 벡터(로컬), +0x78 속도 */
  readonly bendImp = [0, 0, 0];
  readonly bendPos = [0, 0, 0];
  readonly bendVel = [0, 0, 0];
  /** vt19 0x71021efc24 표시 정보 */
  damageInfoActive = false;
  /** 이번 스텝의 사건(시스템이 이벤트로 내보냄) */
  readonly pendingEvents: { type: string; [k: string]: unknown }[] = [];

  constructor(id: number, cfg: SighterConfig) {
    this.id = id;
    this.cfg = cfg;
    this.team = cfg.team;
    this.pos = [...cfg.pos];
    this.rot = cfg.rot;
    this.axes = quatToMat3(cfg.rot);
    this.scale = cfg.param.Scale;
    this.holder = { flags: 6, max: cfg.maxHitPoint, hp: cfg.maxHitPoint, pending: 0 };
    this.recv = { team: cfg.team, extraOn: false, extraRate: 0, extraResult: 8 };
    this.reset();
  }

  get tipsTrial(): boolean {
    return this.cfg.param.IsTipsTrial;
  }

  /** 0x71021ef388 (vt15 리셋) 중 웹에 필요한 부분 */
  reset(): void {
    this.accum = 0;
    this.holderReset();
    this.bendAnimOn = true;
    this.bendImp.fill(0);
    this.bendPos.fill(0);
    this.bendVel.fill(0);
    if (this.cfg.rail) {
      // 레일이 있으면 위치 = 시작 점(ToRailPoint) 위치. 회전은 첫 갱신의 레일 자세로.
      const r = this.cfg.rail;
      r.reset();
      const p = r.rail.pos[r.start];
      this.pos = [p[0], p[1], p[2]];
    } else {
      this.pos = [...this.cfg.pos];
    }
    this.changeState(SighterState.Wait);
    this.counter = 0;
  }

  // ---- HP 홀더 -----------------------------------------------------------
  /** 0x7101a88e1c */
  holderReset(): void {
    this.holder.hp = this.holder.max;
    this.holder.pending = 0;
  }

  /** 0x7101a8905c (dt 감소·회복률 = 0: SlipCure 0, 회복률 설정 없음) */
  holderUpdate(): void {
    const h = this.holder;
    if (h.flags & 1 || h.hp > 0) {
      if (h.pending > 0) h.hp -= h.pending;
      const lo = h.flags & 1 ? -h.max : 0;
      h.hp = h.hp < lo ? lo : Math.min(h.hp, h.max);
    }
    h.pending = 0;
  }

  // ---- 상태 기계 (0x710125a178 / 0x710125a394) ------------------------------
  changeState(s: number): void {
    this.prevState = this.state;
    this.state = s;
    this.counter = 0;
    this.changed = true;
    this.enter(s);
  }

  private exec(dt: number): void {
    this.changed = false;
    switch (this.state) {
      case SighterState.Wait:
        this.execWait();
        break;
      case SighterState.DamageShot:
        if (this.animFinished()) this.changeState(SighterState.Wait); // 0x71021f1464
        break;
      case SighterState.Burst:
        // 0x71021f1864: 팁 시험 표적은 깨진 채로 남는다
        if (!this.tipsTrial && this.animFinished() && (this.state as number) !== SighterState.BurstWait) this.changeState(SighterState.BurstWait);
        break;
      case SighterState.BurstWait:
        this.execBurstWait();
        break;
      case SighterState.Expand:
        // 0x71021f2308: 진행 중에는 몸 크기 보간(0x71021f0dcc, 미구현 — 문서 §11), 끝나면 Wait
        if (this.animFinished() && (this.state as number) !== SighterState.Wait) this.changeState(SighterState.Wait);
        break;
      case SighterState.Flick:
        if (this.animFinished() && (this.state as number) !== SighterState.Wait) this.changeState(SighterState.Wait); // 0x71021f24b8
        break;
    }
    if (!this.changed) this.counter = f32(this.counter + dt);
  }

  private enter(s: number): void {
    this.playAnim(STATE_ANIM[s]);
    switch (s) {
      case SighterState.Wait: // 0x71021f10d8
        this.recv.extraOn = false;
        this.bodiesEnabled = true;
        break;
      case SighterState.Burst: // 0x71021f14a0
        this.bodiesEnabled = false;
        this.setInvincible();
        this.bendAnimOn = false;
        this.pendingEvents.push({ type: "Break", target: this.id, pos: [...this.pos], user: this.cfg.elink });
        break;
      case SighterState.Expand: // 0x71021f1ff8
        this.bodiesEnabled = true;
        this.bendAnimOn = true;
        this.bendWeight = 0;
        break;
      case SighterState.Flick: // 0x71021f2384
        this.holderReset();
        this.accum = 0;
        this.setInvincible();
        break;
    }
  }

  /** R+0x1c4 = 0.0, +0x1c8 = 4(Invincible), +0x1cc = 1 */
  private setInvincible(): void {
    this.recv.extraRate = 0;
    this.recv.extraResult = DamageResult.Invincible;
    this.recv.extraOn = true;
  }

  /** 0x71021f11f0 */
  private execWait(): void {
    const h = this.holder;
    if (h.max <= h.hp) return;
    if (this.counter <= f32(this.cfg.param.NoDamageRefreshFrame)) return;
    if (this.state === SighterState.Flick) return;
    this.changeState(SighterState.Flick);
  }

  /** 0x71021f1a9c */
  private execBurstWait(): void {
    const p = this.cfg.param;
    const h = this.holder;
    const i10 = Math.trunc(f32(this.counter - f32(p.LossOfColorWaitFrame)));
    let t: number;
    if (i10 < 0) t = 0;
    else {
      let d = p.BurstWaitDispFrame - p.LossOfColorWaitFrame;
      if (d < 2) d = 1;
      t = f32(f32(i10) / f32(d));
      if (t > 1) t = 1;
    }
    const v = Math.trunc(f32(t * f32(h.max)));
    const lo = h.flags & 1 ? -h.max : 0;
    h.hp = v >= lo ? Math.min(v, h.max) : lo;
    if (f32(p.BurstWaitDispFrame) < this.counter) {
      this.holderReset();
      this.accum = 0;
      if (this.state !== SighterState.Expand) this.changeState(SighterState.Expand);
    }
  }

  // ---- 애니 --------------------------------------------------------------
  private playAnim(name: string): void {
    this.anim = name;
    this.animFrame = 0;
  }

  get animFrames(): number {
    return SIGHTER_ANIM_FRAMES[this.anim] ?? 0;
  }

  /** 0x710126006c: 프레임 ≥ FrameCount */
  animFinished(): boolean {
    return this.animFrame >= this.animFrames;
  }

  // ---- 피격 --------------------------------------------------------------
  /**
   * 리시버 0x7101a86ec0(결과·배율) → 리스너: DamageHelper(HP 누적 0x7101a89524) + 표적(0x71021ef25c).
   * 반환 = 최종 데미지(0.1 HP)와 결과.
   */
  receive(info: DamageInfo, rate: RateFn): DamageOutcome {
    const out = this.computeResult(info, rate);
    if (out.result === DamageResult.Cure) this.holder.hp = Math.min(this.holder.hp + out.damage, this.holder.max);
    else this.holder.pending += out.damage;
    // 0x71021ef25c
    if (!(this.recv.extraOn && this.recv.extraRate === 0) && out.damage >= 1) {
      this.accum += out.damage;
      this.changeState(SighterState.DamageShot);
    }
    return out;
  }

  /** 0x7101a86ec0 중 표적에 해당하는 부분(이력 모드·시간 창·ObjectEffect_Up 제외 — 문서 §11) */
  computeResult(info: DamageInfo, rate: RateFn): DamageOutcome {
    const r = this.recv;
    // 팀 판정 모드 1(기본): 같은 팀이면 Through
    if (r.team !== -1 && r.team !== 3 && r.team === info.team) return { damage: 0, result: DamageResult.Through };
    let result: number = DamageResult.Damaged;
    let dmg = Math.trunc(info.value);
    if (r.extraOn) {
      dmg = Math.trunc(f32(f32(r.extraRate + EPS_RATE) * f32(dmg)));
      if (r.extraResult !== 8) result = r.extraResult;
    }
    const k = rate(info.rateRow, this.rateCol);
    dmg = Math.trunc(f32(f32(k + EPS_RATE) * f32(dmg)));
    if (dmg === 0) return { damage: 0, result: r.extraOn && r.extraResult !== DamageResult.Damaged ? r.extraResult : DamageResult.Through };
    if (dmg > 99999) dmg = 99998;
    return { damage: dmg, result };
  }

  /**
   * 휨 충격 0x7101e3422c(scale 1.0, 굽힘 계산기, 접촉 위치, 충격 벡터, 종류).
   * 탄 접촉(vt22 0x71021f0348): 충격 = 접촉 속도(y=0) × BulletImpulsScaler, 종류 0.
   */
  addBendImpulse(contact: ArrayLike<number>, imp: ArrayLike<number>, kind: number, scale = 1.0): void {
    if (!(kind >= 0 && kind < 3)) return;
    const m = this.axes;
    const dx = f32(contact[0] - this.pos[0]), dy = f32(contact[1] - this.pos[1]), dz = f32(contact[2] - this.pos[2]);
    let a = f32(f32(f32(f32(dx * m[0]) + f32(dy * m[1])) + f32(dz * m[2])) * -10);
    let c = f32(f32(f32(f32(dx * m[6]) + f32(dy * m[7])) + f32(dz * m[8])) * -10);
    let ny = 0;
    const len = f32(Math.sqrt(f32(f32(f32(a * a) + 0) + f32(c * c))));
    if (len > 0) {
      const inv = f32(1 / len);
      a = f32(a * inv);
      ny = f32(inv * 0);
      c = f32(c * inv);
    }
    const ix = f32(f32(f32(f32(imp[0] * m[0]) + f32(imp[1] * m[1])) + f32(imp[2] * m[2])) * 10);
    const iy = f32(f32(f32(f32(imp[0] * m[3]) + f32(imp[1] * m[4])) + f32(imp[2] * m[5])) * 10);
    const iz = f32(f32(f32(f32(imp[0] * m[6]) + f32(imp[1] * m[7])) + f32(imp[2] * m[8])) * 10);
    let k = f32(BEND_KIND_SCALE[kind] * f32(f32(f32(f32(ix * INV60) * a) + f32(f32(iy * INV60) * ny)) + f32(f32(iz * INV60) * c)));
    if (k > 1) k = 1;
    const sc = f32((scale > 0.4 ? f32(0.4) : scale) / f32(0.4));
    const as = Math.abs(sc);
    let w = 0;
    if (as >= 0.001) {
      const e = f32(Math.exp(f32(f32(Math.log(as)) * f32(2.321928))));
      w = sc >= 0 ? e : -e;
    }
    this.bendImp[0] = f32(this.bendImp[0] + f32(f32(a * k) * w));
    this.bendImp[1] = f32(f32(f32(ny * k) * w) + this.bendImp[1]);
    this.bendImp[2] = f32(f32(f32(c * k) * w) + this.bendImp[2]);
  }

  /** 0x7101e33ed8 */
  private bendUpdate(): void {
    const { Kd, Kp } = this.cfg.bend;
    const v = this.bendVel, p = this.bendPos, im = this.bendImp;
    for (let i = 0; i < 3; i++) {
      v[i] = f32(v[i] + im[i]);
      v[i] = f32(Kd * v[i]);
    }
    for (let i = 0; i < 3; i++) {
      v[i] = f32(v[i] - f32(p[i] * Kp));
      p[i] = f32(v[i] + p[i]);
    }
    const l2 = f32(f32(f32(p[0] * p[0]) + f32(p[1] * p[1])) + f32(p[2] * p[2]));
    if (l2 > 1) {
      const inv = f32(1 / f32(Math.sqrt(l2)));
      for (let i = 0; i < 3; i++) p[i] = f32(p[i] * inv);
    }
    im.fill(0);
  }

  /** 0x7101e34468: 위쪽 축 둘레로 Z 축에서 휨 방향까지의 각, [0, 2π) */
  bendAngle(): number {
    const p = this.bendPos;
    let a = Math.atan2(p[0], p[2]); // 로컬 기준: Y·(Z×w) = p.x, w·Z = p.z
    if (a < 0) a += 2 * Math.PI;
    return f32(a);
  }

  // ---- 프레임 -------------------------------------------------------------
  /** vt18 0x71021ef9f8 (+ DamageHelper 프레임 갱신을 앞에) */
  step(): void {
    this.holderUpdate();
    if (!this.recv.extraOn || this.recv.extraRate !== 0) {
      if (this.holder.hp < 1 && this.state !== SighterState.Burst) this.changeState(SighterState.Burst);
    }
    this.exec(1);
    // 애니 진행 (0x71012664cc) — 1프레임 1 [추정]
    if (this.animFrame < this.animFrames) this.animFrame++;
    this.bendUpdate();
    if (this.bendAnimOn) {
      this.bendAngleDeg = f32(this.bendAngle() * f32(57.295776));
      const p = this.bendPos;
      const l = f32(Math.sqrt(f32(f32(f32(p[0] * p[0]) + f32(p[1] * p[1])) + f32(p[2] * p[2]))));
      this.bendWeight = l > 1 ? 1 : l;
    }
    if (this.cfg.rail) {
      const pose = this.cfg.rail.advance(INV60);
      this.pos = pose.pos;
      this.rot = pose.rot;
      this.axes = quatToMat3(pose.rot);
    }
    // vt19 0x71021efc24
    const h = this.holder;
    this.damageInfoActive = this.cfg.param.IsAlwaysDrawDamageInfo || h.hp < h.max;
  }

  /** 표시 위치 = 위치 + Y축 × DamageInfoOffsetY */
  damageInfoPos(): [number, number, number] {
    const o = this.cfg.param.DamageInfoOffsetY, m = this.axes;
    return [f32(f32(m[3] * o) + this.pos[0]), f32(f32(m[4] * o) + this.pos[1]), f32(f32(m[5] * o) + this.pos[2])];
  }

  /** 로컬 점 → 월드 (스케일 포함) */
  toWorld(l: ArrayLike<number>): [number, number, number] {
    const m = this.axes, s = this.scale;
    const x = l[0] * s, y = l[1] * s, z = l[2] * s;
    return [f32(this.pos[0] + m[0] * x + m[3] * y + m[6] * z), f32(this.pos[1] + m[1] * x + m[4] * y + m[7] * z), f32(this.pos[2] + m[2] * x + m[5] * y + m[8] * z)];
  }
}
