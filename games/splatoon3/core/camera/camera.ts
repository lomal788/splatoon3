// spl:PlayerCamera(vtable 0x7105633960) 1인 연습용 재구현. 프레임 순서·식은 docs/camera/player_camera.md §5~§6.8,
// 원문 analysis/decomp/camrest/cam_main_full.c(0x71024d9ae8 메인 1~3652행, 0x71024e0178 입력 3653~6297행),
// analysis/decomp/camera/batch1.c(리셋 0x71024d6598, 리그 0x71024d6e84, 붐 0x71024d8f94).
// 구현 범위·생략·이식 차이는 docs/impl/camera.md.
import { Layer, type CollisionWorld } from "../types.ts";
import type { PadState } from "../input.ts";
import { bias, clamp01, invLerp01 } from "./curves.ts";
import { aimDirection, aimPitchDeg, pitchAngleToP, pitchMaxDeg } from "./pitch.ts";
import { blendedRig, elevationDeg, rigPose, RIG, type RigValues } from "./rig.ts";

/** 바닥 법선 한계(0x71058bc4e0)와 벽 쪽 한계(0x71058bc4e8). */
const FLOOR_NY = 0.64144969;
const WALL_NY = 0.08541697;
/** 공중 프레임 임계(0x71058bbc20 = 4). */
const AIR_FRAMES = 4;
/** 점프 초기 속도(0x71058bbc60 = 0.115) — 수직 추종 비율의 분모. */
const JUMP_VEL = 0.115;
/** 사람 형태 FOV 목표(본체+0x6dc). writer 미발견, 리셋값 55와 같다고 둠 [추정]. */
const HUMAN_FOV = 55;
/** 붐 형상 질의 근사: 구 반경(=near 0.2, 근평면이 벽을 덜 파고들게) [웹 선택], 대상 레이어 [추정]. */
export const BOOM_PROBE_RADIUS = 0.2;
export const BOOM_PROBE_MASK = Layer.Ground;

/** shared "player"(physics)에서 카메라가 읽는 필드. 없으면 기본값. 원본 본체 오프셋은 docs/impl/camera.md. */
export interface CameraPlayerInput {
  pos: ArrayLike<number>;
  forward?: ArrayLike<number>;
  floorNormal?: ArrayLike<number>;
  /** 본체+0x1cc (표면 법선 y, 본체+0x1c8 의 y) */
  surfaceNormalY?: number;
  velY?: number;
  jumpVel3dY?: number;
  moveVel?: ArrayLike<number>;
  airFrames?: number;
  airRatio?: number;
  squid?: boolean;
  formHeight?: number;
}

/** shared "camera" 에 쓰는 값. */
export interface CameraShared {
  /** 조준 수평 방향(+0x18c)의 yaw(라디안): forward = (sin yaw, 0, cos yaw). */
  yaw: number;
  /** 조준 피치(라디안, 위 +) = 0x7102551780 기본 곡선(p). */
  pitch: number;
  /** 피치 정규값 p(+0x16c) -1..1 */
  pitchNorm: number;
  /** 피치 누적각 s(+0x150c, 도) */
  pitchAngleDeg: number;
  /** 조준 수평 단위벡터(+0x18c) */
  aimForward: Float32Array;
  /** 리그 수평 시선(+0x1a4). 탄 생성 조준(0x71024aff7c param_4=1)의 기준 */
  rigForward: Float32Array;
  /** 3D 조준 방향 = rigForward 를 pitch 만큼 올린 단위벡터(0x7102551fe0). 흔들림 회전 전 */
  aimDir: Float32Array;
  pos: Float32Array;
  target: Float32Array;
  /** 수직 FOV(도) */
  fov: number;
  near: number;
  far: number;
  /** 직전 스텝 값(렌더 보간용) */
  prevPos: Float32Array;
  prevTarget: Float32Array;
  prevFov: number;
  squidBlend: number;
  boomRatio: number;
}

