// [physics] native 솔버·충돌 필터·write-back·접촉 정렬을 원본 실행 하네스 출력(web/tools/phy_port_fixture_dump.py)과 비트 대조.
// fixture: tests/fixtures/phy_native.json(r8 solver/contact), phy_game.json(r6 write-back/정렬/필터/하위 레이어, r6 paint 발밑 모니터).
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  carryStep, contactBias, finalizeStep, initialCurrent, makeSolverInfo, nativeSetLinear, normalRow, normalRowsTwoBody, poseFromCom,
} from "../core/collision/solver.ts";
import { combinedPairFilter, playerSubLayer } from "../core/collision/filter.ts";
import { heapSortMode3 } from "../core/collision/contacts.ts";
import { writeBackPosition } from "../core/player/body.ts";

const NAT = JSON.parse(readFileSync(new URL("./fixtures/phy_native.json", import.meta.url), "utf8"));
const GAME = JSON.parse(readFileSync(new URL("./fixtures/phy_game.json", import.meta.url), "utf8"));

const DV = new DataView(new ArrayBuffer(8));
function num(x) {
  if (typeof x === "string" && x.startsWith("f32:")) {
    const h = x.slice(4);
    DV.setUint32(0, parseInt(h.slice(6, 8) + h.slice(4, 6) + h.slice(2, 4) + h.slice(0, 2), 16), true);
    return DV.getFloat32(0, true);
  }
  return x;
}
function b32(x) {
  DV.setFloat32(0, num(x), true);
  return DV.getUint32(0, true);
}
function b64(x) {
  DV.setFloat64(0, x, true);
  return DV.getBigUint64(0, true);
}
function u2f(u) {
  DV.setUint32(0, u >>> 0, true);
  return DV.getFloat32(0, true);
}
const eq32 = (a, b, msg) => assert.equal(b32(a), b32(b), `${msg}: ${a} vs ${b}`);

test("native: solverInfo 0a452fc→0a4536c (dt·1/sub·tau/damp·damp/tau·gamma)", () => {
  for (const s of NAT.solver_info) {
    const i = makeSolverInfo(s.tau, s.damp, s.dt, s.sub);
    const raw = (off) => s.raw[off >> 2];
    assert.equal(b32(i.dt), raw(0x10), `dt case ${s.i}`);
    assert.equal(b32(i.invSubDt), raw(0x40), `invSubDt case ${s.i}`);
    assert.equal(b32(i.invSub), raw(0x74), `invSub case ${s.i}`);
    assert.equal(b32(i.tauDamp), raw(0xb0), `tau/damp case ${s.i}`);
    assert.equal(b32(i.dampTau), raw(0xc0), `damp/tau case ${s.i}`);
    assert.equal(b32(i.gamma), raw(0xd0), `gamma case ${s.i}`);
  }
  const g = makeSolverInfo();
  assert.equal(g.gamma, 288);
});

test("native: 침투 target/old/carry 0a16d78..0a16e24", () => {
  const B = NAT.bias;
  for (const [n, c] of B.cases.entries()) {
    const o = contactBias(c.old, c.carry, c.depth, c.vel, c.fresh, c.predict, B.dt, B.c0, B.k, B.gamma, B.ratio);
    eq32(o.old, c.stored, `old #${n}`);
    eq32(o.carry, c.newcarry, `carry #${n}`);
    eq32(o.target, c.target, `target #${n}`);
  }
  assert.ok(B.cases.length > 500);
});

test("native: 단일 몸체 법선 충격량 0a1a98c..0a1abd0", () => {
  for (const [n, c] of NAT.normal.entries()) {
    const L = c.linear.slice(0, 3), W = c.angular.slice(0, 3);
    const o = normalRow(L, W, c.normal, c.rowA, c.rowA[3], c.inv, c.oldlambda, c.target);
    for (let i = 0; i < 3; i++) eq32(L[i], c.outL[i], `L${i} #${n}`);
    eq32(o.lambda, c.newlambda, `lambda #${n}`);
    eq32(o.delta, c.delta, `delta #${n}`);
    assert.equal(o.skip, c.skip, `skip #${n}`);
  }
});

test("native: 같은 manifold 여러 행 순차 반복 0a18d8c..0a1911c", () => {
  for (const [n, c] of NAT.multi.entries()) {
    const LA = c.linearA.slice(), LB = c.linearB.slice(), WA = c.WA.slice(), WB = c.WB.slice(), lam = c.lambda_old.slice();
    const rows = c.rows.map((r) => ({ ja: r.slice(0, 4), jb: r.slice(4, 8) }));
    const acc = normalRowsTwoBody(LA, LB, WA, WB, c.normal, rows, lam, c.IA, c.IB);
    const got = [...LA, ...LB, ...WA, ...WB, ...lam, acc, acc];
    assert.equal(got.length, c.output.length);
    for (let i = 0; i < got.length; i++) eq32(got[i], c.output[i], `#${n} field ${i}`);
  }
});

