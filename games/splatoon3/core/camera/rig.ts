// 플레이어 카메라 리그(0x71024d6e84 mode 0) — p(-1..1) 별 주시점 높이 H·전방 F·거리 D·위 오프셋 S 와 고각 회전.
// 근거: docs/camera/player_camera.md §4.1 상수(0x71024d63f0), §6.1 리그, §6.2 오징어 블록(batch1.c 1031~1200행 직접 판독).
import { pieceBez, pieceCtrl } from "./curves.ts";

/** 0x71024d63f0 상수 블록 (전역 조건 *0x7105791bd0+0x143d0 == 0 쪽 값, 의미 미확정). */
export const RIG = {
  fov: 55, // +0x179c 기준 FOV(도)
  dist: [7.2, 6.8, 4.0], // +0x17a0..+0x17a8 (아래, 가운데, 위)
  targetHeight: [2.25, 2.25, 2.75], // +0x17ac..
  targetForward: [1.0, 0.5, 0.0], // +0x17b8..
  upOffset: [0, 0, 0], // +0x17c4..
  tangent: 0.2, // +0x17dc
  elevA: -7.5, // +0x17d4 고각 기준
  elevUp: 60, // +0x17d0
  elevDown: -75, // +0x17d8
  squid: {
    dist: [7.2, 6.8, 5.2], // +0x17e4..
    targetHeight: [1.45, 1.45, 2.35], // +0x17f0..
    targetForward: [0, 0.5, 0.5], // +0x17fc..
    upOffset: [0, 0, 0], // +0x1808..
    tangent: 0.5, // +0x1820
    fov: 60, // 0x71024d9ae8 FOV 목표(오징어 조건 참)
  },
} as const;

/** 오징어 블록 안에서 바닥 법선 y 로 섞는 상수 곡선 (batch1.c 1046~1135행). [P0..P3] p<=0 / p>0 */
const SQ_WALL_H = { neg: [1.45, 1.275, 1.45, 1.45], pos: [1.45, 1.625, 1.8, 1.8] } as const;
const SQ_WALL_D = { neg: [7.5, 7.5, 10, 10], pos: [7.5, 7.5, 10, 10] } as const;

export interface RigValues {
  H: number;
  F: number;
  D: number;
  S: number;
}

export function baseRig(p: number, out: RigValues): RigValues {
  const k = RIG.tangent;
  const [hd, hm, hu] = RIG.targetHeight;
  const [fd, fm, fu] = RIG.targetForward;
  const [dd, dm, du] = RIG.dist;
  const [sd, sm, su] = RIG.upOffset;
  out.H = pieceBez(p, hd, hm, hu, k);
  out.F = pieceBez(p, fd, fm, fu, k);
  out.D = pieceBez(p, dd, dm, du, k);
  out.S = pieceBez(p, sd, sm, su, k);
  return out;
}

/**
 * 오징어 블록 목표값. u = min(1 - 카메라 바닥 법선 y(+0x13c), 1).
 * 원본은 여기에 +0x1550·+0x1570 가중 곡선을 더 섞는다(관전·특수 재시작 모드, 웹 범위 밖이라 0으로 둠).
 */
export function squidRig(p: number, u: number, out: RigValues): RigValues {
  const q = RIG.squid;
  const k = q.tangent;
  const h = pieceBez(p, q.targetHeight[0], q.targetHeight[1], q.targetHeight[2], k);
  const f = pieceBez(p, q.targetForward[0], q.targetForward[1], q.targetForward[2], k);
  const d = pieceBez(p, q.dist[0], q.dist[1], q.dist[2], k);
  const s = pieceBez(p, q.upOffset[0], q.upOffset[1], q.upOffset[2], k);
  out.H = h + u * (pieceCtrl(p, SQ_WALL_H.neg, SQ_WALL_H.pos) - h);
  out.F = f + u * (0 - f);
  out.D = d + u * (pieceCtrl(p, SQ_WALL_D.neg, SQ_WALL_D.pos) - d);
  out.S = s + u * (0 - s);
  return out;
}

/** 기본 리그 → 오징어 블록 가중 블렌드(+0x1764). */
export function blendedRig(p: number, squidW: number, u: number, out: RigValues, tmp: RigValues): RigValues {
  baseRig(p, out);
  if (squidW > 0) {
    squidRig(p, u, tmp);
    out.H += squidW * (tmp.H - out.H);
    out.F += squidW * (tmp.F - out.F);
    out.D += squidW * (tmp.D - out.D);
    out.S += squidW * (tmp.S - out.S);
  }
  return out;
}

/** 고각 변수(도): A + |p|(B - A), B = p>0 ? B↑ : B↓. 리그는 이 값의 음수만큼 돌린다(값이 음수면 카메라가 위로). */
export function elevationDeg(p: number, A: number, Bup: number, Bdown: number): number {
  const B = p > 0 ? Bup : Bdown;
  return A + Math.abs(p) * (B - A);
}

/**
 * 리그 위치 계산(0x71024d6e84 끝부분). base = 추종 위치(+0x120), dir = 리그 수평 시선(+0x1a4).
 * at = base + F·dir + (0,H,0); cam = at - D·dir + S·(dir×(up×dir)); cam 을 at 둘레 축 normalize(-v.z,0,v.x) 로 -θ° 회전.
 */
export function rigPose(
  base: ArrayLike<number>,
  dir: ArrayLike<number>,
  v: RigValues,
  elevDeg: number,
  at: Float32Array,
  cam: Float32Array,
): void {
  const dx = dir[0], dy = dir[1], dz = dir[2];
  const H = v.H;
  at[0] = v.F * dx + base[0];
  at[1] = v.F * dy + H + base[1];
  at[2] = v.F * dz + base[2];
  const wx = dz, wy = 0, wz = -dx;
  let cx = at[0] - v.D * dx;
  let cy = at[1] - v.D * dy;
  let cz = at[2] - v.D * dz;
  cx += (dy * wz - dz * wy) * v.S;
  cy += (dz * wx - dx * wz) * v.S;
  cz += (dx * wy - dy * wx) * v.S;
  const vx = cx - at[0], vy = cy - at[1], vz = cz - at[2];
  let ax = -vz, az = vx;
  const n = Math.hypot(ax, az);
  if (n > 0) {
    ax /= n;
    az /= n;
    const th = elevDeg * -0.017453292;
    const s = Math.sin(th), c = Math.cos(th);
    const d = ax * vx + az * vz;
    cam[0] = at[0] + -vy * az * s + ax * d + (vx - ax * d) * c;
    cam[1] = at[1] + (vx * az - vz * ax) * s + vy * c;
    cam[2] = at[2] + vy * ax * s + az * d + (vz - az * d) * c;
  } else {
    cam[0] = cx;
    cam[1] = cy;
    cam[2] = cz;
  }
}