const v3 = (x = 0, y = 0, z = 0): Float32Array => Float32Array.of(x, y, z);

export class PlayerCamera {
  readonly out: CameraShared = {
    yaw: 0,
    pitch: 0,
    pitchNorm: 0,
    pitchAngleDeg: 0,
    aimForward: v3(0, 0, 1),
    rigForward: v3(0, 0, 1),
    aimDir: v3(0, 0, 1),
    pos: v3(),
    target: v3(),
    fov: RIG.fov,
    near: 0.2,
    far: 2000,
    prevPos: v3(),
    prevTarget: v3(),
    prevFov: RIG.fov,
    squidBlend: 0,
    boomRatio: 1,
  };

  initialized = false;
  private track = v3(); // +0x120
  private trackPrev = v3(); // +0x12c
  private normal = v3(0, 1, 0); // +0x138
  private p = 0; // +0x16c
  private pFollow = 0.2; // +0x168
  private s = 0; // +0x150c
  private rigAt = v3(); // +0x177c (y = 지연 추종된 +0x1780)
  private rigCam = v3(); // +0x1770 (y = +0x1774)
  private desiredAtY = 0; // +0x1788
  private vFollow = 0.25; // +0x1518
  private vFollowBoost = 0; // +0x151c
  private elevA: number = RIG.elevA; // +0x15e0
  private elevUp: number = RIG.elevUp; // +0x15e4
  private elevDown: number = RIG.elevDown; // +0x15dc
  private squidW = 0; // +0x1764
  private squidAccOn = 0; // +0x1768
  private squidAccOff = 0; // +0x176c
  private acc1558 = 0; // +0x1558
  private slopeU = 0; // +0x14d0
  private boomRatio = 1; // +0x14c4
  private boomRatioTarget = 1; // +0x14c8
  private boomLength = 0; // +0x14cc
  private boomRate = 1; // +0x14c0
  private boomUnder = 1; // +0x14f0
  private boomSpd = 0; // +0x14f4
  private viewTurn = 0; // +0x14bc
  private viewDir = v3(0, 0, 1); // *(+0x68)+0x18
  private prevViewDir = v3(); // +0x14b0
  private prevRigCam = v3(); // +0x1498
  private prevRigAt = v3(); // +0x14a4
  private hitN = v3(0, 0, -1); // 마지막 적중 법선(부호 반전)

  private readonly rv: RigValues = { H: 0, F: 0, D: 0, S: 0 };
  private readonly rt: RigValues = { H: 0, F: 0, D: 0, S: 0 };
  private readonly at0 = v3();
  private readonly cam0 = v3();
  private readonly pivot = v3();
  private readonly dir = v3();
  private readonly qFrom = v3();
  private readonly qTo = v3();

  /** 리셋 0x71024d6598. isRestart = 재시작(리스폰 등) 비트: 0이면 p 추종 비율을 0.2 로, 1이면 1.0 으로 둔다. */
  reset(pl: CameraPlayerInput | null, isRestart: boolean, dir?: ArrayLike<number>): void {
    const o = this.out;
    o.fov = RIG.fov;
    o.near = 0.2;
    o.far = 2000;
    const pos = pl?.pos ?? [0, 0, 0];
    this.track.set([pos[0], pos[1], pos[2]]);
    this.trackPrev.set(this.track);
    const n = pl?.floorNormal ?? [0, 1, 0];
    this.normal.set([n[0], n[1], n[2]]);
    this.pFollow = isRestart ? 1 : 0.2;
    this.p = 0;
    this.s = 0;
    const d = dir ?? pl?.forward ?? [0, 0, 1];
    const l = Math.hypot(d[0], d[2]);
    if (l > 0) o.aimForward.set([d[0] / l, 0, d[2] / l]);
    else o.aimForward.set([0, 0, 1]);
    o.rigForward.set(o.aimForward);
    this.elevA = RIG.elevA;
    this.elevUp = RIG.elevUp;
    this.elevDown = RIG.elevDown;
    this.vFollow = 0.25;
    this.vFollowBoost = 0;
    this.acc1558 = 0;
    this.rig(pl);
    this.rigAt.set(this.at0);
    this.rigCam.set(this.cam0);
    this.desiredAtY = this.rigAt[1];
    o.pos.set(this.rigCam);
    o.target.set(this.rigAt);
    this.boomLength = this.boomDef(pl, true);
    this.boomRatio = this.boomRatioTarget = 1;
    this.boomRate = 1;
    this.boomUnder = 1;
    this.boomSpd = 0;
    for (let i = 0; i < 3; i++) this.prevViewDir[i] = o.pos[i] - o.target[i];
    this.viewTurn = 0;
    this.prevRigCam.set(this.rigCam);
    this.prevRigAt.set(this.rigAt);
    this.finishOutput();
    o.prevPos.set(o.pos);
    o.prevTarget.set(o.target);
    o.prevFov = o.fov;
    this.initialized = true;
  }

