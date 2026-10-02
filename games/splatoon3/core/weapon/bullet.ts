// 탄(spl::BulletShooterBase / spl::BulletSplashShooter) 한 발. 근거: docs/weapon/shooter_bullet.md §3~5,
// physics/phive_controller.md §6, combat/damage_hit.md §6, paint/paint_shape.md §4~5·§7.7.
// 갱신 순서: pre(슬롯18) → 물리(바디 스텝) → post(슬롯21·19) → 접촉(슬롯22 → 58/59/60).
import { f32 } from "../fmath.ts";
import type { Team } from "../types.ts";
import { BulletBody } from "./body.ts";
import { fieldRadius, playerRadius } from "./damage.ts";
import type { SplashState } from "./splash.ts";
import { GO_STRAIGHT, initialState, renormalize, stepMoveSM, type MoveSM, type V3 } from "./move.ts";
import type {
  CollisionParam, DamageParam, MoveParam, ShooterPaintParam, SplashPaintParam, SplashSpawnParam, TailLengthParam,
  WallDropCollisionPaintParam,
} from "./params.ts";

export type BulletKind = "Shooter" | "Splash";

const K06 = f32(0.6);
const K088 = f32(0.88);

/** 생성 정보(탄 +0x108 이 가리키는 객체). */
export interface SpawnInfo {
  kind: BulletKind;
  owner: number;
  team: Team;
  weapon: string;
  /** +0x30 발사 위치 */
  pos: V3;
  /** +0x3c 발사 방향(단위) */
  dir: V3;
  /** +0x48 발사 속력 */
  speed: number;
  /** +0x68 전달 속력(로컬 발사는 0) */
  extraSpeed: number;
  /** +0x64 발사 GameFrame (탄 난수 시드) */
  frame: number;
  /** +0x90 분할 인덱스(슈터) / 최근접 스플래시 여부(스플래시) */
  split: number;
  /** +0x98 흔들림 각(rad) */
  angle: number;
  /** +0x6d 로컬 발사(칠 요청 여부) */
  local: boolean;
  /** 스플래시 도색 방향 +0x94/+0x98 (스플래시만) */
  paintDir: [number, number];
}

/** 탄 종류별 파라미터 묶음 */
export interface BulletParams {
  move: MoveParam;
  col: CollisionParam;
  dmg: DamageParam | null;
  paint: ShooterPaintParam | null;
  splashPaint: SplashPaintParam | null;
  splashSpawn: SplashSpawnParam | null;
  tail: TailLengthParam | null;
  wallDropColPaint: WallDropCollisionPaintParam | null;
  /** 슬롯 92: 벽 접촉 정지 프레임(ShooterBase 4) */
  wallHoldFrames: number;
  /** 슬롯 98: 도색 지연(슈터 1.0 → 보관 후 다음 갱신, 스플래시 0 → 즉시) */
  paintDelay: number;
}

export interface Contact {
  /** 0..1 구간 비율 */
  f: number;
  point: V3;
  normal: V3;
  layer: number;
  material: number;
  actor: number;
  /** 지형(원본 레이어 3 Ground) 인지 */
  ground: boolean;
  paintable: boolean;
}

export interface PendingPaint {
  pos: V3;
  normal: V3;
  dir: V3;
  widthHalf: number;
  depthScale: number;
  /** 슬롯105 요청 번호(접촉 시점) */
  stamp: number;
}

export class Bullet {
  readonly id: number;
  readonly info: SpawnInfo;
  readonly params: BulletParams;
  /** +0x134 — 시작 처리(0x7101645590)가 −1 을 쓴다 */
  age = -1;
  sm: MoveSM;
  /** +0x1b0 정지 프레임, 시작 −1 */
  hold = -1;
  /** +0x12a 소멸 대기 카운터 */
  dieWait = 0;
  /** +0x12b 낙하 소멸 처리됨 */
  fellOut = false;
  /** +0x1118 게임 쪽 속도 사본 */
  vel: V3 = [0, 0, 0];
  /** +0x110 이전 위치 */
  prevPos: V3;
  body = new BulletBody();
  /** +0x1200 누적 이동 거리, +0x1204 상태 중 최고 높이 */
  traveled = 0;
  maxY = f32(-1000000);
  /** 스플래시 일정(슬롯15·56) */
  splash: SplashState = { acc: 0, f8: 0, left: 0, near: 0, isLast: false, forced: false };
  /** +0x120c (표시용 회전) */
  randAngle = 0;
  /** 꼬리: +0x11e0 속도, +0x11ec 시작, +0x1210 상태머신, A = +0x11c8 꼬리 점, B = +0x11d4 표시 꼬리 끝 */
  tailVel: V3;
  tailStarted = false;
  tailSM: MoveSM = { state: GO_STRAIGHT, frame: 0 };
  tailA: V3;
  tailB: V3;
  /** 슬롯84 보관 도색(+0x1150) */
  pending: PendingPaint | null = null;
  /** 충돌 반경(슬롯57) */
  rField = 0;
  rPlayer = 0;
  /** 이번 물리 스텝 접촉 */
  contact: Contact | null = null;
  /** 소멸 요청(컴포넌트 0x28) */
  dead = false;
  /** 표시 위치(벽 정지 시 접촉점) */
  showPos: V3;

