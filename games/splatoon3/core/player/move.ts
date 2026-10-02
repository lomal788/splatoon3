// 담당: [physics] — 이동 속도 갱신 0x710245b2b4(일반 경로)와 공중/접지 보정 0x710245f964.
// 근거: docs/player/movement_physics.md §6.1~6.5, 디컴파일 analysis/decomp/move/move_full_main.c 10277~12773행.
// 연산마다 f32 반올림, 디컴파일의 연산 순서를 그대로 따른다(FMA 없음 — §9.4).
import { f32, type Vec3 } from "../fmath.ts";
import * as C from "./consts.ts";
import { curve } from "./gear.ts";
import type { PlayerState } from "./state.ts";
import { isSquidMove } from "./states.ts";

/** sead 방향 보간 0x7101252ff0(t, out, a, b): 크기는 선형, 방향은 구면 보간. 원본은 sead 사인 표를 쓰므로 비트 일치는 아님. */
export function slerpDir(t: number, out: Vec3, a: ArrayLike<number>, b: ArrayLike<number>): Vec3 {
  if (t <= 0) {
    out[0] = a[0]; out[1] = a[1]; out[2] = a[2];
    return out;
  }
  if (t >= 1) {
    out[0] = b[0]; out[1] = b[1]; out[2] = b[2];
    return out;
  }
  let ax = a[0], ay = a[1], az = a[2];
  const la = f32(Math.sqrt(f32(f32(f32(ax * ax) + f32(ay * ay)) + f32(az * az))));
  if (la > 0) {
    const i = f32(1 / la);
    ax = f32(ax * i); ay = f32(ay * i); az = f32(az * i);
  }
  if (la === 0) { ax = 0; ay = 0; az = 0; }
  let bx = b[0], by = b[1], bz = b[2];
  const lb = f32(Math.sqrt(f32(f32(f32(bx * bx) + f32(by * by)) + f32(bz * bz))));
  if (lb > 0) {
    const i = f32(1 / lb);
    bx = f32(bx * i); by = f32(by * i); bz = f32(bz * i);
  }
  if (lb === 0) { bx = 0; by = 0; bz = 0; }
  const d = f32(f32(f32(az * bz) + f32(ay * by)) + f32(ax * bx));
  let wa = f32(1 - t), wb = t;
  if (d <= 0.999999 && d >= -0.999999) {
    const th = f32(Math.acos(d));
    const s = f32(Math.sin(th));
    wa = f32(f32(Math.sin(f32(f32(1 - t) * th))) / s);
    wb = f32(f32(Math.sin(f32(t * th))) / s);
  }
  const mag = f32(f32(la * f32(1 - t)) + f32(lb * t));
  out[0] = f32(f32(f32(bx * wb) + f32(ax * wa)) * mag);
  out[1] = f32(f32(f32(by * wb) + f32(ay * wa)) * mag);
  out[2] = f32(f32(f32(bz * wb) + f32(az * wa)) * mag);
  return out;
}

const TMP = new Float32Array(3);

/**
 * 입력 기준 전방 축(본체+0xd40)과 이동 방향·입력 크기(본체+0xd30/+0xd3c).
 * aim = 본체+0x538(카메라 리그 수평 시선), right = PlayerCamera+0x68 이 가리키는 벡터(카메라 오른쪽으로 추정).
 */
