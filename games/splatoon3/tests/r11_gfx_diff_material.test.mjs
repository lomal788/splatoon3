// r11 gfx-diff 재질: 원본 Hoian_UBER 맵 프로그램(946/917/1714/1689, Negate 보완 재역번역)과
// web forward.ts 가 실제로 만드는 GLSL 을 같은 입력으로 glsl_eval 에서 실행해 출력 색을 비교한다.
// 입력 = 사격장 실제 재질 텍셀(원본 BC 디코드)·베이크 텍셀·주광·카메라. 그림자(SPP)·투영 그림자는 1/0으로 둔다(그림자 담당 범위).
// 환경 BRDF LUT 와 prefilter 내용은 두 쪽 모두 같은 해석 함수로 둔다(내용 동등성은 광원 담당 범위).
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import * as THREE from 'three';
import {compileGLSL, ubo, texFn} from './glsl_eval.mjs';
import {applyForward} from '../client/render/forward.ts';
import {LightingState} from '../client/render/lighting.ts';

const fixture = name => readFileSync(new URL(`./fixtures/r11_gfx_diff_material/${name}`, import.meta.url), 'utf8');
const nz = v => { const l = Math.hypot(...v); return v.map(x => x / l); };
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const dot = (a, b) => a.reduce((s, x, i) => s + x * b[i], 0);
const f32 = Math.fround, neg1 = (() => { const d = new DataView(new ArrayBuffer(4)); d.setInt32(0, -1); return d.getFloat32(0); })();
const bitsF = (i, unsigned = false) => { const d = new DataView(new ArrayBuffer(4)); unsigned ? d.setUint32(0, i) : d.setInt32(0, i); return d.getFloat32(0); };

const L = nz([0.0431, -0.5664, -0.8230]), CAM = [11.0, 3.69, -2.67], LIGHTC = [6.706, 8.51, 10.0];
// Web capture SH (analysis/gfx_r11/probe/env1.json): cAr,cAg,cAb,cBr,cBg,cBb,cC.
const SH = [[0.2390, 0.4383, 0.2903, 0.3681], [0.2843, 0.5262, 0.3576, 0.4406], [0.3943, 0.6948, 0.5418, 0.5666],
  [0.2600, 0.3628, 0.1133, 0.1492], [0.3078, 0.4449, 0.1331, 0.1918], [0.4165, 0.6469, 0.1784, 0.3212], [-0.0529, -0.0647, -0.0875, 1]];
const BAKE = {shScale: 1.875, shOff: 0.71875, aoScale: 1.0625, aoOff: 0.125, aoMain: 0.03125};
const FOG = {dcol: [0.749, 0.765, 0.698, 0.25], dstart: 10, dend: 1000, scat: 0.3125, hcol: [0.098, 0.129, 0.141, 0.6875], hstart: 15, hend: 90};
const brdf = (nov, r) => [0.9 * (1 - r) * nov + 0.05, 0.08 * r + 0.02 * (1 - nov)];
const prefil = (d, layer) => { d = nz(d); return [0.30 + 0.20 * d[1] + 0.02 * layer, 0.34 + 0.15 * d[0], 0.45 + 0.10 * d[2] - 0.01 * layer, 1]; };
const GRID = {origin: [-100, -0.5, -100], inv: [0.1, 1, 0.1]};

// Bake texels sampled at the real range points through visual.glb uv1 x bindings (analysis/gfx_r11/diff/bake_sample.py).
const SAMPLES = [
  {name: 'Wall02 far wall (25,3,43)', prog: 946, P: [25, 3, 42.99], N: [0, 0, -1], T: [-1, 0, 0, 1], alb: [0.2281, 0.2280, 0.2279], rgh: 0.704, mtl: 0, nrm: [0, 0], ao: 0.668, g: 0, bl: [0.0582, 0.0582, 0.0292].map(v => v / 32)},
  {name: 'Wall02 left wall (42.4,3,30)', prog: 946, P: [42.39, 3, 30], N: [-1, 0, 0], T: [0, 0, 1, 1], alb: [0.2281, 0.2280, 0.2279], rgh: 0.70, mtl: 0, nrm: [0.03, -0.02], ao: 0.721, g: 0, bl: [0.0153, 0.0152, 0.0128].map(v => v / 32)},
  {name: 'Floor (24,0,12)', prog: 946, P: [24, 0, 12], N: [0, 1, 0], T: [1, 0, 0, 1], alb: [0.0114, 0.0112, 0.0114], rgh: 0.311, mtl: 0, nrm: [-0.01, 0.02], ao: 0.909, g: 0, bl: [0.7142, 0.5876, 0.419].map(v => v / 32)},
  {name: 'Floor + spot light', prog: 946, P: [24, 0, 12], N: [0, 1, 0], T: [1, 0, 0, 1], alb: [0.0114, 0.0112, 0.0114], rgh: 0.311, mtl: 0, nrm: [0, 0], ao: 0.909, g: 0.3, bl: [0.7142, 0.5876, 0.419].map(v => v / 32),
    dyn: [{pos: [22, 6, 14], col: [3, 2.5, 1.5], invR: 1 / 15, damp: 1.2, spot: true, dir: [0, -1, 0.1], cosc: Math.cos(0.6), adamp: 1}]},
  {name: 'Truss underside', prog: 917, P: [20, 14.9, 10], N: [0, -1, 0], T: [1, 0, 0, 1], alb: [0.9127, 0.7886, 0.0002], rgh: 0.244, mtl: 0, nrm: [0, 0], ao: 0.47, g: 0.05, bl: [0.142, 0.127, 0.070].map(v => v / 32)},
  {name: 'Truss top lit', prog: 917, P: [20, 19.4, 10], N: [0, 1, 0], T: [1, 0, 0, 1], alb: [0.9127, 0.7886, 0.0002], rgh: 0.244, mtl: 0, nrm: [0.05, 0], ao: 0.3, g: 1, bl: [0.2, 0.18, 0.1].map(v => v / 32)},
  {name: 'mLobbyWoodBox (16.4,2,29)', prog: 1714, P: [16.4, 2, 29], N: [0, 0, -1], T: [-1, 0, 0, 1], alb: [0.3517, 0.2652, 0.1523], rgh: 0.6, mtl: 0.2, mtlMap: true, nrm: [0, 0], ao: 0.656, g: 0.091, bl: [0.1265, 0.1192, 0.0732].map(v => v / 32)},
  {name: 'MetalPanel (1689)', prog: 1689, P: [30, 8, 42.9], N: [0, 0, -1], T: [-1, 0, 0, 1], alb: [0.02, 0.02, 0.03], rgh: 0.4, mtl: 0.8, mtlMap: true, nrm: [0, 0], ao: 0.2, g: 0, bl: [0.05, 0.05, 0.05].map(v => v / 32)},
];

