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

test("p=0 좌우 기울기 연속(C1), p=1 끝 기울기 0", () => {
  const e = 1e-4;
  for (const k of ["H", "F", "D", "S"]) {
    const dl = (rig(0)[k] - rig(-e)[k]) / e;
    const dr = (rig(e)[k] - rig(0)[k]) / e;
    near(dl, dr, 1e-2, `${k} 기울기`);
  }
  near((rig(1).D - rig(1 - e).D) / e, 0, 1e-2, "D 끝 기울기");
});

test("고각 +7.5 / -60 / +75 (카메라가 위 +)", () => {
  near(-elevationDeg(0, -7.5, 60, -75), 7.5, 1e-9);
  near(-elevationDeg(1, -7.5, 60, -75), -60, 1e-9);
  near(-elevationDeg(-1, -7.5, 60, -75), 75, 1e-9);
});

test("카메라 위치 (camera_pose, 플레이어 원점, dir=+Z)", () => {
  const exp = {
    "-1": [[0, 2.25, 1.0], [0, 9.204666, -0.863497]],
    "-0.5": [[0, 2.2125, 0.825], [0, 6.986164, -4.61832]],
    "0": [[0, 2.25, 0.5], [0, 3.137578, -6.241825]],
    "0.5": [[0, 2.5375, 0.175], [0, 0.25529, -4.452863]],
    "1": [[0, 2.75, 0.0], [0, -0.714102, -2.0]],
  };
  for (const [p, [at, cam]] of Object.entries(exp)) {
    const r = pose(Number(p));
    for (let i = 0; i < 3; i++) {
      near(r.at[i], at[i], 1e-4, `at[${i}] p=${p}`);
      near(r.cam[i], cam[i], 1e-4, `cam[${i}] p=${p}`);
    }
  }
  const r = pose(0);
  near(Math.hypot(r.cam[0] - r.at[0], r.cam[1] - r.at[1], r.cam[2] - r.at[2]), 6.8, 1e-4, "p=0 거리 = D");
});

test("피치각→p (스틱, gk=0): -28→-1, 0→0, +44→1, 단조, 범위 밖 보정량", () => {
  near(pitchAngleToP(-28 - 75)[0], -1, 1e-9);
  near(pitchAngleToP(0 - 75)[0], 0, 1e-9);
  near(pitchAngleToP(44 - 75 - 1e-9)[0], 1, 1e-6);
  near(pitchAngleToP(-14 - 75)[0], -0.45982142857142855, 1e-9);
  near(pitchAngleToP(10 - 75)[0], 0.27625759852469095, 1e-9);
  near(pitchAngleToP(22 - 75)[0], 0.5852272727272727, 1e-9);
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
  near(pitchMaxDeg(sensK(10)), 1.8, 1e-9);
  near(yawMaxDeg(sensK(20)), 7.0, 1e-9);
  near(pitchMaxDeg(sensK(20)), 2.8, 1e-9);
  near(yawMaxDeg(sensK(0)), 2.4, 1e-9);
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
