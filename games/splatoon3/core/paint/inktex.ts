// 잉크 스탬프 종류(InkTexType)·InkTexInfo 행·변형 번호·높이 범위·스탬프 마스크.
// 근거: docs/paint/paint_and_score.md §3.4, §3.5.3 (그리기 레코드 0x7102c11f80, 원본 실행 600/600).
import { f32 } from "../fmath.ts";
import { SeadRandom } from "../rng.ts";

/** spl::paint::InkTexType 열거 문자열 순서(= 값). paint_and_score.md §3.4. */
export const INK_TEX_TYPES: readonly string[] = (
  "Shot00 Shot01 Shot02 Shot03 Shot04 RlrSplash00 RlrSplash01 RlrSplash02 ChgrSplash00 ChgrSplash01 " +
  "Bomb00 WallDrip00 WallDrip01 Roller00 PaintLift00 PaintLift01 Disk Rectangle InkRutStart InkRutMove " +
  "QuadDonut Rain00_0 Rain00_1 Rain00_2 SprBall00 StampKingFace Common WallDrip00_0 WallDrip00_1 " +
  "WallDrip00_2 WallDrip00_3 WallDrip00_4 WallDrip01_0 WallDrip01_1 WallDrip01_2 WallDrip01_3 " +
  "WallDrip01_4 SpStamp00 Death00 SprLanding00 Manta GachihokoCross00 BombLineMarker Slosher00 Chgr00 " +
  "Bomb00Height3pnt4 Bomb00ForBombFlower TripleTornado DiskHD AllPaint"
).split(" ");

export const HeightRangeType = { MinEdge: 0, MaxEdge: 1, Static: 2, None: 3 } as const;

/** InkTexInfo 행 (RSDB InkTexInfo.Product.100 → analysis/paint/InkTexInfo.json 필드 이름 그대로). */
export interface InkTexInfoRow {
  TextureName: string;
  PatternNum: number;
  AnimationFrame: number;
  AnimationStep: number;
  HeightRangeType: string;
  HeightRangeRate: number;
  StaticHeightRangeMin: number;
  StaticHeightRangeMax: number;
  DisableSlopeScale: boolean;
}

/**
 * 에셋 표(data/InkTexInfo.json)가 없을 때 쓰는 행. 값은 analysis/paint/InkTexInfo.json [데이터] 그대로.
 * 연습장 슈터가 쓰는 Shot00~04(슈터·스플래시·벽 낙하 모두 패턴 0..4)만 둔다.
 */
const FALLBACK_ROWS: Record<string, InkTexInfoRow> = {
  Shot00: row(12),
  Shot01: row(6),
  Shot02: row(6),
  Shot03: row(6),
  Shot04: row(6),
};

function row(pattern: number): InkTexInfoRow {
  return {
    TextureName: "",
    PatternNum: pattern,
    AnimationFrame: 3,
    AnimationStep: 3,
    HeightRangeType: "MinEdge",
    HeightRangeRate: 1.0,
    StaticHeightRangeMin: -1,
    StaticHeightRangeMax: 1,
    DisableSlopeScale: false,
  };
}

export class InkTexTable {
  private readonly rows = new Map<string, InkTexInfoRow>();
  /** 표 출처: "asset" | "fallback" (기록·디버그용) */
  readonly source: string;

  constructor(table: unknown) {
    let n = 0;
    // 에셋 data/ink_tex_info.json = { source, rows: [{ ...필드, name }] } (docs/impl/assets.md)
    if (table && typeof table === "object" && Array.isArray((table as { rows?: unknown }).rows)) table = (table as { rows: unknown[] }).rows;
    if (Array.isArray(table)) {
      for (const r of table as (InkTexInfoRow & { __RowId?: string; RowId?: string; name?: string })[]) {
        const id = r.__RowId ?? r.RowId ?? r.name;
        if (!id) continue;
        const name = id.slice(id.lastIndexOf("/") + 1).split(".")[0];
        this.rows.set(name, r);
        n++;
      }
    } else if (table && typeof table === "object") {
      for (const [k, v] of Object.entries(table as Record<string, InkTexInfoRow>)) {
        this.rows.set(k, v);
        n++;
      }
    }
    this.source = n > 0 ? "asset" : "fallback";
    if (n === 0) for (const [k, v] of Object.entries(FALLBACK_ROWS)) this.rows.set(k, v);
  }