const v4 = a => [a[0], a[1], a[2], a[3] ?? 0];
function originalOutput(s) {
  const prog = compileGLSL(fixture(`p${s.prog}.frag`));
  const B0 = []; B0[18] = [0.05, 1, 0, 0]; B0[21] = [0, 0, 0, 0.3];
  B0[36] = [-BAKE.shOff * BAKE.shScale, BAKE.shScale, 1e6, 0]; B0[37] = [BAKE.aoScale, -BAKE.aoOff * BAKE.aoScale, 0, BAKE.aoMain];
  B0[53] = [FOG.scat, 1 / (FOG.dend - FOG.dstart), FOG.scat, 0]; B0[54] = [1, 0.5, 1, 0];
  const E = []; E[5] = [...LIGHTC, 10]; E[23] = [...L, 0]; E[10] = FOG.dcol; E[11] = [0, 0, 0, -FOG.dstart / (FOG.dend - FOG.dstart)]; E[12] = [1 / (FOG.dend - FOG.dstart), 0, 0, 0];
  E[13] = FOG.hcol; E[14] = [0, -1, 0, -FOG.hstart / (FOG.hend - FOG.hstart)]; E[15] = [1 / (FOG.hend - FOG.hstart), 0, 0, 0];
  for (let i = 0; i < 7; i++) E[25 + i] = SH[i];
  const C = []; C[11] = [0, 0, 0, CAM[0]]; C[12] = [0, 0, 0, CAM[1]]; C[13] = [0, 0, 0, CAM[2]]; C[15] = [0.001, 0, 0, 0]; C[41] = [0, 0, 0, 0];
  const B2 = []; for (let c = 0; c < 400; c++) B2[c] = [neg1, 0, 0, 0];
  B2[0x226] = [...GRID.origin, 0]; B2[0x227] = [...GRID.inv, 0];
  (s.dyn ?? []).forEach((l, i) => {
    const cx = Math.max(0, Math.min(19, Math.trunc((s.P[0] - GRID.origin[0]) * GRID.inv[0]))), cz = Math.max(0, Math.min(19, Math.trunc((s.P[2] - GRID.origin[2]) * GRID.inv[2])));
    B2[cz * 20 + cx] = [bitsF(0xffffff00 | i, true), 0, 0, 0];
    B2[400 + i] = [...l.col, 1]; B2[430 + i] = [l.invR, l.damp, l.cosc, l.adamp]; B2[460 + i] = [...l.pos, 0]; B2[490 + i] = [...nz(l.dir), 0]; B2[520 + i] = [bitsF(l.spot ? 1 : 0), 0, 0, 0];
  });
  const tex = {
    cBlitzWallPaintGrid: texFn(() => [0, 0, 0, 0]), cTexNormal: texFn(() => [...s.nrm, 0, 1]), cTexAlbedo: texFn(() => [...s.alb, 1]),
    cTexRoughness: texFn(() => [s.rgh, 0, 0, 1]), cTexMetalness: texFn(() => [s.mtl, 0, 0, 1]),
    cGSysShadowPrePass: texFn(() => [1, 1, 1, 1]), cGSysProjection0: texFn(() => [1, 1, 1, 1]),
    cTexBakeAOShadow: texFn(() => [s.ao, s.g, 0, 1]), cTexBakeLight: texFn(() => [...s.bl, 1]),
    // Native LUT is sampled at (NoV, -roughness) with repeat; web stores the same values on row r (env_prefilter.ts policy).
    cEnvBRDFMap: texFn(uv => [...brdf(uv[0], 1 - (uv[1] - Math.floor(uv[1]))), 0, 0]),
    cPrefilEnvMapArray: texFn(uv => prefil(uv.slice(0, 3), uv[3])),
  };
  const g = prog.run({
    in_attr0: [0.3, 0.6, 0, 0], in_attr1: [...s.N, 0], in_attr2: s.T, in_attr3: [...s.P, -20], in_attr4: [...s.P.map((v, i) => v - CAM[i]), 0],
    in_attr5: [0, 0, 0.5, 1], in_attr6: [0.1, 0.1, 0.1, 0.1], in_attr7: [0, 0, 0, 1], in_attr8: [0, 0, 1, 0], in_attr9: [1, 0, 0, 0], in_attr10: [0.5, 0.5, 0.5, 0.5],
    BlitzUBO0: ubo(B0), BlitzUBO2: ubo(B2), Env: ubo(E), Context: ubo(C), Mat: {metalness: s.mtlMap ? 0 : s.mtl}, gl_FragCoord: [0, 0, 0.5, 1], output_color: [[0, 0, 0, 0]], ...tex,
  });
  return g.output_color[0].slice(0, 3);
}

