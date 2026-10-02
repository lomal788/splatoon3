// HitEffectConfig 조합표: (행, 반응, 대상) → E1/E2/S1/S2. 로더 0x71027b5980 (docs/effect_sound/effect_sound.md §3.5).
// 셀 이름 "%s___%s_%s"(행___반응_대상), 없으면 "%s___%s_Default".

export interface HitCell {
  E1?: string;
  E2?: string;
  S1?: string;
  S2?: string;
}

/** E2 문자열 → 코드 파티클 종류(로더가 바꿔 둔 값): Splash 0, Hit 1, SplashWater 2, 그 밖 -1 */
export function e2Kind(e2: string | undefined): number {
  if (e2 === "Hit") return 1;
  if (e2 === "SplashWater") return 2;
  if (e2 === "Splash") return 0;
  return -1;
}

/** E2 가 ELink HitEffect 키인 경우(Splash/Hit/SplashWater 는 코드 파티클만) */
export function e2IsElinkKey(e2: string | undefined): boolean {
  return !!e2 && e2 !== "Splash" && e2 !== "Hit" && e2 !== "SplashWater";
}

// 자료가 없을 때 쓰는 Shooter 행(effect_sound.md §3.5 표, 원본 HitEffectConfig.json 과 같은 값) [데이터]
const FALLBACK: Record<string, HitCell> = {
  "Shooter___Damaged_Default": { E1: "HitEffective", E2: "Hit", S1: "ヒット", S2: "インク被弾" },
  "Shooter___Damaged_Shield": { E1: "HitEffective", E2: "Hit", S1: "シールド", S2: "インク被弾" },
  "Shooter___Armored_Default": { E1: "HitInvalid", E2: "Hit", S1: "アーマード", S2: "インク被弾" },
  "Shooter___Invincible_Default": { E1: "HitInvalid", E2: "Splash", S1: "ノーダメージ", S2: "インク被弾" },
  "Shooter___Constant_Default": { E2: "Splash", S2: "インクヒット" },
  "Shooter___Constant_Water": { E2: "SplashWater", S2: "水没" },
  "Shooter___Constant_KebaInk": { E1: "HitInvalidKebaInk", S1: "ケバインクヒット" },
  "Shooter___Cure_Default": { E1: "HitEffective", E2: "Hit", S1: "ヒット" },
};

export class HitEffectTable {
  private readonly cells: Record<string, HitCell>;
  readonly fromData: boolean;

  /** 원본 형식 {CellList: {"행___열": 셀}} 또는 assets 형식 {rows: {행: {열: 셀}}} (docs/impl/assets.md) */
  constructor(json?: unknown) {
    const j = json as { CellList?: Record<string, HitCell>; rows?: Record<string, Record<string, HitCell>> } | undefined;
    let list = j?.CellList ?? null;
    if (!list && j?.rows) {
      list = {};
      for (const [row, cols] of Object.entries(j.rows)) for (const [col, c] of Object.entries(cols)) list[`${row}___${col}`] = c;
    }
    this.cells = list ?? FALLBACK;
    this.fromData = !!list;
  }

  /** 0x71027b5980 의 이름 규칙 */
  cell(row: string, reaction: string, target: string): HitCell | null {
    return this.cells[`${row}___${reaction}_${target}`] ?? this.cells[`${row}___${reaction}_Default`] ?? null;
  }
}

/** 어느 JSON 이든 CellList 를 가진 것을 HitEffectConfig 로 본다. */
export function isHitEffectConfig(j: unknown): boolean {
  return !!j && typeof j === "object" && ("CellList" in (j as object) || ("rows" in (j as object) && "colKeys" in (j as object)));
}
