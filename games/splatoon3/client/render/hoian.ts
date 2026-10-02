// Hoian_UBER 재질의 웹 근사. 근거: docs/graphics/shaders.md §3.6(팀색 혼합식·calc_color), §3.7(UV), team_color.md §6·§7.3.
// 원본 식 그대로인 부분: 팀색 혼합(team_color_map_type 2/3), emission_color_type 1/2 의 방출 색, calc_color 일부(알베도 대상).
// 근사인 부분: 최종 셰이딩(three MeshStandardMaterial PBR) — 원본 조명 블록(Env/Context/BlitzUBO1·2)은 미해독.
import * as THREE from "three";
import type { MaterialTeamParams } from "./teamcolor.ts";

/** glTF material.extras.fres (graphics_bfres2gltf 출력) 중 쓰는 부분 */
export interface FresMaterial {
  name?: string;
  shader?: { archive?: string; options?: Record<string, string>; samplerAssign?: Record<string, string> };
  renderInfo?: Record<string, unknown>;
  params?: Record<string, { type?: string; value?: unknown }>;
  samplers?: { sampler: string; texture: string; slots: string[] }[];
}

export type TexResolver = (name: string) => Promise<THREE.Texture | null>;

const opt = (f: FresMaterial, k: string, def: string): string => {
  const v = f.shader?.options?.[k];
  return v === undefined || v === "<Default Value>" ? def : v;
};
const pnum = (f: FresMaterial, k: string, def: number): number => {
  const v = f.params?.[k]?.value;
  if (Array.isArray(v)) return typeof v[0] === "number" ? v[0] : def;
  return typeof v === "number" ? v : def;
};
const pvec = (f: FresMaterial, k: string, def: number[]): number[] => {
  const v = f.params?.[k]?.value;
  return Array.isArray(v) && v.length >= 3 ? (v as number[]) : def;
};
/** 슬롯(셰이더 샘플러 이름, 예 _su0)에 꽂힌 텍스처 이름 */
export function textureForSlot(f: FresMaterial, slot: string): string | null {
  return f.samplers?.find((s) => s.slots.includes(slot))?.texture ?? null;
}

/** 이 재질이 팀색을 읽는가 — 아니면 셰이더를 고치지 않는다 */
function usesTeam(f: FresMaterial): boolean {
  const tcm = opt(f, "team_color_map_type", "0");
  const ect = opt(f, "emission_color_type", "0");
  if (tcm === "2" || tcm === "3" || ect === "1" || ect === "2") return true;
  for (let i = 0; i < 4; i++) {
    if (opt(f, `enable_calc_color${i}`, "False") !== "True") continue;
    for (const s of ["A", "B", "C", "D"]) if (opt(f, `blitz_calc_color${i}_${s}`, "0") === "50") return true;
  }
  return false;
}

export interface HoianUniforms {
  myTeamColor: { value: THREE.Vector3 };
  myTeamColorHueComplement: { value: THREE.Vector3 };
}

/** calc_color 소스(§3.6.4) → GLSL 식. 지원하지 않는 소스면 null */
function calcSource(f: FresMaterial, id: string): string | null {
  const n = +id;
  if (n === 0) return "calcAlbedo"; // cTexAlbedo — 혼합 전 알베도 [추정: 알베도 대상 계산에서 현재 값]
  if (n === 50) return "myTeamColor";
  if (n >= 100 && n <= 102) {
    const c = pvec(f, `const_color${n - 100}`, [1, 1, 1, 1]);
    return `vec3(${c[0].toFixed(6)}, ${c[1].toFixed(6)}, ${c[2].toFixed(6)})`;
  }
  if (n === 110 || n === 111) return `vec3(${pnum(f, `const_value${n - 110}`, 0).toFixed(6)})`;
  if (n >= 200 && n < 204) return `calc${n - 200}`;
  return null;
}

function calcChannel(expr: string, ch: string): string {
  switch (+ch) {
    case 0: return expr;
    case 1: return `(vec3(1.0) - ${expr})`;
    case 10: return `vec3((${expr}).x)`;
    case 20: return `vec3((${expr}).y)`;
    case 30: return `vec3((${expr}).z)`;
    case 11: return `vec3(1.0 - (${expr}).x)`;
    default: return expr;
  }
}

