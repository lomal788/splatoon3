// 담당: [physics] — 이동 속도 갱신 0x710245b2b4(일반 경로)와 공중/접지 보정 0x710245f964.
// 근거: docs/player/movement_physics.md §6.1~6.5, 디컴파일 analysis/decomp/move/move_full_main.c 10277~12773행.
// 연산마다 f32 반올림, 디컴파일의 연산 순서를 그대로 따른다(FMA 없음 — §9.4).
import { directionSlerp } from "../camera/native_math.ts";
import { f32, type Vec3 } from "../fmath.ts";
import * as C from "./consts.ts";
import { curve, squidSpeedK } from "./gear.ts";
import type { MoveHistoryEntry, PlayerState } from "./state.ts";
import { isSquidMove } from "./states.ts";

/** sead 방향 보간 0x7101252ff0(t, out, a, b, axis = null): 크기는 선형, 방향은 sead 사인·아탄 표 계산(movement_physics.md §6.3.3). */
export function slerpDir(t: number, out: Vec3, a: ArrayLike<number>, b: ArrayLike<number>): Vec3 {
  const r = directionSlerp(t, a, b);
  out[0] = r[0]; out[1] = r[1]; out[2] = r[2];
  return out;
}

/** 아군 잉크 속 잠복 0x7102458cfc: 상태 ∈ S(Surprise 제외) && 천장 타이머 ≤ 0 && 발밑 분류 아군. 코옵·레일·토관 조건은 없음. */
export function squidInk(p: PlayerState): boolean {
  return isSquidMove(p.state) && p.state !== 0x88 && p.ceilTimer <= 0 && p.step.cls < 2;
}

/** 상승 중: vs + jump3d.y > 0.001 && +0x734 < +0x77c && StepPaint+0x30 ∉ {2,3} (§6.8.2) */
export function rising(p: PlayerState): boolean {
  return C.VY_EPS < f32(p.vy + p.jump3d[1]) && p.sinceJump < p.jumpKeep && p.step.cls !== 2 && p.step.cls !== 3;
}

/** 롤로 떠서 발사 높이 위에 있는 동안: L+0x3c && !L+0x41 && L+0x3f && 액터 높이 ≥ L+0x30 */
export function rollAirborne(p: PlayerState): boolean {
  const L = p.launch;
  return L.active && !L.wallJump && L.wasSquid && !(p.pos[1] < L.height);
}

/**
 * 입력 함수 0x710249f494 의 스틱 부분: 본체+0x786(직전 +0x785 기준, 0x71024a0564), 스틱 공급(잠금·덮어쓰기),
 * 기록·데드존(0x71024a0850~0x71024a093c). 원본 실행 3009건 비트 일치식(§6.3.2).
 */
export function inputStick(p: PlayerState, srcX: number, srcY: number): void {
  p.squidHoldFrames = p.squidInput ? (p.squidHoldFrames >= C.SQUID_HOLD_MAX ? C.SQUID_HOLD_MAX : p.squidHoldFrames + 1) : 0;
  p.stickSrc[0] = f32(srcX);
  p.stickSrc[1] = f32(srcY);
  let x = 0, y = 0;
  if (p.state !== 0x10e && p.stickLock < 1) {
    if (p.launch.lock > 0) { x = p.launch.lockStick[0]; y = p.launch.lockStick[1]; }
    else { x = p.stickSrc[0]; y = p.stickSrc[1]; }
  }
  p.stick[0] = x;
  p.stick[1] = y;
  const len = f32(Math.sqrt(f32(f32(y * y) + f32(x * x))));
  let m: number;
  if (len <= C.STICK_DEADZONE) m = 0;
  else if (len >= 1) m = 1;
  else {
    const d = f32(1 - C.STICK_DEADZONE);
    m = d === 0 ? 0 : f32(f32(len - C.STICK_DEADZONE) / d);
  }
  const prev = p.stickMagSmooth;
  p.stickMagSmooth = prev > m ? f32(prev + f32(f32(m - prev) * C.STICK_FALL)) : m;
  p.stickMag01 = m;
}

const sgn1 = (v: number): number => (v >= 0 ? 1 : -1);

