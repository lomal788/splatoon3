// 로비 사격 구역(LobbyShootingArea / _Cylinder) 안쪽 판정. 근거: docs/range/shooting_range.md §6.6.
//   안쪽 판정 0x71012496e8 (case 2 = Cube, case 3 = Cylinder), 모양·배율 = RSDB LocatorInfo.
//   플레이어 쪽 사용: 0x7102483134 안 0x7102484ff8~0x7102489e6c (본체+0x938d = 안쪽, +0x938c = 공중 4프레임 미만일 때만 갱신).
import { f32 } from "../fmath.ts";
import { AIR_FRAMES_LATCH } from "./data.ts";
import { quatToMat3, eulerZYXToQuat } from "./rail.ts";

export interface ShootingArea {
  name: string;
  shape: "Cube" | "Cylinder";
  pos: [number, number, number];
  /** 회전 3x3 열 우선(X, Y, Z 축) */
  axes: number[];
  scale: [number, number, number];
  /** LocatorInfo.Scale (영역 +0x24 배율로 봄 [추정]) */
  mul: number;
}

export function makeArea(name: string, shape: "Cube" | "Cylinder", mul: number, pos: number[], rot: number[], scale: number[]): ShootingArea {
  return {
    name,
    shape,
    pos: [f32(pos[0]), f32(pos[1]), f32(pos[2])],
    axes: quatToMat3(eulerZYXToQuat(rot[0], rot[1], rot[2])),
    scale: [f32(scale[0]), f32(scale[1]), f32(scale[2])],
    mul,
  };
}

/** 0x71012496e8. 로컬 = 축과의 내적(Rᵀ(p−T)) [판독 + 저장 순서는 추정, 문서 §6.6] */
export function insideArea(a: ShootingArea, p: ArrayLike<number>): boolean {
  const dx = f32(p[0] - a.pos[0]), dy = f32(p[1] - a.pos[1]), dz = f32(p[2] - a.pos[2]);
  const m = a.axes;
  const lx = f32(f32(f32(m[0] * dx) + f32(m[1] * dy)) + f32(m[2] * dz));
  const ly = f32(f32(f32(m[3] * dx) + f32(m[4] * dy)) + f32(m[5] * dz));
  const lz = f32(f32(f32(m[6] * dx) + f32(m[7] * dy)) + f32(m[8] * dz));
  const s = a.mul;
  if (a.shape === "Cube") {
    return (
      Math.abs(lx) <= f32(f32(s * a.scale[0]) * 0.5) &&
      Math.abs(ly) <= f32(f32(s * a.scale[1]) * 0.5) &&
      Math.abs(lz) <= f32(f32(s * a.scale[2]) * 0.5)
    );
  }
  // Cylinder: 바닥이 원점, 높이 2·s·Sy, 반지름 s·Sx (r² < R² 엄격)
  if (ly < 0) return false;
  const h = f32(s * a.scale[1]);
  if (f32(h + h) <= ly) return false;
  const r = f32(s * a.scale[0]);
  return f32(f32(lx * lx) + f32(lz * lz)) < f32(r * r);
}

export function insideAnyArea(areas: readonly ShootingArea[], p: ArrayLike<number>): boolean {
  // 원본은 Cube 이름 목록을 먼저, 없으면 Cylinder 목록을 본다. 결과(하나라도 안쪽)는 순서와 무관.
  for (const a of areas) if (a.shape === "Cube" && insideArea(a, p)) return true;
  for (const a of areas) if (a.shape === "Cylinder" && insideArea(a, p)) return true;
  return false;
}

/**
 * 본체+0x938c 갱신 규칙: 안쪽 여부(+0x938d)는 매 프레임, 무기 허용 래치(+0x938c)는 공중 프레임 < 4 일 때만 안쪽 값으로.
 * 반환 = 새 래치 값.
 */
export function updateShootLatch(prevLatch: boolean, inside: boolean, airFrames: number): boolean {
  return airFrames < AIR_FRAMES_LATCH ? inside : prevLatch;
}
