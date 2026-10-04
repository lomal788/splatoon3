// r11 gfx-diff 이펙트: 원본 역번역 GLSL vs web particle_shaders.ts 를 같은 입력으로 해석 실행해 비교.
import { readFileSync } from "node:fs";
import * as THREE from "three";
import { compileGLSL, ubo, halfToFloat } from "./glsl_eval.mjs";
import { VERT, FRAG } from "../client/fx/particle_shaders.ts";
import { ParticleBatch } from "../client/fx/particles.ts";
import { build } from "../../../node_modules/esbuild/lib/main.js";
import { fileURLToPath } from "node:url";
const dataBundle = await build({ entryPoints: [fileURLToPath(new URL("../client/audio/data.ts", import.meta.url))], bundle: true, write: false, platform: "node", format: "esm",
  define: { __GAME_BASE__: '"/game/splatoon3/"', __DEV__: "false" }, logLevel: "silent" });
const { emitterDefinition } = await import("data:text/javascript;base64," + Buffer.from(dataBundle.outputFiles[0].contents).toString("base64"));

const ROOT = new URL("./", import.meta.url);
const res = JSON.parse(readFileSync(new URL("fixtures/r11_fx_res.json", ROOT)));
const doc = JSON.parse(readFileSync(new URL("../assets/effects/shooter/emitters.json", ROOT)));
const glsl = {};
export const nativeShader = (p, st) => (glsl[p + st] ??= compileGLSL(readFileSync(new URL(`fixtures/r11_fx_glsl/p${p}.${st}`, ROOT), "utf8"), { expose: true }));
const webV = compileGLSL(VERT), webF = compileGLSL(FRAG, { expose: true });

