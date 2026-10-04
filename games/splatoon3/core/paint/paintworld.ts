// PaintWorld 구현: 도색 요청 → 그리기 레코드 → 한 프레임 패스(소유 스텐실·카운트·색) → 집계·발밑 샘플.
// 원본 GPU 파이프라인(docs/paint/paint_and_score.md §3.5)을 CPU 텍셀 격자로 옮긴 것. 패스 순서·판정은
// web/tools/paintgpu_frame_sim.py 와 같다(§6.3 1~6단계).
import type { Vec3 } from "../fmath.ts";
import type { InkSample, PaintRequest, PaintWorld, Team } from "../types.ts";
import type { World } from "../world.ts";
import { heightRange, INK_TEX_TYPES, InkTexTable, paintSeed, patternVariant, sampleMask, StampLibrary, type StampMask } from "./inktex.ts";
import { erasepaint, overpaint, toUnorm8 } from "./overpaint.ts";
import { centerShift, rectSize, shooterPattern } from "./shape.ts";
import { TEXELS_PER_UNIT, type PaintSurfaces } from "./surface.ts";

/**
 * PaintRequest.kind 값. 원본 분류(paint_shape.md):
 * - Shooter: 슈터 탄 접촉 순간 요청. 원본은 탄+0x1150 에 보관했다가 다음 갱신(슬롯55)에 구 질의로 칠한다(§7.7)
 *   → 여기서 1 프레임 늦춰 적용하고 반경 0.5·hypot(W,L) 구에 닿는 모든 면에 칠한다.
 * - ShooterDeferred: 무기 쪽이 이미 다음 갱신까지 늦춰 부른 슈터 요청(지연 없이 구 질의만).
 * - Splash: 스플래시 탄(슬롯98 = 0 → 즉시, 패턴 Shot00, 중심 이동 없음, §5).
 * - WallDrop: 벽 낙하 방울 바닥 도색(즉시, 패턴 0, W = L = widthHalf·2, §6).
 * - Erase: 지우기(큐2, 모드 11 → 10). 연습장에서는 쓰지 않음.
 * - 그 밖에 InkTexType 이름("Disk", "Rectangle", "Bomb00" …): 그 스탬프로 즉시, W = 2w·ds^-1/4, L = 2w·ds^3/4,
 *   반경 0.5·hypot(W,L) 구에 닿는 면 전부(폭발·기믹 등 슈터 외 호출자의 웹 입구 — 원본 호출자 15곳 미분류 [미확정]).
 */
export const PaintKind = {
  Shooter: "Shooter",
  ShooterDeferred: "ShooterDeferred",
  Splash: "Splash",
  WallDrop: "WallDrop",
  Erase: "Erase",
} as const;

const TEAM_BIT = [1, 2, 4];
const BIT_TEAM: Record<number, number> = { 1: 0, 2: 1, 4: 2 };
/** 즉시 요청(접촉 목록)의 근사 반경 — 원본은 맞은 탄의 접촉 목록을 그대로 쓴다 [근사]. */
const CONTACT_RADIUS = 0.1;
/** 0x71017646a4 구 반경 하한(전역 최소 기본 0.05)·상한 2000 [판독]. */
const SPHERE_MIN = 0.05;
const SPHERE_MAX = 2000;
/** PlayerStepPaint 덮임 = min(전체/15, 1) (paint_and_score.md §7) [판독]. */
const STEP_PAINT_FULL = 15;

interface ChartDraw {
  page: number;
  idx: Int32Array;
  ink: Float32Array;
}

interface Rec {
  team: number;
  /** 큐: 0 = 플레이어 칠(N+0x44 0/1), 1 = 비플레이어(N+0x44 2), 2 = 지우기(3) */
  queue: number;
  /** 플레이어 번호 0..7 (8 이상 = 카운트 안 함), 큐1은 -1 */
  player: number;
  owner: number;
  pos: Float64Array;
  normal: Float64Array;
  dir: Float64Array;
  W: number;
  L: number;
  hmax: number;
  hmin: number;
  mask: StampMask;
  cAlpha: number;
  af: number;
  as: number;
  age: number;
  radius: number;
  due: number;
  inkTex: number;
  variant: number;
  draws: ChartDraw[] | null;
  shown: boolean;
}