export function updateInputDir(p: PlayerState, aim: ArrayLike<number>, right: ArrayLike<number>): void {
  p.fwdBlend = f32(C.FWD_BLEND_STEP + p.fwdBlend);
  if (p.fwdBlend > 1) p.fwdBlend = 1;
  const N = p.floorN;
  let cx = f32(f32(N[1] * right[2]) - f32(N[2] * right[1]));
  let cy = f32(f32(N[2] * right[0]) - f32(right[2] * N[0]));
  let cz = f32(f32(right[1] * N[0]) - f32(N[1] * right[0]));
  const len = f32(Math.sqrt(f32(f32(f32(cz * cz) + f32(cx * cx)) + f32(cy * cy))));
  if (len > 0) {
    const i = f32(1 / len);
    cz = f32(cz * i); cx = f32(cx * i); cy = f32(cy * i);
  }
  TMP[0] = cx; TMP[1] = cy; TMP[2] = cz;
  // s = 0.5([0x71058bbe74]) 이므로 k = |N × right| 그대로
  slerpDir(f32(1 - len), TMP, TMP, aim);
  slerpDir(p.fwdBlend, p.fwdAxis, p.fwdAxis, TMP);
  const F = p.fwdAxis;
  const d = f32(f32(f32(F[0] * N[0]) + f32(F[1] * N[1])) + f32(F[2] * N[2]));
  F[0] = f32(F[0] - f32(N[0] * d));
  F[1] = f32(F[1] - f32(N[1] * d));
  F[2] = f32(F[2] - f32(N[2] * d));
  const fl = f32(Math.sqrt(f32(f32(f32(F[2] * F[2]) + f32(F[0] * F[0])) + f32(F[1] * F[1]))));
  if (fl > 0) {
    const i = f32(1 / fl);
    F[1] = f32(i * F[1]); F[0] = f32(i * F[0]); F[2] = f32(i * F[2]);
  }
  // 입력 방향: 바닥 평면 위 전방 f 와 f × N
  const fd = f32(f32(f32(F[0] * N[0]) + f32(F[1] * N[1])) + f32(F[2] * N[2]));
  let fx = f32(F[0] - f32(N[0] * fd)), fy = f32(F[1] - f32(N[1] * fd)), fz = f32(F[2] - f32(N[2] * fd));
  const ll = f32(Math.sqrt(f32(f32(f32(fz * fz) + f32(fx * fx)) + f32(fy * fy))));
  if (ll > 0) {
    const i = f32(1 / ll);
    fx = f32(i * fx); fy = f32(i * fy); fz = f32(i * fz);
  }
  const sx = p.stick[0], sy = p.stick[1];
  let px = f32(f32(fx * sy) + 0), py = f32(f32(fy * sy) + 0), pz = f32(f32(fz * sy) + 0);
  px = f32(px - f32(f32(f32(fz * N[1]) - f32(fy * N[2])) * sx));
  py = f32(py - f32(f32(f32(fx * N[2]) - f32(fz * N[0])) * sx));
  pz = f32(pz - f32(f32(f32(fy * N[0]) - f32(fx * N[1])) * sx));
  const m = f32(Math.sqrt(f32(f32(f32(pz * pz) + f32(px * px)) + f32(py * py))));
  if (m > 0) {
    const i = f32(1 / m);
    px = f32(i * px); py = f32(i * py); pz = f32(i * pz);
  }
  p.dir[0] = px; p.dir[1] = py; p.dir[2] = pz;
  p.inputMag = f32(Math.pow(m, C.STICK_POW));
}

