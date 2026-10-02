// 담당: [physics] — Phive 캐릭터 컨트롤러(SplPlayer) 대체. 원본은 hknp 캐릭터 강체라 내부(접촉 해석·지지 판정)는
// 판독하지 않았다. 여기서는 같은 형상(캡슐)과 단계 의미를 지키는 "쓸어 넘기기 + 미끄러짐" 근사를 쓴다.
// 근거·근사 이유: docs/physics/phive_controller.md §3~5, docs/impl/physics.md "캐릭터 컨트롤러 근사".
import { f32, type Vec3 } from "../fmath.ts";
import type { MeshCollisionWorld, Penetration, SweepResult } from "../collision/index.ts";

/** ShapeParam SplPlayer_cct 캡슐 ColGround: CenterA (0,0,0), CenterB (0,0.7,0), Radius 0.6 [데이터]. */
export const CAPSULE_RADIUS = f32(0.6000000238418579);
export const CAPSULE_A = 0;
export const CAPSULE_B = f32(0.699999988079071);
/**
 * 캡슐 기준점 = 발 + (0, 0.6, 0) [추정]: ColGround/ColOthers 둘 다 아래 끝이 −0.6 이고 ColBullet(탄 피격) 캡슐 아래 끝이 0 이며,
 * 모서리 미끄럼 판정(본체+0xa7c = 법선y − max(dy,0)/R)이 평지에서 dy = 0 이 되려면 발 높이가 접점이어야 한다.
 */
export const BODY_OFFSET_Y = CAPSULE_RADIUS;

export interface Contact {
  nx: number;
  ny: number;
  nz: number;
  px: number;
  py: number;
  pz: number;
  tri: number;
}

export interface BodyStepResult {
  /** 지지면(접지) 발견 */
  supported: boolean;
  /** 지지면 법선·접점 */
  gn: [number, number, number];
  gp: [number, number, number];
  /** 지지 삼각형(없으면 -1) */
  gtri: number;
  /** 이동 중·지지 판정 중 닿은 모든 접촉 */
  contacts: Contact[];
}

const PEN: Penetration[] = [];
const A = [0, 0, 0], B = [0, 0, 0], M = [0, 0, 0];

function seg(pos: ArrayLike<number>): void {
  A[0] = pos[0]; A[1] = pos[1] + BODY_OFFSET_Y + CAPSULE_A; A[2] = pos[2];
  B[0] = pos[0]; B[1] = pos[1] + BODY_OFFSET_Y + CAPSULE_B; B[2] = pos[2];
}

export interface BodyParams {
  /** 지면으로 보는 법선 y 하한(보통 0.6414, 오징어 벽 수영이면 −0.2571) */
  groundLimit: number;
  /** 지지 판정 방향(직전 바닥 법선) — 위로 향한 단위 벡터 */
  up: ArrayLike<number>;
  /** 이동 모드 OnGround(지면을 따라 이동) / InAir(게임 속도 그대로) */
  onGround: boolean;
  /** 삼각형 필터 */
  filter: (tri: number) => boolean;
}

/**
 * 한 스텝: 겹침 해소 → 변위 쓸어 넘기기(최대 4회 미끄러짐) → 지지면 탐색.
 * 원본 단계 대응: MoveStateUpdate(GameOnGround/GameInAir) → … → GameApplyVelocity → 강체 적분·접촉 해석.
 */
