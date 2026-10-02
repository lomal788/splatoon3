// 벽 낙하 방울 spl::BulletWallDrop (vtable 0x71055b77d0). 근거: 부모 슬롯59 0x7101764ff8 → 슬롯69 0x7101648c78 →
// 0x7101648824(생성정보) → 슬롯61 0x7101646b10(양자화·난수) → 스폰 0x71018b0bd4 → 슬롯53 0x71018ad66c(초기 속도) → 슬롯15 0x71018ad26c.
// 매 프레임 슬롯54 0x71018ada10, 벽 도색 슬롯59 0x71018ae5e8, 바닥 도색 슬롯58 0x71018ae054, 슬롯55/56.
// 재구현 대조: web/tools/weapon_walldrop_sim.py.
import { f32 } from "../fmath.ts";
import { SeadRandom } from "../rng.ts";
import type { Team } from "../types.ts";
import { FLOOR_NY } from "./body.ts";
import type { V3 } from "./move.ts";
import type { WallDropCollisionPaintParam, WallDropCommonParam, WallDropMoveParam } from "./params.ts";
import { SINCOS_TABLE } from "./sincos_table.ts";

const K005 = f32(0.005);
const NEG005 = f32(-0.005);
const U32 = new Uint32Array(1);
const F32 = new Float32Array(U32.buffer);
const fromBits = (b: number): number => ((U32[0] = b >>> 0), F32[0]);
/** 0x3c03126f / 0x3c75c28f */
const GRAVITY = [fromBits(0x3c03126f), fromBits(0x3c75c28f)];
/** 구 반지름 0.2 (BulletWallDrop 셰이프) [데이터] */
export const WALL_DROP_RADIUS = f32(0.2);

function quantR(r: number): number {
  return Math.trunc(f32(f32(f32(r) / f32(0.05)) + f32(0.001))) | 0;
}

function quantS(s: number): number {
  return Math.trunc(f32(f32(f32(s) / K005) + f32(0.0001))) | 0;
}

/** umulhi(n, next()) = 0..n−1 */
function randBelow(r: SeadRandom, n: number): number {
  return Math.floor((r.u32() * (n >>> 0)) / 4294967296);
}

function norm3(v: V3): [V3, number] {
  const x = v[0], y = v[1], z = v[2];
  const ln = f32(Math.sqrt(f32(f32(f32(x * x) + f32(y * y)) + f32(z * z))));
  if (ln > 0) {
    const inv = f32(1 / ln);
    return [[f32(x * inv), f32(y * inv), f32(z * inv)], ln];
  }
  return [[x, y, z], ln];
}

/** 슬롯61 0x7101646b10 결과(생성정보 +0x94..+0xb8, +0x71) */
export interface WallDropQuant {
  shock: number;
  fall: number;
  ground: number;
  alp: number;
  gravityType: number;
  t1: number;
  t2: number;
  n0: number;
  n1: number;
  n2: number;
  pat: number;
}

/** seed = 탄관리자+0x120 + 부모 생성정보+0x64. 반지름이 모두 0 이하면 null(생성 안 함). */
export function quantize(move: WallDropMoveParam, paint: WallDropCollisionPaintParam, seed: number): WallDropQuant | null {
  const shock = quantR(paint.PaintRadiusShock), fall = quantR(paint.PaintRadiusFall), ground = quantR(paint.PaintRadiusGround);
  if (fall <= 0 && shock <= 0 && ground <= 0) return null;
  const rnd = new SeadRandom((Math.imul(seed >>> 0, 0x3f3) + 0x7d5) >>> 0);
  const lo0 = move.FallPeriodFirstFrameMin | 0, hi0 = move.FallPeriodFirstFrameMax | 0;
  const n0 = lo0 <= hi0 ? lo0 + randBelow(rnd, hi0 - lo0) : lo0;
  const lo2 = move.FallPeriodLastFrameMin | 0, hi2 = move.FallPeriodLastFrameMax | 0;
  const n2 = lo2 <= hi2 ? lo2 + randBelow(rnd, hi2 - lo2) : lo2;
  const pat = randBelow(rnd, 5);
  return {
    shock, fall, ground,
    alp: f32(Math.trunc(f32(f32(f32(paint.FallPeriodFirstSecondTargetAlp) / f32(0.1)) + f32(0.0001)))),
    gravityType: move.FreeGravityType === "value_0_015" ? 1 : 0,
    t1: quantS(move.FallPeriodFirstTargetSpeed),
    t2: quantS(move.FallPeriodSecondTargetSpeed),
    n0, n1: move.FallPeriodSecondFrame | 0, n2, pat,
  };
}

