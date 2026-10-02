// 레일 이동(game::RailMovableSequential) — 이동 표적 SighterTarget_Move 가 spl::RailMovableSequentialHelper 로 쓴다.
// 근거: docs/gimmick/stage_misc.md §1.2~§1.5(일정·시간 평가·이동·자세), docs/range/shooting_range.md §6.5(cSpeed 역방향 길이).
import { f32 } from "../fmath.ts";

export type Quat = [number, number, number, number]; // x, y, z, w

export interface RailPointData {
  hash: string;
  pos: [number, number, number];
  /** game__LiftGraphRailNodeParam.Rotation (도) — 생성자 기본 0 [판독 0x71012fabdc] */
  rotDeg: [number, number, number];
  /** game__LiftGraphRailNodeParam.BreakTime (초) — 생성자 기본 0 [판독 0x71012fabdc] */
  breakTime: number;
}

export interface RailData {
  hash: string;
  closed: boolean;
  /** Banc Rails[].Rotation (라디안, R = Rz·Ry·Rx) */
  rotation: [number, number, number];
  points: RailPointData[];
}

export const RailPatrol = { cStop: 0, cContinue: 1 } as const;
export const RailSpeedCalc = { cTime: 0, cSpeed: 1 } as const;
export const RailInterp = { cLinear: 0, cSin: 1 } as const;

export interface RailMoveParam {
  PatrolType: number;
  SpeedCalcType: number;
  InterpolationType: number;
  /** s32 (0x7101305b40 이 (float)(int) 로 나눔) */
  MoveSpeed: number;
  MoveTime: number;
  WaitTime: number;
}

/** game__RailMovableSequentialParam 생성자 기본값 (stage_misc.md §1.2 표) [판독] */
export const RAIL_MOVE_DEFAULTS: RailMoveParam = {
  PatrolType: RailPatrol.cStop,
  SpeedCalcType: RailSpeedCalc.cTime,
  InterpolationType: RailInterp.cLinear,
  MoveSpeed: 1,
  MoveTime: 1.0,
  WaitTime: 0.0,
};

export function railMoveParam(raw: Record<string, unknown> | undefined): RailMoveParam {
  const p = { ...RAIL_MOVE_DEFAULTS };
  if (!raw) return p;
  const e = (v: unknown, names: readonly string[]): number | undefined => {
    if (typeof v === "number") return v;
    if (typeof v === "string") {
      const i = names.indexOf(v);
      return i >= 0 ? i : undefined;
    }
    return undefined;
  };
  p.PatrolType = e(raw.PatrolType, ["cStop", "cContinue"]) ?? p.PatrolType;
  p.SpeedCalcType = e(raw.SpeedCalcType, ["cTime", "cSpeed"]) ?? p.SpeedCalcType;
  p.InterpolationType = e(raw.InterpolationType, ["cLinear", "cSin"]) ?? p.InterpolationType;
  if (typeof raw.MoveSpeed === "number") p.MoveSpeed = Math.trunc(raw.MoveSpeed);
  if (typeof raw.MoveTime === "number") p.MoveTime = f32(raw.MoveTime);
  if (typeof raw.WaitTime === "number") p.WaitTime = f32(raw.WaitTime);
  return p;
}

// ---- 회전 ------------------------------------------------------------------
function qmul(a: Quat, b: Quat): Quat {
  return [
    f32(a[3] * b[0] + a[0] * b[3] + a[1] * b[2] - a[2] * b[1]),
    f32(a[3] * b[1] - a[0] * b[2] + a[1] * b[3] + a[2] * b[0]),
    f32(a[3] * b[2] + a[0] * b[1] - a[1] * b[0] + a[2] * b[3]),
    f32(a[3] * b[3] - a[0] * b[0] - a[1] * b[1] - a[2] * b[2]),
  ];
}

/** R = Rz·Ry·Rx (라디안) → 사원수 */
export function eulerZYXToQuat(rx: number, ry: number, rz: number): Quat {
  const qx: Quat = [Math.sin(rx / 2), 0, 0, Math.cos(rx / 2)];
  const qy: Quat = [0, Math.sin(ry / 2), 0, Math.cos(ry / 2)];
  const qz: Quat = [0, 0, Math.sin(rz / 2), Math.cos(rz / 2)];
  return qmul(qmul(qz, qy), qx);
}

/** 사원수 → 3x3 (열 우선: m[0..2] = X축, m[3..5] = Y축, m[6..8] = Z축) */
export function quatToMat3(q: Quat): number[] {
  const [x, y, z, w] = q;
  return [
    1 - 2 * (y * y + z * z), 2 * (x * y + z * w), 2 * (x * z - y * w),
    2 * (x * y - z * w), 1 - 2 * (x * x + z * z), 2 * (y * z + x * w),
    2 * (x * z + y * w), 2 * (y * z - x * w), 1 - 2 * (x * x + y * y),
  ].map(f32);
}

