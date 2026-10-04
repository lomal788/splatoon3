import { readFileSync } from "node:fs";
const nativeRig = JSON.parse(readFileSync(new URL("./fixtures/camera_native.json", import.meta.url))).rig;
const nativeInput = JSON.parse(readFileSync(new URL("./fixtures/camera_r10_input_native.json", import.meta.url)));
const bits = a => Array.from(new Uint32Array(Float32Array.from(a).buffer));
// 카메라 리그·피치 매핑·감도 — 기대값은 web/tools/camera_rig.py (selftest/table/altrig) 재구현 출력.
import { test } from "node:test";
import assert from "node:assert/strict";
import { baseRig, elevationDeg, rigPose, RIG } from "../core/camera/rig.ts";
import { pitchAngleToP, pitchMaxDeg, sensK, yawMaxDeg, aimPitchDeg, aimDirection } from "../core/camera/pitch.ts";
import { bias } from "../core/camera/curves.ts";

const near = (a, b, eps, msg) => assert.ok(Math.abs(a - b) <= eps, `${msg ?? ""} ${a} vs ${b}`);
const rig = (p) => baseRig(p, { H: 0, F: 0, D: 0, S: 0 });
const pose = (p) => {
  const at = new Float32Array(3), cam = new Float32Array(3);
  const el = elevationDeg(p, RIG.elevA, RIG.elevUp, RIG.elevDown);
  rigPose([0, 0, 0], [0, 0, 1], rig(p), el, at, cam);
  return { at, cam };
};

test("리그 끝점: 거리 7.2/6.8/4.0, p=0 높이 2.25 (selftest)", () => {
  near(rig(-1).D, 7.2, 1e-6);
  near(rig(0).D, 6.8, 1e-6);
  near(rig(1).D, 4.0, 1e-6);
  near(rig(0).H, 2.25, 1e-6);
});

test("리그 표 값 (camera_rig.py table)", () => {
  const exp = {
    "-1": [2.25, 1.0, 7.2],
    "-0.75": [2.2359375953674316, 0.949999988079071, 7.227499485015869],
    "-0.5": [2.2125, 0.825, 7.24],
    "-0.25": [2.207812547683716, 0.6625000238418579, 7.132500171661377],
    "0": [2.25, 0.5, 6.8],
    "0.25": [2.370312452316284, 0.3375000059604645, 6.09250020980835],
    "0.5": [2.5375, 0.175, 5.16],
    "0.75": [2.6859374046325684, 0.05000000074505806, 4.347499847412109],
    "1": [2.75, 0.0, 4.0],
  };
  for (const [p, [H, F, D]] of Object.entries(exp)) {
    const v = rig(Number(p));
    near(v.H, H, 1e-5, `H p=${p}`);
    near(v.F, F, 1e-5, `F p=${p}`);
    near(v.D, D, 1e-5, `D p=${p}`);
    near(v.S, 0, 1e-9, `S p=${p}`);
  }
});

test("p=0 부근과 끝점 리그: 원본 float32 곡선 결과", () => {
  for (const d of nativeRig.slice(10,14)) {
    const v=rig(d.p);
    assert.deepEqual(bits([v.H,v.F,v.D,v.S]),d.valueBits);
  }
});

test("고각 +7.5 / -60 / +75 (카메라가 위 +)", () => {
  near(-elevationDeg(0, -7.5, 60, -75), 7.5, 1e-9);
  near(-elevationDeg(1, -7.5, 60, -75), -60, 1e-9);
  near(-elevationDeg(-1, -7.5, 60, -75), 75, 1e-9);
});

test("카메라 위치: 원점/+Z에서 원본 사인표 결과", () => {
  for (const d of nativeRig.slice(0,10).filter(d=>d.squid===0)) {
    const r=pose(d.p);
    assert.deepEqual(bits([...r.at,...r.cam]),d.bits);
  }
});

test("피치각→p (스틱, gk=0): -28→-1, 0→0, +44→1, 단조, 범위 밖 보정량", () => {
  near(pitchAngleToP(-28 - 75)[0], -1, 1e-9);
  near(pitchAngleToP(0 - 75)[0], 0, 1e-9);
  near(pitchAngleToP(44 - 75 - 1e-9)[0], 1, 1e-6);
  // Replaces prior double reimplementation values with whole24e64f0 native bits.
  for (const angle of [-89, -65, -53]) {
    const row = nativeInput.pitchMap.find(row => row.input.angle === angle && !row.input.handheldFlag && row.input.stick && row.input.gyroK === 0);
    assert.deepEqual(bits(pitchAngleToP(angle)), row.outputBits);
  }
  assert.deepEqual(pitchAngleToP(-40 - 75), [-1, 12]);
  assert.deepEqual(pitchAngleToP(50 - 75), [1, -6]);
  let prev = -2;
  for (let s = -28; s <= 44; s += 0.5) {
    const p = pitchAngleToP(s - 75)[0];
    assert.ok(p >= prev - 1e-9, `단조 s=${s}`);
    prev = p;
  }
});

test("감도 → 회전 속도 (sens)", () => {
  assert.equal(sensK(10), 0);
  near(yawMaxDeg(sensK(10)), 4.0, 1e-9);
  assert.deepEqual(bits([pitchMaxDeg(sensK(10))]), [0x3fe66666]);
  near(yawMaxDeg(sensK(20)), 7.0, 1e-9);
  assert.deepEqual(bits([pitchMaxDeg(sensK(20))]), [0x40333333]);
  assert.deepEqual(bits([yawMaxDeg(sensK(0))]), [0x4019999a]);
  near(pitchMaxDeg(sensK(0)), 1.0, 1e-9);
});

test("bias: 스틱 응답 m=0.5 (자이로 off) = 0.5^0.3219", () => {
  near(bias(0.5, 0.8), 0.5 ** 0.321928, 1e-5);
  assert.equal(bias(0.3, 0.5), 0.3);
  near(bias(-0.5, 0.8), -(0.5 ** 0.321928), 1e-5);
});

test("조준 피치 기본 곡선 0x7102551780: p=-1/0/+1 → -70/5/75 도, 회전 방향 위 +", () => {
  near(aimPitchDeg(-1), -70, 1e-9);
  near(aimPitchDeg(0), 5, 1e-9);
  near(aimPitchDeg(1), 75, 1e-9);
  const d = aimDirection([0, 0, 1], (30 * Math.PI) / 180, new Float32Array(3));
  near(d[0], 0, 1e-6);
  near(d[1], 0.5, 1e-6);
  near(d[2], Math.cos(Math.PI / 6), 1e-6);
  const e = aimDirection([1, 0, 0], (-20 * Math.PI) / 180, new Float32Array(3));
  near(e[0], Math.cos((20 * Math.PI) / 180), 1e-6);
  near(e[1], -Math.sin((20 * Math.PI) / 180), 1e-6);
  near(e[2], 0, 1e-6);
});
