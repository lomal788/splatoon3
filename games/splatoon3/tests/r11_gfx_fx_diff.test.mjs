// r11 gfx-diff 이펙트: 원본 실행/역번역 셰이더 vs web 의 같은 입력 비교 (docs/port/graphics_r11_diff_이펙트.md).
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import * as THREE from "three";
import { runVertex, runFragment, webDef, nativeExtras, assetDoc, uvTex, halfToFloat, NATIVE_ALBEDO } from "./r11_fx_shader_harness.mjs";
import { ParticleBatch, EmitterInstance, identityMatrix } from "../client/fx/particles.ts";
import { nativeShape, shapeState } from "../client/fx/shapes.ts";
import { VFX_DIR_TABLE } from "../client/fx/vfx_random_table.ts";
import { applyEmitterRender } from "../client/fx/render_state.ts";
import { pickSplash, wallMatrix, floorMatrix, identityFloor, hitTheta, splashKind, T0, T1, WALL_NY } from "../client/fx/splash.ts";
import { predictShotGuide, shotGuideAsset, SHOT_GUIDE_ASSETS } from "../client/fx/shot_guide.ts";

const fixture = name => JSON.parse(readFileSync(new URL(`./fixtures/${name}`, import.meta.url)));
const vatOf = (file, w, h) => { const b = readFileSync(new URL(`../assets/effects/shooter/tex/${file}`, import.meta.url)); return { w, h, texel: (x, y) => [0, 1, 2, 3].map(k => halfToFloat(b.readUInt16LE(((y * w) + x) * 8 + k * 2))) }; };
const VAT = { 1383: vatOf("bulletshtr_vsp.bin", 6, 83), 1385: vatOf("bulletcmn_vsp.bin", 8, 64) };
const PROGRAMS = new Map([[1940, { c1: 1, a1: 0 }], [1897, { c1: 0, a1: 1 }], [1886, { c1: 1, a1: 1 }], [1885, { c1: 0, a1: 1 }], [1747, { c1: 1, a1: 0 }], [1202, { c1: 0, a1: 0 }], [1383, { c1: 0, a1: 0 }], [1385, { c1: 0, a1: 0 }]]);
const emitterKeys = () => Object.entries(assetDoc.emitterSets).flatMap(([es, list]) => list.map(e => [`${es}/${e.name}`, e.shaderIndex]));
function rng(seed) { let s = seed; return () => (s = (s * 1103515245 + 12345) % 2147483648) / 2147483648; }
function randomCase(R, def, prog) {
  const a = R() * 6.28, m = { o: [R() * 4 - 2, R() * 2, R() * 4 - 2], x: [Math.cos(a), 0, -Math.sin(a)], y: [0, 1, 0], z: [Math.sin(a), 0, Math.cos(a)] };
  const now = 10 + R() * def.life * 1.05;
  const p = { P0: [0, 0, 0], V0: def.calcType === 0 ? [0, 0, 0] : [R() * .04 - .02, R() * .04, R() * .04 - .02], birth: 10, life: def.life, scale: [R() + .5, R() + .5, R() + .5], momentum: 1 + R() * .2 - .1, rand: [R(), R(), R(), R()] };
  const vert = { pos: [R() - .5, R() - .5, R() - .5], normal: [0, 1, 0], tangent: [1, 0, 0, 1], color: [R(), R(), R(), R()], uv: [R(), R()], row: Math.floor(R() * (prog === 1383 ? 83 : 64)) };
  return { m, now, p, vert };
}
const culledN = N => N.gl_Position[0] === 0 && N.gl_Position[1] === 0 && N.gl_Position[2] === 15000;
const culledW = W => W.gl_Position[0] === 2 && W.gl_Position[1] === 2 && W.gl_Position[3] === 1;

test("vertex: 8 native programs vs web particle VERT — clip, depth, C0/A0/C1/A1 and near-fade culling on all 17 Lby emitters", () => {
  const R = rng(12345);
  let compared = 0;
  for (const [key, prog] of emitterKeys()) {
    if (!PROGRAMS.has(prog)) continue;
    const def = webDef(key), cs = def.colorScale ?? 1, map = PROGRAMS.get(prog);
    for (let c = 0; c < 12; c++) {
      const { m, now, p, vert } = randomCase(R, def, prog);
      const { N, W } = runVertex(key, prog, { m, p, vert, now, vat: VAT[prog] });
      assert.equal(culledN(N), culledW(W), `${key} cull t=${now - 10}`);
      if (culledN(N)) continue;
      compared++;
      for (const i of [0, 1, 2, 3]) assert(Math.abs(N.gl_Position[i] - W.gl_Position[i]) < 1e-8, `${key} clip[${i}] ${N.gl_Position[i]} ${W.gl_Position[i]}`);
      for (const i of [0, 1, 2]) assert(Math.abs(N.out_attr0[i] - W.vColor[i] * cs) < 1e-9, `${key} C0`);
      assert(Math.abs(N.out_attr0[3] - W.vColor[3]) < 1e-9, `${key} A0`);
      if (map.c1) for (const i of [0, 1, 2]) assert(Math.abs(N.out_attr1[i] - W.vColor1[i] * cs) < 1e-9, `${key} C1`);
      if (map.a1) assert(Math.abs(N.out_attr1[3] - W.vColor1[3]) < 1e-9, `${key} A1`);
    }
  }
  assert(compared > 150, `compared ${compared}`);
});