/** 0x7101250f0c 사원수 slerp: d 클램프, θ=acos|d|, |sinθ|<FLT_EPSILON 이면 선형 가중, d<0 이면 둘째 가중 부호 반전 [판독 — stage_misc §1.5] */
export function slerp(a: Quat, b: Quat, u: number): Quat {
  let d = a[0] * b[0] + a[1] * b[1] + a[2] * b[2] + a[3] * b[3];
  d = Math.min(1, Math.max(-1, d));
  const th = Math.acos(Math.abs(d));
  const s = Math.sin(th);
  let wa: number, wb: number;
  if (Math.abs(s) < 1.1920929e-7) {
    wa = 1 - u;
    wb = u;
  } else {
    wa = Math.sin((1 - u) * th) / s;
    wb = Math.sin(u * th) / s;
  }
  if (d < 0) wb = -wb;
  return [f32(a[0] * wa + b[0] * wb), f32(a[1] * wa + b[1] * wb), f32(a[2] * wa + b[2] * wb), f32(a[3] * wa + b[3] * wb)];
}

const DEG = f32(0.017453292);

// ---- 레일 경로 (LiftRail + 어댑터 vt 0x7105587318) ---------------------------
export class RailPath {
  readonly n: number;
  readonly closed: boolean;
  readonly pos: [number, number, number][];
  readonly rot: Quat[];
  readonly brk: number[];
  /** 누적 거리 (닫힌 레일은 마지막→처음 구간 포함) */
  readonly dist: number[];
  readonly hashes: string[];

  constructor(r: RailData) {
    this.n = r.points.length;
    this.closed = r.closed;
    this.pos = r.points.map((p) => [f32(p.pos[0]), f32(p.pos[1]), f32(p.pos[2])]);
    this.hashes = r.points.map((p) => p.hash);
    this.brk = r.points.map((p) => f32(p.breakTime));
    const railQ = eulerZYXToQuat(r.rotation[0], r.rotation[1], r.rotation[2]);
    // 점 회전 = R_rail · Rz·Ry·Rx(노드 Rotation × 0.017453292) (0x7101301d58) [판독]
    this.rot = r.points.map((p) => qmul(railQ, eulerZYXToQuat(f32(p.rotDeg[0] * DEG), f32(p.rotDeg[1] * DEG), f32(p.rotDeg[2] * DEG))));
    const d = [0];
    const cnt = this.closed ? this.n : this.n - 1;
    for (let i = 0; i < cnt; i++) {
      const a = this.pos[i], b = this.pos[(i + 1) % this.n];
      const dx = f32(b[0] - a[0]), dy = f32(b[1] - a[1]), dz = f32(b[2] - a[2]);
      d.push(f32(d[i] + f32(Math.sqrt(f32(f32(f32(dx * dx) + f32(dy * dy)) + f32(dz * dz))))));
    }
    this.dist = d;
  }

  get total(): number {
    return this.dist[this.dist.length - 1];
  }

  indexOf(hash: string): number {
    return this.hashes.indexOf(hash);
  }

  private step(i: number, d: number): number {
    const j = i + d;
    if (this.closed) return ((j % this.n) + this.n) % this.n;
    return Math.min(Math.max(j, 0), this.n - 1);
  }
  /** vt+0x50 0x710147b57c */
  next(i: number, rev: boolean): number {
    return this.step(i, rev ? -1 : 1);
  }
  /** vt+0x58 0x710147b5e4 */
  prev(i: number, rev: boolean): number {
    return this.step(i, rev ? 1 : -1);
  }
  /** vt+0x68 0x710147b694 */
  isEnd(i: number, rev: boolean): boolean {
    if (this.closed) return false;
    return i === (rev ? 0 : this.n - 1);
  }
  /** vt+0x70 0x710147b6dc: d[b]-d[a], rev 이면 부호 반전, 닫힌 레일은 전체 길이로 나머지(양수) [판독] */
  segLen(a: number, b: number, rev: boolean): number {
    let s = f32(this.dist[b] - this.dist[a]);
    if (rev) s = -s;
    if (this.closed) {
      const t = this.total;
      s = f32(s - f32(t * Math.trunc(f32(s / t))));
      if (!(s >= 0)) s = f32(t + s);
    }
    return s;
  }

  /** 0x71013001f4 구간 (i, u) */
  private seg(s: number): [number, number] {
    const t = this.total;
    let sp = this.closed ? s - t * Math.floor(s / t) : Math.min(Math.max(s, 0), t);
    sp = f32(sp);
    let i = 0;
    const last = this.closed ? this.n - 1 : this.n - 2;
    while (i < last && sp >= this.dist[i + 1]) i++;
    const len = f32(this.dist[i + 1] - this.dist[i]);
    const u = len === 0 ? 0 : Math.min(Math.max(f32(f32(sp - this.dist[i]) / len), 0), 1);
    return [i, u];
  }

  /** 0x71012ffeac: 거리 s 의 위치 (LiftRail 부모 변환 = 단위) */
  posAt(s: number): [number, number, number] {
    const [i, u] = this.seg(s);
    const a = this.pos[i], b = this.pos[(i + 1) % this.n];
    return [f32(a[0] + f32(f32(b[0] - a[0]) * u)), f32(a[1] + f32(f32(b[1] - a[1]) * u)), f32(a[2] + f32(f32(b[2] - a[2]) * u))];
  }

