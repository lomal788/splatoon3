// 담당: [physics] — 플레이어 몸체(PHY01~PHY04). 한 프레임 안 순서(원본 phive_controller.md §6.7):
//   슬롯18 메인 계산 끝 — PlayerCollision 형상 갱신 0x71024f5dd8(오징어 비율 t·하위 레이어) + 속도 전달 0x71024f4f7c
//   → Phive Entity 월드(단계0 그룹6) — 캐릭터 컨트롤러 0x7103a80560(GameOnGround/GameInAir … GameApplyVelocity)
//     → native 솔버(초기 → normal8/carry7 → finalize → pose, core/collision/solver.ts) → 결과 SplResultPlayer 0x7102c5a3c8
//   → 액터 단계1 write-back 0x71024d26f8(본체+0x10 = 몸체 원점 − r·up) → 슬롯19 0x71024f7410(PC 필드).
// 근거: docs/physics/character_controller.md §3~7, phive_controller.md §3·§5·§6.10.4~6.10.5, docs/impl/physics.md.
// 실제 메시의 native 접촉 생성(manifold·TOI)과 SplResultPlayer 의 두 번째 질의(pass 1)는 [미확정](PHY05) — 근사 지점마다 표시한다.
import { f32, type Vec3 } from "../fmath.ts";
import type { BodyContact, MeshCollisionWorld } from "../collision/index.ts";
import { heapSortMode3 } from "../collision/contacts.ts";
import { playerSubLayer } from "../collision/filter.ts";
import {
  CACHE_C0, CACHE_C8, contactBias, effectiveMass, makeSolverInfo, nativeSetLinear, PLAYER_INV_MASS, stepMotion,
  type MotionState, type SolverRow,
} from "../collision/solver.ts";
import type { TriFilter } from "../collision/mesh.ts";
import { GRAVITY } from "./consts.ts";
import { isNativeSquidState } from "./display.ts";
import { FootMonitors } from "./contact.ts";

// ---- PHY01 형상 (기준: PlayerCollision = 본체+0xa690, PC) ----------------------------------------

function fb(bits: number): number {
  const d = new DataView(new ArrayBuffer(4));
  d.setUint32(0, bits >>> 0, true);
  return d.getFloat32(0, true);
}

/** ColGround 요청 반경 0x71024b7b3c 일반 0.6f(0x3f19999a) [판독+데이터]. */
export const COLGROUND_RADIUS_REQ = fb(0x3f19999a);
/** world+0x21c 실행 중 값 0.01 (게임 모듈 0x710344af54 case 0xf 덮어쓰기 [실행]; 기본 설명자 0.05). */
export const WORLD_MIN_RADIUS = f32(0.01);
/** 캡슐 반경 setter 0x7103a6a878: r = min(max(요청, world+0x21c), 2000), NaN/무한이면 1 [판독]. */
export function capsuleRadius(req: number): number {
  if (!Number.isFinite(req)) return 1;
  return Math.min(Math.max(req, WORLD_MIN_RADIUS), 2000);
}
/** 최종 ColGround 반경 = max(0.6, 0.01) = 0.6 — write-back 의 r. */
export const CAPSULE_RADIUS = capsuleRadius(COLGROUND_RADIUS_REQ);
/** ShapeParam SplPlayer_cct ColGround A(0,0,0)–B(0,0.7,0) [데이터], PC+0x144 = 길이 0.7 [판독]. */
export const CAPSULE_A = 0;
export const CAPSULE_B = f32(0.699999988079071);
/** 게임 위치(발) ↔ 몸체 원점 오프셋: 리셋 0x71024f4440 = +r·up, write-back 0x71024d26f8 = −r·up [실행 1024/1024 ×2]. */
export const BODY_OFFSET_Y = CAPSULE_RADIUS;
/**
 * native 몸체 local COM (0, .34999996423721313, 0): r8 원본 native fixture(ColGround 사람 캡슐 단독)의 원본 생산값 [실행 관찰].
 * 실제 복합 형상(ColGround+ColOthers)의 질량 분포와 형상 변경 시 재계산 여부는 [미확정] — 생성 때 값으로 고정한다.
 */
export const LOCAL_COM: readonly number[] = [0, 0.34999996423721313, 0];
/** 캐릭터 특수 MotionProperties13 최대 선속도 20000 [실행: character_controller §4.2]. */
export const NATIVE_MAX_LINEAR = 20000;
/** native manifold 를 만들 접근 여유(유닛). 원본 collision tolerance·AABB 확장 값은 [미확정] — 웹 근사 매개변수. */
export const CONTACT_LOOKAHEAD = 0.05;
/** SplResultPlayer 등급 1 의 거리 한계 0.19999999 [판독]. 접촉 목록 근사 질의 거리. */
export const RESULT_REACH = f32(0.19999999);

/** 사람 ColGround·ColOthers, 오징어 비율 t 로 다시 만든 끝점 (§3.3). */
export interface PlayerShape {
  /** 본체+0x7a4 (10프레임 접근), 본체+0x7a8 (사람 쪽 지수 감쇠), PC+0x168 (0.2 히스테리시스) */
  f1: number;
  f2: number;
  t: number;
  /** ColGround B.y (A = 원점), 반경 */
  groundB: number;
  radius: number;
  /** ColOthers A.y/B.y, 반경 (지형과 충돌하지 않음 — 표시·진단용) */
  othersA: number;
  othersB: number;
  othersR: number;
  /** 플레이어 몸체 하위 레이어 (§3.6) */
  subLayer: number;
}

// ---- 결과 S (ctrl+0x20, SplResultPlayer 출력) ----------------------------------------------------

export interface SupportState {
  /** S+0x20 */
  supported: boolean;
  /** S+0x28 선택 후보 방향(접점 → 직전 몸체 원점) */
  normal: Float32Array;
  /** S+0x34 보정 법선(얼굴 법선, 0.65 미만이면 S+0x28) */
  face: Float32Array;
  /** S+0x40 지지 접점 */
  point: Float32Array;
  /** S+0x58 = 접촉 거리 − Result+0x1c */
  dist: number;
  tri: number;
  /** S+0xf5 / S+0xb4 / S+0xc0 측면 접촉 */
  wall: boolean;
  wallN: Float32Array;
  wallP: Float32Array;
  /** S+0xf4 공중 강제 */
  forceAir: boolean;
}

export interface ResultFlags {
  /** Result+0x1744 PlayerDead, +0x1745 Fence, +0x1746 Ice, +0x1747 KebaInk 바닥, +0x1748 KebaInk 벽, +0x1749 PlayerUnsafe, +0x174a Sponge */
  dead: boolean;
  fence: boolean;
  ice: boolean;
  keba: boolean;
  kebaWall: boolean;
  unsafe: boolean;
  sponge: boolean;
  /** Result+0x16c8/+0x16bc SquidGuard·Slide 지지 법선, +0x16c9 */
  guard: boolean;
  guardN: Float32Array;
  guard16c9: boolean;
}

/** Result 접촉 목록 항목(Phive 128B 접촉의 웹 대응). */
export interface Contact {
  tri: number;
  /** 접점(상대 = 지형 쪽) */
  px: number;
  py: number;
  pz: number;
  /** 법선(지형 → 몸) */
  nx: number;
  ny: number;
  nz: number;
  /** 얼굴 법선 0x7103c4988c(flag1) = 삼각형 (b−a)×(c−a) 정규화 */
  fx: number;
  fy: number;
  fz: number;
  /** +0x30 분리 거리, +0x60 비율 f, +0x64 종류 */
  d: number;
  f: number;
  type: number;
}