// Minimal MeshStandardMaterial fragment around the chunks forward.ts replaces (three r180 order).
const TEMPLATE = `
uniform mat4 viewMatrix; uniform vec3 cameraPosition;
uniform vec3 hAlbedo,hNormal; uniform float hRough,hMetal;
vec3 inverseTransformDirection(in vec3 dir,in mat4 matrix){return normalize((vec4(dir,0.)*matrix).xyz);}
vec3 reflect(vec3 i,vec3 n){return i-2.*dot(n,i)*n;}
void main(){
  vec4 diffuseColor=vec4(hAlbedo,1.);float roughnessFactor=hRough;float metalnessFactor=hMetal;
  vec3 normal=hNormal;vec3 totalEmissiveRadiance=vec3(0.);
  vec3 rl_directDiffuse=vec3(0.),rl_indirectDiffuse=vec3(0.),rl_directSpecular=vec3(0.),rl_indirectSpecular=vec3(0.);
  #include <lights_fragment_begin>
  #include <lights_fragment_maps>
  #include <lights_fragment_end>
  #include <aomap_fragment>
  vec3 outgoingLight=rl_directDiffuse+rl_indirectDiffuse+rl_directSpecular+rl_indirectSpecular+totalEmissiveRadiance;
  gl_FragColor=vec4(outgoingLight,diffuseColor.a);
  #include <fog_fragment>
}`;

function webShader() {
  const lighting = new LightingState();
  const mat = new THREE.MeshStandardMaterial();
  const bakeTex = new THREE.DataTexture(new Uint16Array(4), 1, 1, THREE.RGBAFormat, THREE.HalfFloatType);
  const bake = {ao: {texture: bakeTex, st: new THREE.Vector4(1, 1, 0, 0), type: 3, tableIndex: 2}, light: {texture: bakeTex, st: new THREE.Vector4(1, 1, 0, 0), type: 4, tableIndex: 3}};
  applyForward(mat, {shader: {archive: 'Hoian_UBER', options: {}}}, lighting, bake);
  const sh = {uniforms: {}, vertexShader: '#include <worldpos_vertex>\n#include <uv_vertex>', fragmentShader: TEMPLATE};
  mat.onBeforeCompile(sh, null);
  return {source: sh.fragmentShader.replace(/reflectedLight\./g, 'rl_'), lighting};
}

function webOutput(s, web) {
  const prog = compileGLSL(web.source);
  // three normalmap_fragment_maps with vertex tangents: mapN=tex*2-1 (KTX2 keeps the rebuilt z), normal=normalize(mat3(T,B,N)*mapN).
  const Ng = nz(s.N), T = nz(s.T.slice(0, 3)), B = nz(cross(Ng, T).map(v => v * s.T[3]));
  const mapN = [s.nrm[0], s.nrm[1], Math.sqrt(Math.max(0, 1 - s.nrm[0] ** 2 - s.nrm[1] ** 2))];
  const n = nz([0, 1, 2].map(k => T[k] * mapN[0] + B[k] * mapN[1] + Ng[k] * mapN[2]));
  const eye = Object.assign([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]], {isMat: true});
  const rows = web.lighting.env.rows.map(r => [r.x, r.y, r.z, r.w]);
  const atlas = texFn(uv => {
    const layer = rows.findIndex(r => uv[1] >= r[0] && uv[1] < r[0] + r[1]), r = rows[layer];
    const f = Math.min(5, Math.floor(uv[0] / r[2])), a = (uv[0] / r[2] - f) * 2 - 1, b = (uv[1] - r[0]) / r[1] * 2 - 1;
    const d = [[1, b, -a], [-1, b, a], [a, 1, -b], [a, -1, b], [a, b, 1], [-a, b, -1]][f];
    return prefil(d, layer);
  });
  const dyn = s.dyn ?? [], grid = {fetch: p => {
    const cx = Math.max(0, Math.min(19, Math.trunc((s.P[0] - GRID.origin[0]) * GRID.inv[0]))), cz = Math.max(0, Math.min(19, Math.trunc((s.P[2] - GRID.origin[2]) * GRID.inv[2])));
    return [(p[0] === cx && p[1] === cz && dyn.length) ? (0xffffff00 | 0) >>> 0 : 0xffffffff, 0, 0, 0];
  }, sample: () => [0, 0, 0, 0], size: () => [20, 20]};
  const pad = (a, n) => Array.from({length: n}, (_, i) => a[i] ?? [0, 0, 0, 0]);
  const g = prog.run({
    viewMatrix: eye, cameraPosition: CAM, hAlbedo: s.alb, hNormal: n, hRough: s.rgh, hMetal: s.mtl,
    hWorldPosition: s.P, hBakeUV: [0.5, 0.5, 0.5, 0.5],
    hBakeAO: texFn(() => [s.ao, s.g, 0, 1]), hBakeLightTex: texFn(() => [...s.bl, 1]),
    hLightColor: LIGHTC, hLightDirection: L, hSH: SH.map(v => v4(v)),
    hBakeShadow: [BAKE.shScale, -BAKE.shOff * BAKE.shScale, BAKE.aoScale, -BAKE.aoOff * BAKE.aoScale], hAOMain: BAKE.aoMain,
    hDepthFog: FOG.dcol, hDepthRange: [FOG.dstart, FOG.dend, FOG.scat], hHeightFog: FOG.hcol, hHeightRange: [FOG.hstart, FOG.hend],
    hGrid: grid, hGridOrigin: GRID.origin, hInvCell: GRID.inv,
    hDynColor: pad(dyn.map(l => [...l.col, 1]), 30), hDynAtt: pad(dyn.map(l => [l.invR, l.damp, l.cosc, l.adamp]), 30),
    hDynPos: pad(dyn.map(l => [...l.pos, l.spot ? 1 : 0]), 30), hDynDir: pad(dyn.map(l => [...nz(l.dir), 0]), 30),
    hShadowAvailable: 0, hProjShadowAvailable: 0, hProjShadowDensity: 0, hShadowSplits: [1.5, 20, 60], hShadowFarFade: [40, 0.05],
    hPrefilAtlas: atlas, hEnvBRDF: texFn(uv => [...brdf(uv[0], uv[1]), 0, 0]), hPrefilRows: rows, hPrefilAvailable: 1,
  });
  return g.gl_FragColor.slice(0, 3);
}

