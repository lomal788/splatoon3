// world.shared "player"(physics 담당, core/player/state.ts PlayerState) 읽기.
// render 는 PlayerState 의 일부 필드만 읽고, 이름이 바뀌어도 이 파일만 고치도록 구조적 타입(PlayerLike)으로 받는다.
import type { World } from "../../core/world.ts";

type V3 = ArrayLike<number> | { x: number; y: number; z: number };

/** render 가 읽는 플레이어 필드(임시). 없는 필드는 아래 규칙으로 대신한다. */
export interface PlayerLike {
  /** 모델 원점(발밑) 위치 */
  pos?: V3;
  position?: V3;
  /** 모델 정면(수평 단위) — PlayerState.facing. 없으면 yaw */
  facing?: V3;
  /** 라디안, 앞 = (sin yaw, 0, cos yaw) */
  yaw?: number;
  /** 속도(유닛/프레임) */
  vel?: V3;
  velocity?: V3;
  /** 상태 번호(player_state.md 부록) */
  state?: number;
  /** 보조 상태(슬롯 1) */
  sub?: number;
  /** 오징어 형태 여부 — state 가 없을 때만 씀 */
  squid?: boolean;
  isSquid?: boolean;
  team?: number;
  dead?: boolean;
  /** SM+0xf0 변신 과도기 카운터(PlayerState.transform) — 있으면 render 재계산 대신 사용 */
  transform?: number;
  /** SM+0xd4 이동 애니 속도값 — 있으면 수평 속력 대신 사용 */
  animSpeed?: number;
  /** 상태 요청 재생 속도(0x7102447bfc rate, PlayerState.stateRate) — 있으면 render 규칙 대신 사용 */
  stateRate?: number;
}

export interface PlayerSnap {
  pos: [number, number, number];
  yaw: number;
  speed: number | null;
  state: number | null;
  sub: number | null;
  squid: boolean;
  team: number;
  dead: boolean;
  formCounter: number | null;
  animSpeed: number | null;
  animRate: number | null;
}

function v3(v: V3 | undefined): [number, number, number] | null {
  if (!v) return null;
  if ("x" in v) return [v.x, v.y, v.z];
  return [v[0], v[1], v[2]];
}

const num = (x: unknown): number | null => (typeof x === "number" && Number.isFinite(x) ? x : null);

export function readPlayer(w: World): PlayerSnap | null {
  const p = w.shared.get("player") as PlayerLike | undefined;
  if (!p || typeof p !== "object") return null;
  const pos = v3(p.pos ?? p.position) ?? [0, 0, 0];
  const f = v3(p.facing);
  const yaw = f && (f[0] !== 0 || f[2] !== 0) ? Math.atan2(f[0], f[2]) : num(p.yaw) ?? 0;
  const vel = v3(p.vel ?? p.velocity);
  return {
    pos,
    yaw,
    speed: vel ? Math.hypot(vel[0], vel[2]) : null,
    state: num(p.state),
    sub: num(p.sub),
    squid: !!(p.squid ?? p.isSquid),
    team: num(p.team) ?? 0,
    dead: !!p.dead,
    formCounter: num(p.transform),
    animSpeed: num(p.animSpeed),
    animRate: num(p.stateRate),
  };
}