  step(pl: CameraPlayerInput | null, pad: PadState, collision: CollisionWorld | null): void {
    const o = this.out;
    if (!this.initialized) this.reset(pl, false);
    o.prevPos.set(o.pos);
    o.prevTarget.set(o.target);
    o.prevFov = o.fov;

    // 추종 위치·바닥 법선 (메인 앞부분 228~360행)
    this.trackPrev.set(this.track);
    const pos = pl?.pos ?? [0, 0, 0];
    this.track.set([pos[0], pos[1], pos[2]]);
    const fn = pl?.floorNormal ?? [0, 1, 0];
    this.followNormal(fn);

    this.input(pad);

    // 오징어 블렌드 가중치 +0x1764 (500~545행)
    const squid = !!pl?.squid;
    const air = (pl?.airFrames ?? 0) >= AIR_FRAMES;
    const inc = air ? 0.001 : 0.025;
    if (squid) {
      this.squidAccOn = Math.min(this.squidAccOn + inc, 0.2);
      this.squidAccOff = 0;
      this.squidW += this.squidAccOn * (1 - this.squidW);
    } else {
      this.squidAccOff = Math.min(this.squidAccOff + inc, 0.2);
      this.squidAccOn = 0;
      this.squidW += this.squidAccOff * (0 - this.squidW);
    }
    this.acc1558 = Math.min(this.acc1558 + inc, 0.2);

    // FOV·고각 목표 (1056~1126행)
    const u = Math.min(1 - this.normal[1], 1);
    const rate = Math.min(squid ? this.squidAccOn : this.squidAccOff, this.acc1558);
    const tUp = squid ? u * 40 + 20 : 60;
    const tDown = squid ? u * -15 - 60 : -75;
    const tA = squid ? 0 : -7.5;
    this.elevUp += rate * (tUp - this.elevUp);
    this.elevA += rate * (tA - this.elevA);
    this.elevDown += rate * (tDown - this.elevDown);
    o.fov += rate * ((squid ? RIG.squid.fov : HUMAN_FOV) - o.fov);

    this.rig(pl);
    this.verticalFollow(pl);
    this.boom(pl, collision);
    this.finishOutput();
  }

  /** 입력 0x71024e0178 중 마우스로 대체되는 부분. docs/impl/camera.md "입력 이식 차이". */
  private input(pad: PadState): void {
    const o = this.out;
    const fr = o.fov / RIG.fov;
    const fovRatio = fr < 0 ? 0 : fr > 1 ? 1 : fr;
    const yaw = pad.lookYaw * fovRatio;
    if (yaw !== 0) {
      const f = o.aimForward;
      const c = Math.cos(yaw), s = Math.sin(yaw);
      const x = f[0] * c + f[2] * s;
      const z = f[2] * c - f[0] * s;
      const l = Math.hypot(x, z);
      f[0] = x / l;
      f[1] = 0;
      f[2] = z / l;
    }
    const ds = pad.lookPitch * 57.29578 * fovRatio;
    const yEq = Math.min(Math.abs(ds) / pitchMaxDeg(0), 1);
    this.pFollow += (1 - this.pFollow) * yEq * 0.2;
    let s = this.s + ds;
    s = s > 90 ? 90 : s < -90 ? -90 : s;
    const [pt, corr] = pitchAngleToP(s - 75, 0, false, 0, 0, true);
    this.s = s + corr;
    this.p += this.pFollow * (pt - this.p);
    o.rigForward.set(o.aimForward);
  }