export interface InkSampleEx extends InkSample {
  /** 원 안의 칠 가능 텍셀 수(원본 PlayerStepPaint 의 "전체", 0 이면 원본은 직전 값을 한 번 재사용) */
  texels: number;
}

/** 클라이언트 표시용 메타 (world.shared "paintSurfaces"). */
export interface PaintSurfacesShared {
  surfaces: PaintSurfaces;
  /** 페이지별 바뀐 텍셀 사각형 [x0, y0, x1, y1](포함), 없으면 null. 표시 쪽이 takeDirty 로 비운다. */
  dirty: ([number, number, number, number] | null)[];
  version: number;
  takeDirty(page: number): [number, number, number, number] | null;
  stamps: { original: boolean };
}

export class PaintWorldImpl implements PaintWorld {
  readonly surf: PaintSurfaces;
  readonly inkTex: InkTexTable;
  readonly stamps: StampLibrary;
  readonly shared: PaintSurfacesShared;
  readonly team: [number, number, number] = [0, 0, 0];
  /** 플레이어 번호별 새로 내 팀 소유가 된 텍셀 누적(원본 플레이어 +0xbd4) */
  readonly playerTexels: number[] = [];
  private readonly slots = new Map<number, number>();
  private pending: Rec[] = [];
  private active: Rec[] = [];
  private readonly world: World;
  private readonly tmp = new Float32Array(3);
  tricolor = false;

  constructor(world: World, surf: PaintSurfaces, inkTexTable: unknown, stampTable: unknown) {
    this.world = world;
    this.surf = surf;
    this.inkTex = new InkTexTable(inkTexTable);
    this.stamps = new StampLibrary(stampTable);
    const dirty: ([number, number, number, number] | null)[] = surf.pages.map(() => null);
    this.shared = {
      surfaces: surf,
      dirty,
      version: 0,
      takeDirty(page) {
        const d = dirty[page];
        dirty[page] = null;
        return d;
      },
      stamps: { original: this.stamps.hasOriginal },
    };
  }

  /** 플레이어 id → 원본 플레이어 번호(0..7, 등장 순). */
  playerSlot(owner: number): number {
    if (owner < 0) return -1;
    let s = this.slots.get(owner);
    if (s === undefined) {
      s = this.slots.size;
      this.slots.set(owner, s);
      this.playerTexels[s] = 0;
    }
    return s;
  }

  playerPaintTexels(owner: number): number {
    const s = this.slots.get(owner);
    return s === undefined ? 0 : this.playerTexels[s] ?? 0;
  }

  request(req: PaintRequest): void {
    const w = req.widthHalf;
    if (!(w > 0)) return; // §7.2: w <= 0 이면 칠하지 않음
    const kind = req.kind;
    const n = unit(req.normal, 0, 1, 0);
    const d = unit(req.dir, 1, 0, 0);
    let ds = req.depthScale > 0 ? req.depthScale : 1;
    if (kind === PaintKind.WallDrop) ds = 1;
    const { W, L } = rectSize(w, ds);
    const shooter = kind === PaintKind.Shooter || kind === PaintKind.ShooterDeferred;
    const named = shooter ? -1 : INK_TEX_TYPES.indexOf(kind);
    const inkTex = shooter ? shooterPattern(W, L) : named >= 0 ? named : 0;
    const pos = new Float64Array(3);
    if (shooter) {
      const sh = centerShift(new Float32Array(3), req.normal, req.dir, W, L, inkTex);
      pos[0] = Math.fround(req.pos[0] + sh[0]);
      pos[1] = Math.fround(req.pos[1] + sh[1]);
      pos[2] = Math.fround(req.pos[2] + sh[2]);
    } else {
      pos[0] = req.pos[0];
      pos[1] = req.pos[1];
      pos[2] = req.pos[2];
    }
    const row = this.inkTex.get(inkTex);
    const seed = paintSeed(pos, req.seed);
    const variant = patternVariant(seed, row.PatternNum);
    const mask = this.stamps.get(this.inkTex.textureName(inkTex, variant));
    const [hmax, hmin] = heightRange(row, W, L);
    const erase = kind === PaintKind.Erase;
    const player = erase ? -1 : this.playerSlot(req.owner);
    const radius = shooter || named >= 0 ? Math.min(SPHERE_MAX, Math.max(SPHERE_MIN, 0.5 * Math.hypot(W, L))) : CONTACT_RADIUS;
    this.pending.push({
      team: req.team,
      queue: erase ? 2 : player >= 0 ? 0 : 1,
      player,
      owner: req.owner,
      pos,
      normal: n,
      dir: d,
      W,
      L,
      hmax,
      hmin,
      mask,
      cAlpha: 1, // 슈터 요청 C+0xc = 0xff (§7.6)
      af: Math.max(1, row.AnimationFrame | 0),
      as: Math.max(1, row.AnimationStep | 0),
      age: 0,
      radius,
      due: kind === PaintKind.Shooter ? this.world.frame + 1 : this.world.frame,
      inkTex,
      variant,
      draws: null,
      shown: false,
    });
  }

