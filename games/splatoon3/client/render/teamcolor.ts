// 팀 컬러 계산. docs/graphics/team_color.md 의 TS 이식(참조 구현 web/tools/graphics_verify/teamcolor.mjs 와 같은 식).
//   hsvOffset 0x7101188334, deriveTeamColor 0x7101174534, inkCorrection 0x7101174afc,
//   buildTeamSet 0x71011743a0, buildTeamSets 0x7101176830, materialTeamParams 0x7101103490.
// r8 명령 판독: 분리된 f32 산술, FMA 없음. JS pow/fmod는 SDK libm 전체 비트 동등성을 주장하지 않는다.
import { F, add, sub, mul, div } from "./graphics_math.ts";

export type RGBA = [number, number, number, number];

export const TYPE_NAMES = [
  "Original", "Pale", "Bright", "Dark", "HueBright", "HueBrightHalf", "HueDark", "HueDarkHalf",
  "Model", "Ink", "InkBright", "InkLame", "InkLameRare", "Silhouette",
] as const;

/** RSDB/TeamColorOffset 12행 (Brightness, Hue, Saturation) [데이터] */
const OFFSETS: Record<string, { b: number; h: number; s: number }> = {
  Bright: { b: 0.10000000149011612, h: 0, s: 0 },
  Dark: { b: -0.20000000298023224, h: 0, s: 0.5 },
  HueBright: { b: 0.05000000074505806, h: 0.10000000149011612, s: 0 },
  HueBrightHalf: { b: 0, h: 0.05000000074505806, s: 0 },
  HueDark: { b: 0.05000000074505806, h: -0.10000000149011612, s: 0 },
  HueDarkHalf: { b: 0, h: -0.05000000074505806, s: 0 },
  Ink: { b: -0.25, h: 0, s: 0 },
  InkBright: { b: 0, h: 0, s: 0 },
  InkLame: { b: 0.10000000149011612, h: 0, s: 0 },
  InkLameRare: { b: 0.05000000074505806, h: 0.10000000149011612, s: 0 },
  Pale: { b: 0.10000000149011612, h: 0, s: -0.05000000074505806 },
  Silhouette: { b: 0, h: 0, s: -0.6000000238418579 },
};

/** SingletonParam TeamColorHueDirPeak [데이터] */
const HUE_DIR_PEAK = { bright: 0.20000000298023224, dark: 0.7200000286102295 };
/** InkColorCorrection.CorrectionInkMain [데이터], MinBright 는 생성자 기본값 [판독] */
const INK_MAIN = { lumRate: 0.5, rate1: 0.20000000298023224, rate6: 0.550000011920929, maxSat: 0.9900000095367432, minBright: 0.009999999776482582 };
/** CorrectionInkSSS 생성자 기본값(데이터에 없음) [판독] */
const INK_SSS = { brightnessOffset: 0.10000000149011612, brightnessOffsetLuminance: 0.5 };

function rgbToHsv(r: number, g: number, b: number): [number, number, number] {
  let K = 0;
  if (g < b) {
    [g, b] = [b, g];
    K = -1;
  }
  if (r < g) {
    [r, g] = [g, r];
    K = sub(div(-1, 3), K);
  }
  const chroma = sub(r, Math.min(g, b));
  const h = Math.min(1, Math.abs(add(K, div(sub(g, b), add(mul(chroma, 6), 1e-20)))));
  const s = Math.min(1, Math.max(0, div(chroma, add(r, 1e-20))));
  return [h, s, r];
}

function hsvToRgb(h: number, s: number, v: number, a: number): RGBA {
  if (s === 0) return [v, v, v, 1]; // 원본 특이점: 알파 1, RGB 비클램프
  const x = div(F(F(h) % 1), F(1 / 6)); // fmodf: 부호 유지
  const i = Math.trunc(x);
  const f = sub(x, i);
  const p = mul(v, sub(1, s)), q = mul(v, sub(1, mul(s, f))), t = mul(v, sub(1, mul(s, sub(1, f))));
  let rgb: [number, number, number];
  switch (i < 0 || i > 4 ? 5 : i) {
    case 0: rgb = [v, t, p]; break;
    case 1: rgb = [q, v, p]; break;
    case 2: rgb = [p, v, t]; break;
    case 3: rgb = [p, q, v]; break;
    case 4: rgb = [t, p, v]; break;
    default: rgb = [v, p, q];
  }
  const c = (y: number): number => (y >= 0 ? Math.min(y, 1) : 0);
  return [c(rgb[0]), c(rgb[1]), c(rgb[2]), a];
}