  /** 카메라 바닥 법선 +0x138 ← 플레이어 +0x180 쪽으로 0.1 (0x7101252ff0 [보간 방식 추정: 선형 후 정규화]). */
  private followNormal(fn: ArrayLike<number>): void {
    const n = this.normal;
    for (let i = 0; i < 3; i++) n[i] += (fn[i] - n[i]) * 0.1;
    const l = Math.hypot(n[0], n[1], n[2]);
    if (l > 0.001 && Math.abs(l - 1) > 0.01) for (let i = 0; i < 3; i++) n[i] /= l;
  }

  private rig(pl: CameraPlayerInput | null): void {
    const u = Math.min(1 - this.normal[1], 1);
    const v = blendedRig(this.p, this.squidW, u, this.rv, this.rt);
    v.H += pl?.formHeight ?? 0;
    const el = elevationDeg(this.p, this.elevA, this.elevUp, this.elevDown);
    rigPose(this.track, this.out.rigForward, v, el, this.at0, this.cam0);
  }

  /** 수직 추종 (1660~1850행 일반 경로). rigAt/rigCam 을 채운다. */
  private verticalFollow(pl: CameraPlayerInput | null): void {
    let ratio = ((pl?.velY ?? 0) + (pl?.jumpVel3dY ?? 0)) / JUMP_VEL;
    if (ratio > 1) ratio = 1;
    let target: number;
    if (ratio <= 0) target = ratio === 0 ? 0.25 : ratio <= -1 ? 0.7 : ratio * -0.45 + 0.25;
    else {
      const q = -0.22;
      const ny = pl?.floorNormal?.[1] ?? 1;
      let g = 1;
      if (ny <= 0) g = 0.3;
      else if (ny < FLOOR_NY) {
        const r = ny / FLOOR_NY;
        g = Math.abs(r) >= 0.001 ? bias(r, 0.3) * 0.7 + 0.3 : 0.3;
      }
      target = q * ratio * g + 0.25;
    }
    if (this.vFollow <= target) target = this.vFollow + (target - this.vFollow) * 0.01;
    this.vFollow = target;
    this.vFollowBoost *= 0.9;
    if (target <= this.vFollowBoost) target = this.vFollowBoost;
    this.vFollow = target;
    let r = 0.3 - this.boomUnder * 0.3;
    if (r <= target) r = target;
    const desired = this.at0[1];
    const cur = this.rigAt[1];
    const k = r <= 1 || desired <= cur ? r : 1;
    const atY = cur + (desired - cur) * k;
    this.rigAt[0] = this.at0[0];
    this.rigAt[1] = atY;
    this.rigAt[2] = this.at0[2];
    this.desiredAtY = desired;
    this.rigCam[0] = this.cam0[0];
    this.rigCam[1] = this.cam0[1] - (desired - atY);
    this.rigCam[2] = this.cam0[2];
  }

