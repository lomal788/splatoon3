// Team color derivation re-implemented from main NSO (Splatoon 3 v0). Spec: web/docs/graphics/team_color.md
//   hsvOffset        = 0x7101188334   (RGB->HSV, TeamColorHueDirPeak hue flip, HSV->RGB)
//   deriveTeamColor  = 0x7101174534   (TeamColorOffset rows by type index)
//   inkCorrection    = 0x7101174afc   (index 8 "Model" with no light, 9 "Ink" / 10 "InkBright" with env DirectionalLight)
//   buildTeamSet     = 0x71011743a0   (raw sRGB-ish data color -> pow 2.2 -> 14 colors)
//   buildTeamSets    = 0x7101176830   (TeamColorDataSet -> 4 sets)
// All float math is done in JS doubles; the original is f32 (Math.fround used at the end only). [재구현]

export const TYPE_NAMES = ['Original', 'Pale', 'Bright', 'Dark', 'HueBright', 'HueBrightHalf', 'HueDark', 'HueDarkHalf',
  'Model', 'Ink', 'InkBright', 'InkLame', 'InkLameRare', 'Silhouette'];

// RSDB/TeamColorOffset rows (Brightness, Hue, Saturation) [데이터]
export const OFFSETS = {
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

// SingletonParam game__gfx__parameter__TeamColorHueDirPeak [데이터] (+0x30 BrightPeak, +0x34 DarkPeak)
export const HUE_DIR_PEAK = { bright: 0.20000000298023224, dark: 0.7200000286102295 };

// game::gfx::InkColorCorrection sub-struct (CorrectionInkMain); defaults from ctor 0x71011ae104, data from
// SingletonParam game__gfx__InkColorCorrection [판독+데이터]
export const INK_CORR_MAIN = { lumRate: 0.5, rate1: 0.20000000298023224, rate6: 0.550000011920929, maxSat: 0.9900000095367432, minBright: 0.009999999776482582 };

export function rgbToHsv(r, g, b) {
  // branchless form used by 0x7101188334 / 0x7101174afc
  let K = 0;
  if (g < b) { [g, b] = [b, g]; K = -1; }
  if (r < g) { [r, g] = [g, r]; K = -1 / 3 - K; }
  const mn = Math.min(g, b);
  const chroma = r - mn;
  const h = Math.min(1, Math.abs(K + (g - b) / (chroma * 6 + 1e-20)));
  const s = Math.min(1, Math.max(0, chroma / (r + 1e-20)));
  return [h, s, r];
}

function hsvToRgbClamped(h, s, v, alphaIn) {
  if (s === 0) return [v, v, v, 1]; // original: no [0,1] clamp and alpha forced to 1 when s == 0
  const hh = h % 1; // fmodf(h, 1) keeps sign like C
  const x = hh / (1 / 6);
  const i = Math.trunc(x); // fcvtzs (toward zero); then 'cmp w8,#4; b.hi' unsigned: i<0 or i>4 -> default case
  const f = x - i;
  const p = v * (1 - s), q = v * (1 - s * f), t = v * (1 - s * (1 - f));
  let rgb;
  switch (i < 0 || i > 4 ? 5 : i) {
    case 0: rgb = [v, t, p]; break;
    case 1: rgb = [q, v, p]; break;
    case 2: rgb = [p, v, t]; break;
    case 3: rgb = [p, q, v]; break;
    case 4: rgb = [t, p, v]; break;
    default: rgb = [v, p, q];
  }
  const c = (x) => (x >= 0 ? Math.min(x, 1) : 0);
  return [c(rgb[0]), c(rgb[1]), c(rgb[2]), alphaIn];
}

// 0x7101188334(hueOff, satOff, brightOff, out, in)
export function hsvOffset(hueOff, satOff, brightOff, rgba, peak = HUE_DIR_PEAK) {
  const [h, s, v] = rgbToHsv(rgba[0], rgba[1], rgba[2]);
  if (peak && peak.bright < h && h < peak.dark) hueOff = -hueOff;
  const s2 = Math.min(1, Math.max(0, satOff - Math.abs(brightOff) + s));
  const v2 = v + brightOff <= 0 ? 0 : v + brightOff;
  return hsvToRgbClamped(h + hueOff, s2, v2, rgba[3]);
}

const labF = (t) => (t >= 0.008856452 ? Math.cbrt(t) : t * 7.7870374 + 0.13793103);
const lStar = (r, g, b) => labF(r * 0.2126 + g * 0.7152 + b * 0.0722) * 116 - 16;

// game::gfx::InkColorCorrectionSSS (root +0x38, "CorrectionInkSSS"): ctor 0x71011af154 defaults, reflection 0x71011af210
// (+0x30 "BrightnessOffset", +0x34 "BrightnessOffsetLuminance"). SingletonParam data has no CorrectionInkSSS -> defaults [판독+데이터]
export const INK_CORR_SSS = { brightnessOffset: 0.10000000149011612, brightnessOffsetLuminance: 0.5 };

// 0x7101174afc(out, in, light, _, bright). light = { color:[r,g,b], intensity, skyUp:[r,g,b]|null } or null.
//   Model (index 8): light = null  -> t = 0
//   Ink/InkBright (9/10): light = first agl::env::DirectionalLight of the active env (DiffuseColor +0x128, Intensity +0x1a0),
//   flag 1 -> skyUp = SH irradiance evaluated at (0,1,0) (global 0x71058186e4, written by callback 0x71011767f8) [판독]
export function inkCorrection(rgba, light = null, bright = false, P = INK_CORR_MAIN, S = INK_CORR_SSS) {
  const [h, s, v] = rgbToHsv(rgba[0], rgba[1], rgba[2]);
  let t = 0;
  if (light) {
    t = light.intensity * (lStar(light.color[0], light.color[1], light.color[2]) / 100);
    if (light.skyUp) t += lStar(light.skyUp[0], light.skyUp[1], light.skyUp[2]) / 100;
  }
  const dark = (lStar(rgba[0], rgba[1], rgba[2])) / -100 + 1;
  const k = Math.min(1, Math.max(0, 1 - P.lumRate * dark));
  let r = (P.rate1 * 6 - P.rate6) / 5 + ((P.rate6 - P.rate1) / 5) * t;
  r = r < 0 ? 0 : Math.min(r, P.rate6);
  let d = Math.min(v, r * k);
  if (bright) d = d - S.brightnessOffset * (1 - S.brightnessOffsetLuminance * dark);
  const v2 = Math.max(P.minBright, Math.min(1, Math.max(0, v - d)));
  const s2 = Math.min(s, P.maxSat);
  return hsvToRgbClamped(h, s2, v2, rgba[3]);
}

// index 8 "Model": light param (color 0, scale 0, flag 0) -> t = 0
export function modelCorrection(rgba, P = INK_CORR_MAIN) {
  return inkCorrection(rgba, null, false, P);
}

// envLight: { color, intensity, skyUp } of the active env (see inkCorrection). Without it Ink/InkBright stay unresolved (null):
// the original leaves the output untouched when no env / no DirectionalLight exists (0x7101174534 early return).
export function deriveTeamColor(linear, index, hueExtra = 0, envLight = null) {
  const name = TYPE_NAMES[index];
  if (index === 0) return linear.slice();
  if (index === 8) return modelCorrection(linear);
  if (index === 9 || index === 10) return envLight ? inkCorrection(linear, envLight, index === 10) : null;
  const o = OFFSETS[name];
  if (!o) return null;
  let hue = o.h;
  if (Math.abs(hue) > 1.1920929e-07) hue = hue > 0 ? hue + hueExtra : hue - hueExtra;
  return hsvOffset(hue, o.s, o.b, linear);
}

// 0x71011743a0: raw data color -> linear (pow 2.2, alpha kept) -> 14 colors
export function buildTeamSet(raw, hueExtra = 0, envLight = null) {
  const lin = [Math.pow(raw[0], 2.2), Math.pow(raw[1], 2.2), Math.pow(raw[2], 2.2), raw[3]];
  return { raw: raw.slice(), linear: lin, colors: TYPE_NAMES.map((_, i) => deriveTeamColor(lin, i, hueExtra, envLight)) };
}

const TAGS = ['VersusRegular', 'VersusOption', 'Mission', 'MissionOption', 'VersusTricolor', 'VersusTricolorOption', 'Coop', 'CoopOption', 'Gambit', 'Blitz'];

// 0x7101176830(mgr, data, swap): sets [0..3]
export function buildTeamSets(row, swap = false, envLight = null) {
  const c = (k) => [row[k].R, row[k].G, row[k].B, row[k].A];
  const en = !!row.HueOffsetEnable;
  const tag = TAGS.indexOf(row.Tag);
  const a = c('AlphaTeamColor'), b = c('BravoTeamColor');
  const set2 = (tag & ~1) === 4 ? c('CharlieTeamColor') : c('NeutralColor');
  return [
    buildTeamSet(swap ? b : a, en ? row.AlphaHueOffset : 0, envLight),   // hue offset is NOT swapped (as in original)
    buildTeamSet(swap ? a : b, en ? row.BravoHueOffset : 0, envLight),
    buildTeamSet(set2, en ? row.CharlieHueOffset : 0, envLight),
    buildTeamSet(c('NeutralColor'), en ? row.NeutralHueOffset : 0, envLight),
  ];
}

// 0x7101103490: material params written for Hoian_UBER materials. provider(i) = set.colors[i]
export function materialTeamParams(set, renderInfo = {}) {
  const P = {
    my_team_color: set.colors[8],
    my_team_color_bright: set.colors[2],
    my_team_color_hue_bright: set.colors[4],
    my_team_color_hue_bright_half: set.colors[5],
    my_team_color_hue_dark: set.colors[6],
    my_team_color_hue_dark_half: set.colors[7],
    my_team_color_hue_complement: hsvOffset(0.5, 0, 0, set.linear),
  };
  const type = renderInfo.my_team_color_type;
  const hueOff = +renderInfo.my_team_color_hue_offset || 0;
  if (type === '7') {
    const bo = +renderInfo.my_team_color_bright_offset || 0;
    if (hueOff !== 0 || bo !== 0) P.my_team_color = hsvOffset(hueOff, 0, bo !== 0 ? Math.max(-1, bo) : 0, set.linear);
  } else if (type === '10') {
    P.my_team_color_hue_complement = hsvOffset(hueOff, 0, 0, set.linear);
  } else if (type === '8') {
    P.my_team_color = set.colors[9]; // Ink [미확정 값]
  }
  return P;
}