/** calc_color0..3 중 알베도를 바꾸는 것만(replace_color 0) GLSL 로. 근거 §3.6.4 표, 미지원 조합은 건너뛰고 목록에 남긴다. */
function calcColorGlsl(f: FresMaterial, skipped: string[]): string {
  let src = "";
  for (let i = 0; i < 4; i++) {
    if (opt(f, `enable_calc_color${i}`, "False") !== "True") continue;
    const replace = opt(f, `blitz_calc_color${i}_replace_color`, "0");
    const type = opt(f, `blitz_calc_color${i}_calc_type`, "0");
    const S = (s: string): string | null => {
      const e = calcSource(f, opt(f, `blitz_calc_color${i}_${s}`, "0"));
      return e === null ? null : calcChannel(e, opt(f, `blitz_calc_color${i}_${s}_channel`, "0"));
    };
    const [A, B, C, D] = [S("A"), S("B"), S("C"), S("D")];
    let e: string | null = null;
    if (type === "1" && A && B) e = `${A} + ${B}`;
    else if (type === "2" && A && B) e = `${A} * ${B}`;
    else if (type === "6" && A && B && C && D) e = `${A} * ${B} + ${C} * ${D}`;
    else if (type === "8" && A && B && C) e = `${A} * ${B} + ${C}`;
    else if (type === "9" && A && B) e = C ? `${A} * ${B} * ${C}` : `${A} * ${B}`; // C 가 텍스처(cTexResource 등)면 생략 — 근사
    else if (type === "11" && A && B && C && D) e = `${A} * ${B} * ${C} * ${D}`;
    if (e === null) {
      if (type !== "0") skipped.push(`calc_color${i}(type ${type})`);
      continue;
    }
    if (opt(f, `blitz_calc_color${i}_clamp01`, "False") === "True") e = `clamp(${e}, 0.0, 1.0)`;
    src += `vec3 calc${i} = ${e};\n`;
    if (replace === "0") src += `diffuseColor.rgb = calc${i};\n`;
    else if (replace !== "100") skipped.push(`calc_color${i}(replace ${replace})`);
  }
  return src;
}

/**
 * glTF PBR 재질에 Hoian_UBER 팀색 식을 덧씌운다. 반환: 팀색 uniform(나중에 팀이 바뀌면 값만 갱신) 또는 null.
 * skipped 에 원본 기능 중 빠진 것을 남긴다.
 */