  /**
   * 붐 정의 0x71024d8f94: 피벗(pivot)·방향(dir)·길이 반환, minDist·e 는 this 에 남김.
   * 생략: 다운·수몰 높이(본체+0xdf4/+0xe10), Jetpack·SuperLanding 보정, 충돌 밀림 오프셋(+0x144, 0으로 둠).
   */
  private minDist = 0.8;
  private boomE = 0;
  private boomDef(pl: CameraPlayerInput | null, noDecay: boolean): number {
    let u = Math.min(1 - this.normal[1], 1);
    if (!noDecay && u <= this.slopeU && u < this.slopeU - 0.02) u = this.slopeU - 0.02;
    this.slopeU = u;
    const form = pl?.formHeight ?? 0;
    const py = pl?.pos?.[1] ?? this.track[1];
    let lift = py - this.track[1];
    if (lift <= 0) lift = 0;
    const base = form - lift;
    const atY = this.rigAt[1];
    const br = this.boomRatio;
    const ramp = br < 1 ? (br - 0.2) / 0.8 : 1;
    let h = this.squidW * (1 - u) * (br > 0.2 ? ramp : 0) - 0.5;
    h = atY - base + h + u * (-1.5 - h);
    const desired = this.desiredAtY;
    this.boomE = desired <= atY ? -form : -form + (desired - atY);
    let py2 = desired <= atY ? h : desired - atY + h;
    const pv = this.pivot;
    pv[0] = this.rigAt[0];
    pv[2] = this.rigAt[2];
    if (this.p < 0) {
      const t = Math.abs(this.p) >= 0.001 ? bias(-this.p, 0.4) : 0;
      const m = -(1 - this.squidW) * 0.9 * t;
      const a = this.out.aimForward;
      pv[0] += a[0] * m;
      py2 += a[1] * m;
      pv[2] += a[2] * m;
    }
    pv[1] = py2;
    let dx = this.rigCam[0] - pv[0], dy = this.rigCam[1] - pv[1], dz = this.rigCam[2] - pv[2];
    let l = Math.hypot(dx, dy, dz);
    if (l > 0) {
      dx /= l;
      dy /= l;
      dz /= l;
    }
    const n = this.normal;
    const dn = dx * n[0] + dy * n[1] + dz * n[2];
    let k = dn <= 0 ? 0.8 : dn >= 1 ? 0 : 0.8 - dn * 0.8;
    const ny = pl?.surfaceNormalY ?? pl?.floorNormal?.[1] ?? 1;
    if (FLOOR_NY <= ny) k *= u;
    else k *= Math.abs(u) >= 0.001 ? Math.sign(u) * Math.pow(Math.abs(u), 0.15200314) : 0;
    pv[0] += n[0] * k;
    pv[1] += n[1] * k;
    pv[2] += n[2] * k;
    const d = this.dir;
    d[0] = this.rigCam[0] - pv[0];
    d[1] = this.rigCam[1] - pv[1];
    d[2] = this.rigCam[2] - pv[2];
    l = Math.hypot(d[0], d[1], d[2]);
    if (l > 0) for (let i = 0; i < 3; i++) d[i] /= l;
    if (l < 0.001) d.set(this.out.aimForward);
    this.minDist = 0.8;
    return l <= 0.001 ? 0.001 : l;
  }

