// 슈터 메인 사격 처리(spl::PlayerInkActionShooter 0x7102583008)와 입력 게이트(본체 슬롯19 0x7102483134 의 0x7102485dc0~0x7102486a40).
// 근거: docs/camera/aim_swerve.md §3·§6, 발사 위치 0x7102552170, 생성 정보 0x71025823b0, 초기 속도 0x71026beed0,
// 잉크 0x7102580780/0x7102492120/0x7102353718/0x71025856c8, 발사 후 타이머 0x71024b28b0, 이펙트 액션 0x7102864104(effect_sound.md §3.2).
import { f32 } from "../fmath.ts";
import { inputCountdown } from "./input.ts";
export { INK_RECOVER_STD } from "./ink.ts";
import type { Team } from "../types.ts";
import type { V3 } from "./move.ts";
import type { AdditionParam, SplashSpawnParam, WeaponShooterParam } from "./params.ts";
import { dirSpeed, initialVelocity, MUZZLE_OFFSET, permAt, SHOT_DIR_DEFAULT, spawnPosition, type ShotDirParam } from "./spawn.ts";
import { RepeatTimer, shotSeedU32, Swerve, type MatchSeeds } from "./swerve.ts";

/** InkActionID (effect_sound.md §3.2) */
export const INK_ACTION = { FireImpact: 0, FireOn: 1, FireOff: 2 } as const;
const INK_ACTION_NAME = ["FireImpact", "FireOn", "FireOff"];

/** [0x71058bdf0c] = 6, [0x71058bbf1c] = 2, [0x71058bbf20] = 6 [실행(정적 초기화 에뮬)] */
const POST_DELAY_CAP = 6;
const HELD_MIN = 2;
const HUMAN_MIN = 6;

export interface ShotInput {
  /** 입력 writer의 B+4d0 > 0. 실제 플레이어는 Sender 우선순위/차단을 먼저 소비한다. */
  zr: boolean;
  /** 오징어 상태(사람 프레임 a90 = 0) */
  squid: boolean;
  pos: V3;
  vel: V3;
  aim: V3;
  axis: V3;
  rigForward: V3;
  pitch: number;
  airFramesGe4: boolean;
  jumped: boolean;
  frame: number;
  seeds: MatchSeeds;
  /** 발사 속력 0x7102899980 = MoveParam.SpawnSpeed + 0.0/max(GoStraightToBrakeStateFrame, 1) */
  spawnSpeed: number;
}

export interface ShotOut {
  pos: V3;
  dir: V3;
  speed: number;
  vel: V3;
  split: number;
  angle: number;
  frame: number;
}

/** 본체 잉크 쪽(B+0x698 등). 구현은 runtime(플레이어 필드 또는 임시값). */
export interface InkPort {
  /** 0x7102492120 queryOnly */
  can(cost: number): boolean;
  /** 0x7102492120 소비 */
  consume(cost: number): boolean;
  /** 0x7102353718(player, InkRecoverStop, ok, 0) */
  recoverStop(frames: number, ok: boolean): void;
  /** 0x71025856c8 부족 경로: B+0x6ac = RepeatFrame < 31 ? 30 : RepeatFrame, "잉크 부족" UI */
  lack(frames: number): void;
  /** B+0xac4·B+0xab8 = max(·, n) (오징어 잠금·서브/스페셜 게이트) */
  postDelay(n: number): void;
}

/**
 * 입력 게이트: 원본 B+0x4d4(누른 프레임)·B+0xa90(사람 프레임)·B+0x530/+0x531(탭 래치)·B+0xabc/+0xadc(발사 후 타이머).
 * 원본은 본체 필드이고 physics 쪽에 없어 무기 쪽에 둔다(docs/impl/weapon.md 조정 요청).
 */
export class ShotGate {
  held = 0;
  human = 0;
  latch530 = false;
  latch531 = false;
  abc = 0;
  adc = 0;
  /** B+0xab4 메인 무기 잠금 */
  ab4 = 0;

  reset(): void {
    this.held = 0;
    this.human = 0;
    this.latch530 = false;
    this.latch531 = false;
    this.abc = 0;
    this.adc = 0;
    this.ab4 = 0;
  }