test("native: carry 0a4b514 (상한 포함)", () => {
  const P = NAT.prestep;
  for (const c of P.cases) {
    const cur = Float32Array.from(c.current), base = Float32Array.from(c.baseline);
    carryStep(cur, base, c.cap, P.tau, P.g);
    for (let j = 0; j < 3; j++) {
      eq32(cur[j], c.next_current[j], `cur ${c.i}.${j}`);
      eq32(base[j], c.next_baseline[j], `base ${c.i}.${j}`);
    }
  }
});

test("native: finalize 0a4b8c8 — 저장 속도·위치용 속도·double COM", () => {
  const F = NAT.finalize;
  const info = { ...makeSolverInfo(), dt: F.dt, tauDamp: F.tau, invSub: F.invsub, dampTau: F.invtau };
  for (const c of F.cases) {
    const cur = Float32Array.from(c.current), base = Float32Array.from(c.baseline), com = Float64Array.from(c.old), vel = new Float32Array(3);
    finalizeStep(cur, base, com, vel, info, c.cap);
    for (let j = 0; j < 3; j++) {
      eq32(vel[j], c.physical_delta[j], `vel ${c.i}.${j}`);
      assert.equal(b64(com[j]), b64(c.com[j]), `com ${c.i}.${j}: ${com[j]} vs ${c.com[j]}`);
    }
  }
});

test("native: COM → 몸체 원점·잔차 09d5b68", () => {
  for (const c of NAT.pose) {
    const o = new Float32Array(3), r = new Float32Array(3);
    poseFromCom(Float64Array.from(c.com), c.center, o, r);
    for (let j = 0; j < 3; j++) {
      eq32(o[j], c.origin[j], `origin ${c.i}.${j}`);
      eq32(r[j], c.residual[j], `residual ${c.i}.${j}`);
    }
  }
});

test("native: 초기 current 09d4ba8", () => {
  for (const c of NAT.initial) {
    const out = new Float32Array(3);
    initialCurrent(out, c.vel, c.gs, c.scale, c.massbits);
    eq32(out[0], c.out[4], `x ${c.i}`);
    eq32(out[1], c.out[5], `y ${c.i}`);
    eq32(out[2], c.out[3], `z ${c.i}`);
  }
});

test("native: stage 선속도 setter 3c50c7c→09d9e54 (2^-23 허용차·상한·NaN)", () => {
  const V = NAT.velocity;
  for (const [n, c] of V.cases.entries()) {
    const old = Float32Array.from(c.old.map(u2f));
    if (c.flags[0]) nativeSetLinear(old, c.v.map(u2f), V.cap);
    for (let j = 0; j < 3; j++) assert.equal(b32(old[j]), c.got[j] >>> 0, `#${n}.${j}`);
  }
});

test("write-back 0x71024d26f8: 본체+0x10 = 몸체 원점 − r·up", () => {
  let n = 0;
  for (const c of GAME.writeback) {
    if (!(c.S210 >= 1)) continue; // S+0x210 < 1 이면 보간 행렬 S+0x244 경로(웹 미사용)
    const out = new Float32Array(3);
    writeBackPosition(out, c.body_t, c.r, c.up, c.fa0 !== 0);
    for (let j = 0; j < 3; j++) eq32(out[j], c.hon10[j], `#${n}.${j}`);
    n++;
  }
  assert.ok(n > 100);
});

test("접촉 정렬 0x7103a6144c 모드 3 (같은 키 힙 순서 포함)", () => {
  for (const [n, c] of GAME.contactsort.entries()) {
    const ids = c.keys_in.map((_, i) => i);
    const got = heapSortMode3(ids, (i) => c.keys_in[i], c.cap);
    assert.deepEqual(got, c.original.map((e) => e[0]), `#${n}`);
  }
});

test("COL02 형상 행 + 공통 쌍 필터 0x7103c5e244", () => {
  for (const [n, c] of GAME.shapefilter.entries()) {
    const body = (x) => ({ L: x.L, S: x.S, m18: x.m18, m1c: x.m1c, bit28: x.bit28 });
    const shape = (x) => ({ compound: x.compound, cb8: x.cb8, cbc: x.cbc, row: x.row });
    assert.equal(combinedPairFilter(body(c.A), shape(c.A), body(c.B), shape(c.B), c.tblA, c.tblB), c.original, `#${n}`);
  }
});