  /** 한 게임 프레임. 순서는 0x7102c13750(수명) → 대기→실행 → 렌더 패스 0x7102c14168 (§3.5.7). */
  step(w: World): void {
    const frame = w.frame;
    // 1) 수명: 그 프레임 대상이 유효했던 레코드는 age++ (D+0x6f → D+0x48++), 큐2는 바로, 그 밖은 age > (AF−1)·AS 면 제거
    const keep: Rec[] = [];
    for (const r of this.active) {
      r.age++;
      if (r.queue === 2 || r.age > (r.af - 1) * r.as) continue;
      keep.push(r);
    }
    this.active = keep;
    // 2) 대기 → 실행
    const still: Rec[] = [];
    for (const r of this.pending) {
      if (r.due > frame) {
        still.push(r);
        continue;
      }
      r.draws = this.resolve(r);
      this.active.push(r);
    }
    this.pending = still;
    // 3) 렌더 패스 (age % AS == 0 인 레코드만 그림)
    const now = this.active.filter((r) => r.age % r.as === 0 && r.draws && r.draws.length > 0);
    if (now.length === 0) return;
    const q0 = now.filter((r) => r.queue === 0);
    const q1 = now.filter((r) => r.queue === 1);
    const q2 = now.filter((r) => r.queue === 2);
    for (const r of q0) if (r.player >= 0 && r.player < 8) this.passOwn(r, true); // 모드 4/5/6 (카운트)
    for (const r of q1) this.passOwn(r, false); // 모드 0/1/2
    for (const r of q2) this.passEraseOwn(r); // 모드 11 (스텐실 0) — 프레임 앞 색 기준
    for (const r of q0) this.passColor(r); // 모드 9 (큐0 → 큐1)
    for (const r of q1) this.passColor(r);
    for (const r of q2) this.passEraseColor(r); // 모드 10
    this.shared.version++;
    for (const r of now)
      if (!r.shown) {
        r.shown = true;
        w.events.emit({ type: "Paint", team: r.team, pos: [r.pos[0], r.pos[1], r.pos[2]], owner: r.owner });
      }
  }

  sample(pos: Vec3, radius: number): InkSampleEx {
    const cnt = [0, 0, 0];
    let total = 0;
    const s = this.surf;
    for (const ci of s.chartsInSphere(pos, radius)) {
      const c = s.charts[ci];
      const pg = s.pages[c.page];
      const rx = pos[0] - c.o[0], ry = pos[1] - c.o[1], rz = pos[2] - c.o[2];
      const dn = rx * c.n[0] + ry * c.n[1] + rz * c.n[2];
      const rp2 = radius * radius - dn * dn;
      if (rp2 < 0) continue;
      const cu = (rx * c.e1[0] + ry * c.e1[1] + rz * c.e1[2]) * TEXELS_PER_UNIT;
      const cv = (rx * c.e2[0] + ry * c.e2[1] + rz * c.e2[2]) * TEXELS_PER_UNIT;
      const rt = Math.sqrt(rp2) * TEXELS_PER_UNIT;
      const lim = rp2 * TEXELS_PER_UNIT * TEXELS_PER_UNIT;
      const i0 = Math.max(0, Math.floor(cu - rt)), i1 = Math.min(c.w - 1, Math.ceil(cu + rt));
      const j0 = Math.max(0, Math.floor(cv - rt)), j1 = Math.min(c.h - 1, Math.ceil(cv + rt));
      for (let j = j0; j <= j1; j++) {
        const dv = j + 0.5 - cv;
        const row = (c.y0 + j) * pg.w + c.x0;
        for (let i = i0; i <= i1; i++) {
          const du = i + 0.5 - cu;
          if (du * du + dv * dv > lim) continue;
          const k = row + i;
          if (!pg.inside[k]) continue;
          total++;
          const t = BIT_TEAM[pg.stencil[k]];
          if (t !== undefined) cnt[t]++;
        }
      }
    }
    const cover = Math.min(total / STEP_PAINT_FULL, 1);
    const ratio: [number, number, number] = [0, 0, 0];
    let team: Team = -1;
    let best = 0;
    for (let t = 0; t < 3; t++) {
      ratio[t] = total > 0 ? (cnt[t] / total) * cover : 0;
      if (ratio[t] > best) {
        best = ratio[t];
        team = t as Team;
      }
    }
    return { team, ratio, texels: total };
  }