/**
 * 벽 입력 계수 0x71024a7100(S = 본체+0x474, N = 본체+0x180, D = 본체+0xd40, C = 카메라 기저 Y).
 * +0x484 = S+0x10, +0x488 = S+0x14. 원본 실행 6000건 비트 일치식(§6.3.2).
 */
export function wallInputUpdate(p: PlayerState, cam: ArrayLike<number>): void {
  const N = p.floorN, D = p.fwdAxis;
  const nx = N[0], ny = N[1], nz = N[2], dx = D[0], dy = D[1], dz = D[2], cx = cam[0], cy = cam[1], cz = cam[2];
  const sx = p.stick[0], sy = p.stick[1];
  const ax = Math.abs(sx), sgx = sgn1(sx);
  const wx = f32(f32(ny * dz) - f32(nz * dy));
  const wy = f32(f32(nz * dx) - f32(dz * nx));
  const wz = f32(f32(dy * nx) - f32(ny * dx));
  const e = f32(f32(f32(wx * cx) + f32(wy * cy)) + f32(wz * cz));
  const f = f32(f32(f32(dx * cx) + f32(dy * cy)) + f32(dz * cz));
  const ay = Math.abs(sy), ae = Math.abs(e), sge = sgn1(e), af = Math.abs(f);
  if (!(ny < C.FLOOR_NY)) {
    let o10 = f32(p.wallInputDir + -1);
    if (o10 <= 0) o10 = 0;
    let o14 = f32(p.wallInput - C.WALL_INPUT_DECAY);
    if (o14 <= 0) o14 = 0;
    p.wallInputDir = o10;
    p.wallInput = o14;
    return;
  }
  let w = f32(1 - ny);
  if (w > 1) w = 1;
  const a = f32(f32(f32(sgx * 0.5) * sge) + 0.5);
  const t1 = f32(w * f32(ax * f32(f32(ae * a) + -0.5)));
  const sgf = sgn1(f);
  const s16 = sy >= 0 ? sgf : -sgf;
  const t2 = f32(w * f32(ay * f32(f32(af * f32(0.5 - s16)) + -0.5)));
  const s20 = f32(t1 + t2);
  p.wallInputDir = s20 < -1 ? -1 : s20 > 1 ? 1 : s20;
  let g: number;
  if (f < 0) g = af;
  else {
    const r = ae <= 0 ? 0 : C.WALL_INPUT_E <= ae ? 1 : f32(ae / C.WALL_INPUT_E);
    const k = f32(C.WALL_INPUT_G + f32(f32(1 - C.WALL_INPUT_G) * r));
    g = af <= 0 ? 0 : k <= af ? 1 : k === 0 ? 0 : f32(af / k);
  }
  let pm = f32(-sgx);
  pm = f32(sge * pm);
  const q0 = f32(f32((pm > 0 ? pm : 0) + -0.5));
  const s2 = f32(ax * f32(f32(ae * q0) + 0.5));
  const q = f32(f32(f32((s16 > 0 ? s16 : 0) + -0.5) * g) + 0.5);
  const s1 = f32(s2 + f32(ay * q));
  p.wallInput = s1 < 0 ? 0 : s1 > 1 ? 1 : s1;
}

/** 이동 이력 1항목 추가(입력 함수, [0x71058bbb82] = 1 경로) — §6.4.2 */
export function pushHistory(p: PlayerState): void {
  const v = p.vel;
  let x = v[0], z = v[2], y = 0;
  const l = f32(Math.sqrt(f32(f32(f32(x * x) + 0) + f32(z * z))));
  const wall = p.floorN[1] < C.FLOOR_NY;
  if (0 < l) {
    const i = f32(1 / l);
    x = f32(x * i); y = f32(i * 0); z = f32(z * i);
  }
  const speed = C.FLOOR_NY <= p.floorN[1]
    ? f32(Math.sqrt(f32(f32(f32(v[0] * v[0]) + f32(v[1] * v[1])) + f32(v[2] * v[2]))))
    : f32(v[1] + p.jump3d[1]);
  const H = p.history, cap = H.buf.length;
  if (!(H.count < cap)) {
    H.start = H.start + 1 < cap ? H.start + 1 : 0;
    H.count--;
  }
  let i = H.start + H.count;
  if (cap <= i) i -= cap;
  H.count++;
  const e = H.buf[i];
  e.dir[0] = x; e.dir[1] = y; e.dir[2] = z;
  e.speed = speed;
  e.squidInk = squidInk(p);
  e.wall = wall;
}