  /** 붐 질의·거리 비율·위치 반영 (2150~3530행). 질의 1·전진 오징어 계수(+0x14ec)는 생략 → 질의 2 시작 오프셋 0.8. */
  private boom(pl: CameraPlayerInput | null, col: CollisionWorld | null): void {
    const o = this.out;
    const len = this.boomDef(pl, false);
    this.boomLength = len;
    const pv = this.pivot, d = this.dir;
    const off = 0.8;
    let hitDist = len;
    const rest = Math.max(len - off, 0);
    if (col && rest > 0) {
      const a = this.qFrom, b = this.qTo;
      for (let i = 0; i < 3; i++) {
        a[i] = pv[i] + d[i] * off;
        b[i] = a[i] + d[i] * rest;
      }
      const hit = col.sweepSphere(a, b, BOOM_PROBE_RADIUS, BOOM_PROBE_MASK);
      if (hit) {
        hitDist = Math.max(this.minDist, off + hit.t * rest);
        for (let i = 0; i < 3; i++) this.hitN[i] = -hit.normal[i];
      }
    }

    // 최소거리 미달 정도 +0x14f0
    const c = this.minDist / len;
    const r = this.boomRatioTarget;
    let under: number;
    if (c <= 1) under = r <= c ? 0 : r < 1 && 1 - c !== 0 ? (r - c) / (1 - c) : 1;
    else under = 1 - (r <= 1 ? 0 : r < c && c - 1 !== 0 ? (r - 1) / (c - 1) : 1);
    this.boomUnder = under;

    // 복귀 속도 spd (2960~3048행)
    const mx = this.track[0] - this.trackPrev[0];
    let my = this.track[1] - this.trackPrev[1];
    const mz = this.track[2] - this.trackPrev[2];
    if ((pl?.airFrames ?? 0) >= AIR_FRAMES) my -= pl?.velY ?? 0;
    const along = Math.abs((mx * d[0] + my * d[1] + mz * d[2]) * ((pl?.airRatio ?? 0) * -0.7 + 1)) * 0.5;
    const vd = this.viewDir, pd = this.prevViewDir;
    const cx = vd[1] * pd[2] - vd[2] * pd[1];
    const cy = vd[2] * pd[0] - vd[0] * pd[2];
    const cz = vd[0] * pd[1] - vd[1] * pd[0];
    const ang = Math.atan2(Math.hypot(cx, cy, cz), vd[0] * pd[0] + vd[1] * pd[1] + vd[2] * pd[2]);
    const turn = ang > 0 ? (ang >= 0.01 ? 1 : ang / 0.01) : 0;
    this.viewTurn += (turn - this.viewTurn) * 0.2;
    this.prevViewDir.set(vd);
    let spd = this.viewTurn * (0.05 + this.boomUnder * (0.01 - 0.05));
    if (spd <= this.boomSpd) spd = this.boomSpd + (spd - this.boomSpd) * 0.02;
    this.boomSpd = spd;
    if (spd <= along) spd = along;

    const denom = Math.max(this.minDist, this.boomLength * this.boomRatioTarget);
    const hr = hitDist / this.boomLength;
    const lim = hr >= 0 ? Math.min(hr, 1) : 0;
    this.boomRatioTarget += spd / denom;
    const tgt = Math.min(this.boomRatioTarget, lim);
    let rate: number;
    if (this.boomRatio <= tgt) {
      const df = tgt - this.boomRatio;
      rate = df <= 0 ? 0.1 : df >= 1 ? 0.25 : df * 0.15 + 0.1;
      rate += tgt * (1 - rate);
      if (this.boomRate <= rate) rate = this.boomRate + (rate - this.boomRate) * 0.05;
    } else rate = this.shrinkRate(pl, tgt);
    this.boomRate = rate;
    this.boomRatioTarget = Math.min(this.boomRatioTarget, hr);
    this.boomRatio += rate * (this.boomRatioTarget - this.boomRatio);

    // 위치 반영 (3500~3530행)
    const L = this.boomRatio * len;
    for (let i = 0; i < 3; i++) o.pos[i] = d[i] * L + pv[i];
    const dA = Math.hypot(pv[0] - o.pos[0], pv[2] - o.pos[2]);
    const dR = Math.hypot(pv[0] - this.rigCam[0], pv[2] - this.rigCam[2]);
    if (dR > 0) o.pos[1] -= (this.boomE * (dR - dA)) / dR;
    o.target.set(this.rigAt);
    if (this.boomRatio < 0.999) {
      const w = invLerp01(FLOOR_NY, WALL_NY, this.normal[1]);
      const py = pl?.pos?.[1] ?? this.track[1];
      const k = w * (py - this.rigAt[1] + 0.4) - 0.4;
      o.target[1] += k + this.boomRatio * (0 - k);
    }
    this.prevRigCam.set(this.rigCam);
    this.prevRigAt.set(this.rigAt);
  }