test('Hoian 맵 재질 946/917/1714/1689: 원본 역번역 셰이더 출력 = web forward.ts GLSL 출력(같은 입력, 사격장 표본 8개)', () => {
  const web = webShader();
  for (const s of SAMPLES) {
    const o = originalOutput(s), w = webOutput(s, web);
    for (let k = 0; k < 3; k++) {
      assert.ok(Number.isFinite(o[k]) && o[k] > 0, `${s.name}: original channel ${k} = ${o[k]}`);
      assert.ok(Math.abs(o[k] - w[k]) <= 2e-4 * Math.max(1, Math.abs(o[k])), `${s.name} ch${k}: original ${o[k]} web ${w[k]}`);
    }
  }
});

test('베이크 빛은 (rgb·a·32) 한 번, 간접(1−occAO)·직접(그림자) 두 곳에 들어간다: 원본 셰이더에서 베이크 빛만 바꾼 차분 = web 차분', () => {
  const web = webShader(), s = SAMPLES[0], bright = {...s, bl: s.bl.map(v => v * 4)};
  const dO = originalOutput(bright).map((v, i) => v - originalOutput(s)[i]), dW = webOutput(bright, web).map((v, i) => v - webOutput(s, web)[i]);
  for (let k = 0; k < 3; k++) assert.ok(Math.abs(dO[k] - dW[k]) <= 1e-6, `bake delta ch${k}: ${dO[k]} vs ${dW[k]}`);
  // Hue of the far-wall bake texel (R=G≈2B) is carried unchanged into the shaded delta on both sides.
  assert.ok(dO[0] / dO[2] > 1.9 && dW[0] / dW[2] > 1.9);
});

import {applyInkSurface} from '../client/render/ink_surface.ts';
import {inkSurfaceFrame} from '../client/render/ink_surface_math.ts';
import {PREFILTER_INK_TILE, PREFILTER_ATLAS} from '../client/render/env_prefilter.ts';
const INK = [[0.6, 0.03, 0.2], [0.05, 0.4, 0.5], [0.3, 0.3, 0.05]], INKB = [[0.9, 0.2, 0.4], [0.2, 0.7, 0.8], [0.6, 0.6, 0.2]];
const STEP = [1 / 3200, 1 / 3200], FRAME = 123, EMI = 0.12;
const paint = uv => { const t = uv[0] * 40 + uv[1] * 25; return [0.75 + 0.1 * Math.sin(t), 0.05 + 0.02 * Math.cos(t), 0.04, 1]; };