/** 스폰 0x71018b0bd4(1차 속도) + 슬롯53 0x71018ad66c(재계산) → 초기 속도. vb = 부모 +0x1118, n = 벽 법선. */
export function wallDropVelocity(vb: V3, n: V3, common: WallDropCommonParam): V3 {
  const [d, sp] = norm3(vb);
  const vyIn = f32(d[1] * sp);
  const v0: V3 = [f32(0 - f32(n[0] * K005)), f32(vyIn - f32(n[1] * K005)), f32(0 - f32(n[2] * K005))];
  const [d0, s0] = norm3(v0);
  const vy0 = f32(s0 * d0[1]);
  const rate = vy0 > 0 ? f32(common.InitVelocityRateYPlus) : f32(common.InitVelocityRateYMinus);
  const v1: V3 = [f32(0 - f32(n[0] * K005)), f32(f32(vy0 * rate) - f32(n[1] * K005)), f32(0 - f32(n[2] * K005))];
  const [d1, s1] = norm3(v1);
  const s = f32(s1 + 0);
  return [f32(d1[0] * s), f32(s * d1[1]), f32(s * d1[2])];
}

/** 0x7101648824 생성 조건: 벽에서 멀어지는 탄이면 생성 안 함. */
export function movingIntoWall(vb: V3, n: V3): boolean {
  const [d, len] = norm3(vb);
  if (len === 0) return true;
  void d;
  const dot = f32(f32(f32(n[0] * vb[0]) + f32(n[1] * vb[1])) + f32(n[2] * vb[2]));
  return !(dot > 0);
}

export interface WallDropPaint {
  /** "wall" | "ground" */
  kind: "wall" | "ground";
  pos: V3;
  normal: V3;
  dir: V3;
  /** 지름 W = L */
  size: number;
  inkTexType: number;
  alpha: number;
  /** C+0x1c 직접 시드 = age + 생성정보+0x74 (C+0x18 = 1) */
  seed: number;
  /** B+4 요청 번호 = min(+0x74 + age + 1, 0x1745d1) */
  reqNo: number;
}

export interface WallContact {
  point: V3;
  normal: V3;
  body: number;
}

export class WallDrop {
  readonly id: number;
  readonly owner: number;
  readonly team: Team;
  readonly q: WallDropQuant;
  readonly common: WallDropCommonParam;
  /** 생성정보 +0x64 = +0x74 = 생성 GameFrame */
  readonly frame: number;
  readonly groundSeed: number;
  pos: V3;
  vel: V3;
  age = -1;
  phase = 0;
  cnt = 0;
  accel: number;
  falling = false;
  onWall = true;
  planeN: V3;
  lastBody: number;
  leftBody = 0;
  /** +0x3c0 도색 쿨다운 (s8) */
  c = -1;
  painted = false;
  lastPaint: V3 = [0, 0, 0];
  dead = false;

  constructor(id: number, owner: number, team: Team, pos: V3, vel: V3, n: V3, body: number, q: WallDropQuant, common: WallDropCommonParam, frame: number, seedBase: number) {
    this.id = id;
    this.owner = owner;
    this.team = team;
    this.q = q;
    this.common = common;
    this.frame = frame;
    this.groundSeed = (seedBase + frame) >>> 0;
    this.pos = pos;
    this.vel = vel;
    this.planeN = n;
    this.lastBody = body;
    this.accel = f32(f32(f32(f32(q.t1) * NEG005) - vel[1]) / f32(q.n0));
  }

