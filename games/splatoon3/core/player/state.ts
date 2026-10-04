// 담당: [physics] — 로컬 플레이어 상태 객체(shared "player"). 필드 옆 [본체+0x…] 는 원본 플레이어 본체 오프셋.
// 소유 규칙: 별도 표시가 없는 필드는 physics 만 쓴다. "weapon 소유" 필드는 weapon 이 쓰고 physics 는 읽기만 한다.
// 규칙 전체는 docs/impl/physics.md "player 상태 필드와 소유".
import { v3, type Vec3 } from "../fmath.ts";
import type { Team } from "../types.ts";
import type { PlayerParam } from "./gear.ts";
import { makePlayerParam } from "./gear.ts";
import { createPlayerDisplayState, type PlayerDisplayState, type DisplayBinding } from "./display.ts";

/** 발밑 잉크 PlayerStepPaint(본체+0xa688) — player_state.md §8 */
export interface StepPaint {
  /** +0x30 분류: 0/1 아군, 2/3 적, 4/5 없음 */
  cls: number;
  /** +0x34 발밑 팀(없으면 -1) */
  team: Team;
  /** +0x3c 아군 비율(평활) */
  own: number;
  /** +0x40 아군 비율 원값 */
  ownRaw: number;
  /** +0x44 아군 임계 */
  ownThr: number;
  /** +0x48 적 비율(평활) */
  enemy: number;
  /** +0x4c/+0x50 적 원값 / 느린 감소값 */
  enemyRaw: number;
  enemySlow: number;
  /** +0x54 이동용 적 비율 */
  enemyMove: number;
  /** +0x58 이동용 추종 비율 */
  enemyMoveRate: number;
  /** +0x5c 적 임계 */
  enemyThr: number;
  /** 직전 유효 샘플(+0xa0/+0xa4)과 재사용 여부(+0xa8) */
  lastOwn: number;
  lastEnemy: number;
  reused: boolean;
}

/** 벽 점프·오징어 롤 발사 구조체 L(본체+0x7b8) — movement_physics.md §6.8 */
export interface LaunchState {
  /** [0..2] 발사 속도, [3..5] 방향 */
  vel: Vec3;
  dir: Vec3;
  /** +0x3c(=본체+0x7f4) 활성, +0x3d(=본체+0x7f5), +0x40(=본체+0x7f8) 이번 프레임 적용, +0x41 벽 점프(롤 아님), +0x3f 오징어였음 */
  active: boolean;
  active2: boolean;
  apply: boolean;
  wallJump: boolean;
  wasSquid: boolean;
  /** +0x24 횟수 n (s32), +0x28 마지막 발사 프레임, +0x2c 롤 속력, +0x30 발사 때 높이 */
  count: number;
  frame: number;
  speed: number;
  height: number;
  /** +0x54(=본체+0x80c) 덮어쓰기 스틱 남은 프레임, +0x58/+0x5c 덮어쓰기 스틱, +0x44..+0x4c 고정 입력 축, +0x50 */
  lock: number;
  lockStick: [number, number];
  lockAxis: Vec3;
  lockK: number;
}

/** 이동 이력 항목(0x14 B) — movement_physics.md §6.4.2 */
export interface MoveHistoryEntry {
  dir: Vec3;
  speed: number;
  squidInk: boolean;
  wall: boolean;
}

/** 이동 이력 링 버퍼 본체+0x820(+0x828 capacity 24, +0x82c 시작, +0x830 개수) */
export interface MoveHistory {
  buf: MoveHistoryEntry[];
  start: number;
  count: number;
}

/** weapon 영역이 쓰는 연동 필드 (physics 는 읽기만). */
export interface PlayerWeaponLink {
  /** 이번 프레임 사격 자세(원본 본체+0x4ec/+0x524 > 0 또는 잉크액션 vt[0x28] 참에 대응). weapon 이 매 프레임 쓴다 */
  shooting: boolean;
  /** WeaponShooterParam.MoveSpeed(+0x4c). 0 이면 physics 가 무기 표에서 읽은 값을 쓴다 */
  moveSpeed: number;
  /** weapon 이 마지막으로 쓴 프레임(-1 = 아직 없음 → physics 가 사격 입력으로 대신 판정) */
  frame: number;
}

export interface PlayerState {
  readonly id: number;
  team: Team;
  /** 발 위치 [본체+0x10 이동 성분, 발 기준은 추정] */
  pos: Vec3;
  /** 직전 스텝 위치(표시 보간·낙하 판정용) */
  prevPos: Vec3;
  /** 모델 정면(수평 단위) — 공중 감쇠의 [본체+8] 행렬 열 대용 [추정] */
  facing: Vec3;
  /** 시작 위치·방향 */
  spawnPos: Vec3;
  spawnYaw: number;