function inkOriginal(s, envLayerFree) {
  const prog = compileGLSL(fixture('p946.frag')), fr = inkSurfaceFrame(FRAME);
  const B0 = []; B0[18] = [0.05, 1.8, EMI, 0]; B0[19] = [0.015, 0, 0.5, 0]; B0[20] = fr; B0[21] = [0, 0, 0, 0.3]; B0[22] = [0, 0, STEP[0], STEP[1]];
  B0[45] = [0, 0.625, 0.875, 0];
  // 1185c7c: [3]/[4] team0, [10]/[11] team1, [62]/[63] team2 Ink/InkBright (reference_ink_surface.md §4).
  [B0[3], B0[10], B0[62]] = INK.map(v4); [B0[4], B0[11], B0[63]] = INKB.map(v4);
  B0[36] = [-BAKE.shOff * BAKE.shScale, BAKE.shScale, 1e6, 0]; B0[37] = [BAKE.aoScale, -BAKE.aoOff * BAKE.aoScale, 0, BAKE.aoMain]; B0[53] = [FOG.scat, 1 / (FOG.dend - FOG.dstart), FOG.scat, 0]; B0[54] = [1, 0.5, 1, 0];
  const E = []; E[5] = [...LIGHTC, 10]; E[23] = [...L, 0]; E[10] = FOG.dcol; E[11] = [0, 0, 0, -FOG.dstart / (FOG.dend - FOG.dstart)]; E[12] = [1 / (FOG.dend - FOG.dstart), 0, 0, 0];
  E[13] = FOG.hcol; E[14] = [0, -1, 0, -FOG.hstart / (FOG.hend - FOG.hstart)]; E[15] = [1 / (FOG.hend - FOG.hstart), 0, 0, 0]; for (let i = 0; i < 7; i++) E[25 + i] = SH[i];
  const C = []; C[11] = [0, 0, 0, CAM[0]]; C[12] = [0, 0, 0, CAM[1]]; C[13] = [0, 0, 0, CAM[2]]; C[15] = [0.001, 0, 0, 0]; C[41] = [0, 0, 0, 0];
  const B2 = []; for (let c = 0; c < 400; c++) B2[c] = [neg1, 0, 0, 0]; B2[0x226] = [...GRID.origin, 0]; B2[0x227] = [...GRID.inv, 0];
  const layers = [];
  const g = prog.run({
    in_attr0: [0.3, 0.6, 0, 0], in_attr1: [...s.N, 0], in_attr2: s.T, in_attr3: [...s.P, -20], in_attr4: [...s.P.map((v, i) => v - CAM[i]), 0],
    in_attr5: [0, 0, 0.5, 1], in_attr6: [0.41, 0.37, 0, 0], in_attr7: [0, 0, 0, 1], in_attr8: [0, 0, 1, 0], in_attr9: [...s.paintT, 0], in_attr10: [0.5, 0.5, 0.5, 0.5],
    BlitzUBO0: ubo(B0), BlitzUBO2: ubo(B2), Env: ubo(E), Context: ubo(C), Mat: {metalness: 0}, gl_FragCoord: [0, 0, 0.5, 1], output_color: [[0, 0, 0, 0]],
    cBlitzWallPaintGrid: texFn(paint), cTexNormal: texFn(() => [...s.nrm, 0, 1]), cTexAlbedo: texFn(() => [...s.alb, 1]), cTexRoughness: texFn(() => [s.rgh, 0, 0, 1]),
    cGSysShadowPrePass: texFn(() => [1, 1, 1, 1]), cGSysProjection0: texFn(() => [1, 1, 1, 1]), cTexBakeAOShadow: texFn(() => [s.ao, s.g, 0, 1]), cTexBakeLight: texFn(() => [...s.bl, 1]),
    cEnvBRDFMap: texFn(uv => [...brdf(uv[0], 1 - (uv[1] - Math.floor(uv[1]))), 0, 0]),
    cPrefilEnvMapArray: texFn(uv => { layers.push(uv[3]); return prefil(uv.slice(0, 3), envLayerFree ? 0 : uv[3]); }),
  });
  return {color: g.output_color[0].slice(0, 3), layers};
}

function inkWeb(s, envLayerFree) {
  const lighting = new LightingState(), mat = new THREE.MeshStandardMaterial();
  const bakeTex = new THREE.DataTexture(new Uint16Array(4), 1, 1, THREE.RGBAFormat, THREE.HalfFloatType);
  applyForward(mat, {shader: {archive: 'Hoian_UBER', options: {}}}, lighting, {ao: {texture: bakeTex, st: new THREE.Vector4(1, 1, 0, 0), type: 3, tableIndex: 2}, light: {texture: bakeTex, st: new THREE.Vector4(1, 1, 0, 0), type: 4, tableIndex: 3}});
  const ink = applyInkSurface(mat, {texture: new THREE.Texture(), ink: INK, inkBright: INKB, textureStep: STEP, emission: EMI});
  ink.updateFrame(FRAME);
  const sh = {uniforms: {}, vertexShader: '#include <worldpos_vertex>\n#include <uv_vertex>\n#include <defaultnormal_vertex>', fragmentShader: TEMPLATE.replace('#include <lights_fragment_begin>', '#include <normal_fragment_maps>\n  #include <lights_fragment_begin>')};
  mat.onBeforeCompile(sh, null);
  // The evaluator has no structs: flatten HInkSurface to globals (mechanical rename, same expressions).
  const flat = sh.fragmentShader.replace(/reflectedLight\./g, 'rl_')
    .replace('struct HInkSurface {bool isInk;vec3 albedo;vec3 normal;vec3 irradianceNormal;};', 'bool hInk_isInk;vec3 hInk_albedo,hInk_normal,hInk_irradianceNormal;')
    .replace('HInkSurface hReadInk(', 'void hReadInk(').replace('HInkSurface s;', '').replace(/return s;/g, 'return;')
    .replace(/(^|[^A-Za-z0-9_])s\.(isInk|albedo|normal|irradianceNormal)/gm, '$1hInk_$2')
    .replace('HInkSurface hInkSurface=hReadInk(', 'hReadInk(').replace(/hInkSurface\.(isInk|albedo|normal|irradianceNormal)/g, 'hInk_$1');
  const prog = compileGLSL(flat);
  return {prog, rows: lighting.env.rows.map(r => [r.x, r.y, r.z, r.w]), uniforms: ink.uniforms};
}

