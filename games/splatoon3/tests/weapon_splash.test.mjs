import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { Bullet } from "../core/weapon/bullet.ts";
import { scheduleSplash, splashOnMove } from "../core/weapon/splash.ts";
import { DEFAULTS } from "../core/weapon/params.ts";

const fx = JSON.parse(readFileSync(new URL("./weapon_fixture_splash.json", import.meta.url), "utf8"));
const u32 = new Uint32Array(1);
const f = new Float32Array(u32.buffer);
const bits = (x) => ((f[0] = x), u32[0]);
const hex = (x) => "0x" + bits(x).toString(16).padStart(8, "0");

const MOVE = { ...DEFAULTS.spl__BulletSimpleMoveParam, FreeGravity: 0.01600000075995922, GoStraightStateEndMaxSpeed: 1.4494999647140503, GoStraightToBrakeStateFrame: 4, SpawnSpeed: 2.200000047683716 };
const SPAWN = { ...DEFAULTS.spl__BulletSplashShooterSpawnParam, ForceSpawnNearestAddNumArray: [4], SpawnBetweenLength: 9.199999809265137, SpawnNearestLength: 1.2000000476837158, SpawnNum: 1.5, SplitNum: 8 };
const PARAMS = { move: MOVE, col: DEFAULTS.spl__BulletSimpleCollisionParam, dmg: null, paint: null, splashPaint: null, splashSpawn: SPAWN, tail: null, wallDropColPaint: null, wallHoldFrames: 4, paintDelay: 1 };

function makeBullet(idx) {
  const info = {
    kind: "Shooter", owner: 1, team: 0, weapon: "Shooter_Normal_00", pos: [0, 0, 0], dir: [0, 0, 1], speed: Math.fround(2.2), extraSpeed: 0,
    frame: fx.frame, split: idx, angle: 0, local: true, paintDir: [0, 0],
  };
  const b = new Bullet(1, info, PARAMS, fx.globalSeed);
  scheduleSplash(b, SPAWN, fx.globalSeed);
  return b;
}

test("스플래시 일정(슬롯15) idx 0~7 — 원본 에뮬 비트 일치표(weapon_splash_sim.py)", () => {
  for (const want of fx.bullets) {
    const b = makeBullet(want.idx);
    const s = want.schedule;
    assert.equal(b.splash.isLast, s.isLast, `idx ${want.idx} isLast`);
    assert.equal(b.splash.forced, s.forced, `idx ${want.idx} forced`);
    assert.equal(hex(b.splash.acc), s.f11f4, `idx ${want.idx} +0x11f4`);
    assert.equal(b.splash.left, s.f11fc, `idx ${want.idx} +0x11fc`);
    assert.equal(hex(b.randAngle), s.f120c, `idx ${want.idx} +0x120c`);
    if (s.f1208) assert.equal(hex(b.splash.near), s.f1208);
    if (s.f11f8) assert.equal(hex(b.splash.f8), s.f11f8);
  }
});

test("스플래시 생성 위치·방향·속력·도색 방향 — idx 0~7, y < −10 까지", () => {
  for (const want of fx.bullets) {
    const b = makeBullet(want.idx);
    const got = [];
    const p0 = [0, 0, 0], p1 = [0, 0, 0];
    for (let n = 0; n < 200; n++) {
      b.pre();
      b.body.begin(p0, p1);
      b.body.commit(p1);
      splashOnMove(b, SPAWN, fx.globalSeed, (info) => got.push({ age: b.age, info }));
      if (b.body.pos[1] < -10) break;
    }
    assert.equal(b.age, want.lastAge, `idx ${want.idx} 마지막 age`);
    assert.equal(got.length, want.spawns.length, `idx ${want.idx} 생성 수`);
    got.forEach((g, i) => {
      const e = want.spawns[i];
      assert.equal(g.age, e.age, `idx ${want.idx}#${i} age`);
      assert.equal(g.info.split === 1, e.near, `idx ${want.idx}#${i} nearest`);
      assert.deepEqual(g.info.pos.map(hex), e.pos, `idx ${want.idx}#${i} pos`);
      assert.deepEqual(g.info.dir.map(hex), e.dir, `idx ${want.idx}#${i} dir`);
      assert.equal(hex(g.info.speed), e.speed, `idx ${want.idx}#${i} speed`);
      assert.equal(Math.fround(g.info.paintDir[1]), Math.fround(e.paintDir[1]));
    });
  }
});