/** 슬롯19 0x71024f7410 이 PC 로 옮기는 값(§7) + Result 플래그. */
export interface BodyStepResult {
  /** PC+0xd0 = 이동 상태 OnGround && S+0x20 / PC+0xd1 직전 */
  onGround: boolean;
  prevOnGround: boolean;
  /** PC+0x109 = S+0x20, PC+0x108 = PC+0xd0 && S+0x38 ≥ 0.6414 */
  supported: boolean;
  flat: boolean;
  /** PC+0xac 지지 법선(S+0x34) / PC+0xa0 접점(S+0x40) — PC+0xd0 일 때 */
  gn: [number, number, number];
  gp: [number, number, number];
  /** 지지 삼각형(없으면 -1) */
  gtri: number;
  /** PC+0xec 측면 접촉 / PC+0xe0 법선 / PC+0xd4 접점 */
  wall: boolean;
  wallN: [number, number, number];
  wallP: [number, number, number];
  flags: ResultFlags;
  /** 이번 스텝 접촉 목록(지형 삼각형) */
  contacts: Contact[];
  /** PC+0xb8 = Result+0x13f8(지지 중 바닥 후보 얼굴 법선 y 최소, 없으면 0) */
  surfN: [number, number, number];
}

export interface BodyState {
  motion: MotionState;
  /** 접촉 cache(삼각형별 old/carry) — native manifold cache 의 웹 대응 */
  cache: Map<number, { old: number; carry: number }>;
  /** ctrl S+0x168 이동 방향, S+0x180 이동 속력 */
  moveDir: Float32Array;
  moveSpeed: number;
  /** 이동 상태 M+0x40: 0 OnGround, 1 InAir, 2 Free */
  moveState: number;
  shape: PlayerShape;
  S: SupportState;
  flags: ResultFlags;
  /** Result+0x1320 직전 몸체 원점, +0x132c 직전 지지 보정 법선, +0x1338 게임 속도(유닛/프레임) */
  r1320: Float32Array;
  r132c: Float32Array;
  r1338: Float32Array;
  /** Result+0x135c/+0x1360 이동 상태 유지 프레임 */
  r135c: number;
  r1360: number;
  /** Result+0x1344 입력 수평 방향(0x7102475a54, 본체+0xd30/+0xd3c) */
  r1344: Float32Array;
  /** 발밑·접촉 잉크 모니터(Result+0x1368, 4개) */
  monitors: FootMonitors;
  /** PC+0xd0 직전 값 */
  pcOnGround: boolean;
  /** 마지막 스텝의 native 위치용 실효 속도(진단) */
  comVel: Float32Array;
  /** SplAlongGnd 컴포넌트 +0x28 N(초기 up), +0x1308 strength(초기 0), +0x38 enable(초기 1) */
  alongN: Float32Array;
  alongStrength: number;
  /** 마지막 스텝 manifold 행 수(진단) */
  rows: number;
  /** 마지막 Result 접촉 목록 */
  contacts: Contact[];
  /** Result+0x13f8 바닥 후보 중 y 최소 얼굴 법선(없으면 0) → PC+0xb8 */
  r13f8: Float32Array;
}

const INFO = makeSolverInfo();
const ROW_MASS = effectiveMass([0, 0, 0], [0, 0, 0], PLAYER_INV_MASS);
const STATES = new WeakMap<object, BodyState>();

export function createBodyState(): BodyState {
  return {
    motion: { com: new Float64Array(3), vel: new Float32Array(3), origin: new Float32Array(3), residual: new Float32Array(3), center: Float32Array.from(LOCAL_COM) },
    cache: new Map(),
    moveDir: Float32Array.from([0, 0, 1]),
    moveSpeed: 0,
    moveState: 0,
    shape: { f1: 0, f2: 0, t: 0, groundB: CAPSULE_B, radius: CAPSULE_RADIUS, othersA: f32(-0.21), othersB: f32(0.51), othersR: f32(0.39), subLayer: 3 },
    S: {
      supported: false, normal: Float32Array.from([0, 1, 0]), face: Float32Array.from([0, 1, 0]), point: new Float32Array(3), dist: 0, tri: -1,
      wall: false, wallN: new Float32Array(3), wallP: new Float32Array(3), forceAir: false,
    },
    flags: { dead: false, fence: false, ice: false, keba: false, kebaWall: false, unsafe: false, sponge: false, guard: false, guardN: new Float32Array(3), guard16c9: false },
    r1320: new Float32Array(3),
    r132c: new Float32Array(3),
    r1338: new Float32Array(3),
    r135c: 0,
    r1360: 0,
    r1344: new Float32Array(3),
    monitors: new FootMonitors(),
    pcOnGround: false,
    comVel: new Float32Array(3),
    contacts: [],
    r13f8: new Float32Array(3),
    alongN: Float32Array.from([0, 1, 0]),
    alongStrength: 0,
    rows: 0,
  };
}

/** 플레이어 객체별 몸체 상태(shared player 계약을 늘리지 않기 위해 WeakMap 으로 둔다). */
export function bodyOf(p: object): BodyState {
  let s = STATES.get(p);
  if (!s) {
    s = createBodyState();
    STATES.set(p, s);
  }
  return s;
}

/** write-back 0x71024d26f8: 본체+0x10 = 몸체 원점 − r·up (fmul 뒤 fsub), 본체+0xfa0 이면 빼지 않음 [실행 1024/1024]. */
export function writeBackPosition(out: Float32Array | number[], origin: ArrayLike<number>, r: number, up: ArrayLike<number>, skip: boolean): void {
  for (let j = 0; j < 3; j++) out[j] = skip ? origin[j] : f32(origin[j] - f32(r * up[j]));
}

/**
 * 리셋 0x71024f4440 → ctrl vt+0xb8 → 강체 transform setter: 몸체 원점 = (x+0, y+r, z+0) [실행 1024/1024].
 * native COM 은 원점 + local COM(double) 로 다시 잡는다(회전 identity) [추정: transform setter 의 COM 재계산 산술].
 */
export function resetBody(s: BodyState, pos: ArrayLike<number>): void {
  const m = s.motion;
  m.origin[0] = f32(pos[0] + 0); m.origin[1] = f32(pos[1] + CAPSULE_RADIUS); m.origin[2] = f32(pos[2] + 0);
  for (let j = 0; j < 3; j++) {
    m.com[j] = m.origin[j] + m.center[j];
    m.residual[j] = 0;
    m.vel[j] = 0;
  }
  s.cache.clear();
  s.alongN.set([0, 1, 0]);
  s.alongStrength = 0;
  s.moveSpeed = 0;
  s.moveState = 0;
  s.S.supported = false;
  s.S.forceAir = false;
  s.r1320.set(m.origin);
  s.r132c.fill(0);
  s.pcOnGround = false;
}

// ---- 형상 갱신 0x71024f5dd8 (메인 계산 0x7102475a54 안) ---------------------------------------------

const EPS23 = 2 ** -23;