export function staticRows(key) {
  const b = Buffer.from(res.emitters[key].hex, "hex"), rows = [];
  for (let i = 0; i < b.length / 16; i++) rows.push([0, 1, 2, 3].map(k => b.readFloatLE(i * 16 + k * 4)));
  return rows;
}
/** Fields asset_fx_port.py exports for the r11 vertex ports, read directly from the original ResEmitter bytes. */
export function nativeExtras(key) {
  const b = Buffer.from(res.emitters[key].hex, "hex"), f = o => b.readFloatLE(o);
  return {
    uvShiftAnim: Array.from({ length: 15 }, (_, i) => [0, 1, 2, 3].map(k => f(0x490 + i * 16 + k * 4))),
    staticFlags: [0, 1, 2, 3].map(k => b.readUInt32LE(0x70 + k * 4)),
    depthOffset: f(0xfc),
    paramKeys: Array.from({ length: 8 }, (_, i) => [0, 1, 2, 3].map(k => f(0x940 + i * 16 + k * 4))),
    numParamKeys: b.readUInt32LE(0x94),
    shaderAnimInterpolation: b[0xc3d],
    shapeRaw: { sweepStartRandom: b[0xb81], sweepRandom: f(0xb94), lineCenter: f(0xb9c), lineLength: f(0xba0), divisionMode: b.readUInt32LE(0xbbc),
      divisionCount: b.readInt32LE(0xbc8), divisionRandom: b.readUInt32LE(0xbcc), lineDivisionCount: b.readInt32LE(0xbd0), lineDivisionRandom: b.readUInt32LE(0xbd4) },
  };
}
/** The actual loader definition (asset emitters.json → client/audio/data.ts emitterDefinition). */
export function webDef(key) {
  const [es, name] = key.split("/");
  const em = doc.emitterSets[es].find(e => e.name === name);
  return emitterDefinition(em);
}
export const assetDoc = doc;
const sub = (a, b) => a.map((x, i) => x - b[i]);
const crossV = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const norm = a => { const l = Math.hypot(...a); return a.map(x => x / l); };
// camera: rows of view (3x4) and projection (4x4), plus three-style column matrices
/** Deterministic uv-dependent texture used for both sides (catches uv differences). */
export const uvTex = (seed = 0) => { const fn = uv => [0.5 + 0.4 * Math.sin(5 * uv[0] + seed), 0.5 + 0.4 * Math.cos(3 * uv[1] + seed), 0.5 + 0.3 * Math.sin(2 * uv[0] - 4 * uv[1]), 0.5 + 0.45 * Math.sin(7 * uv[0] + 2 * uv[1] + seed)]; return { sample: fn, fetch: fn, size: () => [1, 1] }; };
export function camera(eye = [3, 2.5, -4], target = [0, 0.3, 0]) {
  const f = norm(sub(target, eye)), s = norm(crossV(f, [0, 1, 0])), u = crossV(s, f);
  const z = f.map(x => -x);
  const view = [[...s, -s.reduce((a, x, i) => a + x * eye[i], 0)], [...u, -u.reduce((a, x, i) => a + x * eye[i], 0)], [...z, -z.reduce((a, x, i) => a + x * eye[i], 0)], [0, 0, 0, 1]];
  const n = 0.1, fa = 3000, t = Math.tan(25 * Math.PI / 180), asp = 16 / 9;
  const proj = [[1 / (t * asp), 0, 0, 0], [0, 1 / t, 0, 0], [0, 0, -(fa + n) / (fa - n), -2 * fa * n / (fa - n)], [0, 0, -1, 0]];
  const cols = m => { const c = [0, 1, 2, 3].map(j => m.map(r => r[j])); c.isMat = true; return c; };
  const viewParam = Array.from({ length: 40 }, () => [0, 0, 0, 0]);
  view.forEach((r, i) => viewParam[i] = r); proj.forEach((r, i) => viewParam[4 + i] = r);
  const vp = proj.map(r => [0, 1, 2, 3].map(j => r.reduce((a, x, k) => a + x * view[k][j], 0)));
  vp.forEach((r, i) => viewParam[8 + i] = r);
  viewParam[29] = [...eye, 1];
  // linear depth = z30 / (d01*w30 - y30) with d01 = ndc depth in [0,1]
  viewParam[30] = [0, fa, n * fa, fa - n];
  return { eye, view, proj, vp, viewParam, viewMatrix: cols(view), projectionMatrix: cols(proj) };
}
const vecOf = v => v instanceof THREE.Vector4 ? [v.x, v.y, v.z, v.w] : v instanceof THREE.Vector3 ? [v.x, v.y, v.z] : v instanceof THREE.Vector2 ? [v.x, v.y] : v;
function webUniforms(batch, tex) {
  const u = {};
  for (const [k, { value }] of Object.entries(batch.uniforms)) {
    if (Array.isArray(value)) u[k] = value.map(vecOf);
    else if (value && value.isTexture) u[k] = tex[k] ?? { sample: () => [1, 1, 1, 1], fetch: () => [0, 0, 0, 0], size: () => [1, 1] };
    else if (value === null) u[k] = tex[k] ?? { sample: () => [1, 1, 1, 1], fetch: () => [0, 0, 0, 0], size: () => [1, 1] };
    else u[k] = vecOf(value);
  }
  return u;
}
const LOCAL_GRAVITY = (def, m) => {
  const g = def.gravityDir.map(x => x * def.gravityScale);
  if (!def.isWorldGravity) return g;
  return [m.x, m.y, m.z].map(a => a[0] * g[0] + a[1] * g[1] + a[2] * g[2]);
};
/** Run both vertex shaders for one particle/vertex. */
export function runVertex(key, prog, { m, p, vert, team = [0.7, 0.13, 0.01], now = 14, cam = camera(), vat = null, fade = 1, override = {}, patch = null }) {
  const def = webDef(key), S = staticRows(key);
  if (patch) patch(S, def);
  const rows = [[m.x[0], m.y[0], m.z[0], m.o[0]], [m.x[1], m.y[1], m.z[1], m.o[1]], [m.x[2], m.y[2], m.z[2], m.o[2]]];
  const dyn = Array.from({ length: 16 }, () => [0, 0, 0, 0]);
  dyn[0] = [...team, 1]; dyn[1] = [...team, 1]; dyn[2] = [now, 0, 0, 0]; dyn[3] = [fade, 1, 1, 1];
  dyn[4] = rows[0]; dyn[5] = rows[1]; dyn[6] = rows[2]; dyn[8] = rows[0]; dyn[9] = rows[1]; dyn[10] = rows[2];
  const C0 = Array.from({ length: 48 }, () => [0, 0, 0, 0]), C1 = Array.from({ length: 16 }, () => [0, 0, 0, 0]);
  C1[11] = [1, 0, 0, 0]; C1[12] = [1, 0, 0, 0]; C1[4] = [0, 0, 0, 0];
  const vatTex = vat ? { fetch: ([x, y]) => vat.texel(x, y), size: () => [vat.w, vat.h], sample: () => [0, 0, 0, 0] } : undefined;
  const N = nativeShader(prog, "vert").run({
    sysPosAttr: [...vert.pos, 1], sysNormalAttr: [...vert.normal, 0], sysTangentAttr: vert.tangent, sysVertexColor0Attr: vert.color,
    sysTexCoordAttr: [vert.uv[0], vert.uv[1], vert.row, 0],
    sysLocalPosAttr: [...p.P0, p.life], sysLocalVecAttr: [...p.V0, p.birth], sysScaleAttr: [...p.scale, p.momentum],
    sysRandomAttr: p.rand, sysInitRotateAttr: [...S[160].slice(0, 3), 0],
    sysEmtMat0Attr: rows[0], sysEmtMat1Attr: rows[1], sysEmtMat2Attr: rows[2],
    NnVfx2EmitterDynamicParam: ubo(dyn), NnVfx2ViewParam: ubo(cam.viewParam), sysEmitterStaticUniformBlock: ubo(S),
    sysCustomShaderUniformBlock0: ubo(C0), sysCustomShaderUniformBlock1: ubo(C1), sysTextureSampler2: vatTex ?? uvTex(2), sysTextureSampler0: uvTex(0), sysTextureSampler1: uvTex(1),
    support_buffer: { viewport_inverse: [0, 0, 0, 0], frag_scale_count: 0, render_scale: new Array(73).fill(1), alpha_test: 0 },
  });
  // web: actual ParticleBatch uniforms; particle state written in web semantics from the same randoms
  const [es, name] = key.split("/");
  const slots = (doc.emitterSets[es].find(e => e.name === name).textures ?? []).map(t => t.slot).filter(x => x !== null);
  const samplers = new Map(slots.map(k => [k, new THREE.DataTexture(new Uint8Array(4), 1, 1)]));
  if (vat) samplers.set(2, new THREE.DataTexture(new Uint16Array(4), 1, 1, THREE.RGBAFormat, THREE.HalfFloatType));
  const batch = new ParticleBatch(key, def, 1, null, null, false, { samplers });
  if (vat) { batch.uniforms.uHasVat.value = 1; }
  const r = p.rand, ri = def.rotateInit, rir = def.rotateInitRand, ra = def.rotateAdd, rar = def.rotateAddRand;
  const state = [m.o, m.x, m.y, m.z, p.P0, p.V0, LOCAL_GRAVITY(def, m), [p.birth, p.life, p.momentum, 1], p.scale,
    [0, 1, 2].map(k => ri[k] + (r[k] - 0.5) * rir[k]),
    [0, 1, 2].map(k => ra[k] + (r[[0, 1, 0][k]] + r[[1, 2, 2][k]] - 1) * rar[k]), r, team].map(v => [...v, 0, 0, 0, 0].slice(0, 4));
  const u = webUniforms(batch, { uParticles: { fetch: ([col]) => state[col] }, uVat: vatTex, uMap: uvTex(0), uMap1: uvTex(1), uMap2: uvTex(2) });
  Object.assign(u, override);
  const W = webV.run({ ...u, aSlot: 0, position: vert.pos, normal: vert.normal, tangent: vert.tangent, fxVertexColor: vert.color, uv: vert.uv, uv1: [vert.row, 0], vatRow: vert.row,
    uNow: now, viewMatrix: cam.viewMatrix, projectionMatrix: cam.projectionMatrix, cameraPosition: cam.eye, modelViewMatrix: cam.viewMatrix });
  batch.dispose();
  return { N, W, u, S, def };
}
export function runFragment(prog, N, W, u, S, tex, cam = camera()) {
  const C0 = Array.from({ length: 48 }, (_, i) => [0, 1, 2, 3].map(k => 0.3 + 0.2 * Math.sin(i * 4 + k))), C1 = Array.from({ length: 16 }, () => [0, 0, 0, 0]);
  C1[11] = [1, 0, 0, 0]; C1[2] = [1, 1, 1, 1]; C1[3] = [1, 1, 1, 1]; C1[4] = [1, 0, 0, 0];
  const ins = {};
  for (let i = 0; i < 16; i++) ins[`in_attr${i}`] = N.__declared?.has(`out_attr${i}`) === false ? [0, 0, 0, 1] : (N[`out_attr${i}`] ?? [0, 0, 0, 1]);
  const stub = v => ({ sample: () => v, fetch: () => v, size: () => [1, 1] });
  const NF = nativeShader(prog, "frag").run({ ...ins, sysTextureSampler0: tex.t0.sample ? tex.t0 : stub(tex.t0), sysTextureSampler1: tex.t1.sample ? tex.t1 : stub(tex.t1), sysTextureSampler2: tex.t2.sample ? tex.t2 : stub(tex.t2),
    sysCustomShaderTextureSampler1: stub([0.5, 0.5, 0, 1]), sysCustomShaderTextureSampler2: stub([0, 0, 0, 0]), sysCustomShaderTextureSampler3: stub([0, 0, 0, 0]), sysCustomShaderTextureSampler4: stub([0, 0, 0, 0]),
    sysCustomShaderTextureArraySampler1: stub([0, 0, 0, 0]), sysDepthBufferTexture: stub([1, 1, 1, 1]), sysFrameBufferTexture: stub([0, 0, 0, 0]),
    NnVfx2ViewParam: ubo(cam.viewParam), sysEmitterStaticUniformBlock: ubo(S), sysCustomShaderUniformBlock0: ubo(C0), sysCustomShaderUniformBlock1: ubo(C1),
    sysCustomShaderUniformBlock2: ubo(Array.from({ length: 16 }, () => [0, 0, 0, 0])), support_buffer: { viewport_inverse: [0, 0, 0, 0], frag_scale_count: 0, render_scale: new Array(73).fill(1), alpha_test: 0 },
    gl_FragCoord: [100, 100, 0.5, 1] });
  const WF = webF.run({ ...u, uMap: tex.t0.sample ? tex.t0 : stub(tex.t0), uMap1: tex.t1.sample ? tex.t1 : stub(tex.t1), uMap2: tex.t2.sample ? tex.t2 : stub(tex.t2), uLightingAvailable: 0,
    vUv: W.vUv, vUv1: W.vUv1, vUvT1: W.vUvT1, vUvT2: W.vUvT2, vNearFade: W.vNearFade, vColor: W.vColor, vColor1: W.vColor1, vPrimitive: W.vPrimitive, vWorld: W.vWorld, vNormal: W.vNormal, vTangent: W.vTangent,
    cameraPosition: cam.eye, gl_FragCoord: [100, 100, 0.5, 1] });
  return { NF, WF };
}
export { halfToFloat };

