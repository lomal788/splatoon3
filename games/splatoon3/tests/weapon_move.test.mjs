import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { initialState, renormalize, stepMoveSM } from "../core/weapon/move.ts";
import { BulletBody, DT, INV60 } from "../core/weapon/body.ts";
import { DEFAULTS } from "../core/weapon/params.ts";

const fx = JSON.parse(readFileSync(new URL("./weapon_fixture_move.json", import.meta.url), "utf8"));
const u32 = new Uint32Array(1);
const f = new Float32Array(u32.buffer);
const bits = (x) => ((f[0] = x), u32[0]);
const fromBits = (b) => ((u32[0] = b), f[0]);
const F = Math.fround;

test("dt·1/60 상수 비트 = 0x3c888889", () => {
  assert.equal(bits(DT), 0x3c888889);
  assert.equal(bits(INV60), 0x3c888889);
});

test("WeaponShooterNormal MoveParam = 재구현 sim 파라미터", () => {
  const p = { ...DEFAULTS.spl__BulletSimpleMoveParam, ...fx.param };
  for (const k of Object.keys(DEFAULTS.spl__BulletSimpleMoveParam)) assert.equal(bits(p[k]), bits(fx.param[k]), k);
});

for (const c of fx.cases) {
  test(`탄 상태머신·바디 적분 비트 일치 (bullet_shooter_sim.py, 발사각 ${c.pitch}°, 갱신 1~30 = age 0~29)`, () => {
    const p = { ...DEFAULTS.spl__BulletSimpleMoveParam, ...fx.param };
    const sm = { state: initialState(p), frame: 0 };
    const d = c.v0.map(fromBits);
    const l = F(Math.sqrt(F(F(F(d[0] * d[0]) + F(d[1] * d[1])) + F(d[2] * d[2]))));
    const s = F(F(p.SpawnSpeed) / l);
    let v = d.map((x) => F(x * s));
    const body = new BulletBody();
    const p0 = [0, 0, 0], p1 = [0, 0, 0];
    let age = -1;
    for (const row of c.rows) {
      age++;
      if (age === 1) renormalize(v, p.SpawnSpeed);
      const out = [0, 0, 0];
      stepMoveSM(sm, p, v, out);
      if (age !== 0) v = out;
      body.setVelocity(v);
      body.begin(p0, p1);
      body.commit(p1);
      assert.equal(age, row.age);
      assert.equal(sm.state, row.state, `age ${age} state`);
      assert.equal(sm.frame, row.sf, `age ${age} stateFrame`);
      assert.deepEqual(v.map(bits), row.vel, `age ${age} vel`);
      assert.deepEqual(body.pos.map(bits), row.pos, `age ${age} pos`);
    }
  });
}

test("수평 발사 표 §10 대표값 (갱신 회차 기준 vy, vz, z)", () => {
  const rows = fx.cases[0].rows;
  const at = (tick) => rows[tick - 1];
  assert.equal(fromBits(at(4).vel[2]).toFixed(5), "2.20000");
  assert.equal(fromBits(at(5).vel[1]).toFixed(5), "-0.07000");
  assert.equal(fromBits(at(5).vel[2]).toFixed(5), "0.92768");
  assert.equal(fromBits(at(9).vel[1]).toFixed(5), "-0.17448");
  assert.equal(fromBits(at(30).vel[2]).toFixed(5), "0.15127");
  assert.equal(fromBits(at(30).pos[2]).toFixed(4), "15.0927");
});