/**
 * 오징어 비율 [판독: move_full_main.c 7085~7164]: target = 상태 ∈ 오징어 집합 ? 1 : 0, 본체+0x7a4 는 프레임당 최대 0.1 접근,
 * 본체+0x7a8 은 사람 쪽으로 ×0.1 지수 감쇠(|차| < 0.001 이면 대입), 오징어 쪽은 즉시. PC+0x168 은 0.2 히스테리시스
 * (끝점 ±2^-23 이면 다를 때, 중간값이면 |old − t| > 0.2 일 때 — ColBullet 원본 실행과 같은 꼴 [실행: §3.3.1], ColGround 적용은 [판독]).
 */
export function updateShape(sh: PlayerShape, state: number): boolean {
  const target = isNativeSquidState(state) ? 1 : 0;
  const d = f32(target - sh.f1);
  sh.f1 = Math.abs(d) <= 0.1 ? target : f32(sh.f1 + (d > 0 ? f32(0.1) : f32(-0.1)));
  if (sh.f1 <= sh.f2) {
    sh.f2 = f32(sh.f2 + f32(f32(sh.f1 - sh.f2) * f32(0.1)));
    if (Math.abs(f32(sh.f1 - sh.f2)) < f32(0.001)) sh.f2 = sh.f1;
  } else sh.f2 = sh.f1;
  const t = sh.f2;
  const edge = Math.abs(t) <= EPS23 || Math.abs(t - 1) <= EPS23;
  let rebuild = false;
  if (edge ? t !== sh.t : Math.abs(f32(sh.t - t)) > f32(0.2)) {
    sh.t = t;
    rebuild = true;
    // ColGround: B = A + len·axis·(1 − t), r = 0.6 (특수 0x12/0x1a/0xf·SuperLanding 분기 없음)
    sh.groundB = f32(CAPSULE_B * f32(1 - t));
    sh.radius = capsuleRadius(COLGROUND_RADIUS_REQ);
    // ColOthers: len1 = 0.72 − 0.72t, r1 = 0.39 + 0.01t, A = A0 + axis·(−t·r1)
    const r1 = f32(f32(0.39) + f32(f32(0.01) * t));
    const len1 = f32(f32(0.72) - f32(f32(0.72) * t));
    sh.othersR = r1;
    sh.othersA = f32(f32(-0.21) + f32(-t * r1));
    sh.othersB = f32(sh.othersA + len1);
  }
  // 하위 레이어 0x71024f5fc4: 특수 0·액터+0x7b9 0·코옵좀비 0·토관 0, flag(본체+0x7a0 등) [미확정] → false
  sh.subLayer = playerSubLayer({ special: 0, actor7b9: false, t: sh.f1, zombie: false, dokan: 0, flag: false });
  return rebuild;
}

// ---- 컨트롤러 (게임 → Phive 속도, 컴포넌트) --------------------------------------------------------

const TINY2 = f32(1.4210855e-14);
const DT = INFO.dt;
/** Phive 중력 = 월드 (0,−9.8,0) × GravityScale(g·60·60/9.8) — 게임이 매 프레임 설정 [판독]. 곱셈 순서 [추정]. */
const PHIVE_G = f32(f32(-9.8) * f32(f32(f32(GRAVITY * 60) * 60) / f32(9.8)));
/** MoveStateUpdate 최대 낙하 속력 S+0x204 생성자 200 [판독]. */
const MAX_FALL = 200;

function len3(x: number, y: number, z: number): number {
  return f32(Math.sqrt(f32(f32(f32(x * x) + f32(y * y)) + f32(z * z))));
}

/** setMoveVelocity ctrl vt 0x68 0x7103a87be8: 정규화해 방향·속력으로 나눠 저장 [판독, 산술 순서 추정]. */
export function setMoveVelocity(dir: Float32Array, m: ArrayLike<number>): number {
  const l = len3(m[0], m[1], m[2]);
  if (l > 0) {
    const i = f32(1 / l);
    dir[0] = f32(m[0] * i); dir[1] = f32(m[1] * i); dir[2] = f32(m[2] * i);
  }
  return l;
}

/**
 * GameOnGround slot4 0x7103a85410 [판독: decomp/physics/phive_batch1.c]: 위쪽 u·이동 방향 d·지지 법선 N 으로
 * t = normalize((u × d) × N), vel += t·(이동 계수(1)·속력). 이어 지지 법선 y(S+0x38) > 1e-5 이면 중력의 법선 성분
 * vel += N·(N·g)·min(|S+0x38/(N·g)|, dt). N 은 S+0x08/S+0x14 중 위쪽에 가까운 것인데 그 두 필드의 writer 가 [미확정]이라
 * 직전 지지 보정 법선(S+0x34)으로 둔다. S+0xd0 bit4 벽 평면 제한·발판(ctrl+0x30) 분기는 생략 [미확정].
 */
function controllerOnGround(s: BodyState, vel: number[]): void {
  const N = s.S.supported ? s.S.face : UPV;
  const d = s.moveDir, u = UPV;
  let sx = f32(f32(d[2] * u[1]) - f32(d[1] * u[2]));
  let sy = f32(f32(d[0] * u[2]) - f32(d[2] * u[0]));
  let sz = f32(f32(d[1] * u[0]) - f32(d[0] * u[1]));
  let tx = d[0], ty = d[1], tz = d[2];
  const sl = len3(sx, sy, sz);
  if (sl > 0) { const i = f32(1 / sl); sx = f32(sx * i); sy = f32(sy * i); sz = f32(sz * i); }
  if (sl >= 1.1920929e-7) {
    let ax = f32(f32(N[2] * sy) - f32(N[1] * sz));
    let ay = f32(f32(N[0] * sz) - f32(N[2] * sx));
    let az = f32(f32(N[1] * sx) - f32(N[0] * sy));
    const al = len3(ax, ay, az);
    if (al > 0) { const i = f32(1 / al); ax = f32(ax * i); ay = f32(ay * i); az = f32(az * i); }
    if (al >= 1.1920929e-7) { tx = ax; ty = ay; tz = az; }
  }
  const k = f32(f32(1 * 1) * s.moveSpeed);
  vel[0] = f32(vel[0] + f32(tx * k));
  vel[1] = f32(f32(ty * k) + vel[1]);
  vel[2] = f32(f32(tz * k) + vel[2]);
  const ny = N[1];
  if (ny > 1e-5) {
    const gn = f32(N[1] * PHIVE_G);
    if (Math.abs(gn) > 1.1920929e-7) {
      const q = Math.abs(f32(ny / gn));
      const time = q <= DT ? q : DT;
      vel[0] = f32(vel[0] + f32(f32(N[0] * gn) * time));
      vel[1] = f32(f32(f32(N[1] * gn) * time) + vel[1]);
      vel[2] = f32(f32(f32(N[2] * gn) * time) + vel[2]);
    }
  }
}

const UPV = Float32Array.from([0, 1, 0]);
/** [0x71058f0cb8] 0.64144969 (정적 초기화 0x7102c5f730 에뮬 [실행]) */
const ALONG_NY = fb(0x3f24360c);
/** SplAlongGnd 내부 질의 형상 반경 max(world+0x21c, 0.1) [판독] */
const ALONG_QUERY_R = Math.max(WORLD_MIN_RADIUS, f32(0.1));
const AG_SR = { t: 0, nx: 0, ny: 0, nz: 0, px: 0, py: 0, pz: 0, tri: -1 };

