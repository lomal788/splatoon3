// 다른 영역의 공유 상태(world.shared "player"·"camera") 읽기. 필드 계약은 docs/impl/weapon.md "조정 요청".
// 아직 없는 필드는 무기 쪽 임시값으로 대신한다(어떤 값이 임시인지는 문서에 기록).
import type { Team } from "../types.ts";
import type { World } from "../world.ts";
import type { V3 } from "./move.ts";

export interface ShooterView {
  id: number;
  team: Team;
  /** 본체+0x58..+0x60 (발사 위치 계산 기준) */
  pos: V3;
  /** 본체+0xe4 최종 속도(유닛/프레임) — 탄 초기 속도 가산 */
  vel: V3;
  /** 조준 방향(0x71024aff7c 결과, 단위) */
  aim: V3;
  /** 본체+0x538/+0x54c 카메라 리그 수평 시선 */
  rigForward: V3;
  /** 본체+0x544/+0x558 카메라 피치 p (−1..1) */
  pitch: number;
  /** 카메라 위치·주시점(조준 기준 축 a = 정규화(주시점 − 위치)) */
  camAxis: V3 | null;
  camPos: V3 | null;
  camAt: V3 | null;
  /** 사격 불가 상태(오징어·전환 중 등) */
  blocked: boolean;
  /** 본체+0xc0 공중 프레임 */
  airFrames: number;
  /** 이번 프레임 점프 시작(흔들림 vt40 0x7102580c4c) */
  jumped: boolean;
  /** 잉크 탱크 잔량(본체+0x698, 0..1). 플레이어 쪽에 없으면 null */
  ink: number | null;
  raw: Record<string, unknown> | null;
}

function vec(v: unknown): V3 | null {
  if (!v || typeof v !== "object") return null;
  const a = v as ArrayLike<number>;
  if (typeof a[0] === "number" && typeof a[1] === "number" && typeof a[2] === "number") return [a[0], a[1], a[2]];
  const o = v as { x?: number; y?: number; z?: number };
  if (typeof o.x === "number" && typeof o.y === "number" && typeof o.z === "number") return [o.x, o.y, o.z];
  return null;
}

function num(v: unknown): number | null {
  return typeof v === "number" && Number.isFinite(v) ? v : null;
}

function pick(o: Record<string, unknown> | null, ...keys: string[]): unknown {
  if (!o) return undefined;
  for (const k of keys) if (o[k] !== undefined) return o[k];
  return undefined;
}

/** 조준 단위벡터: camera.aimDir → player.aim → camera yaw/pitch 의 시선. 없으면 null. */
function aimOf(cam: Record<string, unknown> | null, pl: Record<string, unknown> | null): V3 | null {
  return vec(pick(cam, "aimDir", "aim", "shotDir")) ?? vec(pick(pl, "aimDir", "aim")) ?? null;
}

export function readShooter(w: World, index: number): ShooterView {
  const pl = (w.shared.get("player") ?? null) as Record<string, unknown> | null;
  const cam = (w.shared.get("camera") ?? null) as Record<string, unknown> | null;
  const spec = w.data.players[index];
  const pos = vec(pick(pl, "pos", "position")) ?? [0, 0, 0];
  const vel = vec(pick(pl, "final", "finalVel", "vel", "velocity")) ?? [0, 0, 0];
  const rig = vec(pick(cam, "rigForward", "forward")) ?? vec(pick(pl, "rigForward", "aimForward")) ?? [0, 0, 1];
  const aim = aimOf(cam, pl) ?? rig;
  const pitch = num(pick(cam, "pitchNorm", "pitchP", "p")) ?? num(pick(pl, "pitchP")) ?? 0;
  const squid = pick(pl, "squid", "isSquid") === true;
  const blocked = squid || pick(pl, "shotBlocked") === true || pick(pl, "canShoot") === false;
  return {
    id: num(pick(pl, "id")) ?? index + 1,
    team: (num(pick(pl, "team")) ?? spec?.team ?? 0) as Team,
    pos,
    vel,
    aim,
    rigForward: rig,
    pitch,
    camAxis: vec(pick(cam, "viewForward")),
    camPos: vec(pick(cam, "pos", "position", "eye")),
    camAt: vec(pick(cam, "target", "at", "lookAt")),
    blocked,
    airFrames: num(pick(pl, "airFrames")) ?? 0,
    jumped: w.events.list.some((e) => e.type === "Jump" && (e.owner === undefined || e.owner === pick(pl, "id"))),
    ink: num(pick(pl, "ink", "inkTank")),
    raw: pl,
  };
}