/** 최신 항목부터 k번째(0 = 최신) */
export function historyAt(p: PlayerState, k: number): MoveHistoryEntry {
  const H = p.history, cap = H.buf.length;
  let i = H.start + H.count - 1 - k;
  if (cap <= i) i -= cap;
  return H.buf[i];
}

/**
 * 입력 함수의 나머지: 벽 입력 계수, 이동 이력, 연속 발사 횟수 리셋(§6.8.1), 잠복 연속 프레임 +0x790(0x71024a4318),
 * 스틱 잠금 +0xaec 감소, 사격 자세 유지 +0xad8 = max(x − 1, 조건값), 카메라 리셋 래치 +0xab0.
 */
export function inputPost(p: PlayerState, cam: ArrayLike<number>, frame: number, aimCond: number, camResetPressed = false): void {
  wallInputUpdate(p, cam);
  p.stickLock = Math.max(p.stickLock, 1) - 1;
  p.aimHold = Math.max(p.aimHold - 1, aimCond);
  p.camResetLatch = camResetPressed;
  pushHistory(p);
  const L = p.launch;
  if (0 < L.count) {
    if (!isSquidMove(p.state) || ((L.frame + C.LAUNCH_RESET_FRAMES) | 0) < Math.max(frame | 0, 0)) L.count = 0;
  }
  if (isSquidMove(p.state) && (squidInk(p) || rising(p))) p.squidInkFrames = Math.max(p.squidInkFrames, 0) + 1;
  else p.squidInkFrames = (p.squidInkFrames >= 1 ? 0 : p.squidInkFrames) - 1;
}

/** 메인 계산 시작부 0x7102477780~0x71024778a4: 발사 활성 해제, 덮어쓰기 스틱 프레임 감소. */
export function launchPre(p: PlayerState): void {
  const L = p.launch;
  if (L.active || L.active2) {
    // 대시 패널 없음, [본체+0xa668]+0x1b8 == −1(원격 아님)으로 둔다
    if (!L.apply && 1 <= p.groundFrames && !(C.VY_EPS < p.vy)) {
      L.active = false;
      L.active2 = false;
    } else if (!(p.state >= 0x82 && p.state <= 0x90)) L.active = false;
  }
  L.lock = Math.max(L.lock, 1) - 1;
}

const TMP = new Float32Array(3);

/**
 * 입력 기준 전방 축(본체+0xd40)과 이동 방향·입력 크기(본체+0xd30/+0xd3c).
 * aim = 본체+0x538(카메라 리그 수평 시선), right = PlayerCamera+0x68 이 가리키는 벡터(카메라 오른쪽으로 추정).
 */
export function updateInputDir(p: PlayerState, aim: ArrayLike<number>, right: ArrayLike<number>): void {
  if (!p.camResetLatch) {
    p.fwdBlend = f32(C.FWD_BLEND_STEP + p.fwdBlend);
    if (p.fwdBlend > 1) p.fwdBlend = 1;
  } else p.fwdBlend = 0;
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
  const L = p.launch;
  if (L.lock === C.STICK_LOCK_WALLJUMP) {
    L.lockAxis[0] = TMP[0]; L.lockAxis[1] = TMP[1]; L.lockAxis[2] = TMP[2];
    L.lockK = len;
  }
  if (0 < L.lock) { TMP[0] = L.lockAxis[0]; TMP[1] = L.lockAxis[1]; TMP[2] = L.lockAxis[2]; }
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
    const k = squidSpeedK(pp, 0); // 특수 상태 0x16 없음 → 인자 bit0 = 0
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
  const launchRoll = rollAirborne(p);
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
    // (본체+0xad8 ≥ 1 && 상태 ∉ S) || 전역/플래그(없음)
    if (1 <= p.aimHold && !isSquidMove(p.state)) {
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
  if (rollAirborne(p)) return;
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