/**
 * SplAlongGnd 0x7102c5fdf0 [판독+실행(합성 질의) 1,250건: movement_physics.md §6.6.1].
 * InAir: v −= (1/dt)·N·0.05·strength·min(1, 1−N.y), N → up 0.15, strength ×0.5.
 * OnGround(S+0x20 == 1): strength = 1, N 을 S+0x34 쪽으로 (S+0x38 < 0.6414 ? 0.5 : 0.15) 추종, 예측 위치 Ppred = P + dt·v 에서
 * −N 방향 L = |V|·dt + r − 0.1 질의, 적중점 H 로 Δ = H − Ppred, k = max(|Δ| − r + 0.1, 0), 접촉 법선과 N 사이 < π/4 이면 v += Δ·k/dt.
 * 질의는 반경 0.1 구 쓸어 넘기기로 근사(원본 0x7103a5f36c 질의 형식·필터 [미확정]), 접촉 컬렉션의 "가장 낮은 반대면 접점" 법선은
 * 단일 적중 법선으로 대신한다. SplJump+0x59 [미확정] → 거짓.
 */
function splAlongGnd(col: MeshCollisionWorld, s: BodyState, vel: number[], filter: TriFilter): void {
  const N = s.alongN;
  if (s.moveState === 1) {
    const inv = f32(1 / DT), st = s.alongStrength;
    let z = f32(1 - N[1]);
    if (z > 1) z = 1;
    vel[0] = f32(vel[0] - f32(f32(f32(f32(inv * N[0]) * f32(0.05)) * st) * z));
    vel[1] = f32(vel[1] - f32(f32(f32(f32(inv * N[1]) * f32(0.05)) * st) * z));
    vel[2] = f32(vel[2] - f32(f32(f32(f32(inv * N[2]) * f32(0.05)) * st) * z));
    N[0] = f32(N[0] + f32(f32(0 - N[0]) * f32(0.15)));
    N[1] = f32(N[1] + f32(f32(1 - N[1]) * f32(0.15)));
    N[2] = f32(N[2] + f32(f32(0 - N[2]) * f32(0.15)));
    s.alongStrength = f32(st * 0.5);
    return;
  }
  if (s.moveState !== 0 || !s.S.supported) return;
  s.alongStrength = 1;
  const T = s.S.face;
  const t = T[1] < ALONG_NY ? f32(0.5) : f32(0.15);
  for (let j = 0; j < 3; j++) N[j] = f32(N[j] + f32(t * f32(T[j] - N[j])));
  const P = s.motion.origin;
  const px = f32(f32(DT * vel[0]) + P[0]), py = f32(f32(DT * vel[1]) + P[1]), pz = f32(f32(DT * vel[2]) + P[2]);
  const V = s.motion.vel;
  const L = f32(f32(f32(len3(V[0], V[1], V[2]) * DT) + s.shape.radius) + f32(-0.1));
  const ex = f32(px - f32(N[0] * L)), ey = f32(py - f32(N[1] * L)), ez = f32(pz - f32(N[2] * L));
  const h = col.mesh.sweepSegment(px, py, pz, px, py, pz, ALONG_QUERY_R, ex - px, ey - py, ez - pz, filter, AG_SR);
  if (!h) return;
  const dx = f32(f32(px + f32(f32(ex - px) * h.t)) - px), dy = f32(f32(py + f32(f32(ey - py) * h.t)) - py), dz = f32(f32(pz + f32(f32(ez - pz) * h.t)) - pz);
  let k = f32(f32(len3(dx, dy, dz) - s.shape.radius) + f32(0.1));
  if (k <= 0) k = 0;
  const sn = [h.nx, h.ny, h.nz];
  const cx = f32(f32(sn[0] * N[2]) - f32(N[0] * sn[2])), cy = f32(f32(sn[2] * N[1]) - f32(sn[1] * N[2])), cz = f32(f32(N[0] * sn[1]) - f32(sn[0] * N[1]));
  const ang = f32(Math.atan2(f32(Math.sqrt(f32(f32(f32(cz * cz) + f32(cy * cy)) + f32(cx * cx)))), f32(f32(f32(N[0] * sn[0]) + f32(N[1] * sn[1])) + f32(N[2] * sn[2]))));
  if (ang < f32(0.7853982)) {
    const inv = f32(1 / DT);
    vel[0] = f32(vel[0] + f32(f32(dx * k) * inv));
    vel[1] = f32(f32(f32(dy * k) * inv) + vel[1]);
    vel[2] = f32(f32(f32(dz * k) * inv) + vel[2]);
  }
}

// ---- 한 물리 스텝 --------------------------------------------------------------------------------

export interface BodyStepInput {
  /** 본체+0xe4 최종 속도 F (유닛/프레임) */
  final: ArrayLike<number>;
  /** 본체+0x73c 수직 속도 */
  vy: number;
  /** 메인 계산이 이번 프레임 공중을 강제(수직 속도 > 0.001)했는지 */
  forceAir: boolean;
  /** SM 상태 번호 */
  state: number;
  /** 본체+0xd30 이동 방향, +0xd3c 입력 크기 (Result+0x1344) */
  inputDir: ArrayLike<number>;
  inputMag: number;
  /** 팀(Result+0x3c), 발밑 임계(Result+0x16cc = StepPaint+0x44, +0x16d0 = +0x5c) */
  team: number;
  ownThr: number;
  enemyThr: number;
  /** 접촉점 잉크 모니터 카운트 공급자(없으면 잉크 판정 거짓) */
  inkCounts: ((pos: ArrayLike<number>, n: ArrayLike<number>) => [number, number, number, number]) | null;
  /** 재질 → UserShapeTag 이름·칠 가능 */
  materialOf: (tri: number) => { tags: readonly string[]; paintable: boolean } | undefined;
}

const SEG_A = [0, 0, 0], SEG_B = [0, 0, 0];
/** 이번 스텝 native manifold 를 만든 삼각형(근사) — Result 접촉 목록의 후보 */
const MANIFOLD = new Set<number>();
const BC: BodyContact[] = [];
const VEL = [0, 0, 0];

function capsuleSeg(o: ArrayLike<number>, sh: PlayerShape): void {
  SEG_A[0] = o[0]; SEG_A[1] = o[1] + CAPSULE_A; SEG_A[2] = o[2];
  SEG_B[0] = o[0]; SEG_B[1] = o[1] + sh.groundB; SEG_B[2] = o[2];
}

/**
 * 한 프레임 몸체 처리. 반환값은 슬롯19 가 읽는 PC 필드. 게임 위치는 out 으로 write-back 한다.
 * filter = COL02 플레이어↔지형 삼각형 필터(collision/world.ts playerTerrainFilter, 하위 레이어별).
 */