test("fragment: final alpha/discard and pre-lighting albedo with uv-dependent textures (texture shift anim on every sampler)", () => {
  const R = rng(777);
  let compared = 0;
  for (const [key, prog] of emitterKeys()) {
    if (!PROGRAMS.has(prog)) continue;
    const def = webDef(key);
    for (let c = 0; c < 10; c++) {
      const { m, now, p, vert } = randomCase(R, def, prog);
      const { N, W, u, S } = runVertex(key, prog, { m, p, vert, now, vat: VAT[prog] });
      if (culledN(N) || culledW(W)) continue;
      const { NF, WF } = runFragment(prog, N, W, u, S, { t0: uvTex(0), t1: uvTex(1), t2: uvTex(2) });
      assert.equal(!!NF.__discard, !!WF.__discard, `${key} discard`);
      if (NF.__discard) continue;
      compared++;
      assert(Math.abs(NF.sysOutputColor0[3] - WF.gl_FragColor[3]) < 1e-9, `${key} alpha ${NF.sysOutputColor0[3]} ${WF.gl_FragColor[3]}`);
      if (NATIVE_ALBEDO[prog]) NATIVE_ALBEDO[prog].forEach((t, i) => assert(Math.abs(NF[t] - WF.base[i]) < 1e-9, `${key} albedo[${i}]`));
    }
  }
  assert(compared > 50, `compared ${compared}`);
});

test("shapes 0/1/2/12/13/14: web shapes.ts equals original jump-table functions (600 unicorn cases incl. real Lby volumeType 2)", () => {
  const fx = fixture("r11_fx_shapes.json");
  assert.equal(fx.cases.length, 600);
  for (const c of fx.cases) {
    const st = shapeState(c.seed); st.seq = c.seq;
    const r = nativeShape(c.res, st, c.s0, c.index, c.adv, c.formScale);
    assert.equal(c.ret, 1); assert(r);
    r.pos.forEach((x, i) => assert(Math.abs(x - c.pos[i]) < 2e-6, `vt${c.res.volumeType} pos`));
    r.dir.forEach((x, i) => assert(Math.abs(x - c.dir[i]) < 2e-6, `vt${c.res.volumeType} dir`));
    assert.equal(st.lcg, c.lcg); assert.equal(st.counter, c.counter); assert.equal(st.seq, c.seqAfter);
  }
});

test("direction table: web VFX_DIR_TABLE is the original 0x7100827d04 output (DAT_71057d52f8) bit for bit", () => {
  const t = fixture("r11_fx_tables.json").table52f8;
  const f = new Float32Array(1);
  for (let i = 0; i < 512; i++) for (let k = 0; k < 3; k++) { f[0] = t[i][k]; assert.equal(VFX_DIR_TABLE[i * 3 + k], f[0]); }
});

test("emitter local SRT 0x710080e4cc and first particle 0x710081e3e4 (shape + positionRandom + allDirectionVel + designated)", () => {
  const fx = fixture("r11_fx_cpu.json");
  let srt = 0, birth = 0;
  for (const c of fx.srt) {
    const def = { ...webDef(c.key), emitterTrans: c.vals.slice(0, 3), emitterTransRand: c.vals.slice(3, 6), emitterRotate: c.vals.slice(6, 9), emitterRotateRand: c.vals.slice(9, 12) };
    const b = new ParticleBatch(c.key, def, 1, null, null, false), inst = new EmitterInstance(b, identityMatrix([0, 0, 0]), [1, 1, 1], 0, 0, 1, c.seed);
    const m = inst.matrix;
    [m.x, m.y, m.z, m.o].forEach((v, i) => v.forEach((x, j) => assert(Math.abs(x - c.localRT[i][j]) < 2e-6, `${c.key} SRT`)));
    assert.equal(inst.shape.lcg, c.lcg); b.dispose(); srt++;
  }
  for (const c of fx.birth) {
    const b = new ParticleBatch(c.key, { ...webDef(c.key), velRandom: 0 }, 4, null, null, false), inst = new EmitterInstance(b, identityMatrix([0, 0, 0]), [1, 1, 1], 0, 0, 1, c.seed);
    inst.shape.lcg = c.seed >>> 0; inst.shape.counter = (c.seed >>> 16) & 0xffff;
    b.spawn(inst, 0, () => 0.5, c.s0, c.index);
    const pd = b.particleData;
    for (let k = 0; k < 3; k++) { assert(Math.abs(pd[16 + k] - c.pos[k]) < 2e-6, `${c.key} P0`); assert(Math.abs(pd[20 + k] - c.vel[k]) < 2e-6, `${c.key} V0`); }
    assert.equal(inst.shape.counter, c.counter); b.dispose(); birth++;
  }
  assert.equal(srt, 138); assert.equal(birth, 184);
});