export function hsvOffset(hueOff: number, satOff: number, brightOff: number, c: RGBA): RGBA {
  const [h, s, v] = rgbToHsv(c[0], c[1], c[2]);
  if (HUE_DIR_PEAK.bright < h && h < HUE_DIR_PEAK.dark) hueOff = -hueOff;
  const s2 = Math.min(1, Math.max(0, add(sub(satOff, Math.abs(brightOff)), s)));
  const v2 = add(v, brightOff) <= 0 ? 0 : add(v, brightOff);
  return hsvToRgb(add(h, hueOff), s2, v2, c[3]);
}

const labF = (t: number): number => (t >= F(0.008856452) ? F(Math.pow(t, F(1 / 3))) : add(mul(t, 7.7870374), 0.13793103));
const lStar = (r: number, g: number, b: number): number => sub(mul(labF(add(add(mul(r, 0.2126), mul(g, 0.7152)), mul(b, 0.0722))), 116), 16);

/** 활성 env 의 첫 DirectionalLight (DiffuseColor, Intensity) + 하늘 SH 위쪽 조도 (team_color.md §5.3) */
export interface EnvLight {
  color: [number, number, number];
  intensity: number;
  skyUp: [number, number, number] | null;
}

function inkCorrection(c: RGBA, light: EnvLight | null, bright: boolean): RGBA {
  const [h, s, v] = rgbToHsv(c[0], c[1], c[2]);
  let t = 0;
  if (light) {
    t = mul(light.intensity, div(lStar(light.color[0], light.color[1], light.color[2]), 100));
    if (light.skyUp) t = add(t, div(lStar(light.skyUp[0], light.skyUp[1], light.skyUp[2]), 100));
  }
  const dark = add(div(lStar(c[0], c[1], c[2]), -100), 1);
  const k = Math.min(1, Math.max(0, sub(1, mul(INK_MAIN.lumRate, dark))));
  let r = add(div(sub(mul(INK_MAIN.rate1, 6), INK_MAIN.rate6), 5), mul(div(sub(INK_MAIN.rate6, INK_MAIN.rate1), 5), t));
  r = r < 0 ? 0 : Math.min(r, INK_MAIN.rate6);
  let d = Math.min(v, mul(r, k));
  if (bright) d = sub(d, mul(INK_SSS.brightnessOffset, sub(1, mul(INK_SSS.brightnessOffsetLuminance, dark))));
  const v2 = Math.max(INK_MAIN.minBright, Math.min(1, Math.max(0, sub(v, d))));
  return hsvToRgb(h, Math.min(s, INK_MAIN.maxSat), v2, c[3]);
}

function derive(lin: RGBA, i: number, hueExtra: number, env: EnvLight | null): RGBA | null {
  if (i === 0) return [...lin] as RGBA;
  if (i === 8) return inkCorrection(lin, null, false);
  if (i === 9 || i === 10) return env ? inkCorrection(lin, env, i === 10) : null; // env 없으면 원본도 쓰지 않음
  const o = OFFSETS[TYPE_NAMES[i]];
  if (!o) return null;
  let hue = o.h;
  if (Math.abs(hue) > 1.1920929e-7) hue = hue > 0 ? add(hue, hueExtra) : sub(hue, hueExtra);
  return hsvOffset(hue, o.s, o.b, lin);
}

export interface TeamSet {
  raw: RGBA;
  linear: RGBA;
  colors: (RGBA | null)[];
}

const fr = (c: RGBA | null): RGBA | null => (c ? (c.map(Math.fround) as RGBA) : null);

export function buildTeamSet(raw: RGBA, hueExtra = 0, env: EnvLight | null = null): TeamSet {
  const lin: RGBA = [F(Math.pow(F(raw[0]), F(2.2))), F(Math.pow(F(raw[1]), F(2.2))), F(Math.pow(F(raw[2]), F(2.2))), F(raw[3])];
  return { raw, linear: lin, colors: TYPE_NAMES.map((_, i) => fr(derive(lin, i, hueExtra, env))) };
}