  /**
   * [physics 추가] 발밑 모니터 카운트: 접촉점 pos·법선 n 의 1×1 `Disk` 스탬프(쿼드 ±1 → 반경 1 원) 안 소유 스텐실 수(모드 14/15/16)와
   * 칠 가능 텍셀 수(모드 17). 원본은 PaintMonitor 패스의 GPU 카운트를 1~2 프레임 늦게 읽는다(지연 [미확정], 여기서는 즉시) —
   * paint_and_score.md §7 [r6 paint]. 높이 범위(InkTexInfo Disk 행)·패널 대표 평면 투영은 근사(차트 평면 위 원).
   */
  monitorCounts(pos: ArrayLike<number>, n: ArrayLike<number>): [number, number, number, number] {
    const out: [number, number, number, number] = [0, 0, 0, 0];
    const s = this.surf;
    for (const ci of s.chartsInSphere(pos, 1)) {
      const c = s.charts[ci];
      const pg = s.pages[c.page];
      if (c.n[0] * n[0] + c.n[1] * n[1] + c.n[2] * n[2] <= 0.001) continue;
      const rx = pos[0] - c.o[0], ry = pos[1] - c.o[1], rz = pos[2] - c.o[2];
      const cu = (rx * c.e1[0] + ry * c.e1[1] + rz * c.e1[2]) * TEXELS_PER_UNIT;
      const cv = (rx * c.e2[0] + ry * c.e2[1] + rz * c.e2[2]) * TEXELS_PER_UNIT;
      const rt = TEXELS_PER_UNIT, lim = rt * rt;
      const i0 = Math.max(0, Math.floor(cu - rt)), i1 = Math.min(c.w - 1, Math.ceil(cu + rt));
      const j0 = Math.max(0, Math.floor(cv - rt)), j1 = Math.min(c.h - 1, Math.ceil(cv + rt));
      for (let j = j0; j <= j1; j++) {
        const dv = j + 0.5 - cv;
        const row = (c.y0 + j) * pg.w + c.x0;
        for (let i = i0; i <= i1; i++) {
          const du = i + 0.5 - cu;
          if (du * du + dv * dv > lim) continue;
          const k = row + i;
          if (!pg.inside[k]) continue;
          out[3]++;
          const t = BIT_TEAM[pg.stencil[k]];
          if (t !== undefined) out[t]++;
        }
      }
    }
    return out;
  }

  counts(): { team: [number, number, number]; total: number } {
    return { team: [this.team[0], this.team[1], this.team[2]], total: this.surf.totalInside };
  }

  // ---- 레코드 → 차트별 텍셀 -----------------------------------------------------