export function stepBody(col: MeshCollisionWorld, s: BodyState, pos: Vec3, inp: BodyStepInput, filterFor: (sub: number) => TriFilter): BodyStepResult {
  const sh = s.shape;
  // --- 슬롯18 끝: 형상·하위 레이어 0x71024f5dd8 ---
  updateShape(sh, inp.state);
  const filter = filterFor(sh.subLayer);
  // --- 0x71024f4f7c 게임 → Phive 속도 ---
  // 메인 계산 4938~4957: 수직 속도 > 0.001 이면 InAir 강제(퇴장 → M+0x40 = 1)
  if (inp.forceAir && s.moveState !== 1) s.moveState = 1;
  const v = inp.final;
  const v2 = f32(f32(f32(v[0] * v[0]) + f32(v[1] * v[1])) + f32(v[2] * v[2]));
  if (v2 >= TINY2) {
    const vj = s.moveState === 0 || (s.moveState !== 1 && s.moveState !== 2) ? inp.vy : 0;
    const m = [f32(v[0] * 60), f32(f32(v[1] - vj) * 60), f32(v[2] * 60)];
    const m2 = f32(f32(f32(m[0] * m[0]) + f32(m[1] * m[1])) + f32(m[2] * m[2]));
    if (m2 >= TINY2) s.moveSpeed = setMoveVelocity(s.moveDir, m);
    else s.moveSpeed = 0;
  } else s.moveSpeed = 0;
  // Result+0x1338 = v + ImpactAndReject/3600(0) + 본체+0x4bc(0) [판독]
  s.r1338[0] = v[0]; s.r1338[1] = v[1]; s.r1338[2] = v[2];
  // Result+0x1344 = normalize(본체+0xd30.x, 0, .z) (본체+0xd3c > 0), 아니면 0 [판독: move_full_main.c 6714~6739]
  if (inp.inputMag > 0) {
    const l = f32(Math.sqrt(f32(f32(f32(inp.inputDir[0] * inp.inputDir[0]) + 0) + f32(inp.inputDir[2] * inp.inputDir[2]))));
    if (l > 0) { const i = f32(1 / l); s.r1344[0] = f32(inp.inputDir[0] * i); s.r1344[1] = f32(i * 0); s.r1344[2] = f32(inp.inputDir[2] * i); }
    else { s.r1344[0] = inp.inputDir[0]; s.r1344[1] = 0; s.r1344[2] = inp.inputDir[2]; }
  } else s.r1344.fill(0);

  // --- 캐릭터 컨트롤러 0x7103a80560 ---
  VEL[0] = 0; VEL[1] = 0; VEL[2] = 0;
  if (s.moveState === 1) {
    // GameInAir slot4 0x71012aa138, +0x1c = 1 (플레이어 초기화 0x71024f4270): vel = 이동속력 × 이동방향 [판독]
    VEL[0] = f32(s.moveSpeed * s.moveDir[0]); VEL[1] = f32(s.moveSpeed * s.moveDir[1]); VEL[2] = f32(s.moveSpeed * s.moveDir[2]);
  } else if (s.moveState === 0) controllerOnGround(s, VEL);
  // SplAlongGnd slot8 0x7102c5fdf0 (프리셋 순서상 GameFollowSurface 뒤)
  splAlongGnd(col, s, VEL, filter);
  // MoveStateUpdate: Free 가 아니면 중력 방향 성분 ≤ S+0x204 (200)
  if (s.moveState !== 2 && -VEL[1] > MAX_FALL) VEL[1] = -MAX_FALL;
  // AirDumping 계수 0, SplJump·CliffSlip 속도 불변, GameFollowSurface·ImpactAndReject 외부 입력 0
  // GameApplyVelocity → stage → native setter (2^-23 허용차, 상한 20000)
  nativeSetLinear(s.motion.vel, VEL, NATIVE_MAX_LINEAR);

  // --- native 접촉(근사) → 행 target 0x7100a15b70 ---
  const m = s.motion;
  capsuleSeg(m.origin, sh);
  const speed = len3(m.vel[0], m.vel[1], m.vel[2]);
  col.bodyContacts(SEG_A, SEG_B, sh.radius, f32(speed * DT) + CONTACT_LOOKAHEAD, filter, BC);
  const rows: SolverRow[] = [];
  const nextCache = new Map<number, { old: number; carry: number }>();
  for (const c of BC) {
    const n = Float32Array.from([c.nx, c.ny, c.nz]);
    const d = f32(c.d);
    const prev = s.cache.get(c.tri) ?? { old: 0, carry: 0 };
    // flag(nativeManifold+92) = 1: 원본 fixture 정적·kinematic 접촉에서 관찰된 값 [실행 관찰], producer [미확정] → 예측 항 미사용
    const b = contactBias(prev.old, prev.carry, d, 0, 1, 0, INFO.dt, CACHE_C0, CACHE_C8, INFO.gamma);
    nextCache.set(c.tri, { old: b.old, carry: b.carry });
    rows.push({ n, target: b.target, mass: ROW_MASS, lambda: 0 });
  }
  s.cache = nextCache;
  s.rows = rows.length;
  MANIFOLD.clear();
  for (const c of BC) MANIFOLD.add(c.tri);
  stepMotion(m, rows, INFO, NATIVE_MAX_LINEAR, PLAYER_INV_MASS, { comVel: s.comVel });

  // --- SplResultPlayer 슬롯7 0x7102c5a3c8 ---
  resultStep(col, s, inp, filter);

  // --- 액터 단계1 write-back → 슬롯19 본체+0x10 ---
  writeBackPosition(pos, m.origin, CAPSULE_RADIUS, UPV, false);

  // --- 슬롯19 0x71024f7410 ---
  const S = s.S;
  const prevOnGround = s.pcOnGround;
  const onGround = s.moveState === 0 && S.supported;
  s.pcOnGround = onGround;
  return {
    onGround,
    prevOnGround,
    supported: S.supported,
    flat: onGround && S.face[1] >= fb(0x3f24360c),
    gn: [S.face[0], S.face[1], S.face[2]],
    gp: [S.point[0], S.point[1], S.point[2]],
    gtri: S.supported ? S.tri : -1,
    wall: S.wall,
    wallN: [S.wallN[0], S.wallN[1], S.wallN[2]],
    wallP: [S.wallP[0], S.wallP[1], S.wallP[2]],
    flags: s.flags,
    contacts: s.contacts.slice(),
    surfN: [s.r13f8[0], s.r13f8[1], s.r13f8[2]],
  };
}

/** 충돌 세계가 없을 때(웹 전용): y = 0 평면 위 단순 이동. 원본 경로가 아니다. */
export function noCollisionStep(pos: Vec3, final: ArrayLike<number>): BodyStepResult {
  for (let i = 0; i < 3; i++) pos[i] = f32(pos[i] + final[i]);
  const g = pos[1] <= 0;
  if (pos[1] < 0) pos[1] = 0;
  return {
    onGround: g, prevOnGround: g, supported: g, flat: g, gn: [0, 1, 0], gp: [pos[0], 0, pos[2]], gtri: -1,
    wall: false, wallN: [0, 1, 0], wallP: [0, 0, 0], flags: createBodyState().flags, contacts: [], surfN: [0, 1, 0],
  };
}

// ---- SplResultPlayer 지지 판정 ---------------------------------------------------------------------

const FLOOR_NY = fb(0x3f24360c); // [0x71058f0b70] 0.64144969
const OVERHANG_NY = fb(0xbe83a6e8); // [0x71058f0b7c] −0.25713277
/** CharacterControllerParam MaxSlopeAngle 75° → S+0x190 = 1.3089969 rad [판독+데이터]. */
const MAX_SLOPE = f32(1.3089969);
/** [0x71058f0ba0] = 90° (정적 초기화 0x7102c59750 에뮬 [실행]) */
const VEL_DIR_COS = f32(Math.cos(f32(f32(90) * f32(0.017453292))));
/** [0x71058f0b9c] byte0 = 1 [실행] */
const STEP_LOW_CHECK = true;
const UP_DOT_SAME = f32(0.70710677);
/** Result+0x28 = 본체+0x744 && 본체+0x73c > 0.001 [판독]; 본체+0x744 writer [미확정] → 거짓. */
const R28 = false;

