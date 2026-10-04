// 담당: [physics] — Phive 충돌 필터(레이어 히트 마스크) 값과 웹 Layer 비트 대응.
// 값은 PhiveConfig(analysis/player/PhiveConfig.json) LayerHitMaskEntityCollection / SubLayerHitMaskEntityCollection
// 의 MaskValue 그대로 [데이터]. 삼각형 필터표 의미는 docs/gimmick/collision_mesh.md §3.4.
import { Layer } from "../types.ts";

/** LayerEntityCollection 순번 [데이터]: 3 Ground, 4 Water, 5 SplPlayer, 7 SplCamera, 8 SplInkBullet … */
export const PhiveLayer = { Ground: 3, Water: 4, SplPlayer: 5, SplCamera: 7, SplInkBullet: 8 } as const;

/** SubLayerEntityCollection 순번 [데이터]. 사람/오징어가 서로 다른 하위 레이어다. */
export const PhiveSubLayer = { Unspecified: 0, Ground: 1, SplPlayerHuman: 3, SplPlayerSquid_Visible: 4, SplPlayerSquid_Invisible: 5 } as const;

/** LayerHitMaskEntity 이름 → 값 [데이터]. 맵 충돌 재질 필터표에 나오는 것만. */
export const LAYER_HIT_MASK: Record<string, number> = {
  HitAll: 0xffffffff,
  NoHit: 0,
  Default: 536870911,
  SplSolidGround: 536870910,
  SplKeepOutPlayer: 98,
  SplKeepOutCamera: 130,
  SplKeepOutBullet: 16776962,
  SplKeepOutPlayerAndCamera: 226,
  SplPlayerThrough: 536870814,
  SplCameraThrough: 536870782,
  SplInkThrough: 520928382,
  SplBlowerThrough: 536477694,
  SplWater: 469761990,
};

/** SubLayerHitMaskEntity 이름 → 값 [데이터]. */
export const SUB_LAYER_HIT_MASK: Record<string, number> = {
  HitAll: 0xffffffff,
  NoHit: 0,
  Default: 134217727,
  SquidThrough: 67073487,
  SplSuperHookCheckThrough: 67106303,
  SplWater: 62913031,
};

export function maskValue(v: unknown, table: Record<string, number>): number | null {
  if (typeof v === "number") return v >>> 0;
  if (typeof v === "string") {
    if (v in table) return table[v] >>> 0;
    if (/^0x[0-9a-f]+$/i.test(v)) return parseInt(v, 16) >>> 0;
  }
  return null;
}

/** 필터가 엔티티 레이어(비트 번호)를 맞히는지. */
export function hitsLayer(mask: number, layerIndex: number): boolean {
  return ((mask >>> layerIndex) & 1) === 1;
}

/**
 * 원시 필터 → 웹 Layer 비트(질의 마스크용). 기준:
 * - 플레이어(레이어 5)를 막지 않고 잉크탄(8)도 막지 않으며 이름이 물이면 Water
 * - 플레이어는 막고 잉크탄은 통과(SplKeepOutPlayer*) → KeepOut
 * - 잉크탄을 막으면 Ground
 * 사람·탄 모두 통과하는 면(SplPlayerThrough 는 탄은 막으므로 Ground)은 0.
 */
export function layerFromFilter(hit: number, name: string): number {
  if (/water/i.test(name)) return Layer.Water;
  const player = hitsLayer(hit, PhiveLayer.SplPlayer);
  const bullet = hitsLayer(hit, PhiveLayer.SplInkBullet);
  if (bullet) return Layer.Ground;
  if (player) return Layer.KeepOut;
  return 0;
}

// ---- 원본 충돌 필터 결합 (COL02) ---------------------------------------------------------------

/** 몸체 필터 F 의 판정 입력. L/S = F+8 bits0..5 / 6..11, m18/m1c = F+0x18/+0x1c, bit28 = F+8 bit28(형상 행 사용). */
export interface PairBody {
  L: number;
  S: number;
  m18: number;
  m1c: number;
  bit28: boolean;
  /** 비교 그룹 F+0x30 (0 = Default 표) */
  group?: number;
}

/** 형상 쪽 행: 복합 형상이면 형상+0xb8/+0xbc, 아니면 shapeTag 행(lo = Layer, hi = SubLayer). 행이 없으면 null(= 0xffffffff, 0xffffffff). */
export interface ShapeRow {
  compound: boolean;
  cb8: number;
  cbc: number;
  row: [number, number] | null;
}

/** 32비트 가변 shift 는 하위 5비트만 쓴다 [실행]. */
function bitAt(w: number, n: number): number {
  return (w >>> (n & 31)) & 1;
}

