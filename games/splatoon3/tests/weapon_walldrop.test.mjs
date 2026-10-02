import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { quantize, WALL_DROP_RADIUS, wallDropVelocity, WallDrop, WallDropThinOut } from "../core/weapon/wall_drop.ts";
import { DEFAULTS } from "../core/weapon/params.ts";

const fx = JSON.parse(readFileSync(new URL("./weapon_fixture_walldrop.json", import.meta.url), "utf8"));
const u32 = new Uint32Array(1);
const f = new Float32Array(u32.buffer);
const bits = (x) => ((f[0] = x), u32[0]);
const F = Math.fround;

const MOVE = {
  ...DEFAULTS.spl__BulletWallDropMoveParam, FallPeriodFirstFrameMax: 40, FallPeriodFirstFrameMin: 20, FallPeriodFirstTargetSpeed: 0.05999999865889549,
  FallPeriodLastFrameMax: 35, FallPeriodLastFrameMin: 15, FallPeriodSecondFrame: 10, FallPeriodSecondTargetSpeed: 0.05999999865889549, FreeGravityType: "value_0_008",
};
const PAINT = { ...DEFAULTS.spl__BulletWallDropCollisionPaintParam, PaintRadiusFall: 0.6499999761581421, PaintRadiusGround: 0.6000000238418579, PaintRadiusShock: 1.559999942779541 };
const COMMON = {
  ...DEFAULTS.spl__BulletWallDropCommonParam, InitVelocityRateYMinus: 0.03500000014901161, InitVelocityRateYPlus: 0.014999999664723873,
  PaintWallDropDistance: 0.15000000596046448, PaintWallSpanMaxFrame: 60, PaintWallSpanMinFrame: 4,
};

function setup(seedGround = 0) {
  const q = quantize(MOVE, PAINT, 0);
  const n = [1, 0, 0];
  const v = wallDropVelocity([F(-2.2), F(-0.3), 0], n, COMMON);
  const pos = [F(0 + F(1 * F(0.05))), 0, 0];
  const wd = new WallDrop(1, 1, 0, pos, v, n, 1, q, COMMON, 0, seedGround);
  return { q, wd };
}

test("벽 낙하 양자화·난수 (weapon_walldrop_sim.py, seed61 0)", () => {
  const { q } = setup();
  assert.deepEqual(
    { shock: q.shock, fall: q.fall, ground: q.ground, t1: q.t1, t2: q.t2, n0: q.n0, n1: q.n1, n2: q.n2, pat: q.pat },
    { shock: 31, fall: 13, ground: 12, t1: 12, t2: 12, n0: fx.quant.n0, n1: 10, n2: fx.quant.n2, pat: fx.quant.pat },
  );
});

test("벽 낙하 이동·벽 도색 프레임별 비트 일치 (수직 벽 x=0, 법선 +x, 60프레임)", () => {
  const { wd } = setup();
  const r0 = fx.rows[0];
  assert.deepEqual(wd.pos.map(bits), r0.pos);
  assert.deepEqual(wd.vel.map(bits), r0.vel);
  assert.equal(bits(wd.accel), r0.accel);
  const paints = [];
  for (const row of fx.rows.slice(1)) {
    wd.move();
    wd.integrate();
    if (wd.pos[0] < WALL_DROP_RADIUS) {
      const p = wd.onWallContact({ point: [0, wd.pos[1], wd.pos[2]], normal: [1, 0, 0], body: 1 });
      if (p) paints.push({ frame: row.frame, ...p });
    }
    wd.post();
    assert.equal(wd.phase, row.phase, `f${row.frame} phase`);
    assert.equal(wd.cnt, row.cnt, `f${row.frame} cnt`);
    assert.equal(wd.c, row.c, `f${row.frame} c`);
    assert.deepEqual(wd.pos.map(bits), row.pos, `f${row.frame} pos`);
    assert.deepEqual(wd.vel.map(bits), row.vel, `f${row.frame} vel`);
    assert.equal(bits(wd.accel), row.accel, `f${row.frame} accel`);
  }
  assert.deepEqual(paints.map((p) => p.frame), fx.events.map((e) => e.frame));
  paints.forEach((p, i) => {
    const e = fx.events[i];
    assert.equal(bits(p.size), bits(e.size));
    assert.equal(p.inkTexType, e.pattern);
    assert.equal(p.alpha, e.alpha);
    assert.equal(bits(p.pos[1]), bits(e.pos[1]));
  });
});

test("벽 낙하 바닥 도색: 무작위 회전(ground-seed 12345)·크기 1.2·소멸", () => {
  const { wd } = setup(12345);
  const p = wd.onGroundContact({ point: [F(0.05), -1, 0], normal: [0, 1, 0], body: 1 });
  assert.equal(wd.dead, true);
  assert.equal(p.size, F(1.2));
  assert.equal(p.dir[0], F(-0.9699241518974304));
  assert.equal(p.dir[2], F(-0.24338644742965698));
});

test("솎아내기: 같은 바디·60프레임 안·0.3 이내면 생성 안 함", () => {
  const t = new WallDropThinOut(10, 0.3);
  assert.equal(t.admit(1, 100, [0, 0, 0]), true);
  assert.equal(t.admit(1, 120, [0.2, 0, 0]), false);
  assert.equal(t.admit(1, 160, [0.2, 0, 0]), true);
  assert.equal(t.admit(2, 120, [0.0, 0, 0]), true);
});