test('잉크 분기(946 temp_50): 원본 = web ink_surface(같은 입력, 층 무관 환경 표본); 원본은 cube array 층 12 고정 요청', () => {
  for (const s of [{...SAMPLES[2], paintT: [1, 0, 0]}, {...SAMPLES[0], paintT: [-1, 0, 0]}, {...SAMPLES[1], paintT: [0, 0, 1]}]) {
    const o = inkOriginal(s, true), web = inkWeb(s, true);
    assert.deepEqual([...new Set(o.layers)], [12], `${s.name}: native ink env layer`);
    const Ng = nz(s.N), T = nz(s.T.slice(0, 3)), B = nz(cross(Ng, T).map(v => v * s.T[3]));
    const mapN = [s.nrm[0], s.nrm[1], Math.sqrt(Math.max(0, 1 - s.nrm[0] ** 2 - s.nrm[1] ** 2))];
    const n = nz([0, 1, 2].map(k => T[k] * mapN[0] + B[k] * mapN[1] + Ng[k] * mapN[2]));
    const eye = Object.assign([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]], {isMat: true});
    const webLayers = [];
    const atlas = texFn(uv => {
      const T = PREFILTER_INK_TILE, ix = uv[0] * PREFILTER_ATLAS.width - T.x, iy = uv[1] * PREFILTER_ATLAS.height - T.y;
      if (ix >= 0 && iy >= 0 && iy <= T.size) { webLayers.push(12); const f = Math.min(5, Math.floor(ix / T.size)), a = (ix / T.size - f) * 2 - 1, b = iy / T.size * 2 - 1;
        return prefil([[1, b, -a], [-1, b, a], [a, 1, -b], [a, -1, b], [a, b, 1], [-a, b, -1]][f], 0); }
      const layer = web.rows.findIndex(r => uv[1] >= r[0] && uv[1] < r[0] + r[1]); webLayers.push(layer); const r = web.rows[layer];
      const f = Math.min(5, Math.floor(uv[0] / r[2])), a = (uv[0] / r[2] - f) * 2 - 1, b = (uv[1] - r[0]) / r[1] * 2 - 1;
      return prefil([[1, b, -a], [-1, b, a], [a, 1, -b], [a, -1, b], [a, b, 1], [-a, b, -1]][f], 0); });
    const u = web.uniforms;
    const g = web.prog.run({
      viewMatrix: eye, cameraPosition: CAM, hAlbedo: s.alb, hNormal: n, hRough: s.rgh, hMetal: s.mtl, hWorldPosition: s.P, hBakeUV: [0.5, 0.5, 0.5, 0.5],
      hInkUV: [0.41, 1 - 0.37], hInkVertexNormal: Ng, hInkTangent: s.paintT, hInkTexture: texFn(paint),
      hInkColors: INK, hInkBright: INKB, hInkStep: STEP, hInkFrame: u.hInkFrame.value.toArray(), hInkEmission: u.hInkEmission.value,
      hBakeAO: texFn(() => [s.ao, s.g, 0, 1]), hBakeLightTex: texFn(() => [...s.bl, 1]), hLightColor: LIGHTC, hLightDirection: L, hSH: SH.map(v => v4(v)),
      hBakeShadow: [BAKE.shScale, -BAKE.shOff * BAKE.shScale, BAKE.aoScale, -BAKE.aoOff * BAKE.aoScale], hAOMain: BAKE.aoMain,
      hDepthFog: FOG.dcol, hDepthRange: [FOG.dstart, FOG.dend, FOG.scat], hHeightFog: FOG.hcol, hHeightRange: [FOG.hstart, FOG.hend],
      hGrid: {fetch: () => [0xffffffff, 0, 0, 0], sample: () => [0, 0, 0, 0], size: () => [20, 20]}, hGridOrigin: GRID.origin, hInvCell: GRID.inv,
      hDynColor: Array.from({length: 30}, () => [0, 0, 0, 0]), hDynAtt: Array.from({length: 30}, () => [0, 0, 0, 0]), hDynPos: Array.from({length: 30}, () => [0, 0, 0, 0]), hDynDir: Array.from({length: 30}, () => [0, 0, 0, 0]),
      hShadowAvailable: 0, hProjShadowAvailable: 0, hProjShadowDensity: 0, hShadowSplits: [1.5, 20, 60], hShadowFarFade: [40, 0.05],
      hPrefilAtlas: atlas, hEnvBRDF: texFn(uv => [...brdf(uv[0], uv[1]), 0, 0]), hPrefilRows: web.rows, hPrefilAvailable: 1, hPrefilInkAvailable: 1,
    });
    assert.ok(g.hInk_isInk, `${s.name}: web ink gate`);
    assert.deepEqual([...new Set(webLayers)], [12], `${s.name}: web ink env layer = native 12 (0x7101036d84 illuminate tile)`);
    const w = g.gl_FragColor.slice(0, 3);
    for (let k = 0; k < 3; k++) assert.ok(Math.abs(o.color[k] - w[k]) <= 2e-4 * Math.max(1, Math.abs(o.color[k])), `${s.name} ink ch${k}: original ${o.color[k]} web ${w[k]}`);
  }
});

import {applyHoian} from '../client/render/hoian.ts';
import {fresOf} from '../client/render/model.ts';
import {applyNativeRoughnessColorSpace} from '../client/render/part_material.ts';
import {buildTeamSets, materialTeamParams, FALLBACK_ROW} from '../client/render/teamcolor.ts';
const srgbEotf = c => c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
const partGlb = p => { const b = readFileSync(new URL(`../assets/maps/Lby_Lobby00/${p}`, import.meta.url)); const n = b.readUInt32LE(12); return JSON.parse(b.subarray(20, 20 + n).toString()); };
const targetFormats = JSON.parse(readFileSync(new URL('../assets/maps/Lby_Lobby00/tex/Obj_SighterTarget/native_formats.json', import.meta.url), 'utf8'));