/** RSDB TeamColorDataSet 행 (RGBA 객체 필드) */
export interface TeamColorRow {
  AlphaTeamColor: { R: number; G: number; B: number; A: number };
  BravoTeamColor: { R: number; G: number; B: number; A: number };
  CharlieTeamColor: { R: number; G: number; B: number; A: number };
  NeutralColor: { R: number; G: number; B: number; A: number };
  AlphaHueOffset?: number;
  BravoHueOffset?: number;
  CharlieHueOffset?: number;
  NeutralHueOffset?: number;
  HueOffsetEnable?: boolean;
  Tag?: string;
  __RowId?: string;
}

const TAGS = ["VersusRegular", "VersusOption", "Mission", "MissionOption", "VersusTricolor", "VersusTricolorOption", "Coop", "CoopOption", "Gambit", "Blitz"];

/** 0x7101176830: 행 → 세트 0..3. swap 이면 색만 바꾸고 hue 오프셋은 바꾸지 않음(원본 그대로). */
export function buildTeamSets(row: TeamColorRow, swap = false, env: EnvLight | null = null): TeamSet[] {
  const c = (k: "AlphaTeamColor" | "BravoTeamColor" | "CharlieTeamColor" | "NeutralColor"): RGBA => [row[k].R, row[k].G, row[k].B, row[k].A];
  const en = !!row.HueOffsetEnable;
  const tag = TAGS.indexOf(row.Tag ?? "");
  const a = c("AlphaTeamColor"), b = c("BravoTeamColor");
  const set2 = tag >= 0 && (tag & ~1) === 4 ? c("CharlieTeamColor") : c("NeutralColor");
  return [
    buildTeamSet(swap ? b : a, en ? row.AlphaHueOffset ?? 0 : 0, env),
    buildTeamSet(swap ? a : b, en ? row.BravoHueOffset ?? 0 : 0, env),
    buildTeamSet(set2, en ? row.CharlieHueOffset ?? 0 : 0, env),
    buildTeamSet(c("NeutralColor"), en ? row.NeutralHueOffset ?? 0 : 0, env),
  ];
}

export interface MaterialTeamParams {
  my_team_color: RGBA;
  my_team_color_bright: RGBA;
  my_team_color_hue_bright: RGBA;
  my_team_color_hue_bright_half: RGBA;
  my_team_color_hue_dark: RGBA;
  my_team_color_hue_dark_half: RGBA;
  my_team_color_hue_complement: RGBA;
}

const ONE: RGBA = [1, 1, 1, 1];

/** 0x7101103490: Hoian_UBER 재질에 쓰는 팀색 파라미터(선형). renderInfo 는 재질 renderInfo(문자열·숫자 값 그대로). */
export function materialTeamParams(set: TeamSet, ri: Record<string, unknown> = {}): MaterialTeamParams {
  const col = (i: number): RGBA => set.colors[i] ?? ONE;
  const P: MaterialTeamParams = {
    my_team_color: col(8),
    my_team_color_bright: col(2),
    my_team_color_hue_bright: col(4),
    my_team_color_hue_bright_half: col(5),
    my_team_color_hue_dark: col(6),
    my_team_color_hue_dark_half: col(7),
    my_team_color_hue_complement: hsvOffset(0.5, 0, 0, set.linear),
  };
  const type = first(ri.my_team_color_type);
  const hueOff = +(first(ri.my_team_color_hue_offset) ?? 0) || 0;
  if (type === "7") {
    const bo = +(first(ri.my_team_color_bright_offset) ?? 0) || 0;
    if (hueOff !== 0 || bo !== 0) P.my_team_color = hsvOffset(hueOff, 0, bo !== 0 ? Math.max(-1, bo) : 0, set.linear);
  } else if (type === "10") {
    P.my_team_color_hue_complement = hsvOffset(hueOff, 0, 0, set.linear);
  } else if (type === "8" && set.colors[9]) {
    P.my_team_color = set.colors[9];
  }
  return P;
}

