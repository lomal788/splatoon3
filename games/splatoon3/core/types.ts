// 영역 간 계약. 구현은 각 영역 폴더가 맡고, 다른 영역은 이 인터페이스로만 접근한다.
import type { Vec3 } from "./fmath.ts";

/** 팀 번호: 원본 생성정보 +0x2c 와 같은 0=Alpha 1=Bravo 2=Charlie, -1=없음. */
export type Team = -1 | 0 | 1 | 2;

// ---- 충돌 (담당: core/collision) -------------------------------------------
export const Layer = {
  Ground: 1 << 0, // 지형 (원본 레이어 Ground=3)
  Object: 1 << 1, // 맵 오브젝트·표적
  Player: 1 << 2,
  Water: 1 << 3, // 낙하 판정
  KeepOut: 1 << 4, // 플레이어 전용 벽
} as const;

export interface Hit {
  /** 구간 비율 0..1 (sweep) 또는 거리 (raycast) */
  t: number;
  point: Vec3;
  normal: Vec3;
  layer: number;
  /** 재질 이름 인덱스(맵 collision 재질표) — 칠 가능 여부 등 */
  material: number;
  /** 충돌한 액터(표적 등)의 id. 지형이면 -1 */
  actor: number;
  /** Raw native point normal when present; entry bit0 chooses camera normal sign. */
  nativeEntryFlags?: number;
  /** Native raw point separation; bit0=0 adjusts query1 point by normal*separation.
   * Omit when the collision adapter already returns a surface contact point. */
  nativeSeparation?: number;
}

/** Native query layer/masks, separate from the web layer selection. */
export interface SphereQueryFilter {
  layerIndex: number;
  subIndex: number;
  hitMask: number;
  subMask: number;
}
export interface CollisionWorld {
  raycast(origin: Vec3, dir: Vec3, maxDist: number, mask: number): Hit | null;
  sweepSphere(from: Vec3, to: Vec3, radius: number, mask: number, query?: SphereQueryFilter): Hit | null;
  /** 현재 구에 닿는 면 목록. 실제 Havok 후보 순서/태그는 별도 미확정. */
  overlapSphere?(center: Vec3, radius: number, mask: number): Hit[];
  materialName(material: number): string;
  /** 움직이는 충돌체(표적 등) 등록·갱신 */
  setDynamic(actor: number, shape: DynamicShape | null): void;
}

export type DynamicShape =
  | { kind: "sphere"; center: Vec3; radius: number; layer: number }
  | { kind: "box"; center: Vec3; half: Vec3; yaw: number; layer: number }
  | { kind: "capsule"; a: Vec3; b: Vec3; radius: number; layer: number };

// ---- 도색 (담당: core/paint) ---------------------------------------------
export interface PaintRequest {
  team: Team;
  owner: number; // 플레이어 id
  pos: Vec3;
  normal: Vec3;
  dir: Vec3; // 진행 방향(스탬프 회전)
  widthHalf: number;
  depthScale: number;
  /** 원본 도색 종류(슈터/스플래시/벽 낙하 등) — paint 문서의 분류 이름 */
  kind: string;
  seed: number;
}

export interface InkSample {
  /** 발밑에서 가장 많은 팀, 없으면 -1 */
  team: Team;
  /** 팀별 덮임 비율 0..1 (Alpha, Bravo, Charlie) */
  ratio: [number, number, number];
}

export interface PaintWorld {
  request(req: PaintRequest): void;
  sample(pos: Vec3, radius: number): InkSample;
  /** 팀별 칠한 텍셀 수, 플레이어별 새로 칠한 텍셀 수 */
  counts(): { team: [number, number, number]; total: number };
  /** 발밑 Disk 1×1 모니터 4개의 스텐실 카운트 (paint_and_score.md §6.3) */
  monitorCounts?(pos: ArrayLike<number>, n: ArrayLike<number>): [number, number, number, number];
}

// ---- 피격 (담당: core/combat 공용, 대상 구현은 각 영역) -------------------
export interface DamageInfo {
  attacker: number;
  team: Team;
  /** 원본 정수 단위(1 = 0.1 HP) */
  value: number;
  pos: Vec3;
  dir: Vec3;
  /** DamageRateInfo 행 이름(예: "Shooter") */
  rateRow: string;
  critical: boolean;
  /** 이번 물리 스텝의 상대 탄 몸 속도(유닛/초), receiver 배율 전 값과 별도. */
  contactVelocity?: Vec3;
  /** 표적 Actor_Bullet 휨은 접촉점 대신 상대 몸 위치를 사용한다. */
  bodyPos?: Vec3;
}

export interface BulletContactInfo {
  pos: Vec3; // 상대 탄 몸 위치
  velocity: Vec3; // body+dc 이번 스텝 속도(유닛/초)
}

export interface Hittable {
  readonly id: number;
  readonly team: Team;
  /** DamageRateInfo 열 이름(예: "Default", 표적 종류) */
  readonly rateCol: string;
  onDamage(info: DamageInfo): void;
  /** native 표적 vt22 물리 접촉. Through/무적도 데미지 리시버와 별개. */
  onBulletContact?(info: BulletContactInfo): void;
}