  /** 반환 [in0 트리거, in1 차단, in2 잠금]. pdh = PreDelayFrame_HumanShot, pds = PreDelayFrame_SquidShot − SquidShotShorteningFrame. */
  update(zr: boolean, squid: boolean, pdh: number, pds: number): [boolean, boolean, boolean] {
    this.human = squid ? 0 : this.human + 1;
    if (squid) {
      if (zr) {
        this.latch531 = !(this.abc > 0);
        this.latch530 = false;
      }
    }
    const trig = zr || this.latch530 || this.latch531;
    this.held = this.ab4 < 1 && trig ? this.held + 1 : 0;
    const H = this.held >= HELD_MIN + pdh;
    if (!squid && !H && zr && !this.latch531 && this.adc < 1) this.latch530 = !(this.abc > 0);
    const ready = H && this.human >= HUMAN_MIN + pds;
    const in0 = zr || this.latch530 || this.latch531;
    return [in0, !ready, this.ab4 > 0];
  }

  /** 발사 틱(빈 발사 포함): B+0x530(u16) = 0 */
  clearLatch(): void {
    this.latch530 = false;
    this.latch531 = false;
  }

  /** 0x71024b28b0 중 게이트에 쓰는 것: abc = max(·, n), adc = max(·, n+4) */
  afterShot(n: number): void {
    this.abc = Math.max(this.abc, n);
    this.adc = Math.max(this.adc, n + 4);
  }

  /** 입력 단계 포화 감소 [실행]. adc의 감소 생산자는 여전히 근사. */
  tick(): void {
    this.abc = inputCountdown(this.abc);
    if (this.adc > 0) this.adc--;
    this.ab4 = inputCountdown(this.ab4);
  }
}

export class ShooterAction {
  readonly owner: number;
  readonly team: Team;
  readonly timer = new RepeatTimer();
  readonly swerve = new Swerve();
  readonly gate = new ShotGate();
  /** +0x91 패턴 바이트 */
  pattern = 0;
  /** +0x98 발사 수 */
  shots = 0;
  /** +0x90 */
  firing = false;
  /** +0xa0 잉크 부족 카운터 */
  noInk = 0;
  /** 무기 InkAction(+0x320), 보류(+0x384), 마지막 즉시 변경 프레임(+0x374), FireOn 연속 프레임(+0x380) */
  action: number = INK_ACTION.FireOff;
  pendingAction = -1;
  lastImpactFrame = -1;
  fireOnFrames = 0;
  shotDir: ShotDirParam = SHOT_DIR_DEFAULT;

  constructor(owner: number, team: Team, p: WeaponShooterParam, frame: number, playerIndex: number, seeds: MatchSeeds) {
    this.owner = owner;
    this.team = team;
    this.reset(p, frame, playerIndex, seeds);
  }

  /** vt36 0x7102582e3c: 타이머·bias·점프 카운터 0, +0x91 = 첫 getU32 하위 바이트(시드 F + Pidx·100), 대기(리셋 경로) */
  reset(p: WeaponShooterParam, frame: number, playerIndex: number, seeds: MatchSeeds): void {
    this.timer.phase = 0;
    this.timer.rem = 0;
    this.timer.count = 0;
    this.timer.limit = 999;
    this.swerve.reset();
    this.firing = false;
    this.pattern = shotSeedU32((frame < 0 ? 0 : frame) + Math.imul(playerIndex, 100), seeds) & 0xff;
    this.timer.idle(p.RepeatFrame, true, false);
    this.gate.reset();
  }