/** 목표 속도(§6.1)와 경사 제한 여부. raw = 사격·경사 조정 전 값(공중 상한 보간에 씀). */
function targetSpeed(p: PlayerState, shooting: boolean): { target: number; raw: number; slopeLimited: boolean } {
  const pp = p.gear;
  const st = pp.speedType === 0 ? 0 : pp.speedType === 2 ? 2 : 1;
  const human = pp.human[st];
  const enemy = p.step.enemyMove;
  let t: number;
  let shotBase = C.SHOT_CLAMP;
  const sq = isSquidMove(p.state);
  if (sq) {
    const squid = pp.squid[st];
    const k = 1; // 0x710266c6e4 미판독 — 기본 1 [추정]
    t = f32(f32(C.SQUID_DRY + f32(f32(f32(squid * k) - C.SQUID_DRY) * p.step.own)) + f32(f32(C.SQUID_ENEMY - C.SQUID_DRY) * enemy));
  } else {
    t = human;
    if (enemy > 0) {
      const op = pp.opMove, opShot = pp.opMoveShot;
      if (op < human) t = f32(human + f32(f32(op - human) * enemy));
      if (opShot < shotBase) shotBase = f32(shotBase + f32(f32(opShot - shotBase) * enemy));
    }
  }
  void shotBase;
  const raw = t;
  if (!sq && shooting) {
    // 잉크액션 보조 vt[0x30] → 슈터 0x71025859ac
    const ms = p.weapon.moveSpeed > 0 ? p.weapon.moveSpeed : p.weaponMoveSpeed;
    let v = f32(ms * pp.shotRate);
    if (enemy > 0 && pp.opMoveShot < v) v = f32(v + f32(f32(pp.opMoveShot - v) * enemy));
    if (v < t) t = v;
  }
  // 벽 점프 차지 감속 (bbb8f == 0)
  const c = p.wallJumpCharge;
  if (c - C.WALLJUMP_CHARGE_START !== 0 && C.WALLJUMP_CHARGE_START <= c) {
    let f = f32(f32(c - C.WALLJUMP_CHARGE_START) / f32(C.WALLJUMP_CHARGE_END - C.WALLJUMP_CHARGE_START));
    f = f > 1 ? 1 : f < 0 ? 0 : f;
    const lim = f32(C.SQUID_REF * f32(f32(f32(C.WALLJUMP_CHARGE_SPEEDK - 1) * f) + 1));
    if (lim < t) t = lim;
  }
  let slopeLimited = false;
  if (sq) {
    // LAB_710245bfd0: 표면 법선 y 를 cos50°..cos90° 로 역보간해 벽일수록 0.096 쪽으로
    const c50 = COS50, c90 = COS90;
    const ny = p.surfN[1];
    let w0 = 0;
    if (c90 < ny) {
      if (c50 <= ny) w0 = 1;
      else if (f32(c50 - c90) !== 0) w0 = f32(f32(ny - c90) / f32(c50 - c90));
    }
    const w = f32(1 - w0);
    const cand = f32(f32(w * f32(C.WALL_SPEED - t)) + t);
    if (!(t <= cand)) {
      slopeLimited = true;
      t = cand;
    }
  }
  return { target: t, raw, slopeLimited };
}

const COS50 = f32(Math.cos(f32(f32(50) * f32(0.017453292))));
const COS90 = f32(Math.cos(f32(f32(90) * f32(0.017453292))));

export interface MoveContext {
  /** 이번 프레임 사격 자세 */
  shooting: boolean;
  /** 공중 감쇠 접기 조건(본체+0xad8 ≥ 1 && 상태 ∉ S) — 사격 자세로 대신함 [추정] */
  aimFold: boolean;
}