  /**
   * 요청 하나가 닿는 차트와 텍셀·스탬프 값. 스탬프는 차트 평면 위에 실제 크기로 놓는다
   * (원본: 회전 = 진행 방향의 면 투영 각 0x7102c1233c, 경사 보정 0x7102c124bc 로 경사면에서도 실제 크기 [판독]).
   * 텍셀 위치의 요청 법선 방향 높이가 높이 범위(D+0x20/+0x24) 밖이면 버린다(원본 MASK 변형 [추정: 적용 대상]).
   */
  private resolve(r: Rec): ChartDraw[] {
    const s = this.surf;
    const out: ChartDraw[] = [];
    const halfW = (r.W * 0.5) * TEXELS_PER_UNIT, halfL = (r.L * 0.5) * TEXELS_PER_UNIT;
    const nq = r.normal, dq = r.dir;
    for (const ci of s.chartsInSphere(r.pos, r.radius)) {
      const c = s.charts[ci];
      const np = c.n;
      const nn = np[0] * nq[0] + np[1] * nq[1] + np[2] * nq[2];
      if (nn <= 0.001) continue; // 뒷면·수직면 거부(0x7102c40cd0 의 법선·축 < 0.001 [근사])
      const dd = dq[0] * np[0] + dq[1] * np[1] + dq[2] * np[2];
      let fx = dq[0] - dd * np[0], fy = dq[1] - dd * np[1], fz = dq[2] - dd * np[2];
      let lf = Math.hypot(fx, fy, fz);
      if (lf < 1e-4) {
        fx = c.e2[0];
        fy = c.e2[1];
        fz = c.e2[2];
        lf = 1;
      }
      fx /= lf;
      fy /= lf;
      fz /= lf;
      // right = fwd × n (텍스처 u 증가 방향 [추정: 좌우 거울 미확정])
      const rx = fy * np[2] - fz * np[1], ry = fz * np[0] - fx * np[2], rz = fx * np[1] - fy * np[0];
      const ox = r.pos[0] - c.o[0], oy = r.pos[1] - c.o[1], oz = r.pos[2] - c.o[2];
      const dc = ox * np[0] + oy * np[1] + oz * np[2];
      const cu = (ox * c.e1[0] + oy * c.e1[1] + oz * c.e1[2]) * TEXELS_PER_UNIT;
      const cv = (ox * c.e2[0] + oy * c.e2[1] + oz * c.e2[2]) * TEXELS_PER_UNIT;
      const r1 = rx * c.e1[0] + ry * c.e1[1] + rz * c.e1[2], r2 = rx * c.e2[0] + ry * c.e2[1] + rz * c.e2[2];
      const f1 = fx * c.e1[0] + fy * c.e1[1] + fz * c.e1[2], f2 = fx * c.e2[0] + fy * c.e2[1] + fz * c.e2[2];
      const eu = Math.abs(r1) * halfW + Math.abs(f1) * halfL, ev = Math.abs(r2) * halfW + Math.abs(f2) * halfL;
      const i0 = Math.max(0, Math.floor(cu - eu)), i1 = Math.min(c.w - 1, Math.ceil(cu + eu));
      const j0 = Math.max(0, Math.floor(cv - ev)), j1 = Math.min(c.h - 1, Math.ceil(cv + ev));
      if (i0 > i1 || j0 > j1) continue;
      const h0 = -dc * nn;
      const hn1 = (c.e1[0] * nq[0] + c.e1[1] * nq[1] + c.e1[2] * nq[2]) / TEXELS_PER_UNIT;
      const hn2 = (c.e2[0] * nq[0] + c.e2[1] * nq[1] + c.e2[2] * nq[2]) / TEXELS_PER_UNIT;
      const pg = s.pages[c.page];
      const idx: number[] = [];
      const ink: number[] = [];
      for (let j = j0; j <= j1; j++) {
        const dv = j + 0.5 - cv;
        const row = (c.y0 + j) * pg.w + c.x0;
        for (let i = i0; i <= i1; i++) {
          const du = i + 0.5 - cu;
          const x = (du * r1 + dv * r2) / halfW;
          const y = (du * f1 + dv * f2) / halfL;
          if (x < -1 || x >= 1 || y <= -1 || y > 1) continue;
          const h = h0 + du * hn1 + dv * hn2;
          if (h > r.hmax || h < r.hmin) continue;
          const v = sampleMask(r.mask, x * 0.5 + 0.5, 0.5 - y * 0.5);
          if (!(v > 0)) continue;
          idx.push(row + i);
          ink.push(v);
        }
      }
      if (idx.length) out.push({ page: c.page, idx: Int32Array.from(idx), ink: Float32Array.from(ink) });
    }
    return out;
  }

  // ---- 패스 ------------------------------------------------------------------