test('SighterTarget M_Body: 원본 3443 재질 값(팀색 Tcl 혼합·sRGB _r0·금속) = web part_material 경로(applyHoian+applyForward+sRGB 거칠기)', async () => {
  assert.equal(targetFormats.textures.M_Body_Tcl.format, 'BC1_SRGB');
  assert.equal(targetFormats.textures.M_Body_Rgh.format, 'BC1_SRGB');
  const j = partGlb('parts/Obj_SighterTarget.glb'), m = j.materials.find(x => x.name === 'M_Body');
  const mat = new THREE.MeshStandardMaterial(); mat.name = 'M_Body'; mat.userData = {...m.extras};
  mat.map = new THREE.Texture(); const mr = new THREE.Texture(); mat.roughnessMap = mr; mat.metalnessMap = mr; mat.metalness = 1; mat.roughness = 1;
  const f = fresOf(mat), geom = new THREE.BufferGeometry();
  for (const [k, n] of [['position', 3], ['normal', 3], ['uv', 2], ['uv1', 2], ['tangent', 4]]) geom.setAttribute(k, new THREE.BufferAttribute(new Float32Array(3 * n), n));
  const sets = buildTeamSets(FALLBACK_ROW, false, {color: [0.6706, 0.851, 1], intensity: 10, skyUp: null}), team = materialTeamParams(sets[1], f.renderInfo);
  const tex = async name => Object.assign(new THREE.Texture(), {name});
  applyHoian(mat, f, team, tex, [], geom); await new Promise(r => setTimeout(r, 0));
  applyForward(mat, f, new LightingState(), null);
  assert.ok(applyNativeRoughnessColorSpace(mat, f, targetFormats));
  const tpl = TEMPLATE.replace('uniform vec3 hAlbedo,hNormal; uniform float hRough,hMetal;', 'uniform vec3 hAlbedo,hNormal; uniform float hMetal,roughness; uniform sampler2D roughnessMap; varying vec2 vRoughnessMapUv;\nvec3 dbgAlb; float dbgRough,dbgMetal;')
    .replace('float roughnessFactor=hRough;float metalnessFactor=hMetal;', 'float metalnessFactor=hMetal;\n  #include <roughnessmap_fragment>')
    .replace('vec3 normal=hNormal;vec3 totalEmissiveRadiance=vec3(0.);', 'vec3 normal=hNormal;vec3 totalEmissiveRadiance=vec3(0.);\n  #include <emissivemap_fragment>\n  dbgAlb=diffuseColor.rgb;dbgRough=roughnessFactor;dbgMetal=metalnessFactor;');
  const sh = {uniforms: {}, vertexShader: '#include <worldpos_vertex>\n#include <uv_vertex>', fragmentShader: tpl};
  mat.onBeforeCompile(sh, null);
  const web = compileGLSL(sh.fragmentShader.replace(/reflectedLight\./g, 'rl_'));
  const src = fixture('p3443.frag').replace('layout (location = 0) out vec4 output_color[0];', 'layout (location = 0) out vec4 output_color[0];\nvec3 dbgAlb; float dbgRough,dbgMetal;')
    .replace('    temp_96 = temp_74;', '    temp_96 = temp_74;\n    dbgAlb = vec3(temp_86, temp_87, temp_92); dbgRough = temp_85; dbgMetal = temp_88;');
  const orig = compileGLSL(src);
  for (const smp of [{alb: [0.12, 0.13, 0.16], tcl: 1, rgh: 0.451, mtl: 0.03}, {alb: [0.30, 0.28, 0.35], tcl: 0.25, rgh: 0.549, mtl: 0}, {alb: [0.05, 0.05, 0.06], tcl: 0, rgh: 0.42, mtl: 0.1}]) {
    const tclLin = srgbEotf(smp.tcl), rghByte = smp.rgh;
    const B0 = []; B0[21] = [0, 0, 0, 0.3]; B0[18] = [0.05, 1.8, 0, 0.05]; B0[20] = [0.95, 0.75, 1.75, 0]; B0[45] = [0, 0.625, 0.875, 0];
    const o = orig.run({
      in_attr0: [0.3, 0.6, 0, 0], in_attr1: [0, 0, -1, 0], in_attr2: [-1, 0, 0, 1], in_attr3: [16, 2, 29, -20], in_attr4: [5, -1.7, 31, 0], in_attr5: [0, 0, 0.5, 1], in_attr6: [0, 0, 1, 0],
      BlitzUBO0: ubo(B0), BlitzUBO2: ubo([]), Env: ubo([]), Context: ubo([]), gl_FragCoord: [0, 0, 0.5, 1], output_color: [[0, 0, 0, 0]],
      Mat: {my_team_color: team.my_team_color, team_color_blend_alpha: 0, two_comp_paint_team: 0, two_color_complement_paint_intensity: 0, comp_paint_texcoord_offset: 0.002, comp_paint_norm_intens: 1, emission_color: [1, 1, 1, 1], transmission_color_backlight: [1, 1, 1, 1], metalness: 0, edge_light_color: [0, 0, 0, 0], edge_light_intens: 0, edge_light_power: 1, edge_transmission_power: 1, emission_intensity: 0, scattering_rate: 0.6, transmission_rate: 0.3},
      cTexNormal: texFn(() => [0, 0, 0, 1]), cTexAlbedo: texFn(() => [...smp.alb, 1]), cTexEmission: texFn(() => [0.94, 0.94, 0.94, 1]), cGSysShadowPrePass: texFn(() => [1, 1, 1, 1]),
      cTexCompPaint: texFn(() => [0.4, 0, 0, 0]), cTexSubstitution: texFn(() => [tclLin, tclLin, tclLin, 1]), cTexRoughness: texFn(() => [srgbEotf(rghByte), 0, 0, 1]),
      cTexMetalness: texFn(() => [smp.mtl, 0, 0, 1]), cGSysProjection0: texFn(() => [1, 1, 1, 1]), cEnvBRDFMap: texFn(() => [0.5, 0.05, 0, 0]), cPrefilEnvMapArray: texFn(() => [0.3, 0.3, 0.3, 1]),
    });
    const w = web.run({
      viewMatrix: Object.assign([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]], {isMat: true}), cameraPosition: CAM, hAlbedo: smp.alb, hNormal: [0, 0, -1], hMetal: smp.mtl, roughness: 1,
      roughnessMap: texFn(() => [0, rghByte, smp.mtl, 1]), vRoughnessMapUv: [0.3, 0.6], hUV0: [0.3, 0.6], hTcl: texFn(() => [tclLin, tclLin, tclLin, 1]),
      myTeamColor: team.my_team_color.slice(0, 3), myTeamColorHueComplement: team.my_team_color_hue_complement.slice(0, 3),
      hLiveAlbedo: [1, 1, 1, 1], hLiveTeamBlend: 0, hLiveTeamBlendAlpha: 0, hLiveEmissionIntensity: 0, hWorldPosition: [16, 2, 29],
      hLightColor: LIGHTC, hLightDirection: L, hSH: SH.map(v => v4(v)), hBakeShadow: [0, 0, 0, 0], hAOMain: 0, hDepthFog: [0, 0, 0, 0], hDepthRange: [10, 1000, 0.3], hHeightFog: [0, 0, 0, 0], hHeightRange: [15, 90],
      hGrid: {fetch: () => [0xffffffff, 0, 0, 0], sample: () => [0, 0, 0, 0], size: () => [20, 20]}, hGridOrigin: GRID.origin, hInvCell: GRID.inv,
      hDynColor: [], hDynAtt: [], hDynPos: [], hDynDir: [], hShadowAvailable: 0, hProjShadowAvailable: 0, hProjShadowDensity: 0, hShadowSplits: [1.5, 20, 60], hShadowFarFade: [40, 0.05],
      hPrefilAtlas: texFn(() => [0, 0, 0, 1]), hEnvBRDF: texFn(() => [0, 0, 0, 0]), hPrefilRows: [], hPrefilAvailable: 0,
    });
    for (let k = 0; k < 3; k++) assert.ok(Math.abs(o.dbgAlb[k] - w.dbgAlb[k]) < 1e-6, `albedo ch${k}: original ${o.dbgAlb[k]} web ${w.dbgAlb[k]}`);
    assert.ok(Math.abs(o.dbgRough - w.dbgRough) < 1e-6, `roughness: original ${o.dbgRough} web ${w.dbgRough}`);
    assert.ok(Math.abs(o.dbgMetal - w.dbgMetal) < 1e-6, `metalness: original ${o.dbgMetal} web ${w.dbgMetal}`);
  }
});

