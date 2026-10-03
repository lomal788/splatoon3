// spl:PlayerCamera(vtable 0x7105633960) 1인 연습용 재구현. 프레임 순서·식은 docs/camera/player_camera.md §5~§6.8,
// 원문 analysis/decomp/camrest/cam_main_full.c(0x71024d9ae8 메인 1~3652행, 0x71024e0178 입력 3653~6297행),
// analysis/decomp/camera/batch1.c(리셋 0x71024d6598, 리그 0x71024d6e84, 붐 0x71024d8f94).
// 구현 범위·생략·이식 차이는 docs/impl/camera.md.
import { Layer, type CollisionWorld, type SphereQueryFilter } from "../types.ts";
import { F, add, sub, mul, div, mix, dot, length, directionSlerp, updateBasis, power0 } from "./native_math.ts";
import { rotateY } from "../weapon/swerve.ts";
import { advanceBoom, forwardCoefficient, collisionSpring, boomPosition } from "./boom.ts";
import type { PadState } from "../input.ts";
import { bias, clamp01, invLerp01 } from "./curves.ts";
import { aimDirection, aimPitchDeg, pitchAngleToP, pitchMaxDeg } from "./pitch.ts";
import { blendedRig, elevationDeg, rigPose, RIG, type RigValues } from "./rig.ts";