function inv4(m){const a=m.flat(),inv=new Array(16);const [a0,a1,a2,a3,a4,a5,a6,a7,a8,a9,a10,a11,a12,a13,a14,a15]=a;
inv[0]=a5*a10*a15-a5*a11*a14-a9*a6*a15+a9*a7*a14+a13*a6*a11-a13*a7*a10;inv[4]=-a4*a10*a15+a4*a11*a14+a8*a6*a15-a8*a7*a14-a12*a6*a11+a12*a7*a10;inv[8]=a4*a9*a15-a4*a11*a13-a8*a5*a15+a8*a7*a13+a12*a5*a11-a12*a7*a9;inv[12]=-a4*a9*a14+a4*a10*a13+a8*a5*a14-a8*a6*a13-a12*a5*a10+a12*a6*a9;
inv[1]=-a1*a10*a15+a1*a11*a14+a9*a2*a15-a9*a3*a14-a13*a2*a11+a13*a3*a10;inv[5]=a0*a10*a15-a0*a11*a14-a8*a2*a15+a8*a3*a14+a12*a2*a11-a12*a3*a10;inv[9]=-a0*a9*a15+a0*a11*a13+a8*a1*a15-a8*a3*a13-a12*a1*a11+a12*a3*a9;inv[13]=a0*a9*a14-a0*a10*a13-a8*a1*a14+a8*a2*a13+a12*a1*a10-a12*a2*a9;
inv[2]=a1*a6*a15-a1*a7*a14-a5*a2*a15+a5*a3*a14+a13*a2*a7-a13*a3*a6;inv[6]=-a0*a6*a15+a0*a7*a14+a4*a2*a15-a4*a3*a14-a12*a2*a7+a12*a3*a6;inv[10]=a0*a5*a15-a0*a7*a13-a4*a1*a15+a4*a3*a13+a12*a1*a7-a12*a3*a5;inv[14]=-a0*a5*a14+a0*a6*a13+a4*a1*a14-a4*a2*a13-a12*a1*a6+a12*a2*a5;
inv[3]=-a1*a6*a11+a1*a7*a10+a5*a2*a11-a5*a3*a10-a9*a2*a7+a9*a3*a6;inv[7]=a0*a6*a11-a0*a7*a10-a4*a2*a11+a4*a3*a10+a8*a2*a7-a8*a3*a6;inv[11]=-a0*a5*a11+a0*a7*a9+a4*a1*a11-a4*a3*a9-a8*a1*a7+a8*a3*a5;inv[15]=a0*a5*a10-a0*a6*a9-a4*a1*a10+a4*a2*a9+a8*a1*a6-a8*a2*a5;
const det=a0*inv[0]+a1*inv[4]+a2*inv[8]+a3*inv[12];return [0,1,2,3].map(r=>[0,1,2,3].map(c=>inv[r*4+c]/det));}

export function worldOf(c, cam = camera()) { const IVP = inv4(cam.vp); const w = IVP.map(r => r.reduce((a, x, i) => a + x * c[i], 0)); return w.slice(0, 3).map(x => x / w[3]); }
export { inv4 };

/** Native albedo temps before lighting (Custom1[2]/[3] blend set to identity). */
export const NATIVE_ALBEDO = { 1940: ["temp_58", "temp_57", "temp_59"], 1886: ["temp_92", "temp_95", "temp_94"], 1747: ["temp_88", "temp_90", "temp_89"], 1897: ["temp_7", "temp_5", "temp_6"], 1885: ["temp_6", "temp_9", "temp_0"], 1202: ["temp_91", "temp_94", "temp_93"], 1383: ["temp_70", "temp_72", "temp_71"] };
