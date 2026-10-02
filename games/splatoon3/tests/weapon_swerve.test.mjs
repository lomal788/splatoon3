import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { biasCurve, RepeatTimer, seedsFrom, shotRandom01, sinCos, Swerve } from "../core/weapon/swerve.ts";
import { DEFAULTS } from "../core/weapon/params.ts";

const fx = JSON.parse(readFileSync(new URL("./weapon_fixture_swerve.json", import.meta.url), "utf8"));
const u32 = new Uint32Array(1);
const f = new Float32Array(u32.buffer);
const bits = (x) => ((f[0] = x), u32[0]);
const fromBits = (b) => ((u32[0] = b), f[0]);

test("bias 곡선 비트 일치 (camera_swerve.py bias_curve)", () => {
  for (const [u, b, want] of fx.biasCurve) assert.equal(bits(biasCurve(fromBits(u), fromBits(b))), want, `u=${fromBits(u)} b=${fromBits(b)}`);
});

test("sead 사인표 조회 비트 일치", () => {
  for (const [rad, s, c] of fx.sincos) {
    const [gs, gc] = sinCos(fromBits(rad));
    assert.equal(bits(gs), s);
    assert.equal(bits(gc), c);
  }
});

function run(aim, seed, frame0, frames, jump) {
  const P = { ...DEFAULTS.spl__WeaponShooterParam, ...fx.param };
  const s = new Swerve();
  s.bias = Math.fround(P.Stand_DegBiasMin);
  const tm = new RepeatTimer();
  tm.phase = Math.fround(1 - Math.fround(1 / P.RepeatFrame));
  const seeds = seedsFrom(...seed);
  const rows = [];
  for (let fr = 0; fr < frames; fr++) {
    if (fr === jump) s.onJump(P);
    if (tm.update(P.RepeatFrame)) {
      const out = [0, 0, 0];
      s.fire(P, aim, frame0 + fr, seeds, out);
      rows.push({ frame: fr, dir: out.map(bits), r: bits(shotRandom01(frame0 + fr, seeds)) });
    }
    s.endFrame(P, 0, true, true);
  }
  return rows;
}

test("연사 흔들림 방향 비트 일치 (camera_swerve.py sim, 수평 조준)", () => {
  const rows = run([0, 0, 1], [1, 2, 3, 4], 5000, 60, -1);
  assert.equal(rows.length, fx.horiz.length);
  rows.forEach((r, i) => {
    assert.equal(r.frame, fx.horiz[i].frame);
    assert.equal(r.r, fx.horiz[i].r, `frame ${r.frame} r`);
    assert.deepEqual(r.dir, fx.horiz[i].dir, `frame ${r.frame} dir`);
  });
});

test("연사 흔들림 방향 비트 일치 (임의 조준·점프 20프레임)", () => {
  const aim = fx.aim2.aim.map(fromBits);
  const rows = run(aim, [7, 11, 13, 17], 123, 60, 20);
  assert.equal(rows.length, fx.aim2.rows.length);
  rows.forEach((r, i) => assert.deepEqual(r.dir, fx.aim2.rows[i].dir, `frame ${r.frame}`));
});

test("연사 타이머: RepeatFrame 6, 대기 상태에서 누르면 0프레임째 발사, 이후 6프레임 간격", () => {
  const tm = new RepeatTimer();
  tm.idle(6, true, false);
  const fired = [];
  for (let i = 0; i < 30; i++) if (tm.update(6)) fired.push(i);
  assert.equal(fired[0], 0);
  for (let i = 1; i < fired.length; i++) assert.equal(fired[i] - fired[i - 1], 6);
});