  // ---- 상태 번호 (player_state.md) ----
  /** 현재 상태 번호 [SM+0xc8] — 이름은 stateName() */
  state: number;
  /** 직전 상태 번호 [SM+0xcc] */
  prevState: number;
  /** 활성 슬롯 진행 프레임(cur) / 끝 프레임(end) / 재생 속도 — 근사 애니 드라이버 */
  stateFrame: number;
  stateEnd: number;
  stateRate: number;
  /** 상태가 바뀐 프레임 수(같은 프레임에 여러 번 바뀌면 마지막만) */
  stateChanged: boolean;
  /** 이동 오징어 경로(state ∈ S) */
  squid: boolean;
  /** 오징어 모델 ASB 가 활성(표시용) */
  squidModel: boolean;
  /** 변신 과도기 카운터 [SM+0xf0] (≥61 이면 사람 _Hlf 모델) */
  transform: number;
  /** ToSquid 지연 버퍼 [SM+0xdc] */
  squidBuf: number;
  /** ToHuman 시각 [SM+0x1f4] */
  toHumanFrame: number;
  /** 이동 사분면 [본체+0x720] 0 앞 1 뒤 2 왼 3 오른 */
  quadrant: number;

  // ---- 입력 ----
  /** [본체+0x474/+0x478] 이동 스틱 */
  stick: [number, number];
  /** [본체+0x47c] 데드존 재매핑 크기, [+0x480] 내려갈 때만 0.2 추종하는 크기 */
  stickMag01: number;
  stickMagSmooth: number;
  /** 컨트롤러 왼쪽 스틱 원값(컨트롤러+0x120) */
  stickSrc: [number, number];
  /** [본체+0x484] 벽 입력 방향값, [+0x488] 벽 입력 계수 x (0x71024a7100) */
  wallInputDir: number;
  wallInput: number;
  /** [본체+0x786] 오징어 입력 지속 프레임(min(+1,100)) */
  squidHoldFrames: number;
  /** [본체+0x790] 잠복·상승 연속 프레임(양수)/그 밖 연속 프레임(음수) */
  squidInkFrames: number;
  /** [본체+0xaec] 스틱 잠금 프레임 */
  stickLock: number;
  /** [본체+0xad8] 사격 자세 유지 타이머(입력 함수가 max(x−1, 조건값)) */
  aimHold: number;
  /** [본체+0xab0] 카메라 리셋 버튼 눌림 래치(입력 전방 축 보간 비율을 0으로) */
  camResetLatch: boolean;
  /** 이동 이력 */
  history: MoveHistory;
  /** [본체+0x72c/+0x72d] 점프 버튼 누름/이번 프레임 눌림 */
  jumpHeld: boolean;
  jumpPressed: boolean;
  /** [본체+0x784] 오징어 요청(홀드 레벨), [+0x785] 원 입력, [+0x788] 잠금 중 래치 */
  squidRequest: boolean;
  squidInput: boolean;
  squidLatch: boolean;
  /** [본체+0xac4] 오징어 잠금 타이머 — weapon 소유(사격 직후 설정), physics 가 매 프레임 1씩 줄임 */
  squidLock: number;
  /** 사격 버튼(ZR) 누름 */
  fireHeld: boolean;
  /** 입력 우선순위 목록(InputSender+0x30..): 새로 누른 버튼이 앞 */
  inputOrder: number[];
  /** 컨트롤러 누름 비트 2(ZL) — 롤 gate, 우선순위 맨 앞 종류(Sender+0x54/+0x55/+0x56) */
  squidButton: boolean;
  inputFirst: number;