  /** 슬롯54 0x71018ada10 (age++ 는 기반 슬롯18) */
  move(): void {
    this.age++;
    this.painted = false;
    const v: V3 = [this.vel[0], this.vel[1], this.vel[2]];
    const rawVy = v[1];
    const q = this.q;
    if (this.onWall) {
      const n = this.planeN;
      const d = f32(f32(f32(v[0] * n[0]) + f32(v[1] * n[1])) + f32(v[2] * n[2]));
      v[0] = f32(v[0] - f32(n[0] * d));
      v[1] = f32(v[1] - f32(n[1] * d));
      v[2] = f32(v[2] - f32(n[2] * d));
      if (this.falling) {
        this.falling = false;
        if (this.leftBody === this.lastBody && this.lastBody !== 0) this.dead = true;
        else {
          this.phase = 0;
          this.accel = f32(f32(f32(f32(q.t1) * NEG005) - rawVy) / f32(q.n0));
          this.cnt = 0;
        }
      }
      v[1] = f32(v[1] + this.accel);
      this.cnt = ((this.cnt + 1) << 16) >> 16;
      const cnt = this.cnt;
      if (this.phase === 2) {
        if (cnt >= q.n2) this.dead = true;
      } else if (this.phase === 1) {
        if (q.n1 <= cnt) {
          this.phase = 2;
          this.accel = f32(f32(0 - v[1]) / f32(q.n2));
          this.cnt = 0;
        }
      } else if (this.phase === 0) {
        if (cnt < q.n0) this.accel = f32(f32(f32(f32(q.t1) * NEG005) - v[1]) / f32(q.n0 - cnt));
        else {
          this.phase = 1;
          this.accel = f32(f32(f32(f32(q.t2) * NEG005) - v[1]) / f32(q.n1));
          this.cnt = 0;
        }
      }
    } else {
      if (!this.falling) {
        this.falling = true;
        if (!(rawVy > 0)) this.leftBody = this.lastBody;
      }
      if (this.phase === 0) this.cnt = ((this.cnt + 1) << 16) >> 16;
      const g = GRAVITY[q.gravityType] ?? GRAVITY[0];
      const m0 = -0;
      v[0] = f32(v[0] + f32(v[0] * m0));
      v[1] = f32(v[1] + f32(f32(v[1] * m0) - g));
      v[2] = f32(v[2] + f32(v[2] * m0));
    }
    this.vel = v;
    this.onWall = false;
  }

  /** 물리: 일반 강체 적분 pos += v [추정 — weapon_walldrop_sim.py 와 같은 가정] */
  integrate(): void {
    for (let i = 0; i < 3; i++) this.pos[i] = f32(this.pos[i] + this.vel[i]);
  }

  /** 벽 접촉 콜백(슬롯59 0x71018ae5e8). 칠하면 요청을 돌려준다. */
  onWallContact(ct: WallContact): WallDropPaint | null {
    const common = this.common;
    const spanMax = ((common.PaintWallSpanMaxFrame | 0) << 24) >> 24;
    const spanMin = ((common.PaintWallSpanMinFrame | 0) << 24) >> 24;
    const c = this.c;
    let out: WallDropPaint | null = null;
    if (c <= spanMax - spanMin) {
      let ok = true;
      if (c > 0) {
        const dd = f32(common.PaintWallDropDistance);
        const dx = f32(ct.point[0] - this.lastPaint[0]), dy = f32(ct.point[1] - this.lastPaint[1]), dz = f32(ct.point[2] - this.lastPaint[2]);
        const d2 = f32(f32(f32(dx * dx) + f32(dy * dy)) + f32(dz * dz));
        if (d2 < f32(dd * dd)) ok = false;
      }
      if (ok) {
        this.lastPaint = [ct.point[0], ct.point[1], ct.point[2]];
        const ri = c < 0 ? this.q.shock : this.q.fall;
        const r = f32(f32(ri) * f32(0.05));
        const size = f32(r + r);
        const [k, pat] = this.phaseAlpha();
        const s0 = f32(k * f32(spanMax - (c > 0 ? c : 0)));
        const a = s0 < 0 ? 0 : Math.min(s0, 1);
        out = {
          kind: "wall", pos: [ct.point[0], ct.point[1], ct.point[2]], normal: [ct.normal[0], ct.normal[1], ct.normal[2]], dir: [0, 1, 0],
          size, inkTexType: pat, alpha: Math.trunc(f32(a * 255)) | 0, seed: (this.age + this.frame) | 0, reqNo: this.reqNo(),
        };
        this.painted = true;
      }
    }
    this.onWall = true;
    this.planeN = [ct.normal[0], ct.normal[1], ct.normal[2]];
    this.lastBody = ct.body;
    return out;
  }