/** 바닥 법선 한계(0x71058bc4e0)와 벽 쪽 한계(0x71058bc4e8). */
const FLOOR_NY = F(0.64144969);
const WALL_NY = F(0.08541697);
/** 공중 프레임 임계(0x71058bbc20 = 4). */
const AIR_FRAMES = 4;
/** 점프 초기 속도(0x71058bbc60 = 0.115) — 수직 추종 비율의 분모. */
const JUMP_VEL = F(0.11499999463558197); // original bits 0x3deb851e, r9_state_sources
/** 사람 형태 FOV 목표(본체+0x6dc). writer 미발견, 리셋값 55와 같다고 둠 [추정]. */
const HUMAN_FOV = 55;
/** Sphere/.3: r9_boom_query §6.1. near=.2 is independent. */
export const BOOM_PROBE_RADIUS = F(0.3);
export const BOOM_PROBE_MASK = Layer.Ground | Layer.KeepOut;
export const BOOM_QUERY: SphereQueryFilter = { layerIndex: 7, subIndex: 0, hitMask: 8, subMask: 0xffffffff };

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
  /** B+e4, distinct from B+114 moveVel. */
  finalVel?: ArrayLike<number>;
  /** Raw native consumers. Their scene producers are not inferred from web flags. */
  native?: CameraNativeInput;
}
export interface CameraNativeInput {
  springDelta?: ArrayLike<number>; // rig/head producer D
  bodyResidual?: ArrayLike<number>; // B210, not B1f8
  springHold?: number; // B e0c
  wall7a0?: boolean;
  ad0?: number;
  d9?: boolean;
  blend1760?: number;
  positionGateDe0?: number;
  skipQueries?: boolean; // additional native Dokan/global gates
  skipBoom?: boolean; // pipeline/a6d0+38
  minimumQueryOffset?: number; // rare state82..84 producer offS, default .8
  humanFov?: number; // B6dc producer
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
  /** Original X/Y/Z basis columns; Z points backwards. */
  right: Float32Array;
  up: Float32Array;
  viewZ: Float32Array;
  viewForward: Float32Array;
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
  prevRight: Float32Array;
  prevUp: Float32Array;
  prevViewZ: Float32Array;
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
    right: v3(1, 0, 0), up: v3(0, 1, 0), viewZ: v3(0, 0, 1), viewForward: v3(0, 0, -1),
    pos: v3(),
    target: v3(),
    fov: RIG.fov,
    near: 0.2,
    far: 2000,
    prevPos: v3(),
    prevTarget: v3(),
    prevFov: RIG.fov,
    prevRight: v3(1, 0, 0), prevUp: v3(0, 1, 0), prevViewZ: v3(0, 0, 1),
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
  private boomRate = 1; // +0x14c0
  private boomUnder = 1; // +0x14f0
  private boomSpd = 0; // +0x14f4
  private viewTurn = 0; // +0x14bc
  private viewDir = this.out.viewZ; // *(+0x68)+0x18
  private prevViewDir = v3(); // +0x14b0
  private prevRigCam = v3(); // +0x1498
  private prevRigAt = v3(); // +0x14a4
  private hitN = v3(0, 0, 1);
  private spring = v3(); // C144; raw producer inputs remain explicit
  private forwardK = 0; // C14ec

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
    this.spring.fill(0);
    this.forwardK = 0;
    this.rig(pl);
    this.rigAt.set(this.at0);
    this.rigCam.set(this.cam0);
    this.desiredAtY = this.rigAt[1];
    o.pos.set(this.rigCam);
    o.target.set(this.rigAt);
    this.boomDef(pl, true);
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
    o.prevRight.set(o.right); o.prevUp.set(o.up); o.prevViewZ.set(o.viewZ);
    this.initialized = true;
  }

  step(pl: CameraPlayerInput | null, pad: PadState, collision: CollisionWorld | null): void {
    const o = this.out;
    if (!this.initialized) this.reset(pl, false);
    o.prevPos.set(o.pos);
    o.prevTarget.set(o.target);
    o.prevFov = o.fov;
    o.prevRight.set(o.right); o.prevUp.set(o.up); o.prevViewZ.set(o.viewZ);

    // 추종 위치·바닥 법선 (메인 앞부분 228~360행)
    this.trackPrev.set(this.track);
    const pos = pl?.pos ?? [0, 0, 0];
    this.track.set([pos[0], pos[1], pos[2]]);
    const fn = pl?.floorNormal ?? [0, 1, 0];
    this.followNormal(fn);

    const native = pl?.native;
    collisionSpring(this.spring, this.track, native?.springDelta ?? [0, 0, 0],
      native?.bodyResidual ?? [0, 0, 0], pl?.finalVel ?? [0, 0, 0],
      o.aimForward, this.boomRatio, native?.springHold ?? 0);
    this.input(pad);

    // 오징어 블렌드 가중치 +0x1764 (500~545행)
    const squid = !!pl?.squid;
    const air = (pl?.airFrames ?? 0) >= AIR_FRAMES;
    const inc = air ? 0.001 : 0.025;
    if (squid) {
      this.squidAccOn = Math.min(add(this.squidAccOn, inc), F(0.2));
      this.squidAccOff = 0;
      this.squidW = mix(this.squidW, 1, this.squidAccOn);
    } else {
      this.squidAccOff = Math.min(add(this.squidAccOff, inc), F(0.2));
      this.squidAccOn = 0;
      this.squidW = mix(this.squidW, 0, this.squidAccOff);
    }
    this.acc1558 = Math.min(add(this.acc1558, inc), F(0.2));

    // FOV·고각 목표 (1056~1126행)
    const u = Math.min(sub(1, this.normal[1]), 1);
    const rate = Math.min(squid ? this.squidAccOn : this.squidAccOff, this.acc1558);
    const tUp = squid ? add(mul(u, 40), 20) : 60;
    const tDown = squid ? add(mul(u, -15), -60) : -75;
    const tA = squid ? 0 : -7.5;
    this.elevUp = mix(this.elevUp, tUp, rate);
    this.elevA = mix(this.elevA, tA, rate);
    this.elevDown = mix(this.elevDown, tDown, rate);
    o.fov = mix(o.fov, squid ? RIG.squid.fov : (native?.humanFov ?? HUMAN_FOV), rate);

    this.rig(pl);
    this.verticalFollow(pl);
    if (native?.skipBoom) { o.pos.set(this.rigCam); o.target.set(this.rigAt); }
    else this.boom(pl, collision);
    this.finishOutput();
  }

  /** 입력 0x71024e0178 중 마우스로 대체되는 부분. docs/impl/camera.md "입력 이식 차이". */
  private input(pad: PadState): void {
    const o = this.out;
    const fr = div(o.fov, RIG.fov);
    const fovRatio = fr < 0 ? 0 : fr > 1 ? 1 : fr;
    const yaw = mul(pad.lookYaw, fovRatio);
    if (yaw !== 0) {
      const f = o.aimForward;
      const rotated: [number, number, number] = [0, 0, 0];
      rotateY([f[0], f[1], f[2]], yaw, rotated);
      const l = length(rotated);
      f.set(l > 0 ? rotated.map(v => mul(v, div(1, l))) : rotated);
    }
    const ds = mul(mul(pad.lookPitch, 57.29578), fovRatio);
    const yEq = Math.min(Math.abs(ds) / pitchMaxDeg(0), 1);
    this.pFollow = add(this.pFollow, mul(mul(sub(1, this.pFollow), yEq), .2));
    let s = add(this.s, ds);
    s = s > 90 ? 90 : s < -90 ? -90 : s;
    const [pt, corr] = pitchAngleToP(s - 75, 0, false, 0, 0, true);
    this.s = add(s, corr);
    this.p = mix(this.p, pt, this.pFollow);
    o.rigForward.set(o.aimForward);
  }

  /** 0x7101252ff0: sead table slerp with null opposite-direction axis. */
  private followNormal(fn: ArrayLike<number>): void {
    this.normal.set(directionSlerp(F(.1), this.normal, fn));
  }

  private rig(pl: CameraPlayerInput | null): void {
    const u = Math.min(sub(1, this.normal[1]), 1);
    const v = blendedRig(this.p, this.squidW, u, this.rv, this.rt);
    v.H = add(v.H, pl?.formHeight ?? 0);
    const el = elevationDeg(this.p, this.elevA, this.elevUp, this.elevDown);
    rigPose(this.track, this.out.rigForward, v, el, this.at0, this.cam0);
  }

  /** 수직 추종 (1660~1850행 일반 경로). rigAt/rigCam 을 채운다. */
  private verticalFollow(pl: CameraPlayerInput | null): void {
    let ratio = div(add(pl?.velY ?? 0, pl?.jumpVel3dY ?? 0), JUMP_VEL);
    if (ratio > 1) ratio = 1;
    let target: number;
    if (ratio <= 0) target = ratio === 0 ? 0.25 : ratio <= -1 ? 0.7 : add(mul(ratio, -.45), .25);
    else {
      const q = -0.22;
      const ny = pl?.floorNormal?.[1] ?? 1;
      let g = 1;
      if (ny <= 0) g = 0.3;
      else if (ny < FLOOR_NY) {
        const r = ny / FLOOR_NY;
        g = Math.abs(r) >= 0.001 ? bias(r, 0.3) * 0.7 + 0.3 : 0.3;
      }
      target = add(mul(mul(q, ratio), g), .25);
    }
    if (this.vFollow <= target) target = mix(this.vFollow, target, .01);
    this.vFollow = target;
    this.vFollowBoost = mul(this.vFollowBoost, .9);
    if (target <= this.vFollowBoost) target = this.vFollowBoost;
    this.vFollow = target;
    let r = sub(.3, mul(this.boomUnder, .3));
    if (r <= target) r = target;
    const desired = this.at0[1];
    const cur = this.rigAt[1];
    const k = r <= 1 || desired <= cur ? r : 1;
    const atY = mix(cur, desired, k);
    this.rigAt[0] = this.at0[0];
    this.rigAt[1] = atY;
    this.rigAt[2] = this.at0[2];
    this.desiredAtY = desired;
    this.rigCam[0] = this.cam0[0];
    this.rigCam[1] = sub(this.cam0[1], sub(desired, atY));
    this.rigCam[2] = this.cam0[2];
  }

  /**
   * 붐 정의 0x71024d8f94: 피벗(pivot)·방향(dir)·길이 반환, minDist·e 는 this 에 남김.
   * 생략: 다운·수몰 높이(본체+0xdf4/+0xe10), Jetpack·SuperLanding 보정, 일부 특수 상태 공급자(impl/camera.md 참고).
   */
  private minDist = 0.8;
  private boomE = 0;
  private boomDef(pl: CameraPlayerInput | null, noDecay: boolean): number {
    let u = Math.min(sub(1, this.normal[1]), 1);
    if (!noDecay && u <= this.slopeU && u < sub(this.slopeU, .02)) u = sub(this.slopeU, .02);
    this.slopeU = u;
    const form = pl?.formHeight ?? 0;
    const py = pl?.pos?.[1] ?? this.track[1];
    let lift = sub(py, this.track[1]);
    if (lift <= 0) lift = 0;
    const base = sub(form, lift);
    const atY = this.rigAt[1];
    const br = this.boomRatio;
    const ramp = br < 1 ? div(sub(br, .2), .8) : 1;
    let h = sub(mul(mul(this.squidW, sub(1, u)), br > F(.2) ? ramp : 0), .5);
    h = add(add(sub(atY, base), h), mul(u, sub(-1.5, h)));
    const desired = this.desiredAtY;
    this.boomE = desired <= atY ? F(-form) : add(-form, sub(desired, atY));
    let py2 = desired <= atY ? h : add(sub(desired, atY), h);
    const pv = this.pivot;
    pv[0] = add(this.rigAt[0], this.spring[0]);
    pv[2] = add(this.rigAt[2], this.spring[2]);
    if (this.p < 0) {
      const t = Math.abs(this.p) >= 0.001 ? bias(-this.p, 0.4) : 0;
      const m = mul(mul(F(-sub(1, this.squidW)), .9), t);
      const a = this.out.aimForward;
      pv[0] = add(pv[0], mul(a[0], m));
      py2 = add(py2, mul(a[1], m));
      pv[2] = add(pv[2], mul(a[2], m));
    }
    pv[1] = py2;
    let dx = sub(this.rigCam[0], pv[0]), dy = sub(this.rigCam[1], pv[1]), dz = sub(this.rigCam[2], pv[2]);
    let l = length([dx, dy, dz]);
    if (l > 0) {
      const inv = div(1, l);
      dx = mul(dx, inv); dy = mul(dy, inv); dz = mul(dz, inv);
    }
    const n = this.normal;
    const dn = dot([dx, dy, dz], n);
    let k = dn <= 0 ? F(.8) : dn >= 1 ? 0 : sub(.8, mul(dn, .8));
    const ny = pl?.surfaceNormalY ?? pl?.floorNormal?.[1] ?? 1;
    if (FLOOR_NY <= ny) k = mul(k, u);
    else k = mul(k, power0(u, F(.15200314)));
    pv[0] = add(pv[0], mul(n[0], k));
    pv[1] = add(pv[1], mul(n[1], k));
    pv[2] = add(pv[2], mul(n[2], k));
    const d = this.dir;
    d[0] = sub(this.rigCam[0], pv[0]);
    d[1] = sub(this.rigCam[1], pv[1]);
    d[2] = sub(this.rigCam[2], pv[2]);
    l = length(d);
    if (l > 0) { const inv = div(1, l); for (let i = 0; i < 3; i++) d[i] = mul(d[i], inv); }
    if (l < 0.001) d.set(this.out.aimForward);
    this.minDist = add(.8, Math.max(dot(d, this.spring), 0));
    return l <= 0.001 ? 0.001 : l;
  }

  /** Two casts and C14ec/C14c0..14f4 consumers, r7/r9 original evidence. */
  private boom(pl: CameraPlayerInput | null, col: CollisionWorld | null): void {
    const o = this.out, n = pl?.native;
    const len = this.boomDef(pl, false);
    const pv = this.pivot, d = this.dir;
    let near = 0, hitDist = len;
    const blend = n?.blend1760 ?? 0;
    const cast = !!col && blend <= F(.1) && !n?.skipQueries;
    this.hitN.set(o.aimForward);
    if (cast) {
      for (let i = 0; i < 3; i++) this.qTo[i] = add(pv[i], mul(d[i], len));
      const hit = col!.sweepSphere(pv, this.qTo, BOOM_PROBE_RADIUS, BOOM_PROBE_MASK, BOOM_QUERY);
      if (hit) {
        // CollisionWorld.point is the surface contact. Native raw point adapters
        // convert pos+direction*depth before returning this common contract.
        near = sub(1, clamp01(div(sub(length([0, 1, 2].map(i => sub(hit.point[i], pv[i]))), .6), .1)));
      }
    }
    this.forwardK = forwardCoefficient(pl?.finalVel ?? [0, 0, 0], o.aimForward, !!pl?.squid, this.forwardK);
    const wall = invLerp01(FLOOR_NY, WALL_NY, this.normal[1]);
    let off = add(.8, mul(.8, clamp01(mul(mul(sub(1, near), sub(1, wall)), this.forwardK))));
    if (this.vFollow > F(.03)) off = mix(off, .8, clamp01(div(sub(this.vFollow, .03), .22)));
    off = add(Math.max(off, n?.minimumQueryOffset ?? F(.8), F(.8)), Math.max(dot(d, this.spring), 0));
    const rest = Math.max(sub(len, off), 0);
    if (cast && rest > 0) {
      for (let i = 0; i < 3; i++) {
        this.qFrom[i] = add(pv[i], mul(d[i], off));
        this.qTo[i] = add(this.qFrom[i], mul(d[i], rest));
      }
      const hit = col!.sweepSphere(this.qFrom, this.qTo, BOOM_PROBE_RADIUS, BOOM_PROBE_MASK, BOOM_QUERY);
      if (hit) {
        hitDist = Math.max(this.minDist, add(off, mul(hit.t, rest)));
        // Native point normal: entry bit0 determines sign. Web geometry supplies
        // outward normals instead, converted once to the camera's inward normal.
        const sign = hit.nativeEntryFlags === undefined ? -1 : (hit.nativeEntryFlags & 1) ? 1 : -1;
        for (let i = 0; i < 3; i++) this.hitN[i] = mul(hit.normal[i], sign);
      }
    }
    const state = { target: this.boomRatioTarget, ratio: this.boomRatio, rate: this.boomRate,
      speed: this.boomSpd, angle: this.viewTurn, under: this.boomUnder };
    advanceBoom(state, { minimum: this.minDist, length: len,
      move: [0, 1, 2].map(i => sub(this.track[i], this.trackPrev[i])),
      vy: pl?.velY ?? 0, dc: pl?.airRatio ?? 0, air: pl?.airFrames ?? 0,
      wall: n?.wall7a0 ?? false, normalY: this.normal[1], basis: this.viewDir, prevBasis: this.prevViewDir,
      aim: o.aimForward, dir: d, ad0: n?.ad0 ?? 0, d9: n?.d9 ?? false, d0: this.slopeU,
      blend, hitN: this.hitN, hitDist, camDelta: [0, 1, 2].map(i => sub(this.rigCam[i], this.prevRigCam[i])),
      atDelta: [0, 1, 2].map(i => sub(this.rigAt[i], this.prevRigAt[i])), vel: pl?.moveVel ?? [0, 0, 0] });
    this.boomRatioTarget = state.target; this.boomRatio = state.ratio; this.boomRate = state.rate;
    this.boomSpd = state.speed; this.viewTurn = state.angle; this.boomUnder = state.under;
    this.prevViewDir.set(this.viewDir);
    boomPosition(o.pos, pv, d, this.boomRatio, len, this.boomE, this.rigCam, n?.positionGateDe0 ?? 0);
    o.target.set(this.rigAt);
    if (this.boomRatio < F(.999)) {
      const py = pl?.pos?.[1] ?? this.track[1];
      const k = sub(mul(wall, add(sub(py, this.rigAt[1]), .4)), .4);
      o.target[1] = add(o.target[1], mix(k, 0, this.boomRatio));
    }
    for (let i = 0; i < 3; i++) {
      o.pos[i] = mix(o.pos[i], this.rigCam[i], blend);
      o.target[i] = mix(o.target[i], this.rigAt[i], blend);
    }
    this.prevRigCam.set(this.rigCam); this.prevRigAt.set(this.rigAt);
  }

  /** 근접 보정(2363~2378행) → 시선 방향 → 조준 방향·공유값. */
  private finishOutput(): void {
    const o = this.out;
    const a = o.aimForward;
    const dd = dot([0, 1, 2].map(i => sub(o.pos[i], o.target[i])), a);
    if (dd > F(-.16)) {
      const k = add(dd, .16);
      for (let i = 0; i < 3; i++) o.pos[i] = sub(o.pos[i], mul(a[i], k));
    }
    updateBasis(o.pos, o.target, o.right, o.up, o.viewZ);
    for (let i = 0; i < 3; i++) o.viewForward[i] = F(-o.viewZ[i]);
    o.yaw = Math.atan2(a[0], a[2]);
    o.pitchNorm = this.p;
    o.pitchAngleDeg = this.s;
    o.pitch = aimPitchDeg(this.p) * 0.017453292;
    aimDirection(o.rigForward, o.pitch, o.aimDir);
    o.squidBlend = this.squidW;
    o.boomRatio = this.boomRatio;
  }
}