import {shareMaterialSamplers} from '../client/render/model.ts';
import {materialFragmentSamplers, resolveIncludes, preprocess, standardDefines} from './glsl_sampler_budget.mjs';
test('사격장 파츠(SighterTarget/Move) Hoian 재질: 16 텍스처 유닛 이내, sRGB 거칠기 훅은 texelRoughness 선언 뒤', async () => {
  const over = [];let n = 0;
  for (const file of ['parts/Obj_SighterTarget.glb', 'parts/Obj_SighterTargetMove.glb']) {
    const j = partGlb(file);
    for (const m of j.materials.filter(x => x.extras?.hoian)) {
      const p = m.pbrMetallicRoughness ?? {}, mat = new THREE.MeshStandardMaterial(); mat.name = m.name; mat.userData = {...m.extras};
      const t = i => i === undefined ? null : Object.assign(new THREE.Texture(), {name: j.images[j.textures[i].extensions?.KHR_texture_basisu?.source ?? j.textures[i].source].name});
      mat.map = t(p.baseColorTexture?.index); mat.normalMap = t(m.normalTexture?.index); const mr = t(p.metallicRoughnessTexture?.index); mat.roughnessMap = mr; mat.metalnessMap = mr;
      mat.emissiveMap = t(m.emissiveTexture?.index); mat.metalness = p.metallicFactor ?? 1; mat.roughness = p.roughnessFactor ?? 1;
      const f = fresOf(mat), g = new THREE.BufferGeometry();
      for (const [k, s] of [['position', 3], ['normal', 3], ['uv', 2], ['uv1', 2], ['tangent', 4], ['skinIndex', 4], ['skinWeight', 4]]) g.setAttribute(k, new THREE.BufferAttribute(new Float32Array(3 * s), s));
      const u = applyHoian(mat, f, {my_team_color: [0.1, 0.6, 0.5, 1], my_team_color_hue_complement: [0.6, 0.1, 0.2, 1]}, async name => Object.assign(new THREE.Texture(), {name}), [], g);
      await new Promise(r => setTimeout(r, 0));
      applyForward(mat, f, new LightingState(), null); applyNativeRoughnessColorSpace(mat, f, targetFormats); if (u) shareMaterialSamplers(mat, f);
      const s = materialFragmentSamplers(mat, {skinning: true}); if (s.length > 16) over.push(`${file} ${m.name}: ${s.length} ${s.join(',')}`);
      if (mat.userData.nativeRoughnessFormat) {
        const sh = {uniforms: {}, defines: mat.defines, vertexShader: THREE.ShaderLib.standard.vertexShader, fragmentShader: THREE.ShaderLib.standard.fragmentShader};
        mat.onBeforeCompile(sh, {});
        const code = preprocess(resolveIncludes(sh.fragmentShader), standardDefines(mat));
        assert.ok(code.indexOf('vec4 texelRoughness') >= 0 && code.indexOf('hNativeSrgbToLinear(texelRoughness.g)') > code.indexOf('vec4 texelRoughness'));
      }
      n++;
    }
  }
  assert.ok(n >= 3); assert.deepEqual(over, []);
});