  get(type: number): InkTexInfoRow {
    const name = INK_TEX_TYPES[type] ?? "Shot00";
    return this.rows.get(name) ?? FALLBACK_ROWS[name] ?? FALLBACK_ROWS.Shot00;
  }

  /** 행이 가리키는 스탬프 텍스처 이름(변형 k). PatternNum > 1 이면 `<이름>_<k>`. */
  textureName(type: number, variant: number): string {
    const r = this.get(type);
    const base = r.TextureName || INK_TEX_TYPES[type] || "Shot00";
    return r.PatternNum > 1 ? `${base}_${variant}` : base;
  }
}

/** 0x7102c11f80 D+0x20/+0x24 높이 범위 (max, min). */
export function heightRange(r: InkTexInfoRow, W: number, L: number): [number, number] {
  const t = HeightRangeType[r.HeightRangeType as keyof typeof HeightRangeType] ?? HeightRangeType.None;
  if (t === HeightRangeType.Static) return [f32(r.StaticHeightRangeMax), f32(r.StaticHeightRangeMin)];
  if (t === HeightRangeType.MinEdge || t === HeightRangeType.MaxEdge) {
    const e = t === HeightRangeType.MaxEdge ? (W > L ? W : L) : W < L ? W : L;
    const h = f32(f32(r.HeightRangeRate) * f32(e * 0.5));
    return [h, -h];
  }
  return [20000, -20000];
}

/**
 * 0x7102c11f80 D+0x54 시드: |fcvtzs((p.z + (p.x + p.y)) × 100)| + N+4 (u32).
 * p = 대상 공간 위치(Floor 는 위치 그대로 — 원본 실행 검증은 Floor 만), reqNo = 요청 번호(N+4, 탄 슬롯105).
 */
export function paintSeed(p: ArrayLike<number>, reqNo: number): number {
  const s = f32(f32(p[2] + f32(p[0] + p[1])) * 100);
  let i = Number.isNaN(s) ? 0 : Math.trunc(s);
  if (i > 2147483647) i = 2147483647;
  if (i < -2147483648) i = -2147483648;
  return (Math.abs(i) + (reqNo >>> 0)) >>> 0;
}

/** D+0x60 변형 번호: sead::Random(seed) 첫 u32 % PatternNum (0 이면 그대로, 개수 이상이면 0). */
export function patternVariant(seed: number, patternNum: number): number {
  const r = new SeadRandom(seed).u32();
  const idx = patternNum === 0 ? r : r % patternNum;
  return idx < patternNum ? idx : 0;
}

// ---- 스탬프 마스크 ----------------------------------------------------------

/** 스탬프 마스크: R 채널 8비트, 행 0 = 텍스처 v=0 (PNG 위쪽). */
export interface StampMask {
  w: number;
  h: number;
  data: Uint8Array;
  /** 원본 텍스처에서 왔는지(false = 해석적 근사) */
  original: boolean;
}

/**
 * 에셋 표 `data/ink_stamps.json` 형식(조정 요청, docs/impl/paint.md):
 *   { "<텍스처 이름>": { "w": 32, "h": 32, "data": "<base64 R8, 행 우선, 행 0 = PNG 위>" | number[] } }
 */
export class StampLibrary {
  private readonly cache = new Map<string, StampMask>();
  private readonly table: Record<string, { w: number; h: number; data: string | number[] }> | null;

  constructor(table: unknown) {
    this.table = table && typeof table === "object" ? (table as StampLibrary["table"]) : null;
  }

  get hasOriginal(): boolean {
    return !!this.table && Object.keys(this.table).length > 0;
  }

  get(name: string): StampMask {
    let m = this.cache.get(name);
    if (m) return m;
    const e = this.table?.[name];
    if (e && e.w > 0 && e.h > 0) {
      const data = typeof e.data === "string" ? decodeBase64(e.data) : Uint8Array.from(e.data);
      if (data.length >= e.w * e.h) m = { w: e.w, h: e.h, data, original: true };
    }
    m ??= analyticMask(name);
    this.cache.set(name, m);
    return m;
  }
}