test("emission 0x710081b784 frame loop: web EmitterInstance.step emits on the same frames with the same base count", () => {
  for (const c of fixture("r11_fx_emit.json").cases) {
    const p = c.plan;
    const def = { ...webDef("CmnFloorSplash1Emit/Splash"), emitInterval: p.interval, emitIntervalRandom: p.irand, emitRate: p.rate, emitRateRandom: p.rrand, hasEmitEnd: p.hasEnd, emitStart: p.start, emitDuration: p.dur, volumeType: 0 };
    const b = new ParticleBatch("emit", def, 64, null, null, false), inst = new EmitterInstance(b, identityMatrix([0, 0, 0]), [1, 1, 1], 0, 0, 1, 1234);
    const got = new Map();
    b.spawn = () => { got.set(frame, (got.get(frame) ?? 0) + 1); };
    let frame = 0;
    for (frame = 0; frame < 40; frame++) inst.step(frame, () => 0);
    assert.deepEqual([...got.entries()], c.emits.map(([f, n]) => [f, n]), JSON.stringify(p));
    b.dispose();
  }
});

test("render state: web adapter equals original 0x710082804c NVN setter arguments for 11 real emitters", () => {
  const BF = { 1: THREE.ZeroFactor, 2: THREE.OneFactor, 3: THREE.SrcColorFactor, 5: THREE.SrcAlphaFactor, 6: THREE.OneMinusSrcAlphaFactor, 10: THREE.OneMinusDstColorFactor };
  const EQ = { 1: THREE.AddEquation, 2: THREE.SubtractEquation, 3: THREE.ReverseSubtractEquation };
  const DF = { 1: THREE.NeverDepth, 2: THREE.LessDepth, 3: THREE.EqualDepth, 4: THREE.LessEqualDepth, 5: THREE.GreaterDepth, 6: THREE.NotEqualDepth, 7: THREE.GreaterEqualDepth, 8: THREE.AlwaysDepth };
  for (const c of fixture("r11_fx_render_capture.json").cases) {
    const raw = [...Buffer.from(c.render_hex, "hex")];
    const def = { nativeRender: { blendEnable: raw[0] !== 0, depthTest: raw[1] !== 0, depthCompare: raw[2], depthWrite: raw[3] !== 0, blendMode: raw[6], cullMode: raw[7] } };
    assert.deepEqual(webDef(c.key).nativeRender.rawBytes, raw, c.key);
    const m = new THREE.ShaderMaterial(); applyEmitterRender(m, def);
    const n = c.nvn, blend = n.nvnColorStateSetBlendEnable[1] !== 0;
    assert.equal(m.blending !== THREE.NoBlending, blend, c.key);
    if (blend) {
      const [s, d, sa, da] = n.nvnBlendStateSetBlendFunc, [e, ea] = n.nvnBlendStateSetBlendEquation;
      assert.deepEqual([m.blendSrc, m.blendDst, m.blendSrcAlpha, m.blendDstAlpha, m.blendEquation, m.blendEquationAlpha], [BF[s], BF[d], BF[sa], BF[da], EQ[e], EQ[ea]], c.key);
    }
    assert.equal(m.depthTest, n.nvnDepthStencilStateSetDepthTestEnable[0] !== 0);
    assert.equal(m.depthWrite, n.nvnDepthStencilStateSetDepthWriteEnable[0] !== 0);
    assert.equal(m.depthFunc, DF[n.nvnDepthStencilStateSetDepthFunc[0]]);
    // NVN CullFace 2 = BACK (cull back faces) → three FrontSide; 1 = FRONT → BackSide; FrontFace 1 = CCW
    const cull = n.nvnPolygonStateSetCullFace[0];
    assert.equal(m.side, cull === 2 ? THREE.FrontSide : cull === 1 ? THREE.BackSide : THREE.DoubleSide, c.key);
    assert.equal(n.nvnPolygonStateSetFrontFace[0], 1);
    m.dispose();
  }
});

