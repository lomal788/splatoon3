import { test } from "node:test";
import assert from "node:assert/strict";
import { cameraAxis, initialVelocity, MUZZLE_OFFSET, permAt, SHOT_DIR_DEFAULT, spawnPosition } from "../core/weapon/spawn.ts";
import { DEFAULTS } from "../core/weapon/params.ts";

const u32 = new Uint32Array(1);
const f = new Float32Array(u32.buffer);
const bits = (x) => ((f[0] = x), u32[0]);
const F = Math.fround;
const A = { ...DEFAULTS.spl__SpawnBulletAdditionMovePlayerParam, ZRate: 2.0 };

function iv(p, d = [0, 0, 1], a = [0, 0, 1]) {
  const out = [0, 0, 0];
  initialVelocity(F(2.2), d.map(F), p.map(F), a.map(F), A, false, out);
  return out.map(bits);
}

test("초기 속도 4경우 (shooter_bullet.md §10, bullet_shooter_sim.initial_velocity 비트)", () => {
  assert.deepEqual(iv([0, 0, 0]), [0, 0, 0x400ccccd]);
  assert.deepEqual(iv([0, 0, 0.096]), [0, 0, 0x40191687]);
  assert.deepEqual(iv([0.096, 0, 0]), [0x3d1d4952, 0, 0x400ccccd]);
  assert.deepEqual(iv([0, 0.115, 0]), [0, 0x3deb851f, 0x400ccccd]);
});

test("초기 속도: 하강(YMinusRate 0)·대각 이동, 임의 조준·축", () => {
  assert.deepEqual(iv([0.05, -0.08, 0.07]), [0x3ca3d70b, 0, 0x4015c290]);
  assert.deepEqual(iv([0.05, -0.08, 0.07], [0.6, -0.2, 0.7745967], [0.6, 0, 0.8]), [0x3fb61672, 0xbee147af, 0x3febccfa]);
});

test("분할 인덱스 순열 표 0x7104a9b0a1", () => {
  const rows = {
    2: [1, 0], 3: [2, 0, 1], 4: [3, 1, 2, 0], 5: [4, 2, 0, 3, 1], 6: [5, 1, 4, 2, 0, 3], 7: [6, 1, 4, 2, 5, 0, 3],
    8: [7, 4, 1, 6, 3, 0, 5, 2], 9: [8, 5, 0, 3, 6, 2, 7, 4, 1], 10: [9, 2, 5, 8, 1, 4, 7, 0, 3, 6],
    11: [10, 2, 5, 8, 0, 3, 6, 9, 1, 4, 7], 12: [11, 2, 7, 10, 4, 1, 9, 6, 3, 0, 8, 5],
    13: [12, 4, 9, 1, 6, 11, 3, 8, 0, 5, 10, 2, 7], 14: [13, 2, 7, 10, 0, 3, 6, 12, 9, 4, 1, 11, 8, 5],
    15: [14, 3, 8, 11, 4, 7, 12, 0, 5, 10, 1, 6, 13, 2, 9],
  };
  for (const [n, perm] of Object.entries(rows)) {
    const N = Number(n);
    assert.deepEqual(perm.map((_, i) => permAt(N, i)), perm, `N=${N}`);
    assert.deepEqual([...perm].sort((a, b) => a - b), perm.map((_, i) => i), `N=${N} 순열`);
    for (let i = N; i < 16; i++) assert.equal(permAt(N, i), 0);
  }
  assert.equal(permAt(8, 4), 3);
  assert.equal(permAt(16, 3), 0);
});

const fb = (b) => ((u32[0] = b), f[0]);

test("발사 위치 0x7102552170 — 원본 에뮬 실행 17경우 비트 일치 (weapon_spawnpos_emu.py)", () => {
  const P = [1, 2, 3];
  const Ls = { a: [0, 0, 1], b: [1, 0, 0], c: [fb(0x3f19999a), 0, fb(0x3f4ccccd)] };
  const ps = [-1, -0.5, 0, 0.5, 1];
  const want = {
    a: [[0x3f428f5c, 0x4048b54c, 0x406805ae], [0x3f428f5c, 0x4050aba7, 0x4053e500], [0x3f428f5c, 0x4047676a, 0x404b79ae], [0x3f428f5c, 0x404dff4a, 0x4048a8a6], [0x3f428f5c, 0x405186d7, 0x4042fb3d]],
    b: [[0x3fd00b5c, 0x4048b54c, 0x404f5c29], [0x3fa7ca00, 0x4050aba7, 0x404f5c29], [0x3f96f35c, 0x4047676a, 0x404f5c29], [0x3f91514c, 0x404dff4a, 0x404f5c29], [0x3f85f67a, 0x405186d7, 0x404f5c29]],
    c: [[0x3f97735c, 0x4048b54c, 0x40693bd7], [0x3f7e984a, 0x4050aba7, 0x405921b2], [0x3f6a6385, 0x4047676a, 0x40526570], [0x3f63a10c, 0x404dff4a, 0x4050249e], [0x3f5600dc, 0x405186d7, 0x404b99e3]],
  };
  for (const k of ["a", "b", "c"]) {
    ps.forEach((p, i) => {
      const out = [0, 0, 0];
      spawnPosition(P, Ls[k], p, SHOT_DIR_DEFAULT, MUZZLE_OFFSET, out);
      assert.deepEqual(out.map(bits), want[k][i], `L=${k} p=${p}`);
    });
  }
  const charger = { PitchDegMin: -65, PitchDegHorizon: 0, PitchDegMax: 60, BezierKMin: 0.185, BezierKHor: 0.165, BezierKMax: 0.148 };
  const o1 = spawnPosition(P, Ls.c, -0.5, charger, MUZZLE_OFFSET, [0, 0, 0]);
  assert.deepEqual(o1.map(bits), [0x3f7e5f53, 0x4050d974, 0x40590eb5]);
  const o2 = spawnPosition(P, Ls.c, 0.5, charger, MUZZLE_OFFSET, [0, 0, 0]);
  assert.deepEqual(o2.map(bits), [0x3f668720, 0x404c588c, 0x40511bfa]);
});

test("조준 기준 축 a = 정규화(주시점 − 카메라), 거의 수직이면 유지", () => {
  const a = cameraAxis([0, 2, -4], [0, 2, 0], [0, 0, 0]);
  assert.equal(Math.abs(a[0]), 0);
  assert.equal(Math.abs(a[1]), 0);
  assert.equal(a[2], 1);
  assert.equal(cameraAxis([0, 10, 0], [0, 0, 0], [0, 0, 0]), null);
});