  /**
   * 한 프레임(입력 게이트 → 0x7102583008). 쏜 탄 정보를 돌려준다(없으면 null).
   * actions 로 이번 프레임 InkAction 변경("FireImpact"/"FireOn"/"FireOff")을, noInk 로 "잉크 부족" 표시 요청을 알린다.
   */
  step(p: WeaponShooterParam, split: SplashSpawnParam, add: AdditionParam, inp: ShotInput, ink: InkPort, actions: string[]): ShotOut | null {
    this.gate.tick(); // 249f494 입력 감소 → 슬롯19 사격 게이트
    if (inp.jumped) this.swerve.onJump(p);
    const pds = (p.PreDelayFrame_SquidShot | 0) - (p.SquidShotShorteningFrame | 0);
    const [trigger, blocked, locked] = this.gate.update(inp.zr, inp.squid, p.PreDelayFrame_HumanShot | 0, pds);
    const cost = f32(f32(p.InkConsume) * f32(1 * 1));
    let shot: ShotOut | null = null;
    let fired = false;
    if (!blocked && trigger && !locked) {
      const due = this.timer.update(p.RepeatFrame);
      if (!due) {
        if (!ink.can(cost)) ink.lack(p.RepeatFrame < 31 ? 30 : p.RepeatFrame);
        this.firing = true;
      } else {
        if (!ink.can(cost)) ink.lack(p.RepeatFrame < 31 ? 30 : p.RepeatFrame);
        const ok = ink.consume(cost);
        if (!ok) {
          this.noInk = (this.noInk + 1) | 0;
        } else {
          shot = this.fire(p, split, add, inp);
          fired = true;
          this.gate.afterShot(p.PostDelayFrame | 0);
          ink.postDelay(p.PostDelayFrame | 0);
        }
        if (shot === null) {
          const nb = f32(f32(p.Stand_DegBiasKf) + this.swerve.bias);
          this.swerve.bias = nb <= f32(p.Stand_DegBiasMax) ? nb : f32(p.Stand_DegBiasMax);
        }
        ink.recoverStop(p.InkRecoverStop | 0, ok);
        this.firing = true;
        this.gate.clearLatch();
      }
      ink.postDelay(Math.min(p.PostDelayFrame | 0, POST_DELAY_CAP));
    } else {
      this.firing = false;
      this.timer.idle(p.RepeatFrame, false, false);
      if (this.lastImpactFrame < inp.frame) this.pendingAction = INK_ACTION.FireOff;
    }
    this.swerve.endFrame(p, this.timer.rem, trigger, inp.airFramesGe4);
    this.inkAction(fired, trigger && !blocked, inp.frame, actions);
    return shot;
  }

  private fire(p: WeaponShooterParam, sp: SplashSpawnParam, add: AdditionParam, inp: ShotInput): ShotOut {
    const n = (sp.SplitNum | 0) === 0 ? 1 : sp.SplitNum | 0;
    this.pattern = (this.pattern % n) & 0xff;
    const split = permAt(n, this.pattern);
    const pos: V3 = [0, 0, 0];
    spawnPosition(inp.pos, inp.rigForward, inp.pitch, this.shotDir, MUZZLE_OFFSET, pos);
    const dir0: V3 = [0, 0, 0];
    const frame = inp.frame < 0 ? 0 : inp.frame;
    const angle = this.swerve.fire(p, inp.aim, frame, inp.seeds, dir0);
    this.pattern = (this.pattern + 1) & 0xff;
    const v: V3 = [0, 0, 0];
    initialVelocity(f32(inp.spawnSpeed), dir0, inp.vel, inp.axis, add, false, v);
    const dir: V3 = [0, 0, 0];
    const speed = dirSpeed(v, dir);
    this.shots++;
    return { pos, dir, speed, vel: v, split, angle, frame };
  }

  /** 0x7102864104 즉시/보류 규칙과 슬롯19 0x710286540c 보류 적용(최소 유지 프레임 미확정 → 0). */
  private inkAction(fired: boolean, held: boolean, frame: number, out: string[]): void {
    if (fired) {
      if (this.action !== INK_ACTION.FireImpact) out.push(INK_ACTION_NAME[INK_ACTION.FireImpact]);
      this.action = INK_ACTION.FireImpact;
      this.lastImpactFrame = Math.max(this.lastImpactFrame, frame);
    }
    if (held && !(frame <= this.lastImpactFrame)) this.pendingAction = INK_ACTION.FireOn;
    if (this.pendingAction >= 0 && this.pendingAction !== this.action) {
      this.action = this.pendingAction;
      out.push(INK_ACTION_NAME[this.action]);
    }
    this.pendingAction = -1;
    this.fireOnFrames = this.action === INK_ACTION.FireOn ? this.fireOnFrames + 1 : 0;
  }
}

/** 0x7102492120 (partialOff = 1 경로): ok = r ≥ cost 이거나 |r − cost| ≤ 1e-5, 성공하면 r − cost, 회복량 thr 미만이면 0. */
export function consumeInk(r: number, cost: number, thr: number): number | null {
  const d = f32(r - cost);
  const near = r < cost && d >= f32(-1e-5) && d <= f32(1e-5);
  if (!(r >= cost) && !near) return null;
  return d < thr ? 0 : d;
}

export function canConsumeInk(r: number, cost: number): boolean {
  const d = f32(r - cost);
  return r >= cost || (r < cost && d >= f32(-1e-5) && d <= f32(1e-5));
}