/**
 * 해석적 근사 마스크 (원본 텍스처가 없을 때만). 원본 Shot00~04 (32×32/42/54/70/91, 각 변형 평균)에서
 * 잰 "≥ 0.3 텍셀 비율"과 그 영역 무게중심 높이(v)를 맞춘 원뿔형 원: 값 = 1 − d/(r/0.7) (d = 픽셀 거리).
 * 꼬리 무늬·변형 차이는 없다. Rectangle = 전부 1, Disk = 원 안 1, 그 밖 이름은 Shot00 모양. 측정: Shot00 0.252/0.480, Shot01 0.302/0.569, Shot02 0.219/0.675,
 * Shot03 0.178/0.712, Shot04 0.168/0.710.
 */
const ANALYTIC: Record<string, [number, number, number]> = {
  Shot00: [32, 0.252, 0.48],
  Shot01: [42, 0.302, 0.569],
  Shot02: [54, 0.219, 0.675],
  Shot03: [70, 0.178, 0.712],
  Shot04: [91, 0.168, 0.71],
};

export function analyticMask(name: string): StampMask {
  const base = name.replace(/_\d+$/, "");
  if (base === "Rectangle") return { w: 4, h: 4, data: new Uint8Array(16).fill(255), original: false };
  if (base === "Disk" || base === "DiskHD") {
    const n = 64, data = new Uint8Array(n * n);
    for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) data[y * n + x] = Math.hypot(x + 0.5 - n / 2, y + 0.5 - n / 2) <= n / 2 ? 255 : 0;
    return { w: n, h: n, data, original: false };
  }
  const [h, frac, cy] = ANALYTIC[base] ?? ANALYTIC.Shot00;
  const w = 32;
  const r = Math.sqrt((frac * w * h) / Math.PI);
  const R = r / 0.7;
  const data = new Uint8Array(w * h);
  const cxp = w * 0.5, cyp = h * cy;
  for (let y = 0; y < h; y++)
    for (let x = 0; x < w; x++) {
      const d = Math.hypot(x + 0.5 - cxp, y + 0.5 - cyp);
      const v = 1 - d / R;
      data[y * w + x] = v <= 0 ? 0 : Math.min(255, Math.round(v * 255));
    }
  return { w, h, data, original: false };
}

/** 쌍선형 샘플(가장자리 클램프). 원본 샘플러 필터·랩은 [추정: linear, clamp]. */
export function sampleMask(m: StampMask, u: number, v: number): number {
  const x = u * m.w - 0.5, y = v * m.h - 0.5;
  let x0 = Math.floor(x), y0 = Math.floor(y);
  const fx = x - x0, fy = y - y0;
  let x1 = x0 + 1, y1 = y0 + 1;
  const mw = m.w - 1, mh = m.h - 1;
  x0 = x0 < 0 ? 0 : x0 > mw ? mw : x0;
  x1 = x1 < 0 ? 0 : x1 > mw ? mw : x1;
  y0 = y0 < 0 ? 0 : y0 > mh ? mh : y0;
  y1 = y1 < 0 ? 0 : y1 > mh ? mh : y1;
  const d = m.data, w = m.w;
  const a = d[y0 * w + x0], b = d[y0 * w + x1], c = d[y1 * w + x0], e = d[y1 * w + x1];
  const top = a + (b - a) * fx, bot = c + (e - c) * fx;
  return f32((top + (bot - top) * fy) / 255);
}

const B64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
function decodeBase64(s: string): Uint8Array {
  const clean = s.replace(/[^A-Za-z0-9+/]/g, "");
  const out = new Uint8Array(Math.floor((clean.length * 3) / 4));
  let o = 0;
  for (let i = 0; i + 1 < clean.length; i += 4) {
    const a = B64.indexOf(clean[i]), b = B64.indexOf(clean[i + 1]);
    const c = i + 2 < clean.length ? B64.indexOf(clean[i + 2]) : -1;
    const d = i + 3 < clean.length ? B64.indexOf(clean[i + 3]) : -1;
    out[o++] = (a << 2) | (b >> 4);
    if (c >= 0 && o < out.length) out[o++] = ((b & 15) << 4) | (c >> 2);
    if (d >= 0 && o < out.length) out[o++] = ((c & 3) << 6) | d;
  }
  return out.subarray(0, o);
}
