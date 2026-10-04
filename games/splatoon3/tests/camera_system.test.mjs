// PlayerCamera 통합 동작과 마우스 대응식.
import { test } from "node:test";
import assert from "node:assert/strict";
import { PlayerCamera } from "../core/camera/camera.ts";
import { emptyPad } from "../core/input.ts";
import { mouseToLook, defaultCameraSettings, MOUSE_BASE_DEG_PER_PX } from "../client/input.ts";
import { floatBits } from "../core/camera/native_math.ts";

const near = (a, b, eps, msg) => assert.ok(Math.abs(a - b) <= eps, `${msg ?? ""} ${a} vs ${b}`);
const player = (extra = {}) => ({ pos: [0, 0, 0], forward: [0, 0, 1], floorNormal: [0, 1, 0], ...extra });

test("정지 상태: 리그 위치 그대로 (p=0, 충돌 없음) — 카메라 (0, 3.1376, -6.2418)", () => {
  const c = new PlayerCamera();
  const pl = player();
  for (let i = 0; i < 30; i++) c.step(pl, emptyPad(), null);
  near(c.out.pos[0], 0, 1e-4);
  near(c.out.pos[1], 3.137578, 1e-3);
  near(c.out.pos[2], -6.241825, 1e-3);
  near(c.out.target[1], 2.25, 1e-4);
  near(c.out.target[2], 0.5, 1e-4);
  near(c.out.fov, 55, 1e-6);
  near(c.out.boomRatio, 1, 1e-6);
});

test("수평은 즉시 추종, 주시점 높이는 지연 추종", () => {
  const c = new PlayerCamera();
  const pl = player();
  c.step(pl, emptyPad(), null);
  pl.pos = [3, 0, 0];
  c.step(pl, emptyPad(), null);
  near(c.out.target[0], 3, 1e-5, "x 즉시");
  pl.pos = [3, 2, 0];
  c.step(pl, emptyPad(), null);
  const dy = c.out.target[1] - 2.25;
  assert.ok(dy > 0 && dy < 2, `y 지연 ${dy}`);
  near(dy, 2 * 0.25, 1e-3, "정지·접지(비율 0.25) 1프레임");
});

test("lookYaw 양수 = 원본 rotateY 양의 방향(+Z → +X)", () => {
  const c = new PlayerCamera();
  const pad = emptyPad();
  pad.lookYaw = Math.PI / 2;
  c.step(player(), pad, null);
  near(c.out.aimForward[0], 1, 1e-6);
  near(c.out.aimForward[2], 0, 1e-6);
  near(c.out.yaw, Math.PI / 2, 1e-6);
});

test("lookPitch → 누적각 s → p: 위 44° 에서 멈춤, 아래 -28°", () => {
  const c = new PlayerCamera();
  const pad = emptyPad();
  pad.lookPitch = (5 * Math.PI) / 180;
  for (let i = 0; i < 40; i++) c.step(player(), pad, null);
  near(c.out.pitchAngleDeg, 44, 1e-4);
  near(c.out.pitchNorm, 1, 1e-3);
  near((c.out.pitch * 180) / Math.PI, 75, 0.1);
  pad.lookPitch = (-5 * Math.PI) / 180;
  for (let i = 0; i < 60; i++) c.step(player(), pad, null);
  near(c.out.pitchAngleDeg, -28, 1e-4);
  near(c.out.pitchNorm, -1, 1e-3);
});

test("오징어 블렌드 +0x1764: 접지 0→0.9 14프레임, 공중 67프레임 (camera_rig.py altrig)", () => {
  for (const [air, frames] of [[0, 14], [10, 67]]) {
    const c = new PlayerCamera();
    c.reset(player(), false);
    let n = 0;
    while (c.out.squidBlend < 0.9 && n < 200) {
      c.step(player({ squid: true, airFrames: air }), emptyPad(), null);
      n++;
    }
    assert.equal(n, frames);
  }
});

test("오징어 상태: FOV 60 쪽, 거리 6.8(p=0) 유지", () => {
  const c = new PlayerCamera();
  for (let i = 0; i < 200; i++) c.step(player({ squid: true }), emptyPad(), null);
  near(c.out.fov, 60, 1e-3);
  const d = Math.hypot(c.out.pos[0] - c.out.target[0], c.out.pos[1] - c.out.target[1], c.out.pos[2] - c.out.target[2]);
  near(d, 6.8, 1e-3);
  near(c.out.target[1], 1.45, 1e-3);
});

test("벽 회피: 뒤쪽 벽에 붐이 막히면 거리 비율이 즉시 줄고, 벽이 사라지면 천천히 복귀", () => {
  const wall = {
    sweepSphere(from, to, r) {
      const z0 = -3 + r;
      if (to[2] >= z0 || from[2] <= z0) return null;
      const t = (from[2] - z0) / (from[2] - to[2]);
      return { t, point: Float32Array.of(from[0] + (to[0] - from[0]) * t, from[1] + (to[1] - from[1]) * t, -3), normal: Float32Array.of(0, 0, 1), layer: 1, material: 0, actor: -1 };
    },
    raycast: () => null,
    materialName: () => "",
    setDynamic() {},
  };
  const c = new PlayerCamera();
  c.step(player(), emptyPad(), wall);
  assert.ok(c.out.boomRatio < 0.9, `첫 프레임부터 줄어듦 ${c.out.boomRatio}`);
  for (let i = 0; i < 30; i++) c.step(player(), emptyPad(), wall);
  near(c.out.pos[2], -2.7, 0.01, "벽(z=-3) - 원본 질의 반경 0.3 에서 멈춤");
  const blocked = c.out.boomRatio;
  c.step(player(), emptyPad(), null);
  assert.ok(c.out.boomRatio - blocked < 0.1, "1프레임에 다 풀리지 않음");
  for (let i = 0; i < 600; i++) c.step(player({ pos: [0, 0, (i + 1) * 0.02] }), emptyPad(), null);
  assert.ok(c.out.boomRatio > 0.99, `복귀 ${c.out.boomRatio}`);
});

test("마우스 대응식: 감도 0 기준 0.15°/px, 감도 비율·피치 비율은 원본 yawMax/pitchMax", () => {
  const s = defaultCameraSettings();
  const [y0, p0] = mouseToLook(100, 100, s);
  near(y0, (-100 * MOUSE_BASE_DEG_PER_PX * Math.PI) / 180, 1e-12);
  near(p0, y0 * (floatBits(0x3fe66666) / 4), 1e-12);
  const [y5, p5] = mouseToLook(100, 100, { ...s, sens: 5 });
  near(y5 / y0, 7 / 4, 1e-12);
  near(p5 / y0, floatBits(0x40333333) / 4, 1e-12);
  const [ym, pm] = mouseToLook(100, 100, { ...s, sens: -5 });
  near(ym / y0, floatBits(0x4019999a) / 4, 1e-12);
  near(pm / y0, 1.0 / 4, 1e-12);
  const [yi, pi] = mouseToLook(100, 100, { ...s, invertX: true, invertY: true });
  near(yi, -y0, 1e-12);
  near(pi, -p0, 1e-12);
});