  /** 붐이 줄어들 때 평활 비율 (3071~3241행). n = 적중 법선 반대(붐 방향 쪽). */
  private shrinkRate(pl: CameraPlayerInput | null, tgt: number): number {
    const n = this.hitN, a = this.out.aimForward;
    const dcx = this.rigCam[0] - this.prevRigCam[0];
    const dcy = this.rigCam[1] - this.prevRigCam[1];
    const dcz = this.rigCam[2] - this.prevRigCam[2];
    const dax = this.rigAt[0] - this.prevRigAt[0];
    const day = this.rigAt[1] - this.prevRigAt[1];
    const daz = this.rigAt[2] - this.prevRigAt[2];
    const rx = dcx - dax, ry = dcy - day, rz = dcz - daz;
    const nr = n[0] * rx + n[1] * ry + n[2] * rz;
    const na = n[0] * dax + n[1] * day + n[2] * daz;
    let side =
      (a[2] - n[2]) * (rz - n[2] * nr) + (a[0] - n[0]) * (rx - n[0] * nr) + (a[1] - n[1]) * (ry - n[1] * nr);
    const mv = pl?.moveVel ?? [0, 0, 0];
    let fwd = a[0] * mv[0] + a[1] * mv[1] + a[2] * mv[2];
    if (fwd <= 0) fwd = 0;
    if (side <= 0) side = 0;
    const push = side * fwd * 0.5 - (n[0] * dcx + n[1] * dcy + n[2] * dcz);
    let gap = this.boomRatio - tgt;
    if (gap <= 0) gap = 0;
    const e = (this.boomRatio - 0.5) / -0.45 - gap;
    const pushN = clamp01(push / 0.3);
    const g = clamp01((e >= 0 ? 1 - Math.min(e, 1) : 1) * pushN);
    const gB = Math.abs(g) >= 0.001 ? bias(g, 0.35) : 0;
    const back = clamp01(na / -0.2);
    const backB = Math.abs(back) >= 0.001 ? bias(back, 0.35) : 0;
    const f48 = na < -0.001 ? -1 - push / na : 1;
    let rate = f48 >= 0 ? Math.min(f48, 1) * 0.35 + 0.35 : 0.35;
    rate = Math.min(gB * 0.9 + 0.1, rate);
    const minRate = backB * 0.9 + 0.1;
    const facing = Math.abs(n[0] * a[0] + n[1] * a[1] + n[2] * a[2]);
    const fB = facing >= 0.001 ? bias(facing, 0.3) : 0;
    rate += (0.25 - rate) * fB;
    if (rate > 0.25 && tgt < this.boomRatioTarget) {
      const dd = this.boomRatioTarget - tgt;
      const ddB = Math.abs(dd) >= 0.001 ? bias(dd, 0.3) : 0;
      rate += (0.25 - rate) * ddB;
    }
    return rate <= minRate ? minRate : rate;
  }

  /** 근접 보정(2363~2378행) → 시선 방향 → 조준 방향·공유값. */
  private finishOutput(): void {
    const o = this.out;
    const a = o.aimForward;
    const dd = (o.pos[0] - o.target[0]) * a[0] + (o.pos[1] - o.target[1]) * a[1] + (o.pos[2] - o.target[2]) * a[2];
    if (dd > -0.16) {
      const k = dd + 0.16;
      for (let i = 0; i < 3; i++) o.pos[i] -= a[i] * k;
    }
    const vx = o.target[0] - o.pos[0], vy = o.target[1] - o.pos[1], vz = o.target[2] - o.pos[2];
    const l = Math.hypot(vx, vy, vz);
    if (l > 0 && Math.abs(vy / l) <= 0.9999999) this.viewDir.set([vx / l, vy / l, vz / l]);
    o.yaw = Math.atan2(a[0], a[2]);
    o.pitchNorm = this.p;
    o.pitchAngleDeg = this.s;
    o.pitch = aimPitchDeg(this.p) * 0.017453292;
    aimDirection(o.rigForward, o.pitch, o.aimDir);
    o.squidBlend = this.squidW;
    o.boomRatio = this.boomRatio;
  }
}
