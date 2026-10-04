// r11 gfx-diff 광원: Hoian_Proc 원본 셰이더(Negate 보완 역번역)를 glsl_eval 로 실행해 fixture 를 만든다.
// 웹 쪽은 tests/r11_gfx_diff_light.test.mjs 가 같은 입력·같은 mock 텍스처로 웹 GLSL 을 실행해 대조한다.
// 사용: node web/tools/r11_gfx_diff_light_shaders.mjs
import { readFileSync, writeFileSync } from "node:fs";
import { Program, Bits, F } from "./glsl_eval.mjs";
import { vanDerCorput, illuminateUBO, nativeLayerRoughness } from "../games/splatoon3/client/render/env_prefilter.ts";
import { lonLatToDir } from "../games/splatoon3/client/render/map.ts";

const ROOT = new URL("../../", import.meta.url);
const P = new URL("analysis/gfx_r11/proc_fixed/", ROOT);

/** 두 쪽이 공유하는 해석적 mock 텍스처(내용 동등은 가정이 아니라 입력 정의). */
export const MOCK = {
  vdc: uv => [vanDerCorput(Math.floor(uv[0] * 256) + 256 * Math.floor(uv[1] * 4)), 0, 0, 0],
  cube: (d, lod = 0) => {
    const l = Math.hypot(d[0], d[1], d[2]), n = d.map(x => x / l);
    return [F(.3 + .2 * n[1] + .05 * lod + .1 * n[0] * n[2]), F(.34 + .15 * n[0] - .02 * lod), F(.45 + .1 * n[2] + .3 * Math.max(0, n[1]) ** 4), 1];
  },
  highlight: uv => { const r = Math.hypot(uv[0] - .5, uv[1] - .5); return [F(Math.max(0, 1 - 4 * r)), F(Math.max(0, 1 - 5 * r)), F(Math.max(0, 1 - 3 * r)), 1]; },
};
export const DIRS = [[1, .2, -.3], [-1, .4, .1], [.2, 1, .3], [.1, -1, -.2], [.3, -.1, 1], [-.2, .3, -1]];
export const BRDF_POINTS = [[.1, .1], [.5, .5], [.9, .2], [.3, .8], [1, .05], [.05, 1], [.7, .35], [.2, .6]];
export const LAYERS = [0, 3, 7, 11];
export const SH_IDS = [0, 1, 127, 128, 8191, 16383, 16384, 20000, 32768 + 777, 49152 + 5000, 65536 + 9999, 81920 + 16383];

function prefilterOrig(file, param0, ubo) {
  const p = new Program(readFileSync(new URL(file, P), "utf8"));
  const g = { undef: 0, support_buffer: {}, fp_c1: {}, cVanDerCorputMap: MOCK.vdc, cBase: MOCK.cube, cHighlight: MOCK.highlight,
    RegisterUBO: { data: Object.assign(Array.from({ length: 32 }, () => [0, 0, 0, 0]), { 18: param0 }), cParam0: [param0] } };
  for (let i = 0; i < 6; i++) { g["in_attr" + i] = [...DIRS[i], 0]; g["out_attr" + i] = [0, 0, 0, 0]; }
  if (ubo) {
    const data = Array.from({ length: 40 }, () => [0, 0, 0, 0]); ubo.lights.forEach((l, i) => { data[2 + i] = l; });
    g.IlluminateUBO = { cLightParam: [...ubo.param, 0], cLightColor: ubo.color, data };
  }
  p.run(g);
  return DIRS.map((_, i) => g["out_attr" + i].slice(0, 3));
}

function main() {
  const env = JSON.parse(readFileSync(new URL("web/games/splatoon3/assets/maps/Lby_Lobby00/env.json", ROOT), "utf8"));
  const ubo = illuminateUBO(env, lonLatToDir(-3, 34.5), [0.6705883145332336, 0.8509804010391235, 1, 1]);
  const brdfProg = new Program(readFileSync(new URL("GGXEnvBRDF__default.pixel.glsl", P), "utf8"));
  const brdf = BRDF_POINTS.map(([nov, r]) => { const g = { in_attr0: [nov, r, 0, 0], out_attr0: [0, 0, 0, 0], cVanDerCorputMap: MOCK.vdc, support_buffer: {}, fp_c1: {} }; brdfProg.run(g); return { nov, r, out: g.out_attr0.slice(0, 2) }; });
  const illumParam0 = [.05, 4, 1024, 1];
  const illuminate = { param0: illumParam0, ubo, out: prefilterOrig("GGXPrefilterEnvMap__MRT-1_FILTER_TYPE-2_ILLUMINATE-1.pixel.glsl", illumParam0, ubo) };
  const layers = LAYERS.map(l => { const param0 = [nativeLayerRoughness(l), 4, 1024, 400]; return { layer: l, param0, out: prefilterOrig("GGXPrefilterEnvMap__MRT-1_FILTER_TYPE-2_ILLUMINATE-0.pixel.glsl", param0, null) }; });
  const shProg = new Program(readFileSync(new URL("sh/IrradianceCubeMapAllToSH__CUBE_MAP_WIDTH_INT-128.pixel.glsl", P), "utf8"));
  const sh = SH_IDS.map(id => {
    const g = { undef: 0, support_buffer: {}, fp_c1: {}, CubeMapAllToSHContext: { cMipLevel: [1, 0, 0, 0] }, cTexture0: MOCK.cube, in_attr0: [new Bits(id), 0, 0, 0] };
    for (let i = 0; i < 7; i++) g["out_attr" + i] = [0, 0, 0, 0];
    shProg.run(g);
    return { id, out: Array.from({ length: 7 }, (_, i) => g["out_attr" + i]) };
  });
  const out = new URL("web/games/splatoon3/tests/fixtures/r11_gfx_diff_light_shader_native.json", ROOT);
  writeFileSync(out, JSON.stringify({ source: "analysis/gfx_r11/proc_fixed (Hoian_Proc, Negate-corrected prog-sharc)", programs: ["GGXEnvBRDF", "GGXPrefilterEnvMap MRT1 FILTER2 ILLUMINATE1/0", "IrradianceCubeMapAllToSH W128"], brdf, illuminate, layers, sh }));
  console.log("brdf", brdf.length, "illuminate faces", illuminate.out.length, "layers", layers.length, "sh", sh.length);
}
if (process.argv[1] && import.meta.url.endsWith(process.argv[1].replace(/\\/g, "/").split("/").pop())) main();