  // ---- 이동 (movement_physics.md §4.1) ----
  /** [본체+0x114] 이동 속도(유닛/프레임) */
  vel: Vec3;
  /** [본체+0x120] 원하는 이동 벡터 */
  desired: Vec3;
  /** [본체+0xd2c] 속도 상한 cap */
  cap: number;
  /** [본체+0xd30] 이동 방향, [+0xd3c] 입력 크기 m */
  dir: Vec3;
  inputMag: number;
  /** [본체+0xd40] 입력 기준 전방 축, [+0xd4c] 그 보간 비율 */
  fwdAxis: Vec3;
  fwdBlend: number;
  /** [본체+0xc0] 공중 프레임, [+0xd0] 보조, [+0xd4] 단계, [+0xdc] 공중 비율, [+0xe0] */
  airFrames: number;
  airFrames2: number;
  airStep: number;
  airRatio: number;
  airStepRatio: number;
  /** [본체+0xc8/+0xcc] */
  airC8: number;
  /** [본체+0x268] 접지 프레임, [+0x26c], [+0x270] 평지를 떠난 뒤 프레임 */
  groundFrames: number;
  ground26c: number;
  offFlatFrames: number;
  /** [본체+0x734] 점프 시작 뒤 프레임 */
  sinceJump: number;
  /** [본체+0x738] 상승·공중 연속 프레임 */
  riseFrames: number;
  /** [본체+0x73c] 수직 속도(위 +), [+0x740] 수직 합계 */
  vy: number;
  vySum: number;
  /** [본체+0x745] 공중 수평 감쇠 0.96 선택 플래그 */
  airDampAlt: boolean;
  /** [본체+0x750] 3D 점프 속도 X, [+0x780] 벽 점프 진행 래치(X+0x30), [+0x782] 유지 가산 차단, [+0x75c] 래치 때 X 사본 */
  jump3d: Vec3;
  jump3dHold: boolean;
  holdBlock: boolean;
  jump3dLatch: Vec3;
  /** [본체+0x77c] 점프 직후 지속 프레임 */
  jumpKeep: number;
  /** [본체+0x774] 벽 점프 차지 프레임, [+0x778] 차지 중 벽 밖 연속 프레임 */
  wallJumpCharge: number;
  wallJumpOff: number;
  /** [본체+0xe4..] 최종 속도 F[0..2] */
  final: Vec3;
  /** [본체+0xfc] 이륙 관성 + 모서리 밀기 */
  takeoff: Vec3;
  /** [본체+0x144] 착지 경직 프레임 */
  landStiff: number;
  /** [본체+0x168/+0x16c] 넉백 프레임·벡터 (외부 입력, 지금은 0) */
  knockFrames: number;
  knock: Vec3;
  /** [본체+0xa2c] 경사·벽 미끄럼 속도, [+0xa38] 미끄럼 양, [+0xa40] 천장 타이머 */
  slide: Vec3;
  slideAmt: number;
  ceilTimer: number;
  /** [본체+0x180] 바닥 법선(오징어 벽이면 벽 법선), [+0x198] 원 법선, [+0x1c8] 표면 법선 */
  floorN: Vec3;
  floorNRaw: Vec3;
  surfN: Vec3;
  /** [본체+0x1f8] 속도로 설명되지 않는 변위 */
  unexplained: Vec3;
  /** 측면 접촉 법선 S [본체+0x454], 있음 여부 */
  sideN: Vec3;
  sideContact: boolean;
  /** Phive 쪽 접지(PC+0xd0) / 직전(PC+0xd1) / 이번 프레임 공중 강제 */
  onGround: boolean;
  prevOnGround: boolean;
  forceAir: boolean;
  /** 오징어 벽 붙기(지면 한계 −0.2571 적용 중) */
  wallCling: boolean;
  /** 접지 법선(PC+0xac) / 접점(PC+0xa0) / 지지 삼각형의 충돌 재질 번호(없으면 -1, 발소리·칠 가능 판정용) */
  groundN: Vec3;
  groundP: Vec3;
  groundMaterial: number;
  /** 이동 애니 속도값 SM+0xd4 (0x710246d060 미판독 → |이동 속도| 근사) */
  animSpeed: number;
  /** 아군 잉크 속 잠복 이동(0x7102458cfc) */
  swimming: boolean;
  /** B7a0/B794/B798. Ordinary display producer before the SM; scope diagnostics separate. */
  display: PlayerDisplayState;
  displayBinding: DisplayBinding | null;
  /** 발밑 잉크 */
  step: StepPaint;
  /** 발사(벽 점프·롤) */
  launch: LaunchState;

  // ---- 잉크 탱크 ----
  /** [본체+0x698] 잉크 잔량 0..1 — weapon 이 소비(감소)하고 physics 가 회복(증가) */
  ink: number;
  /** [본체+0x6a8/6ac/6b0] 인간/부족/오징어 정지 카운터. 이전 max로 회복 판단 후 음수까지 감소. */
  inkRecoverStop: number;
  inkRecoverStopNoInk: number;
  inkRecoverStopSquid: number;
  inkConsumeHold: number;
  inkStealthFrames: number;
  inkStealthBlend: number;
  /** B7a0/24591c8 실제 공급을 받을 때 설정. 없으면 swimming 근사. */
  inkFastStealth?: boolean;
  mainInputFrames: number;
  clearMainLatches: boolean;
  mainInputGates: import("../weapon/input.ts").MainInputGate;
  /** weapon 소유 필드 */
  weapon: PlayerWeaponLink;