interface Candidate {
  px: number; py: number; pz: number;
  dx: number; dy: number; dz: number;
  f: number; d: number; w: number; grade: number; merged: boolean;
  fx: number; fy: number; fz: number;
  c: Contact;
}

function atan2Angle(ax: number, ay: number, az: number): number {
  // 0x7102c5dd20: atan2(|g × a|, −g·a), g = (0,−1,0) (ctrl vt 0x200 중력 방향), 원본 외적·내적 항 순서
  const gx = 0, gy = -1, gz = 0;
  const c17 = f32(f32(gz * ax) - f32(gx * az));
  const c20 = f32(f32(gy * az) - f32(gz * ay));
  const c15 = f32(f32(gx * ay) - f32(gy * ax));
  const l = f32(Math.sqrt(f32(f32(f32(c15 * c15) + f32(c20 * c20)) + f32(c17 * c17))));
  const d = f32(f32(f32(ay * -gy) - f32(gx * ax)) - f32(gz * az));
  return f32(Math.atan2(l, d));
}

/** 0x7101252998 계열 수평 각(표 기반 atan2 → [−π, π]) — host atan2 + f32 [근사: sead 표]. 절댓값. */
function horizAngle(dir: ArrayLike<number>, n: ArrayLike<number>): number {
  const y = f32(f32(dir[2] * n[0]) - f32(dir[0] * n[2]));
  const x = f32(f32(n[0] * dir[0]) + f32(dir[2] * n[2]));
  return Math.abs(f32(Math.atan2(y, x)));
}

interface ClassifyCtx {
  s: BodyState;
  inp: BodyStepInput;
  bodyPos: Float32Array;
  inkMemo: number;
  c: Contact;
  P: number[];
}

/** 접촉 잉크 판정 0x7102c5e6a8 [판독: analysis/decomp/phy_port/step_ray.c] — 접촉별 1회 계산. */
function inkCheck(cx: ClassifyCtx): boolean {
  if (cx.inkMemo >= 0) return cx.inkMemo === 1;
  cx.inkMemo = 0;
  const s = cx.s, inp = cx.inp;
  const r39 = squidResult(s, inp.state);
  if (!r39 || inp.team === 3 || inp.team === -1) return false;
  const mat = inp.materialOf(cx.c.tri);
  if (!mat?.paintable) return false; // 0x71012ed800 [추정: 칠 가능 대상 검사]
  // Result+0x26 = 1 [추정] → 모니터 질의 0x7102c71a00 (같은 모니터 배열; 질의 식 미판독 → 0x7102c71650 배치 규칙으로 근사)
  const face = [cx.c.fx, cx.c.fy, cx.c.fz];
  const q = s.monitors.query(cx.c.tri, cx.P, face, inp.inkCounts);
  if (!s.shape || !(s.shape.f2 >= 0.5)) return false; // Result+0x38 == 0 → 거짓
  if (!q || !(q.w > 0)) return false;
  const total = q.c[3];
  let k = f32(total / 15);
  if (k > 1) k = 1;
  let r0 = 0, r1 = 0, r2 = 0;
  if (total !== 0) { r1 = f32(q.c[1] / total); r0 = f32(q.c[0] / total); r2 = f32(q.c[2] / total); }
  const team = inp.team;
  const t0 = f32(f32(k * r0) + 0);
  let own = team === 0 ? t0 : 0, enemy = team === 0 ? 0 : t0;
  if (team === 1) own = f32(f32(k * r1) + own); else enemy = f32(f32(k * r1) + enemy);
  if (team === 2) own = f32(f32(k * r2) + own); else enemy = f32(f32(k * r2) + enemy);
  const a = f32(own - inp.ownThr);
  if (a > 0 && f32(enemy - inp.enemyThr) <= a) cx.inkMemo = 1;
  return cx.inkMemo === 1;
}

/** Result+0x39 = (본체+0x7a8 ≥ 0.5 && 나이스볼 없음) || 상태 ∈ 오징어 집합 [판독: 0x71024f5dd8 6xx행]. */
function squidResult(s: BodyState, state: number): boolean {
  return s.shape.f2 >= 0.5 || isNativeSquidState(state);
}

/** 접촉 분류 0x7102c5dd20 (pass 0): 0 버림 / 1 바닥 / 2 벽 [판독: decomp/phys4/p4_resultplayer.c]. */
function classify(cx: ClassifyCtx, dir: number[], face: number[]): number {
  const s = cx.s, R = s.shape.radius, P = cx.P;
  const FLOOR = 1, WALL = 2;
  let ca = f32(f32(R + f32(-0.2)) / R);
  ca = ca < -1 ? f32(Math.PI) : ca > 1 ? 0 : f32(Math.acos(ca));
  const rx = f32(P[0] - cx.bodyPos[0]), ry = f32(P[1] - cx.bodyPos[1]), rz = f32(P[2] - cx.bodyPos[2]);
  if (0 < f32(f32(f32(rx * face[0]) + f32(ry * face[1])) + f32(rz * face[2]))) return 0;
  const state = s.moveState;
  const v = s.r1338;
  const dotPrev = f32(f32(f32(face[0] * s.r132c[0]) + f32(face[1] * s.r132c[1])) + f32(face[2] * s.r132c[2]));
  let velCheck = true;
  if (state !== 0 || UP_DOT_SAME <= dotPrev) {
    if (state !== 1) velCheck = false;
    else if (FLOOR_NY <= face[1]) {
      if (0.001 < f32(f32(f32(face[0] * v[0]) + f32(face[1] * v[1])) + f32(face[2] * v[2]))) return 0;
      velCheck = false;
    }
  }
  if (velCheck) {
    const vl = len3(v[0], v[1], v[2]);
    let hx = v[0], hy = v[1], hz = v[2];
    if (vl > 0) { const i = f32(1 / vl); hx = f32(hx * i); hy = f32(hy * i); hz = f32(hz * i); }
    if (0.001 < f32(f32(f32(v[0] * face[0]) + f32(v[1] * face[1])) + f32(v[2] * face[2])) &&
      VEL_DIR_COS < f32(f32(f32(hx * face[0]) + f32(hy * face[1])) + f32(hz * face[2]))) return 0;
  }
  const theta = atan2Angle(face[0], face[1], face[2]);
  const horiz = horizAngle(dir, face);
  if (MAX_SLOPE <= theta && !(horiz <= 0.87266463)) return 0;
  if (1.8308504 <= theta) {
    const theta2 = atan2Angle(dir[0], dir[1], dir[2]);
    if (R28) return theta2 < 2.6179938 ? 0 : WALL;
    if (theta2 < 2.2671826) return cx.inp.materialOf(cx.c.tri)?.tags.includes("SquidGuard") ? WALL : 0;
    return WALL;
  }
  // param_8 = 아래 (−0, −1, −0): −rel·down = rel.y
  if (face[1] < FLOOR_NY && f32(R * f32(-0.6414497)) < ry) {
    const l = len3(rx, ry, rz);
    let nx = -rx, ny = -ry, nz = -rz;
    if (l > 0) { const i = f32(1 / l); nx = f32(i * nx); ny = f32(i * ny); nz = f32(i * nz); }
    if (f32(f32(f32(nx * face[0]) + f32(ny * face[1])) + f32(nz * face[2])) < f32(Math.cos(ca)) && !inkCheck(cx)) return WALL;
  }
  if (theta < MAX_SLOPE) {
    const theta3 = atan2Angle(dir[0], dir[1], dir[2]);
    return MAX_SLOPE <= theta3 ? 0 : FLOOR;
  }
  if (STEP_LOW_CHECK && ry <= f32(0.2 - R)) {
    const ok = inkCheck(cx);
    if (ok && -0.656059 < -1) return FLOOR;
    if (face[1] < FLOOR_NY) return 0;
    const l = len3(rx, ry, rz);
    let nx = -rx, ny = -ry, nz = -rz;
    if (l > 0) { const i = f32(1 / l); nx = f32(i * nx); ny = f32(i * ny); nz = f32(i * nz); }
    if (f32(f32(f32(nx * face[0]) + f32(ny * face[1])) + f32(nz * face[2])) < f32(Math.cos(ca))) return 0;
    return FLOOR;
  }
  if (!inkCheck(cx)) return WALL;
  if (state === 0 && s.r132c[1] < FLOOR_NY) return horiz <= 0.6981317 ? FLOOR : WALL;
  if (0.5235988 < horiz) return WALL;
  if (dir[1] < face[1] && dir[1] < OVERHANG_NY) return WALL;
  let hx = face[0], hz = face[2], hy = 0;
  const hl = f32(Math.sqrt(f32(f32(f32(hx * hx) + 0) + f32(hz * hz))));
  if (hl > 0) { const i = f32(1 / hl); hx = f32(hx * i); hy = f32(i * 0); hz = f32(hz * i); }
  const r1344 = s.r1344;
  const r27 = false; // Result+0x27 (본체 쪽 바이트, 출처 [미확정])
  if (!r27 && r1344[0] === 0 && r1344[1] === 0 && r1344[2] === 0) {
    if (face[1] < 0.087155804) return WALL;
  } else if (state === 0 && face[1] < FLOOR_NY && -0.50000006 < f32(f32(f32(hx * r1344[0]) + f32(hy * r1344[1])) + f32(hz * r1344[2]))) return WALL;
  return FLOOR;
}