  constructor(id: number, info: SpawnInfo, params: BulletParams, seedBase: number) {
    this.id = id;
    this.info = info;
    this.params = params;
    this.sm = { state: initialState(params.move), frame: 0 };
    this.prevPos = [info.pos[0], info.pos[1], info.pos[2]];
    this.body.pos = [info.pos[0], info.pos[1], info.pos[2]];
    this.showPos = [info.pos[0], info.pos[1], info.pos[2]];
    void seedBase;
    // 0x7101645590 끝: s = speed + extra, v = (dir.x·s, s·dir.y, s·dir.z) → setVelocity
    const s = f32(f32(info.speed) + f32(info.extraSpeed));
    this.setVelocity([f32(info.dir[0] * s), f32(s * info.dir[1]), f32(s * info.dir[2])]);
    const sp = f32(info.speed);
    this.tailVel = [f32(sp * info.dir[0]), f32(sp * info.dir[1]), f32(sp * info.dir[2])];
    this.tailA = [info.pos[0], info.pos[1], info.pos[2]];
    this.tailB = [info.pos[0], info.pos[1], info.pos[2]];
  }

  get kind(): BulletKind {
    return this.info.kind;
  }

  setVelocity(v: V3): void {
    this.vel[0] = v[0];
    this.vel[1] = v[1];
    this.vel[2] = v[2];
    this.body.setVelocity(v);
  }

  /** 슬롯18 0x71016460fc */
  pre(): boolean {
    if (this.age >= 0) {
      this.prevPos[0] = this.body.pos[0];
      this.prevPos[1] = this.body.pos[1];
      this.prevPos[2] = this.body.pos[2];
    }
    this.age++;
    const holdEnded = this.move();
    if (this.kind === "Shooter") this.tailMove();
    this.updateRadius();
    if (this.dieWait === 1) this.setVelocity([0, 0, 0]);
    return holdEnded;
  }

  /** 슬롯54 (BulletSimple 0x7101763a10). 정지 프레임이 0 이 되면 true(소멸 요청). */
  private move(): boolean {
    if (this.hold >= 1) {
      this.setVelocity([0, 0, 0]);
      this.hold -= 1;
      return this.hold === 0;
    }
    const v: V3 = [this.vel[0], this.vel[1], this.vel[2]];
    const out: V3 = [0, 0, 0];
    if (this.age === 1) {
      renormalize(v, this.info.speed);
      stepMoveSM(this.sm, this.params.move, v, out);
    } else {
      stepMoveSM(this.sm, this.params.move, v, out);
      if (this.age === 0) {
        out[0] = v[0];
        out[1] = v[1];
        out[2] = v[2];
      }
    }
    this.setVelocity(out);
    return false;
  }

  /** ShooterBase 슬롯54 뒷부분 0x7101750d6c: 정지 중 꼬리 수렴, DelayShotFrame 부터 꼬리 상태머신 */
  private tailMove(): void {
    if (this.hold >= 0) {
      const p = this.body.pos, d = this.body.pos;
      for (let i = 0; i < 3; i++) {
        this.tailA[i] = f32(p[i] + f32(f32(this.tailA[i] - p[i]) * K06));
        this.tailB[i] = f32(d[i] + f32(f32(this.tailB[i] - d[i]) * K06));
        this.tailVel[i] = 0;
      }
    }
    const tl = this.params.tail;
    if (!this.tailStarted && tl && this.age >= (tl.DelayShotFrame | 0)) {
      this.tailSM = { state: initialState(this.params.move), frame: 0 };
      this.tailStarted = true;
    }
    if (this.tailStarted) {
      const out: V3 = [0, 0, 0];
      stepMoveSM(this.tailSM, this.params.move, this.tailVel, out);
      this.tailVel = out;
    }
  }

  /** ShooterBase 슬롯55 0x71017510c0 앞부분: 꼬리 점 이동·보간 */
  tailPost(): void {
    if (this.tailStarted && this.hold < 0) {
      for (let i = 0; i < 3; i++) {
        const v = this.tailVel[i];
        this.tailA[i] = f32(this.tailA[i] + v);
        this.tailB[i] = f32(f32(f32(f32(v + this.tailB[i]) - this.tailA[i]) * K088) + this.tailA[i]);
      }
    } else if (this.hold >= 0) {
      for (let i = 0; i < 3; i++) this.tailB[i] = f32(this.tailA[i] + f32(f32(this.tailB[i] - this.tailA[i]) * K088));
    }
  }

  /** 슬롯57: ShooterBase 0x7101764ef8 은 Field·Player 반경, SplashShooter 0x71017ffb64 는 Field 만(Player 는 셰이프 그대로, 플레이어와 충돌 안 함 [데이터]). */
  updateRadius(): void {
    this.rField = fieldRadius(this.age, this.params.col);
    this.rPlayer = this.kind === "Shooter" ? playerRadius(this.age, this.params.col) : 0;
  }
}

export function wallDropRadiusInt(r: number): number {
  return Math.trunc(f32(f32(f32(r) / f32(0.05)) + f32(0.001))) | 0;
}