  /** 0x710147b7a8 회전부: 점 회전 slerp */
  rotAt(s: number): Quat {
    const [i, u] = this.seg(s);
    return slerp(this.rot[i], this.rot[(i + 1) % this.n], u);
  }
}

interface SchedEntry {
  start: number;
  kind: number; // 0 시작, 1 점 대기, 2 이동, 3 끝
  pos: number;
  rev: boolean;
}

export interface RailPose {
  pos: [number, number, number];
  rot: Quat;
}

/** game::RailMovableSequential (일정 0x7101305238, 시간 평가 0x71013043d8, 구간 처리 표 0x7105577e48) */
export class RailMover {
  readonly rail: RailPath;
  readonly prm: RailMoveParam;
  readonly start: number;
  readonly sched: SchedEntry[] = [];
  waitTime = 0;
  period = 0;
  /** +0x18f0 현재 시간(초), 리셋(slot5 0x71013046c4) 0 */
  time = 0;

  constructor(rail: RailPath, prm: RailMoveParam, startIndex: number) {
    this.rail = rail;
    this.prm = prm;
    this.start = startIndex;
    this.build();
  }

  /** 0x7101305b40 */
  moveDur(seg: number, pos: number, rev: boolean): number {
    if (this.prm.SpeedCalcType === RailSpeedCalc.cSpeed) return f32(this.rail.segLen(seg, pos, rev) / f32(this.prm.MoveSpeed));
    if (this.prm.SpeedCalcType === RailSpeedCalc.cTime) return this.prm.MoveTime;
    return 1.0;
  }

  private build(): void {
    const r = this.rail;
    if (r.n < 2) {
      this.sched.push({ start: 0, kind: 3, pos: this.start, rev: false });
      return;
    }
    let t = 0, kind = 0, pos = this.start, rev = false;
    for (let guard = 0; guard < 4096; guard++) {
      let d = 0, nk = 0, npos: number = pos, nrev: boolean = rev;
      if (kind === 0) {
        d = this.prm.WaitTime;
        this.waitTime = d;
        npos = r.next(pos, rev);
        nk = 2;
      } else if (kind === 2) {
        d = this.moveDur(r.prev(pos, rev), pos, rev);
        nk = this.prm.PatrolType === RailPatrol.cStop && r.isEnd(pos, rev) ? 3 : 1;
      } else {
        d = r.brk[pos];
        if (this.prm.PatrolType === RailPatrol.cContinue) nrev = rev !== r.isEnd(pos, rev);
        npos = r.next(pos, nrev);
        nk = 2;
      }
      const t2 = f32(t + d);
      if (d > 0) this.sched.push({ start: t, kind, pos, rev });
      t = t2;
      kind = nk;
      pos = npos;
      rev = nrev;
      if (this.sched.some((e) => e.kind === kind && e.pos === pos && e.rev === rev)) break;
      if (kind === 3) {
        this.sched.push({ start: t, kind: 3, pos, rev });
        break;
      }
    }
    this.period = f32(t - this.waitTime);
  }

  reset(): void {
    this.time = 0;
  }

  /** 객체 vt+0x30 (0x71013046d4): t += dt (역재생 플래그 없음) → 평가 */
  advance(dt: number): RailPose {
    this.time = f32(this.time + dt);
    return this.evaluate(this.time);
  }

  /** 0x71013043d8 */
  evaluate(tIn: number): RailPose {
    const t = tIn <= 0 ? 0 : tIn;
    let te: number;
    if (this.prm.PatrolType === RailPatrol.cStop) {
      const e = f32(this.waitTime + this.period);
      te = t <= e ? t : e;
    } else if (this.period === 0) te = 0;
    else {
      let u = f32(t - this.waitTime);
      if (u > 0) {
        u = f32(u - f32(this.period * Math.trunc(f32(u / this.period))));
        if (u < 0) u = f32(this.period + u);
      }
      te = f32(this.waitTime + u);
    }
    let e = this.sched[0];
    for (const x of this.sched) if (x.start <= te) e = x;
    return this.pose(e, f32(te - e.start));
  }

  private pose(e: SchedEntry, tau: number): RailPose {
    const r = this.rail;
    if (e.kind === 2) {
      // 0x7101304cec (AttCalcType 기본 cInMove)
      const seg = r.prev(e.pos, e.rev);
      const D = this.moveDur(seg, e.pos, e.rev);
      let x = D === 0 ? 1 : f32(tau / D);
      if (this.prm.InterpolationType === RailInterp.cSin) x = f32(f32(f32(Math.sin(f32(f32(x * f32(3.1415927)) - f32(1.5707964)))) + 1) * 0.5);
      const s = f32(f32(x * r.segLen(seg, e.pos, false)) + r.dist[seg]);
      return { pos: r.posAt(s), rot: r.rotAt(s) };
    }
    // 0x7101304984 점 대기 / 0x71013046f4 시작·끝 (cInMove → 점 자세)
    return { pos: [...r.pos[e.pos]] as [number, number, number], rot: r.rot[e.pos] };
  }
}
