// 플레이어 카메라 리그(0x71024d6e84 mode 0) — p(-1..1) 별 주시점 높이 H·전방 F·거리 D·위 오프셋 S 와 고각 회전.
// 근거: docs/camera/player_camera.md §4.1 상수(0x71024d63f0), §6.1 리그, §6.2 오징어 블록(batch1.c 1031~1200행 직접 판독).
import { F, add, sub, mul, div, mix } from "./native_math.ts";
import { sinCos } from "../weapon/swerve.ts";

function rigCubic(p: number, c: readonly number[]): number {
  p=F(p);
  const t=Math.abs(p),u=p<=0 ? add(p,1) : sub(1,p);
  const m=mul(mul(p,p<=0 ? -3 : 3),u);
  const c0=mul(mul(u,u),u),c1=mul(u,m),c2=mul(m,t),c3=mul(mul(p,p),t);
  return add(mul(c3,c[3]),add(mul(c2,c[2]),add(mul(c0,c[0]),mul(c1,c[1]))));
}
function pieceBez(p: number, down: number, mid: number, up: number, k: number): number {
  const tangent=mul(sub(up,down),k);
  return rigCubic(p,p<=0 ? [mid,sub(mid,tangent),down,down] : [mid,add(mid,tangent),up,up]);
}
function pieceCtrl(p: number, neg: readonly number[], pos: readonly number[]): number {
  return rigCubic(p,p<=0 ? neg : pos);
}

/** 0x71024d63f0 상수 블록 (Lby_Lobby00의 LobbyVersus: G+0x143d0=0, r9_state_sources §6.1). */
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
const SQ_WALL_H = { neg: [1.45, 1.2750000953674316, 1.45, 1.45], pos: [1.45, 1.625, 1.8, 1.8] } as const;
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
  out.H = mix(h, pieceCtrl(p, SQ_WALL_H.neg, SQ_WALL_H.pos), u);
  out.F = mix(f, 0, u);
  out.D = mix(d, pieceCtrl(p, SQ_WALL_D.neg, SQ_WALL_D.pos), u);
  out.S = mix(s, 0, u);
  return out;
}

/** 기본 리그 → 오징어 블록 가중 블렌드(+0x1764). */
export function blendedRig(p: number, squidW: number, u: number, out: RigValues, tmp: RigValues): RigValues {
  baseRig(p, out);
  if (squidW > 0) {
    squidRig(p, u, tmp);
    out.H = mix(out.H, tmp.H, squidW);
    out.F = mix(out.F, tmp.F, squidW);
    out.D = mix(out.D, tmp.D, squidW);
    out.S = mix(out.S, tmp.S, squidW);
  }
  return out;
}

/** 고각 변수(도): A + |p|(B - A), B = p>0 ? B↑ : B↓. 리그는 이 값의 음수만큼 돌린다(값이 음수면 카메라가 위로). */
export function elevationDeg(p: number, A: number, Bup: number, Bdown: number): number {
  const B = p > 0 ? Bup : Bdown;
  return mix(A, B, Math.abs(p));
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
  const dx=F(dir[0]),dy=F(dir[1]),dz=F(dir[2]),zeroH=mul(v.H,0);
  at[0]=add(add(mul(v.F,dx),base[0]),zeroH);
  at[1]=add(mul(v.F,dy),add(v.H,base[1]));
  at[2]=add(add(mul(v.F,dz),zeroH),base[2]);
  const wx=sub(dz,mul(dy,0)),wy=sub(mul(dx,0),mul(dz,0)),wz=sub(mul(dy,0),dx);
  cam[0]=add(mul(sub(mul(dy,wz),mul(dz,wy)),v.S),sub(at[0],mul(v.D,dx)));
  cam[1]=add(mul(sub(mul(dz,wx),mul(dx,wz)),v.S),sub(at[1],mul(v.D,dy)));
  cam[2]=add(mul(sub(mul(dx,wy),mul(dy,wx)),v.S),sub(at[2],mul(v.D,dz)));
  const vx=sub(cam[0],at[0]),vy=sub(cam[1],at[1]),vz=sub(cam[2],at[2]);
  let ax=sub(mul(vy,0),vz),ay=sub(mul(vz,0),mul(vx,0)),az=sub(vx,mul(vy,0));
  const n=F(Math.sqrt(add(add(mul(az,az),mul(ax,ax)),mul(ay,ay))));
  if (n>0) {
    const inv=div(1,n);ax=mul(inv,ax);ay=mul(inv,ay);az=mul(inv,az);
    const [sn,cs]=sinCos(mul(elevDeg,-.017453292));
    const dot=add(mul(vz,az),add(mul(vx,ax),mul(vy,ay)));
    cam[0]=add(at[0],add(mul(sub(mul(vz,ay),mul(vy,az)),sn),add(mul(ax,dot),mul(sub(vx,mul(ax,dot)),cs))));
    cam[1]=add(at[1],add(mul(sub(mul(vx,az),mul(vz,ax)),sn),add(mul(ay,dot),mul(sub(vy,mul(ay,dot)),cs))));
    cam[2]=add(at[2],add(mul(sub(mul(vy,ax),mul(vx,ay)),sn),add(mul(az,dot),mul(sub(vz,mul(az,dot)),cs))));
  }
}