const TAG_BITS: Record<string, number> = {
  PhiveUnridable: 3, SquidGuard: 19, Slide: 20, PlayerDead: 21, PlayerUnsafe: 22, Fence: 25, Ice: 26, KebaInk: 30, Sponge: 31,
};
function hasTag(tags: readonly string[] | undefined, name: string): boolean {
  return !!tags && tags.includes(name) && TAG_BITS[name] !== undefined;
}

/**
 * SplResultPlayer 슬롯7 0x7102c5a3c8 pass 0 [판독-부분: decomp/phys4/p4_world_ctrl.c 1348~3854]. 접촉 목록은 근사(PHY05):
 * 스텝 뒤 몸 캡슐과 삼각형별 최근접 접촉(d ≤ 0.2), f = 0, 종류 2. 두 번째 질의(pass 1, Result+0x39 조건)·움직이는 상대 취소·
 * Result+0x1418 의 본체+0x184 < 0.6414 접점 보정은 생략 [미확정].
 */
function resultStep(col: MeshCollisionWorld, s: BodyState, inp: BodyStepInput, filter: TriFilter): void {
  const S = s.S, F = s.flags, m = s.motion;
  // 시작: 이동 상태 유지 프레임
  if (s.r135c === s.moveState) s.r1360 = Math.min(s.r1360, 0x270d) + 1;
  else { s.r1360 = 0; s.r135c = s.moveState; }
  // Result+0x132c = S+0x20 == 1 ? S+0x34 : DAT_7104a981f4 (0,0,0) [판독+데이터]
  if (S.supported) s.r132c.set(S.face); else s.r132c.fill(0);
  s.monitors.weightUpdate(DT);
  F.guard = false; F.guard16c9 = false; F.dead = false; F.fence = false; F.ice = false; F.keba = false; F.kebaWall = false; F.unsafe = false; F.sponge = false;
  // S 초기화(1567~1598)
  S.supported = false; S.normal.set([0, 1, 0]); S.face.set([0, 1, 0]); S.point.fill(0); S.dist = 0; S.tri = -1;
  S.wall = false; S.wallN.set([0, 1, 0]); S.wallP.fill(0);
  // S+0xf4 = Result+0x1358(본체+0x73c) > 0 || SplJump 쿨다운 > 0 (0) || SuperLanding 3 (없음) || 본체+0x746 ([미확정] → 거짓)
  S.forceAir = inp.vy > 0;
  // 접촉 목록 근사(PHY05): 이번 스텝 manifold 삼각형(시작 자세 + 접근 여유) ∪ 끝 자세 분리 < 0.02 인 삼각형, 거리는 끝 자세 값.
  // 원본 몸체 접촉 컬렉션(+0x188)의 생산(manifold 이벤트·TOI 처리기·종류/비율)은 [미확정] — 종류 2·f 0 으로 둔다.
  capsuleSeg(m.origin, s.shape);
  col.bodyContacts(SEG_A, SEG_B, s.shape.radius, RESULT_REACH, filter, BC);
  let list: Contact[] = BC.filter((c) => c.d < 0.02 || MANIFOLD.has(c.tri)).map((c) => ({ tri: c.tri, px: c.px, py: c.py, pz: c.pz, nx: c.nx, ny: c.ny, nz: c.nz, fx: c.fx, fy: c.fy, fz: c.fz, d: f32(c.d), f: 0, type: 2 }));
  // 접촉 정리 0x7103a6144c 모드 3 (키 f, 불안정 힙 정렬). 캐릭터 목록의 실제 모드는 [미확정] — 지시에 따라 모드 3.
  list = heapSortMode3(list, (c) => c.f);
  s.contacts = list;
  const bodyPos = m.origin;
  // 벽 누적
  let wn = 0, wpx = 0, wpy = 0, wpz = 0, wfx = 0, wfy = 0, wfz = 0, w0x = 0, w0y = 0, w0z = 0;
  const cands: Candidate[] = [];
  let r13f8: number[] | null = null;
  for (const c of list) {
    const tags = inp.materialOf(c.tri)?.tags;
    // 막는 접촉(+0x68 bit1)·상대 레이어 3(Ground): 필터 통과 지형 삼각형 = 막는 Ground 접촉
    let grade: number;
    if (c.d < 0.02 || 0 < c.f || c.type === 4) grade = 0;
    else if (c.d <= RESULT_REACH && c.type === 2) grade = 1;
    else if (c.type === 5) grade = 2;
    else continue;
    const P = [c.px, c.py, c.pz];
    const face = [c.fx, c.fy, c.fz];
    if (hasTag(tags, "PhiveUnridable") && atan2Angle(face[0], face[1], face[2]) < MAX_SLOPE) continue;
    if (hasTag(tags, "SquidGuard")) F.guard16c9 = true;
    let dx = f32(s.r1320[0] - P[0]), dy = f32(s.r1320[1] - P[1]), dz = f32(s.r1320[2] - P[2]);
    const dl = len3(dx, dy, dz);
    if (dl > 0) { const i = f32(1 / dl); dx = f32(i * dx); dy = f32(i * dy); dz = f32(i * dz); }
    const dir = [dx, dy, dz];
    const cx: ClassifyCtx = { s, inp, bodyPos, inkMemo: -1, c, P };
    const cls = classify(cx, dir, face);
    if (cls === 0) continue;
    if (cls === 2) {
      let ff = face;
      if (hasTag(tags, "SquidGuard") && dir[1] < OVERHANG_NY) ff = [-0, -1, -0];
      wpx = f32(wpx + P[0]); wpy = f32(wpy + P[1]); wpz = f32(wpz + P[2]);
      wfy = f32(wfy + ff[1]); wfx = f32(wfx + ff[0]); wfz = f32(wfz + ff[2]);
      if (wn === 0) { w0x = ff[0]; w0y = ff[1]; w0z = ff[2]; }
      wn++;
      if (hasTag(tags, "KebaInk")) F.kebaWall = true;
      continue;
    }
    // 바닥 후보
    const fp = c.f < 1e-5 && !(c.f <= 0) ? 1e-5 : c.f;
    const w0 = f32(0.1 - f32(f32(f32(-0 * dir[0]) + f32(-1 * dir[1])) + f32(-0 * dir[2])));
    let merged = false;
    for (const e of cands) {
      const ex = f32(e.px - P[0]), ey = f32(e.py - P[1]), ez = f32(e.pz - P[2]);
      if (!(len3(ex, ey, ez) < 0.05)) continue;
      if (!(0.99 < f32(f32(f32(e.dx * dir[0]) + f32(e.dy * dir[1])) + f32(e.dz * dir[2])))) continue;
      if (f32(f32(f32(e.fx * face[0]) + f32(e.fy * face[1])) + f32(e.fz * face[2])) <= 0.99) e.merged = true;
      if (e.f < fp || (fp <= e.f && c.d < e.d)) {
        e.px = P[0]; e.py = P[1]; e.pz = P[2]; e.dx = dir[0]; e.dy = dir[1]; e.dz = dir[2];
        e.f = fp; e.d = c.d; e.w = Math.abs(w0); e.grade = grade; e.c = c;
      }
      merged = true;
    }
    if (merged) continue;
    cands.push({ px: P[0], py: P[1], pz: P[2], dx: dir[0], dy: dir[1], dz: dir[2], f: fp, d: c.d, w: Math.abs(w0), grade, merged: false, fx: face[0], fy: face[1], fz: face[2], c });
    if (r13f8 === null || face[1] < r13f8[1]) r13f8 = face;
  }
  // 벽 정리(2280~2311)
  if (wn > 0) {
    let nx = wfx, ny = wfy, nz = wfz, px = wpx, py = wpy, pz = wpz;
    if (wn !== 1) {
      const l = len3(nz, ny, nx);
      if (l > 0) { const i = f32(1 / l); nx = f32(nx * i); ny = f32(ny * i); nz = f32(nz * i); }
      if (l <= 1.1920929e-7) { nx = w0x; ny = w0y; nz = w0z; }
      const inv = f32(1 / wn);
      px = f32(inv * px); py = f32(inv * py); pz = f32(inv * pz);
    }
    S.wallN[0] = nx; S.wallN[1] = ny; S.wallN[2] = nz;
    S.wallP[0] = px; S.wallP[1] = py; S.wallP[2] = pz;
    S.wall = true;
  }
  if (cands.length === 0) {
    if (S.wall) { S.normal.set(S.wallN); S.point.set(S.wallP); }
  } else {
    // 정렬: d×1000 오름차순(왕복 교환) → f 내림차순(안정), 첫 후보 선택(2324~2503)
    const sorted = cocktail(cocktail(cands, (a, b) => f32(a.d * 1000) - f32(b.d * 1000) > 0), (a, b) => b.f - a.f > 0);
    const best = sorted[0];
    // 움직이는 상대 취소(2571~2616): 정적 지형만 → 생략
    S.supported = true;
    S.normal[0] = best.dx; S.normal[1] = best.dy; S.normal[2] = best.dz;
    S.point[0] = best.px; S.point[1] = best.py; S.point[2] = best.pz;
    S.dist = best.d; // − Result+0x1c ([미확정] 0)
    S.tri = best.c.tri;
    S.face[0] = best.c.fx; S.face[1] = best.c.fy; S.face[2] = best.c.fz;
    if (f32(f32(f32(S.face[0] * best.dx) + f32(S.face[1] * best.dy)) + f32(S.face[2] * best.dz)) < 0.65 || best.merged) S.face.set(S.normal);
    const mat = inp.materialOf(best.c.tri);
    const tags = mat?.tags;
    if (hasTag(tags, "PlayerDead")) F.dead = true;
    if (hasTag(tags, "Fence")) F.fence = true;
    if (hasTag(tags, "Ice")) F.ice = true;
    if (hasTag(tags, "KebaInk")) F.keba = true;
    if (hasTag(tags, "PlayerUnsafe")) F.unsafe = true;
    if (hasTag(tags, "Sponge")) F.sponge = true;
    if ((hasTag(tags, "SquidGuard") || hasTag(tags, "Slide")) && S.face[1] < 0.9999999 && FLOOR_NY <= S.face[1]) { F.guardN.set(S.face); F.guard = true; }
    // 발밑 모니터 배치(R+0x1418 항목: S+0x20 && Result+0x26 && 칠 가능 0x71012ed800 [추정]) → 0x7102c71650
    if (mat?.paintable) s.monitors.placeFoot(best.c.tri, [best.px, best.py, best.pz], [S.face[0], S.face[1], S.face[2]], inp.inkCounts);
  }
  // Result+0x13f8 (2149~2154): 바닥 후보마다 (비어 있음 || 얼굴 법선 y < 기존 y) 이면 갱신 — 함수 시작에서 0 으로 지움
  if (r13f8) s.r13f8.set(r13f8); else s.r13f8.fill(0);
  // S+0xf4 해제(3568~): 지지 && S+0x38 < 0.6414 && (InAir 아님 || 유지 > 3 || Result+0x27)
  if (S.forceAir && S.supported && S.face[1] < FLOOR_NY && (s.moveState !== 1 || 3 < s.r1360)) S.forceAir = false;
  // 이동 상태 전이 §5: GameOnGround vt+0x30 0x71012aa648 / GameInAir 0x71012aa108
  if (s.moveState === 0) s.moveState = (!S.supported || S.forceAir) ? 1 : 0;
  else if (s.moveState === 1) s.moveState = (S.supported && !S.forceAir) ? 0 : 1;
  s.r1320.set(m.origin);
}

/** 원본 왕복 교환 정렬(인접 교환만 — 같은 키 순서 유지). gt(a, b) 가 참이면 a 가 b 뒤로. */
function cocktail<T>(xs: T[], gt: (a: T, b: T) => boolean): T[] {
  const a = xs.slice();
  let lo = 0, hi = a.length - 1, swapped = true;
  while (swapped && lo < hi) {
    swapped = false;
    for (let i = lo; i < hi; i++) if (gt(a[i], a[i + 1])) { const t = a[i]; a[i] = a[i + 1]; a[i + 1] = t; swapped = true; }
    hi--;
    for (let i = hi; i > lo; i--) if (gt(a[i - 1], a[i])) { const t = a[i]; a[i] = a[i - 1]; a[i - 1] = t; swapped = true; }
    lo++;
  }
  return a;
}