/** 0x710245b2b4 일반 경로. p.vel 갱신, p.desired/p.cap 기록. */
export function updateMove(p: PlayerState, ctx: MoveContext): void {
  const v = p.vel;
  const m = p.inputMag;
  const { target, raw, slopeLimited } = targetSpeed(p, ctx.shooting);

  // ---- cap 갱신 (§6.2) ----
  let rate = C.CAP_RATE_UP;
  const lhs = f32(f32(f32(target * m) * target) * m);
  const rhs = f32(f32(f32(v[2] * v[2]) + f32(v[1] * v[1])) + f32(v[0] * v[0]));
  if (lhs <= rhs) {
    rate = C.CAP_RATE_AIR;
    if (p.riseFrames < 1) {
      rate = C.CAP_RATE_GROUND;
      // slopeLimited: 각도 보간 0.05~1.0 은 본체+0x1d8 이 필요해 미구현 → 0.1 유지
      void slopeLimited;
    }
  }
  p.cap = f32(p.cap + f32(rate * f32(target - p.cap)));

  // ---- 공중 상한 보간·착지 경직 → desired ----
  let capEff = p.cap;
  const launchRoll = p.launch.active && !p.launch.wallJump && p.launch.wasSquid;
  if (p.airFrames > 0 && !launchRoll) {
    let vx = v[0], vyy = v[1], vz = v[2];
    const vl = f32(Math.sqrt(f32(f32(f32(vx * vx) + f32(vyy * vyy)) + f32(vz * vz))));
    if (vl > 0) {
      const i = f32(1 / vl);
      vx = f32(vx * i); vyy = f32(vyy * i); vz = f32(vz * i);
    }
    const d = f32(m * f32(f32(f32(vx * p.dir[0]) + f32(vyy * p.dir[1])) + f32(vz * p.dir[2])));
    let base = C.AIR_CAP_BASE;
    if (d > 0) {
      const r = vl <= raw ? vl : raw;
      base = f32(base + f32(f32(r - base) * d));
    }
    const n = isSquidMove(p.state) ? C.AIR_CAP_FRAMES_SQUID : C.AIR_CAP_FRAMES_HUMAN;
    let f = f32(f32(p.airFrames) / f32(n));
    if (f > 1) f = 1;
    capEff = f32(capEff + f32(f32(base - capEff) * f));
  }
  if (C.LANDING_SPEED < capEff) {
    const ls = p.landStiff;
    let f = 0;
    if (ls > 0) f = C.LANDING_STIFF_DIV <= ls ? 1 : f32(f32(ls) / f32(C.LANDING_STIFF_DIV));
    capEff = f32(capEff + f32(f32(C.LANDING_SPEED - capEff) * f));
  }
  const mag = f32(capEff * m);
  const des = p.desired;
  des[0] = f32(p.dir[0] * mag);
  des[1] = f32(mag * p.dir[1]);
  des[2] = f32(mag * p.dir[2]);

  // ---- 가속량 (§6.3.1) ----
  const cap2 = f32(p.cap * p.cap);
  const dv = f32(f32(f32(des[0] * v[0]) + f32(des[1] * v[1])) + f32(des[2] * v[2]));
  const neg = -dv;
  let o = 0;
  if (0 <= cap2) {
    if (dv < 0) o = cap2 <= neg ? 1 : cap2 !== 0 ? f32(neg / cap2) : 0;
  }
  const om = f32(1 - o);
  let full: number, base: number;
  const knockIdle = p.knockFrames >= 1 && p.knock[0] === 0 && p.knock[1] === 0 && p.knock[2] === 0;
  if (!ctx.shooting) {
    if (!knockIdle) {
      const airBranch = p.swimming || (f32(p.vy + p.jump3d[1]) > C.VY_EPS && p.sinceJump < p.jumpKeep && p.step.cls !== 2 && p.step.cls !== 3);
      if (airBranch) {
        const at = p.gear.accType;
        const accBase = at === 2 ? C.ACC_TYPE2 : at === 0 ? C.ACC_TYPE0 : C.ACC_TYPE1;
        const vl = f32(Math.sqrt(f32(f32(f32(v[0] * v[0]) + f32(v[1] * v[1])) + f32(v[2] * v[2]))));
        const b1 = curve(f32(vl / C.SQUID_REF), C.ACC_CURVE);
        const b2 = curve(om, C.ACC_CURVE);
        const fb2 = f32(f32(1 - C.ACC_CURVE) * b2);
        base = f32(b1 * C.ACC_SWIM_BASE);
        full = f32(accBase * f32(C.ACC_CURVE + fb2));
      } else {
        const b = curve(om, C.ACC_CURVE);
        full = f32(f32(C.ACC_CURVE + f32(f32(1 - C.ACC_CURVE) * b)) * C.ACC_GROUND_FULL);
        base = C.ACC_GROUND_BASE;
      }
    } else {
      const b = curve(om, C.ACC_CURVE);
      full = f32(f32(C.ACC_CURVE + f32(f32(1 - C.ACC_CURVE) * b)) * C.ACC_KNOCK_FULL);
      base = C.ACC_KNOCK_BASE;
    }
  } else {
    const b = curve(om, C.ACC_CURVE);
    full = f32(f32(C.ACC_CURVE + f32(f32(1 - C.ACC_CURVE) * b)) * C.ACC_SHOT);
    base = C.ACC_SHOT_BASE;
  }
  let accel = f32(base + f32(p.stickMag01 * f32(full - base)));

  // 상승 보정
  if (!launchRoll) {
    let f = f32(p.vy / C.JUMP_VEL);
    if (f > 1) f = 1;
    if (f <= 0) f = 0;
    const a5c = 0; // 본체+0xa5c 의미 미확정 → 0
    const w = f32(p.airRatio * f32(1 - f32(a5c * f)));
    accel = f32(accel + f32(w * f32(C.ACC_RISE - accel)));
  }

  // 밀림 보정(ImpactAndReject 가속 0) — 정규화 후 같은 길이로 되돌리는 연산은 그대로 둔다
  let dx = des[0], dy = des[1], dz = des[2];
  {
    const l = f32(Math.sqrt(f32(f32(f32(dx * dx) + f32(dy * dy)) + f32(dz * dz))));
    let s = 0;
    if (0 < l) {
      const i = f32(1 / l);
      dx = f32(dx * i); dy = f32(dy * i); dz = f32(dz * i);
      const push = 0; // n·(가속합/3600 + 본체+0x4bc) — 외력 없음
      const r = f32(l - f32(Math.fround(1.2000000476837158) * push));
      s = 0 < r ? r : 0;
    }
    dx = f32(dx * s); dy = f32(dy * s); dz = f32(dz * s);
  }
  // delta = desired − v
  let ddy = f32(dy - v[1]);
  let ddx = f32(dx - v[0]);
  let ddz = f32(dz - v[2]);

  // 공중 감쇠 (공중 ≥ 4)
  if (C.AIR_DAMP_START <= p.airFrames) {
    const l = f32(Math.sqrt(f32(f32(f32(ddx * ddx) + f32(ddy * ddy)) + f32(ddz * ddz))));
    let nx = ddx, ny = ddy, nz = ddz;
    if (0 < l) {
      const i = f32(1 / l);
      nx = f32(ddx * i); ny = f32(ddy * i); nz = f32(ddz * i);
    }
    const F = p.facing;
    let h = f32(f32(f32(f32(f32(nx * F[0]) + f32(ny * F[1])) + f32(nz * F[2])) + 1) * 0.5);
    if (ctx.aimFold) {
      if (h <= 0.5) h = f32(C.AIR_H_A - f32(f32(f32(h - 0.5) + f32(h - 0.5)) * f32(C.AIR_H_B - C.AIR_H_A)));
      else h = f32(1 - f32(f32(f32(h - 1) + f32(h - 1)) * f32(C.AIR_H_A - 1)));
    }
    const sl = f32(Math.sqrt(f32(f32(p.stick[0] * p.stick[0]) + f32(p.stick[1] * p.stick[1]))));
    let r = sl > 1 ? 1 : sl;
    if (!(0 <= sl)) r = 0;
    let f33 = f32(f32(p.airFrames) / f32(C.AIR_ACC_FADE));
    if (f33 > 1) f33 = 1;
    const bs = curve(r, C.AIR_STICK_S);
    f33 = f32(1 - f33);
    let f40 = f32(C.AIR_F40_BASE + f32(f32(0 - C.AIR_F40_BASE) * bs));
    if (f40 <= h) f40 = h;
    accel = f32(f32(accel * f40) * f33);
  }

  // 바닥 법선 성분 제거
  const N = p.floorN;
  const dn = f32(f32(f32(ddx * N[0]) + f32(ddy * N[1])) + f32(ddz * N[2]));
  let nx = f32(ddx - f32(N[0] * dn));
  const ny = f32(ddy - f32(N[1] * dn));
  let nz = f32(ddz - f32(N[2] * dn));
  if (0 < p.airFrames) {
    // 공중이면 수평 성분이 원래보다 커지지 않게(디컴파일 그대로)
    let a = nx <= ddx ? nx : ddx;
    let b = 0 <= nx ? a : 0;
    if (0 <= ddx) nx = b;
    a = 0 < nx ? 0 : nx;
    b = ddx <= nx ? a : ddx;
    if (ddx <= 0) nx = b;
    let c = nz <= ddz ? nz : ddz;
    const e = 0 <= nz ? c : 0;
    c = 0 <= ddz ? e : nz;
    let z = c;
    if (ddz <= 0) {
      z = ddz;
      if (ddz <= c) z = c;
    }
    nz = z;
  }
  let fx = nx, fy = ny, fz = nz;
  const l2 = f32(f32(f32(fz * fz) + f32(fy * fy)) + f32(fx * fx));
  if (f32(accel * accel) < l2) {
    const s = f32(accel / f32(Math.sqrt(l2)));
    fx = f32(fx * s); fy = f32(fy * s); fz = f32(fz * s);
  }

  // 위로 향한 가속 제한(경사 오르기·점프 직후) — 0x710245ea90 부근
  if (0 < fy) {
    const s = p.state;
    let b6: boolean;
    if (s >= 0x82 && s <= 0x84) b6 = p.stateFrame > 10;
    else b6 = (s >= 0x85 && s <= 0x90) || (s >= 0xaa && s <= 0xac) || s === 0x10c || s === 0xed || s === 0xee;
    const air = p.airFrames;
    let k = 0, ka = 0;
    if (air >= 1) {
      k = f32(f32(air) * 0.25);
      ka = 1;
      if (3 < air) k = 1;
      if (air < 60) ka = f32(f32(air) / 60);
    }
    const vy0 = p.vy;
    if (0 < vy0) {
      fy = f32(fy - f32((b6 ? k : 1) * vy0));
      if (fy <= 0) fy = 0;
    }
    if (!b6) ka = k;
    fy = f32(f32(1 - ka) * fy);
    if (0 < fy) {
      const over = f32(f32(f32(f32(fy + vy0) + v[1]) + p.jump3d[1]) - C.UP_DELTA_LIMIT);
      if (0 < over) {
        fy = f32(fy - over);
        if (fy <= 0) fy = 0;
      }
    }
  }

  v[0] = f32(fx + v[0]);
  let vy = f32(fy + v[1]);
  v[2] = f32(fz + v[2]);
  if (C.V_Y_MAX < vy) vy = C.V_Y_MAX;
  v[1] = vy;
  airCorrection(p, v);
}