  // ---- 기어·무기 ----
  gear: PlayerParam;
  /** 무기 MoveSpeed 기본값(무기 표 WeaponParam.MoveSpeed) */
  weaponMoveSpeed: number;
  /** 무기 표 이름(예: WeaponShooterNormal) */
  weaponTable: string;

  /** 리스폰 횟수(낙하·리셋) */
  respawns: number;
}

export function createPlayerState(id: number, team: Team): PlayerState {
  return {
    id,
    team,
    pos: v3(),
    prevPos: v3(),
    facing: v3(0, 0, 1),
    spawnPos: v3(),
    spawnYaw: 0,
    state: 0x56,
    prevState: 0x56,
    stateFrame: 0,
    stateEnd: 0,
    stateRate: 1,
    stateChanged: false,
    squid: false,
    squidModel: false,
    transform: 0,
    squidBuf: 0,
    toHumanFrame: 0,
    quadrant: 0,
    stick: [0, 0],
    stickMag01: 0,
    stickMagSmooth: 0,
    stickSrc: [0, 0],
    wallInputDir: 0,
    wallInput: 0,
    squidHoldFrames: 0,
    squidInkFrames: 0,
    stickLock: 0,
    aimHold: 0,
    camResetLatch: false,
    history: { buf: Array.from({ length: 24 }, () => ({ dir: v3(), speed: 0, squidInk: false, wall: false })), start: 0, count: 0 },
    jumpHeld: false,
    jumpPressed: false,
    squidRequest: false,
    squidInput: false,
    squidLatch: false,
    squidLock: 0,
    fireHeld: false,
    inputOrder: [],
    squidButton: false,
    inputFirst: 0,
    vel: v3(),
    desired: v3(),
    cap: 0,
    dir: v3(),
    inputMag: 0,
    fwdAxis: v3(0, 0, 1),
    fwdBlend: 1, // 생성자 0x3f800000 (player_components_vt.c 5082행)
    airFrames: 0,
    airFrames2: 0,
    airStep: 0,
    airRatio: 0,
    airStepRatio: 0,
    airC8: 0,
    groundFrames: 0,
    ground26c: 0,
    offFlatFrames: 0,
    sinceJump: 9999, // 생성자 0x710245717c plVar12[0xe6] = 0x270f00000000
    riseFrames: 0,
    vy: 0,
    vySum: 0,
    airDampAlt: false,
    jump3d: v3(),
    jump3dHold: false,
    holdBlock: false,
    jump3dLatch: v3(),
    jumpKeep: 0,
    wallJumpCharge: 0,
    wallJumpOff: 0,
    final: v3(),
    takeoff: v3(),
    landStiff: 0,
    knockFrames: 0,
    knock: v3(),
    slide: v3(),
    slideAmt: 0,
    ceilTimer: 0,
    floorN: v3(0, 1, 0),
    floorNRaw: v3(0, 1, 0),
    surfN: v3(0, 1, 0),
    unexplained: v3(),
    sideN: v3(),
    sideContact: false,
    onGround: true,
    prevOnGround: true,
    forceAir: false,
    wallCling: false,
    groundN: v3(0, 1, 0),
    groundP: v3(),
    groundMaterial: -1,
    animSpeed: 0,
    swimming: false,
    display: createPlayerDisplayState(),
    displayBinding: null,
    step: {
      cls: 4, team: -1, own: 0, ownRaw: 0, ownThr: 0.65, enemy: 0, enemyRaw: 0, enemySlow: 0,
      enemyMove: 0, enemyMoveRate: 0, enemyThr: 0.35, lastOwn: 0, lastEnemy: 0, reused: false,
    },
    launch: {
      vel: v3(), dir: v3(0, 0, 1), active: false, active2: false, apply: false, wallJump: false, wasSquid: false,
      count: 0, frame: 0, speed: 0, height: 0, lock: 0, lockStick: [0, 0], lockAxis: v3(), lockK: 0,
    },
    ink: 1, // 본체 생성 0x71024575bc 가 1.0 으로 초기화 (network/04_player_state.md #15)
    inkRecoverStop: 0, inkRecoverStopNoInk: 0, inkRecoverStopSquid: 0, inkConsumeHold: 0, inkStealthFrames: 0, inkStealthBlend: 0,
    mainInputFrames: 0, clearMainLatches: false,
    mainInputGates: { blocked: false, inkBlocked: false, rFrames: 0, rFlag: false, aFrames: 0, aFlag: false, denied: false, sideMode: 0, sideAllowed: false },
    weapon: { shooting: false, moveSpeed: 0, frame: -1 },
    gear: makePlayerParam(),
    weaponMoveSpeed: 0,
    weaponTable: "",
    respawns: 0,
  };
}