  /** 모드 4/5/6(count=true, 스텐실 NOTEQUAL 팀비트) / 0/1/2(ALWAYS): 알파 테스트 통과 텍셀의 소유 스텐실 = 팀비트. */
  private passOwn(r: Rec, count: boolean): void {
    const bit = TEAM_BIT[r.team];
    if (bit === undefined) return;
    const o = this.tmp;
    let passed = 0;
    for (const d of r.draws!) {
      const pg = this.surf.pages[d.page];
      const col = pg.color, st = pg.stencil, ins = pg.inside;
      for (let k = 0; k < d.idx.length; k++) {
        const t = d.idx[k];
        if (count && (st[t] & bit) === bit) continue;
        const c = t * 4;
        if (!overpaint(U8F[col[c]], U8F[col[c + 1]], this.tricolor ? U8F[col[c + 2]] : 0, d.ink[k], r.cAlpha, r.team, true, o)) continue;
        this.setStencil(st, ins, t, bit);
        if (count && ins[t]) passed++;
      }
    }
    if (count) this.playerTexels[r.player] = (this.playerTexels[r.player] ?? 0) + passed;
  }

  /** 모드 11: 지우기 알파 테스트(세 채널 모두 0.3 미만이 될 때) 통과 → 스텐실 0. */
  private passEraseOwn(r: Rec): void {
    const o = this.tmp;
    for (const d of r.draws!) {
      const pg = this.surf.pages[d.page];
      const col = pg.color;
      for (let k = 0; k < d.idx.length; k++) {
        const t = d.idx[k], c = t * 4;
        if (erasepaint(U8F[col[c]], U8F[col[c + 1]], this.tricolor ? U8F[col[c + 2]] : 0, d.ink[k], r.cAlpha, true, o))
          this.setStencil(pg.stencil, pg.inside, t, 0);
      }
    }
  }

  /** 모드 9: 알파 테스트 없이 색(RG, 3팀이면 RGB)만 기록. 그리기마다 배리어 → 순차 갱신. */
  private passColor(r: Rec): void {
    const o = this.tmp;
    const nch = this.tricolor ? 3 : 2;
    for (const d of r.draws!) {
      const pg = this.surf.pages[d.page];
      const col = pg.color;
      for (let k = 0; k < d.idx.length; k++) {
        const t = d.idx[k], c = t * 4;
        if (!overpaint(U8F[col[c]], U8F[col[c + 1]], nch === 3 ? U8F[col[c + 2]] : 0, d.ink[k], r.cAlpha, r.team, false, o)) continue;
        for (let ch = 0; ch < nch; ch++) col[c + ch] = toUnorm8(o[ch]);
        this.markDirty(d.page, t);
      }
    }
  }

  private passEraseColor(r: Rec): void {
    const o = this.tmp;
    const nch = this.tricolor ? 3 : 2;
    for (const d of r.draws!) {
      const pg = this.surf.pages[d.page];
      const col = pg.color;
      for (let k = 0; k < d.idx.length; k++) {
        const t = d.idx[k], c = t * 4;
        if (!erasepaint(U8F[col[c]], U8F[col[c + 1]], nch === 3 ? U8F[col[c + 2]] : 0, d.ink[k], r.cAlpha, false, o)) continue;
        for (let ch = 0; ch < nch; ch++) col[c + ch] = toUnorm8(o[ch]);
        this.markDirty(d.page, t);
      }
    }
  }

  private setStencil(st: Uint8Array, ins: Uint8Array, t: number, bit: number): void {
    const old = st[t];
    if (old === bit) return;
    st[t] = bit;
    if (!ins[t]) return;
    const a = BIT_TEAM[old], b = BIT_TEAM[bit];
    if (a !== undefined) this.team[a]--;
    if (b !== undefined) this.team[b]++;
  }

  private markDirty(page: number, t: number): void {
    const w = this.surf.pages[page].w;
    const x = t % w, y = (t - x) / w;
    const d = this.shared.dirty[page];
    if (!d) this.shared.dirty[page] = [x, y, x, y];
    else {
      if (x < d[0]) d[0] = x;
      if (y < d[1]) d[1] = y;
      if (x > d[2]) d[2] = x;
      if (y > d[3]) d[3] = y;
    }
  }
}

/** UNORM8 → f32 (c/255) */
const U8F = new Float32Array(256).map((_, i) => i / 255);

function unit(v: ArrayLike<number>, dx: number, dy: number, dz: number): Float64Array {
  const out = new Float64Array(3);
  const l = Math.hypot(v[0], v[1], v[2]);
  if (l > 0 && Number.isFinite(l)) {
    out[0] = v[0] / l;
    out[1] = v[1] / l;
    out[2] = v[2] / l;
  } else {
    out[0] = dx;
    out[1] = dy;
    out[2] = dz;
  }
  return out;
}