function first(v: unknown): string | undefined {
  if (Array.isArray(v)) v = v[0];
  return v === undefined || v === null ? undefined : String(v);
}

/** 데이터가 번들에 없을 때 쓰는 행: RSDB TeamColorDataSet "OrangeBlue" [데이터 — analysis/graphics/rsdb/TeamColorDataSet.json]. 로비 연습장이 어느 행을 쓰는지는 [미확정]. */
export const FALLBACK_ROW: TeamColorRow = {
  AlphaTeamColor: { R: 0.8745098114013672, G: 0.4000000059604645, B: 0.1450980007648468, A: 1 },
  BravoTeamColor: { R: 0.2078430950641632, G: 0.23529410362243652, B: 0.7725489735603333, A: 1 },
  CharlieTeamColor: { R: 0, G: 0, B: 1, A: 1 },
  NeutralColor: { R: 0.8039215803146362, G: 0.8039215803146362, B: 0.2039216011762619, A: 1 },
  HueOffsetEnable: false,
  Tag: "VersusRegular",
  __RowId: "Work/Gyml/OrangeBlue.game__gfx__parameter__TeamColorDataSet.gyml",
};

/** sead::Random (xorshift128). getU32 = 0x7101179d78..0x7101179d94 inline copy in 0x7101179c80. */
export class SeadRandom {
  s: [number, number, number, number];
  constructor(state: [number, number, number, number]) {
    this.s = state.map((v) => v >>> 0) as [number, number, number, number];
  }
  /** sead::Random::init(u32) library form. Which seed the global *0x7105997950 receives is [미확정]. */
  static fromSeed(seed: number): SeadRandom {
    const s: number[] = [];
    let p = seed >>> 0;
    for (let i = 1; i <= 4; i++) {
      p = (Math.imul(1812433253, (p ^ (p >>> 30)) >>> 0) + i) >>> 0;
      s.push(p);
    }
    return new SeadRandom(s as [number, number, number, number]);
  }
  nextU32(): number {
    const [x, y, z, w] = this.s;
    const t = (x ^ (x << 11)) >>> 0;
    const n = (t ^ (t >>> 8) ^ w ^ (w >>> 19)) >>> 0;
    this.s = [y, z, w, n];
    return n;
  }
}

/** 0x7101179c80(table, column 0xc Tag, value 0 = VersusRegular): n matching rows, index = (r·n)>>32 by umull/lsr. */
export function seadRandomIndex(r: number, n: number): number {
  return Number((BigInt(r >>> 0) * BigInt(n >>> 0)) >> 32n);
}

/** Lobby selector 0 (0x7101179fd0) after boot init 0x7101179448: one uniformly drawn VersusRegular row, swap 0.
 * Row order is the RSDB TeamColorDataSet table order [데이터]. No matching row → YellowPurple (model_character.md §3.1). */
export function selectLobbyTeamRow(rows: (TeamColorRow & { name?: string })[], rng: SeadRandom): TeamColorRow {
  const regular = rows.filter((r) => r.Tag === "VersusRegular");
  if (!regular.length) return rows.find((r) => r.name === "YellowPurple") ?? FALLBACK_ROW;
  return regular[seadRandomIndex(rng.nextU32(), regular.length)];
}

const lobbyRows = new WeakMap<object, TeamColorRow>();
/** One boot-time choice shared by the player/stage material and paint views of the same table object. */
export function lobbyTeamRow(table: { dataSets?: (TeamColorRow & { name?: string })[] } | undefined, seed: () => number): TeamColorRow {
  if (!table?.dataSets?.length) return FALLBACK_ROW;
  let row = lobbyRows.get(table);
  if (!row) {
    row = selectLobbyTeamRow(table.dataSets, SeadRandom.fromSeed(seed()));
    lobbyRows.set(table, row);
  }
  return row;
}

/** Web seed for the boot draw: `?teamSeed=<u32>` for reproducible captures, otherwise a fresh random u32. */
export function lobbyTeamSeed(): number {
  const q = typeof location !== "undefined" ? new URLSearchParams(location.search).get("teamSeed") : null;
  if (q !== null && /^\d+$/.test(q)) return Number(q) >>> 0;
  const a = new Uint32Array(1);
  globalThis.crypto.getRandomValues(a);
  return a[0];
}
