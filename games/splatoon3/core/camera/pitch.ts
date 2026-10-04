// 피치 누적각 → p 매핑, 감도 → 회전 속도, 조준 피치 곡선.
// 근거: docs/camera/player_camera.md §6.3(0x71024d6598 감도), §6.5(0x71024e64f0 pitchAngleToP),
// 조준 방향 0x71024aff7c → 0x7102551640/0x7102551780(곡선) → 0x7102551fe0(회전) — docs/impl/camera.md "조준 방향".
import { f32 } from "../fmath.ts";
import { pieceBez } from "./curves.ts";
import { add, sub, mul, div, floatBits as bits } from "./native_math.ts";

/** 세이브 감도 정수(0..20) → k = clamp((v-10)/10, -1, 1). UI -5..+5 는 k = UI/5 [UI 대응 추정]. */
export function sensK(saveValue: number): number {
  const k = (saveValue - 10) / 10;
  return k < -1 ? -1 : k > 1 ? 1 : k;
}

/** 0x71024d6598: 스틱 최대 회전 속도(도/프레임). */
export function yawMaxDeg(k: number): number {
  k = f32(k);
  return add(mul(k, k < 0 ? bits(0x3fcccccc) : 3), 4);
}

export function pitchMaxDeg(k: number): number {
  k = f32(k);
  return add(k < 0 ? mul(k, bits(0x3f4ccccc)) : k, bits(0x3fe66666));
}

/**
 * 0x71024e64f0 (param_1 = 자이로 감도 gk, param_2 = 각, param_3/4 = 보정, param_5 = !flag, param_6 = stick).
 * 반환 [p, out]: out 은 범위를 넘은 만큼 되돌리는 보정량(호출부가 누적각에 더함).
 * 재구현 web/tools/camera_rig.py pitch_angle_to_p 를 그대로 옮김.
 */
export function pitchAngleToP(angle: number, gk = 0, handheldFlag = false, offA = 0, offB = 0, stick = true): [number, number] {
  angle = f32(angle); gk = f32(gk); offA = f32(offA); offB = f32(offB);
  // Raw24e6514 FMIN(+180) was removed as unreachable in cached decompilation.
  const bounded = Math.min(angle, 180), a = angle < -180 ? -180 : bounded;
  let f7 = add(mul(gk >= 0 ? 3 : 11, gk), -103);
  let f8 = add(mul(gk >= 0 ? 0 : -0, gk), -75);
  let f11 = add(mul(gk >= 0 ? -6 : -18, gk), -31);
  if (handheldFlag) {
    f7 = add(f7, 10);
    f8 = add(f8, 10);
    f11 = add(f11, 10);
  }
  let t: number;
  let P0: number, P1: number, P2: number, P3: number;
  if (a >= -165) {
    const lo = sub(add(f7, offA), offB);
    if (a < lo) return [-1, mul(add(lo, -165), .5) <= a ? sub(lo, a) : add(a, 165)];
    const mid = sub(f8, offB);
    if (a < mid) {
      const f4 = gk >= 0 ? 0 : -6;
      const f11b = gk >= 0 ? -2 : -4;
      const f6 = gk >= 0 ? f32(-gk) : mul(gk, -3);
      const span = sub(mid, lo);
      let f9 = add(mul(f11b, gk), 10);
      let f11c = add(mul(f4, gk), 0);
      if (stick) {
        f9 = add(f6, 7);
        f11c = add(mul(f11b, gk), 10);
      }
      t = span !== 0 ? div(sub(a, lo), span) : 0;
      P0 = -1;
      P1 = add(div(f11c, span), -1);
      P2 = div(f32(-f9), span);
      P3 = 0;
    } else {
      const hi = sub(add(f11, offA), offB);
      if (a < hi) {
        let f7b = add(mul(gk >= 0 ? -4 : -8, gk), 26);
        const f11d = gk >= 0 ? -4 : -6;
        let f11e = add(mul(gk >= 0 ? 0 : -0, gk), 0);
        if (stick) {
          f7b = add(mul(f11d, gk), 18);
          f11e = sub(8, add(gk, gk));
        }
        const span = sub(hi, mid);
        t = span !== 0 ? div(sub(a, mid), span) : 0;
        P0 = 0;
        P1 = div(f7b, span);
        P2 = sub(1, div(f11e, span));
        P3 = 1;
      } else if (a < 60) {
        return [1, !(mul(add(hi, 60), .5) <= a) ? sub(hi, a) : add(a, -60)];
      } else {
        t = div(add(a, -60), 135);
        P0 = 1;
        P1 = 1;
        P2 = -1;
        P3 = -1;
      }
    }
  } else {
    t = div(add(a, 300), 135);
    P0 = 1;
    P1 = 1;
    P2 = -1;
    P3 = -1;
  }
  const u = sub(1, t), q = mul(mul(t, 3), u);
  const term3 = mul(P3, mul(t, mul(t, t)));
  const term2 = mul(P2, mul(t, q));
  const term1 = mul(mul(u, q), P1);
  const term0 = mul(mul(mul(u, u), u), P0);
  return [add(term3, add(term2, add(term1, term0))), 0];
}

/** 조준 피치 곡선(도). 기본값 = 0x7102551640 이 0x71058bdeb0+0x14..+0x28 에서 채우는 임시 파라미터 [판독 + 실행(정적 초기화 에뮬)]. */
export interface AimPitchCurve {
  up: number; // +0x40
  mid: number; // +0x3c
  down: number; // +0x44
  kMid: number; // +0x30
  kUp: number; // +0x34
  kDown: number; // +0x38
}

export const DEFAULT_AIM_PITCH: AimPitchCurve = { up: 75, mid: 5, down: -70, kMid: 0.17, kUp: 0.152, kDown: 0.178 };

/** 0x7102551780: p → 조준 피치(도). */
export function aimPitchDeg(p: number, c: AimPitchCurve = DEFAULT_AIM_PITCH): number {
  return pieceBez(p, c.down, c.mid, c.up, c.kMid, c.kDown, c.kUp);
}

/**
 * 0x7102551fe0: 수평 시선 h 를 축 normalize(-h.z, 0, h.x) 둘레로 rad 만큼 돌린다(양수 = 위).
 * h 가 수평 단위벡터일 때 결과 = (h.x cos, sin, h.z cos).
 */
export function aimDirection(h: ArrayLike<number>, rad: number, out: Float32Array): Float32Array {
  const hx = h[0], hy = h[1], hz = h[2];
  let ax = -hz, az = hx;
  const n = Math.sqrt(ax * ax + az * az);
  if (n > 0) {
    ax /= n;
    az /= n;
  }
  const c = Math.cos(rad * 0.5), s = Math.sin(rad * 0.5);
  const qx = ax * s, qz = az * s, w = c;
  out[0] = f32(hx * (1 - 2 * qz * qz) + hy * (2 * (-w * qz)) + hz * (2 * qx * qz));
  out[1] = f32(hx * (2 * w * qz) + hy * (1 - 2 * (qx * qx + qz * qz)) + hz * (-2 * w * qx));
  out[2] = f32(hx * (2 * qx * qz) + hy * (2 * w * qx) + hz * (1 - 2 * qx * qx));
  return out;
}