/** 0x710245f964 — 이동 속도 v 의 공중/접지 보정 (§6.5). */
export function airCorrection(p: PlayerState, v: Vec3): void {
  const L = p.launch;
  if (L.active && !L.wallJump && L.wasSquid) return; // 롤 발사 중(시각 조건은 근사: 활성 동안)
  const air = p.airFrames;
  if (air < C.AIR_DAMP_START) {
    if (0 < air || (p.sinceJump === 0 && C.VY_EPS < p.vy)) {
      let nx = p.floorN[0], ny = p.floorN[1], nz = p.floorN[2];
      const u = p.unexplained;
      const thr = f32(C.F964_PUSH - 0.0001);
      if (f32(thr * thr) < f32(f32(f32(u[0] * u[0]) + f32(u[1] * u[1])) + f32(u[2] * u[2]))) {
        const ul = f32(Math.sqrt(f32(f32(f32(u[0] * u[0]) + f32(u[1] * u[1])) + f32(u[2] * u[2]))));
        if (ul !== 0) {
          const vl = f32(Math.sqrt(f32(f32(f32(v[0] * v[0]) + f32(v[1] * v[1])) + f32(v[2] * v[2]))));
          const hi = C.F964_BLEND_HI, lo = C.F964_PUSH;
          let t = 0;
          if (lo < vl) t = hi <= vl ? 1 : f32(f32(vl - lo) / f32(hi - lo));
          t = f32(1 - t);
          const i = f32(1 / ul);
          const un = [f32(u[0] * i), f32(u[1] * i), f32(u[2] * i)];
          const o = new Float32Array([nx, ny, nz]);
          slerpDir(t, o, o, un);
          nx = o[0]; ny = o[1]; nz = o[2];
        }
      }
      const k = -C.F964_PUSH;
      const pushY = f32(C.F964_PUSH * ny);
      const horiz = C.AIR_DAMP_START <= p.sinceJump || C.AIR_DAMP_START <= air;
      v[0] = f32(v[0] + (horiz ? f32(nx * k) : 0));
      v[1] = f32(v[1] - pushY);
      v[2] = f32((horiz ? f32(nz * k) : 0) + v[2]);
    }
  } else {
    // 본체+0x745 ? 0.96 : (JumpGimmick+0x30 ? 1.0 : 0.935) — 점프 기믹 없음
    const k = p.airDampAlt ? C.AIR_DAMP_XZ_ALT : C.AIR_DAMP_XZ;
    const y = f32(C.AIR_DAMP_Y * v[1]);
    v[2] = f32(k * v[2]);
    v[0] = f32(k * v[0]);
    v[1] = f32(y - C.AIR_DAMP_Y_SUB);
  }
}