/**
 * 공통 강체 쌍 필터 0x7103c4dd30 → 0x7103af44e8 양방향 [실행 4096/4096]. tblA = 표 T[L(A)] 행(u32), tblB = T[L(B)] 행.
 * T 는 그룹에 따라 Default/Same/Other block 배열(PhiveConfig 값 2 → bit) [실행: character_controller §3.5.1].
 */
export function commonPairFilter(A: PairBody, B: PairBody, tblA: number, tblB: number): number {
  return bitAt(tblA, B.L) & bitAt(A.m18, B.L) & bitAt(A.m1c, B.S) & bitAt(tblB, A.L) & bitAt(B.m18, A.L) & bitAt(B.m1c, A.S);
}

/** 0x7103c34b7c: X 의 형상 행이 상대 O 의 레이어·하위 레이어를 허용하는지 [실행]. */
export function shapeRowOk(X: PairBody, xs: ShapeRow, O: PairBody): number {
  if (!X.bit28) return 1;
  let lo: number, hi: number;
  if (xs.compound) { lo = xs.cb8; hi = xs.cbc; }
  else if (xs.row) { lo = xs.row[0]; hi = xs.row[1]; }
  else return 1;
  return bitAt(lo, O.L) & bitAt(hi, O.S);
}

/** 형상 행 + 공통 쌍 필터 결합 0x7103c5e244 [실행 4096/4096]. */
export function combinedPairFilter(A: PairBody, As: ShapeRow, B: PairBody, Bs: ShapeRow, tblA: number, tblB: number): number {
  let shape = 1;
  if (A.bit28 || B.bit28) shape = shapeRowOk(B, Bs, A) & shapeRowOk(A, As, B);
  return shape & commonPairFilter(A, B, tblA, tblB);
}

/** LayerEntityParamTableSet(Default/Same/Other) 행 → block 비트 행(값 2 만) [실행: 0x7103b16ad8/0x7103b1ae90]. */
export function blockRow(row: ArrayLike<number>): number {
  let m = 0;
  for (let i = 0; i < row.length && i < 32; i++) if (row[i] === 2) m |= 1 << i;
  return m >>> 0;
}

/** PhiveConfig Default 표의 Ground(3)·SplPlayer(5) 행 [데이터: analysis/player/PhiveConfig.json LayerEntityParamTableSet]. */
export const LAYER_TABLE_DEFAULT_GROUND = blockRow([0, 1, 1, 0, 0, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 0, 2, 2, 1, 1, 0, 2, 2, 2, 2, 2, 2]);
export const LAYER_TABLE_DEFAULT_SPLPLAYER = blockRow([0, 1, 1, 2, 2, 2, 2, 0, 2, 2, 0, 2, 2, 0, 2, 0, 2, 1, 2, 2, 1, 2, 0, 0, 2, 2, 2, 1, 1]);

export interface SubLayerInput {
  /** 특수 번호(본체+0x588 쌍 → +0x658/+0x65c, 쌍 없음 0) */
  special: number;
  /** 액터+0x7b9 */
  actor7b9: boolean;
  /** f1 = 본체+0x7a4 */
  t: number;
  /** [본체+0xa7c0](PlayerCoopZombie)+0xeec */
  zombie: boolean;
  /** [본체+0xa880](PlayerDokanWarp)+0x30 */
  dokan: number;
  /** 4번째 인자(출처 본체+0x7a0·+0x789 등 [미확정]) */
  flag: boolean;
}

/** 플레이어 몸체 하위 레이어 0x71024f5fc4~0x71024f60f8 [실행 4000/4000]. */
export function playerSubLayer(i: SubLayerInput): number {
  let v = i.actor7b9 ? 12 : 7;
  if (i.special !== 0x1a && !i.actor7b9) {
    if (f32x(i.t) < f32x(1.1920929e-7) || i.zombie) v = 3;
    else if (((i.dokan - 1) >>> 0) < 2) v = 6;
    else v = i.flag ? 5 : 4;
  }
  return v;
}

const f32x = Math.fround;

/** 이름(Layer 키 또는 Phive 마스크 이름) → 웹 Layer 비트. */
export function layerFromName(name: string): number {
  switch (name) {
    case "Ground": return Layer.Ground;
    case "Object": return Layer.Object;
    case "Player": return Layer.Player;
    case "Water": return Layer.Water;
    case "KeepOut": return Layer.KeepOut;
  }
  const m = LAYER_HIT_MASK[name];
  if (m !== undefined) return layerFromFilter(m, name);
  return Layer.Ground;
}