export function stepBody(world: MeshCollisionWorld, pos: Vec3, disp: ArrayLike<number>, prm: BodyParams): BodyStepResult {
  const contacts: Contact[] = [];
  const r = CAPSULE_RADIUS;
  // 1) 겹침 해소(이전 프레임 끝이나 리스폰에서 파고든 경우)
  for (let it = 0; it < 4; it++) {
    seg(pos);
    world.overlapBody(A, B, r, prm.filter, PEN);
    if (PEN.length === 0) break;
    const p = PEN[0];
    const push = p.depth + 1e-4;
    pos[0] = f32(pos[0] + p.nx * push);
    pos[1] = f32(pos[1] + p.ny * push);
    pos[2] = f32(pos[2] + p.nz * push);
    contacts.push({ nx: p.nx, ny: p.ny, nz: p.nz, px: p.px, py: p.py, pz: p.pz, tri: p.tri });
  }
  // 2) 변위. OnGround 면 지면 평면으로 방향을 투영하고 크기는 유지한다(GameOnGround: 접지 법선으로 이동 방향 투영 × 이동속력).
  let dx = disp[0], dy = disp[1], dz = disp[2];
  if (prm.onGround) {
    const l = Math.hypot(dx, dy, dz);
    const u = prm.up;
    const d = dx * u[0] + dy * u[1] + dz * u[2];
    let tx = dx - u[0] * d, ty = dy - u[1] * d, tz = dz - u[2] * d;
    const tl = Math.hypot(tx, ty, tz);
    if (tl > 1e-9) {
      tx *= l / tl; ty *= l / tl; tz *= l / tl;
      dx = tx; dy = ty; dz = tz;
    }
  }
  // 지면 접선 방향 이동량(지지 탐색 거리 계산용)
  const ud = dx * prm.up[0] + dy * prm.up[1] + dz * prm.up[2];
  const horiz = Math.hypot(dx - prm.up[0] * ud, dy - prm.up[1] * ud, dz - prm.up[2] * ud);
  // 이동 중 막아 선 "지면으로 볼 수 있는 다른 면"(경사 시작·오징어가 붙을 벽 등): 지지 탐색 방향을 그 면으로 바꾼다
  let newUp: [number, number, number] | null = null;
  for (let it = 0; it < 4; it++) {
    const len = Math.hypot(dx, dy, dz);
    if (len < 1e-7) break;
    seg(pos);
    M[0] = dx; M[1] = dy; M[2] = dz;
    const hit = world.sweepBody(A, B, r, M, prm.filter);
    if (!hit) {
      pos[0] = f32(pos[0] + dx);
      pos[1] = f32(pos[1] + dy);
      pos[2] = f32(pos[2] + dz);
      break;
    }
    const t = hit.t;
    pos[0] = f32(pos[0] + dx * t);
    pos[1] = f32(pos[1] + dy * t);
    pos[2] = f32(pos[2] + dz * t);
    contacts.push({ nx: hit.nx, ny: hit.ny, nz: hit.nz, px: hit.px, py: hit.py, pz: hit.pz, tri: hit.tri });
    let rx = dx * (1 - t), ry = dy * (1 - t), rz = dz * (1 - t);
    let nx = hit.nx, ny = hit.ny, nz = hit.nz;
    if (prm.onGround && ny >= prm.groundLimit && nx * prm.up[0] + ny * prm.up[1] + nz * prm.up[2] < 0.9999) newUp = [nx, ny, nz];
    // 지면 모드에서 지면이 아닌 면(벽)은 수직 벽처럼 다뤄 올라타지 않게 한다
    if (prm.onGround && ny < prm.groundLimit && ny > -0.0001) {
      const hl = Math.hypot(nx, nz);
      if (hl > 1e-6) { nx /= hl; ny = 0; nz /= hl; }
    }
    const into = rx * nx + ry * ny + rz * nz;
    if (into < 0) { rx -= nx * into; ry -= ny * into; rz -= nz * into; }
    dx = rx; dy = ry; dz = rz;
  }
  // 3) 지지면 탐색: up 반대 방향으로 짧게 쓸어 넘긴다.
  //    지면 모드: 수평 이동량 × tan(50.1°) + 0.02 (경사 한계까지는 따라 내려감) [근사]
  //    공중 모드: 0.001 (이미 닿아 있는 경우만 — 착지는 이동 쓸어 넘기기의 접촉으로 판정)
  const probe = prm.onGround ? horiz * 1.1963 + 0.02 : 0.001;
  let supported = false;
  const gn: [number, number, number] = [0, 1, 0];
  const gp: [number, number, number] = [pos[0], pos[1], pos[2]];
  let gtri = -1;
  const u = newUp ?? prm.up;
  seg(pos);
  M[0] = -u[0] * probe; M[1] = -u[1] * probe; M[2] = -u[2] * probe;
  const h = world.sweepBody(A, B, r, M, prm.filter);
  if (h && h.ny >= prm.groundLimit && supportsAlong(h, u)) {
    supported = true;
    gn[0] = h.nx; gn[1] = h.ny; gn[2] = h.nz;
    gp[0] = h.px; gp[1] = h.py; gp[2] = h.pz;
    gtri = h.tri;
    if (prm.onGround) {
      pos[0] = f32(pos[0] + M[0] * h.t);
      pos[1] = f32(pos[1] + M[1] * h.t);
      pos[2] = f32(pos[2] + M[2] * h.t);
    }
    contacts.push({ nx: h.nx, ny: h.ny, nz: h.nz, px: h.px, py: h.py, pz: h.pz, tri: h.tri });
  } else {
    // 이동 중 닿은 접촉 가운데 지면 법선이 있으면 접지
    for (const c of contacts) {
      if (c.ny >= prm.groundLimit && c.nx * u[0] + c.ny * u[1] + c.nz * u[2] > 0) {
        supported = true;
        gn[0] = c.nx; gn[1] = c.ny; gn[2] = c.nz;
        gp[0] = c.px; gp[1] = c.py; gp[2] = c.pz;
        gtri = c.tri;
        break;
      }
    }
  }
  return { supported, gn, gp, gtri, contacts };
}

function supportsAlong(h: SweepResult, u: ArrayLike<number>): boolean {
  return h.nx * u[0] + h.ny * u[1] + h.nz * u[2] > 0;
}