test("hit splash 0x71027b877c: wall/floor matrices, floor kind (θ) and zero-velocity identity equal the original", () => {
  const fx = fixture("r11_fx_splash.json");
  assert.equal(Math.fround(fx.wallNormalY), WALL_NY);
  assert.deepEqual(fx.floorThresholds.map(Math.fround), [T0, T1]);
  let wall = 0, floor = 0, still = 0;
  for (const c of fx.cases) {
    const s = pickSplash(c.normal, c.vel, c.paint === 1), moving = Math.hypot(...c.vel) > 0;
    if (s.wall || !moving) {
      assert.equal(c.emitters.length, 1);
      const M = c.emitters[0].matrix, nat = { x: [M[0], M[4], M[8]], y: [M[1], M[5], M[9]], z: [M[2], M[6], M[10]], o: [M[3], M[7], M[11]] };
      const w = s.wall ? wallMatrix(c.pos, c.normal) : identityFloor(c.pos);
      for (const k of ["x", "y", "z", "o"]) nat[k].forEach((v, i) => assert(Math.abs(v - w[k][i]) < 1e-4, `${s.eset} ${k}`));
      s.wall ? wall++ : still++;
    } else {
      assert.equal(c.floor.length, 1);
      const f = c.floor[0], p = f.info, w = floorMatrix(c.pos, c.normal, c.vel);
      assert(Math.abs(hitTheta(c.vel, c.normal) - f.theta) < 2e-5);
      assert.equal(splashKind(f.theta), f.kind); assert.equal(f.paint, c.paint);
      [p.slice(3, 6), p.slice(6, 9), p.slice(9, 12)].forEach((axis, i) => axis.forEach((v, j) => assert(Math.abs(v - w["xyz"[i]][j]) < 1e-4, "floor axis")));
      floor++;
    }
  }
  assert(wall > 800 && floor > 500 && still > 50, `${wall} ${floor} ${still}`);
});

test("asset: r11 fields in emitters.json are the original ResEmitter bytes for all 46 emitters", () => {
  let n = 0;
  for (const [key] of emitterKeys()) {
    const def = webDef(key), x = nativeExtras(key);
    for (const k of Object.keys(x)) assert.deepEqual(def[k], x[k], `${key}.${k}`);
    n++;
  }
  assert.equal(n, 46);
});

test("shot guide: PlayerShotGuide keys map to bundled emitter sets; prediction kind follows the first contact", () => {
  for (const name of Object.values(SHOT_GUIDE_ASSETS)) assert(assetDoc.emitterSets[name], name);
  assert.equal(shotGuideAsset("Shooter_HitMarker", 0), null);
  assert.equal(shotGuideAsset("Shooter_Center", 0), "WpShtrSite");
  assert.equal(shotGuideAsset("Shooter_HitMarker", 2), "WpShtrHitMarker");
  const mk = (hitAt) => {
    const shared = new Map([["player", { id: 1, team: 0, pos: [0, 1, 0], vel: [0, 0, 0], aim: [0, 0, 1], rigForward: [0, 0, 1] }], ["camera", { viewForward: [0, 0, 1] }]]);
    const hittables = new Map([[7, { id: 7, team: 1 }], [8, { id: 8, team: 0 }]]);
    const collision = {
      overlapSphere: () => [],
      sweepSphere: (from, to, r, mask) => {
        if (!hitAt || !(mask & hitAt.mask) || !(from[2] <= hitAt.z && to[2] >= hitAt.z)) return null;
        const t = (hitAt.z - from[2]) / (to[2] - from[2] || 1);
        return { t, point: new Float32Array([from[0], from[1], hitAt.z]), normal: new Float32Array([0, 0, -1]), layer: hitAt.mask, material: 0, actor: hitAt.actor };
      },
    };
    return { frame: 0, data: { params: null, tables: {}, players: [] }, shared, hittables, collision, events: { list: [] } };
  };
  assert.equal(predictShotGuide(mk(null)).kind, 0);
  assert.equal(predictShotGuide(mk({ z: 3, mask: 2, actor: 7 })).kind, 2);
  assert.equal(predictShotGuide(mk({ z: 3, mask: 2, actor: 8 })).kind, 1);
  assert.equal(predictShotGuide(mk({ z: 3, mask: 1, actor: -1 })).kind, 1);
  const g = predictShotGuide(mk({ z: 3, mask: 2, actor: 7 }));
  assert(g.show && Math.abs(g.center[2] - 3) < 1e-6);
  const squid = mk(null); squid.shared.get("player").squid = true;
  assert.equal(predictShotGuide(squid).show, false);
});