test("COL02 하위 레이어 0x71024f5fc4", () => {
  for (const [n, c] of GAME.sublayer.entries()) {
    const v = playerSubLayer({ special: c.sp, actor7b9: c.a7b9 !== 0, t: c.t, zombie: c.zombie_eec !== 0, dokan: c.dokan30, flag: c.flag !== 0 });
    assert.equal(v, c.original, `#${n}`);
  }
});

test("native: 원본 MT 첫 프레임 전체 사슬(초기→normal8/carry7→finalize→pose) 재현", async () => {
  const { stepMotion, effectiveMass, PLAYER_INV_MASS, CACHE_C0, CACHE_C8 } = await import("../core/collision/solver.ts");
  // phive_controller §6.10.5 실제 값: 바닥 법선 (0,1,0), depth −.15000003576278687, old0/carry0/flag1, native 세계 중력 −9.81 fixture
  const info = makeSolverInfo();
  const bias = contactBias(0, 0, -0.15000003576278687, 0, 1, 0, info.dt, CACHE_C0, CACHE_C8, info.gamma);
  eq32(bias.target, 2.1600022315979004, "target");
  const M = effectiveMass([0, 0, 0], [0, 0, 0], PLAYER_INV_MASS);
  eq32(M, 99.90243530273438, "effective mass");
  const m = {
    com: Float64Array.from([0, 0.800000011920929, 0]), vel: Float32Array.from([0, -3, 0]),
    origin: new Float32Array(3), residual: new Float32Array(3), center: Float32Array.from([0, 0.34999996423721313, 0]),
  };
  const comVel = new Float32Array(3);
  const rows = [{ n: Float32Array.from([0, 1, 0]), target: bias.target, mass: M, lambda: 0 }];
  stepMotion(m, rows, info, 100, PLAYER_INV_MASS, { subGravity: NAT.prestep.g, gravityScale: 1, comVel });
  eq32(m.vel[1], 0.003538846969604492, "저장 속도 y");
  eq32(comVel[1], 0.449705570936203, "위치용 속도 y");
  assert.equal(b64(m.com[1]), b64(0.8074951050803065), `COM y ${m.com[1]}`);
  eq32(m.origin[1], 0.45749515295028687, "몸체 원점 y");
});

test("MOV04 발밑 모니터 델리게이트 0x7102c5ec74 (가중 합·유효 바이트·캐시)", async () => {
  const { footDelegate } = await import("../core/player/contact.ts");
  for (const [n, c] of GAME.footmon_delegate.entries()) {
    const R = { valid: c.r.valid.map(Boolean), id: c.r.id.slice(), cache: c.r.cache.map((x) => x.slice()) };
    const ents = c.r.ents.map((e) => ({
      key: -1, cache: e.cache.slice(), act: !!e.act, cnt: e.cnt, w: e.w, id: e.id, valid: !!e.valid, reg: !!e.reg,
      pos: [0, 0, 0], n: [0, 1, 0], monC: e.mon.c.slice(), monV: e.mon.v.map(Boolean), monHas: !!e.mon_has,
    }));
    const o = footDelegate(R, ents);
    assert.deepEqual(o.out, c.got.slice(0, 4), `#${n} out`);
    assert.equal(b32(o.wmax), c.got[4] >>> 0, `#${n} wmax`);
    assert.deepEqual(R.valid.map(Number), c.got_valid, `#${n} valid`);
  }
});

test("MOV04 모니터 가중치 갱신 0x7102c71330 (배치 2프레임 → 1.0, 1/6초 감쇠·해제)", async () => {
  const { footWeight } = await import("../core/player/contact.ts");
  for (const [n, c] of GAME.footmon_weight.entries()) {
    const ents = c.ents.map((e) => ({ key: -1, cache: [0, 0, 0, 0], act: !!e.act, cnt: e.cnt, w: e.w, id: 0, valid: false, reg: !!e.reg,
      pos: [0, 0, 0], n: [0, 1, 0], monC: [0, 0, 0, 0], monV: [false, false, false, false], monHas: !!e.mon_has }));
    const rel = footWeight(c.rate, c.frames, ents, Math.fround(0.016666668));
    assert.equal(rel, c.released, `#${n} released`);
    ents.forEach((e, i) => assert.deepEqual([Number(e.act), e.cnt >>> 0, b32(e.w), Number(e.reg)], c.got[i].map((x) => x >>> 0), `#${n}.${i}`));
  }
});