export function applyHoian(
  mat: THREE.MeshStandardMaterial,
  f: FresMaterial,
  team: MaterialTeamParams,
  tex: TexResolver,
  skipped: string[],
): HoianUniforms | null {
  if (f.shader?.archive && f.shader.archive !== "Hoian_UBER") return null;
  if (!usesTeam(f)) return null;
  const tcm = opt(f, "team_color_map_type", "0");
  const ect = opt(f, "emission_color_type", "0");
  const albedoTex = opt(f, "enable_albedo_tex", "1") !== "False" && opt(f, "enable_albedo_tex", "1") !== "0";
  const albedoColor = pvec(f, "albedo_color", [1, 1, 1, 1]);
  const u: HoianUniforms = {
    myTeamColor: { value: new THREE.Vector3(...team.my_team_color.slice(0, 3)) },
    myTeamColorHueComplement: { value: new THREE.Vector3(...team.my_team_color_hue_complement.slice(0, 3)) },
  };
  const tclUniform = { value: null as THREE.Texture | null };
  const tclName = tcm === "2" ? textureForSlot(f, "_su0") : null;
  if (tcm === "2" && tclName) {
    void tex(tclName).then((t) => {
      tclUniform.value = t;
      if (!t) skipped.push(`_su0 텍스처 ${tclName} 없음`);
      mat.needsUpdate = true;
    });
  }
  if (opt(f, "texcoord_select_teamcolormap", "0") !== "0") skipped.push("texcoord_select_teamcolormap≠0");
  const calc = calcColorGlsl(f, skipped);
  const blendAlpha = pnum(f, "team_color_blend_alpha", 0);
  const blend = pnum(f, "team_color_blend", 0);
  const emiInt = pnum(f, "emission_intensity", 0);
  const emiCol = pvec(f, "emission_color", [1, 1, 1, 1]);
  if (!albedoTex) {
    mat.map = null;
    mat.color.setRGB(1, 1, 1);
  }
  // vUv(TEXCOORD_0) 를 쓰려고 USE_UV 를 켠다 (@types/three 에는 MeshStandardMaterial.defines 가 없음)
  const md = mat as unknown as { defines?: Record<string, string> };
  md.defines = { ...(md.defines ?? {}), USE_UV: "" };
  mat.onBeforeCompile = (sh) => {
    sh.uniforms.myTeamColor = u.myTeamColor;
    sh.uniforms.myTeamColorHueComplement = u.myTeamColorHueComplement;
    sh.uniforms.tclMap = tclUniform;
    const hasTcl = !!tclUniform.value;
    let frag = "";
    frag += `vec3 calcAlbedo = ${albedoTex ? "diffuseColor.rgb" : `vec3(${albedoColor.slice(0, 3).map((x) => x.toFixed(6)).join(", ")})`};\n`;
    if (tcm === "2") {
      // §3.6.1: k = clamp(Tcl.r + team_color_blend_alpha), albedo = mix(base, my_team_color, k)
      frag += `float tcK = clamp(${hasTcl ? "texture2D(tclMap, vUv).r" : "0.0"} + ${blendAlpha.toFixed(6)}, 0.0, 1.0);\n`;
      frag += `diffuseColor.rgb = mix(calcAlbedo, myTeamColor, tcK);\n`;
    } else if (tcm === "3") {
      // §3.6.2: k = clamp(team_color_blend), albedo = mix(albedo_color, my_team_color, k)
      frag += `diffuseColor.rgb = mix(vec3(${albedoColor.slice(0, 3).map((x) => x.toFixed(6)).join(", ")}), myTeamColor, clamp(${blend.toFixed(6)}, 0.0, 1.0));\n`;
    } else frag += `diffuseColor.rgb = calcAlbedo;\n`;
    frag += `calcAlbedo = diffuseColor.rgb;\n`;
    frag += calc;
    sh.fragmentShader = "uniform vec3 myTeamColor;\nuniform vec3 myTeamColorHueComplement;\nuniform sampler2D tclMap;\n" +
      sh.fragmentShader.replace("#include <map_fragment>", "#include <map_fragment>\n" + frag);
    if (ect === "2" || ect === "1") {
      // §3.6.1: emission_color_type 2 = my_team_color, 1 = 혼합된 알베도 × _e0. 세기 = emission_intensity × emission_color (근사: 곱 순서)
      const e = ect === "2" ? "myTeamColor" : "diffuseColor.rgb * emissiveColorTex";
      sh.fragmentShader = sh.fragmentShader.replace(
        "#include <emissivemap_fragment>",
        `${ect === "1" ? "vec3 emissiveColorTex = vec3(1.0);\n#ifdef USE_EMISSIVEMAP\nemissiveColorTex = texture2D(emissiveMap, vEmissiveMapUv).rgb;\n#endif\n" : ""}` +
          `totalEmissiveRadiance = ${e} * vec3(${(emiCol[0] * emiInt).toFixed(6)}, ${(emiCol[1] * emiInt).toFixed(6)}, ${(emiCol[2] * emiInt).toFixed(6)});\n`,
      );
    }
  };
  mat.customProgramCacheKey = () => `hoian:${tcm}:${ect}:${albedoTex}:${!!tclUniform.value}:${calc}`;
  mat.needsUpdate = true;
  return u;
}

export function setTeam(u: HoianUniforms, team: MaterialTeamParams): void {
  u.myTeamColor.value.set(team.my_team_color[0], team.my_team_color[1], team.my_team_color[2]);
  u.myTeamColorHueComplement.value.set(team.my_team_color_hue_complement[0], team.my_team_color_hue_complement[1], team.my_team_color_hue_complement[2]);
}
