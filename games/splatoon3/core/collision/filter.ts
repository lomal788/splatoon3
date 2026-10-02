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