  private phaseAlpha(): [number, number] {
    const q = this.q;
    let k: number, base: number;
    if (this.phase === 2) {
      const t = f32(f32(this.cnt) / f32(q.n2));
      if (t > f32(0.9)) k = f32(f32(f32(f32(t + f32(-0.9)) / fromBits(0x3dccccd0)) * f32(0.9)) + f32(0.1));
      else k = f32(1 - f32(f32(t / f32(0.9)) * f32(0.9)));
      base = 0x20;
    } else if (this.phase === 1) {
      k = f32(f32(Math.trunc(q.alp)) * f32(0.1));
      base = 0x20;
    } else {
      k = f32(f32(f32(f32(this.cnt) / f32(q.n0)) * f32(f32(f32(Math.trunc(q.alp)) * f32(0.1)) + -1)) + 1);
      base = 0x1b;
    }
    return [k, this.c < 0 ? 0 : base + q.pat];
  }

  /** 바닥 접촉 콜백(슬롯58 0x71018ae054): 무작위 회전 원형 도색 후 소멸. */
  onGroundContact(ct: WallContact): WallDropPaint {
    const r = new SeadRandom(this.groundSeed).u32();
    const i = (r >>> 24) * 4;
    const fr = f32(f32(r & 0xffffff) * fromBits(0x33800000));
    const s = f32(SINCOS_TABLE[i] + f32(SINCOS_TABLE[i + 1] * fr));
    const co = f32(SINCOS_TABLE[i + 2] + f32(SINCOS_TABLE[i + 3] * fr));
    const g = f32(f32(this.q.ground) * f32(0.05));
    this.dead = true;
    return {
      kind: "ground", pos: [ct.point[0], ct.point[1], ct.point[2]], normal: [ct.normal[0], ct.normal[1], ct.normal[2]], dir: [s, 0, co],
      size: f32(g + g), inkTexType: 0, alpha: 255, seed: (this.age + this.frame) | 0, reqNo: this.reqNo(),
    };
  }

  private reqNo(): number {
    const n = (this.frame + this.age + 1) | 0;
    return n >>> 0 < 0x1745d1 ? n : 0x1745d1;
  }

  /** 슬롯55·56 */
  post(): void {
    if (this.painted) this.c = ((((this.common.PaintWallSpanMaxFrame | 0) - 1) << 24) >> 24);
    else if (this.c >= 1) this.c -= 1;
    if (this.falling) this.c = 0;
    if (this.pos[1] < -10) this.dead = true;
  }

  isFloorNormal(n: V3): boolean {
    return n[1] > FLOOR_NY;
  }
}

/** 솎아내기 링(스폰 0x71018b0bd4): 부모 종류별 BulletSettingInfo.WallDropPositionStoreNum, ThinOutDistance 0.3, 60 프레임. */
export class WallDropThinOut {
  private ring: { body: number; frame: number; pos: V3 }[] = [];
  private next = 0;
  readonly size: number;
  readonly dist: number;

  constructor(size: number, dist: number) {
    this.size = size;
    this.dist = f32(dist);
  }

  /** 생성해도 되면 true(기록), 솎아내면 false. */
  admit(body: number, frame: number, pos: V3): boolean {
    const d2max = f32(this.dist * this.dist);
    for (const e of this.ring) {
      if (e.body !== body || !(frame < e.frame + 60)) continue;
      const dx = f32(pos[0] - e.pos[0]), dy = f32(pos[1] - e.pos[1]), dz = f32(pos[2] - e.pos[2]);
      if (f32(f32(f32(dx * dx) + f32(dy * dy)) + f32(dz * dz)) <= d2max) return false;
    }
    const rec = { body, frame, pos: [pos[0], pos[1], pos[2]] as V3 };
    if (this.ring.length < this.size) this.ring.push(rec);
    else this.ring[this.next] = rec;
    this.next = (this.next + 1) % Math.max(1, this.size);
    return true;
  }
}
