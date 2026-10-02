// 담당: [physics] — 시작 위치. placement.json(맵 배치, 원본 bcett 변환)에서 StartPos 를 고른다.
// 근거(데이터 판단): Lby_Lobby00 의 StartPos 10개 중 9개는 spl__StartPosParam.Name 이 ResultPlayer0..7(결과 화면)·
// FromReplay(리플레이 복귀)이고, 이름 없는 1개만 TeamCmp Alpha 다(-0.149, 0.01, -11.959, yaw −0.382). StartPosTipsTrial 은
// 팁 체험 모드 전용 이름(Restore/Aim/Front10m …)이다. 그래서 이름 없는 팀 StartPos 를 로비(사격장) 입장 위치로 본다 [추정].
// 이 위치는 LobbyShootingArea(중심 -8.17, 6.82, -8.41, 크기 20×34) 안이다 [데이터].
import type { Team } from "../types.ts";

export interface SpawnPoint {
  pos: [number, number, number];
  /** Y 회전(라디안). 정면 = (sin yaw, 0, cos yaw) [추정: 모델 정면 +Z] */
  yaw: number;
  source: string;
}

interface ActorLike {
  [k: string]: unknown;
}

function str(v: unknown): string {
  return typeof v === "string" ? v : "";
}

function vec(v: unknown): [number, number, number] | null {
  if (Array.isArray(v) && v.length >= 3 && v.every((x) => typeof x === "number")) return [v[0], v[1], v[2]];
  if (v && typeof v === "object") {
    const o = v as Record<string, unknown>;
    const x = o.X ?? o.x, y = o.Y ?? o.y, z = o.Z ?? o.z;
    if (typeof x === "number" && typeof y === "number" && typeof z === "number") return [x, y, z];
  }
  return null;
}

function actors(placement: unknown): ActorLike[] {
  if (!placement || typeof placement !== "object") return [];
  if (Array.isArray(placement)) return placement as ActorLike[];
  const o = placement as Record<string, unknown>;
  for (const k of ["Actors", "actors", "objects", "items"]) if (Array.isArray(o[k])) return o[k] as ActorLike[];
  return [];
}

function typeName(a: ActorLike): string {
  return str(a.Gyaml ?? a.gyaml ?? a.type ?? a.Name ?? a.name);
}

function teamOf(a: ActorLike): string {
  const t = a.TeamCmp as Record<string, unknown> | undefined;
  return str(t?.Team ?? a.team ?? a.Team);
}

function paramName(a: ActorLike): string {
  // bcett 원형: a.spl__StartPosParam.Name / 웹 placement.json: a.params.spl__StartPosParam.Name
  const params = (a.params ?? {}) as Record<string, unknown>;
  const p = (a.spl__StartPosParam ?? params.spl__StartPosParam) as Record<string, unknown> | undefined;
  return str(p?.Name ?? a.startName);
}

const TEAM_NAME = ["Alpha", "Bravo", "Charlie"];

/** StartPos 고르기: 이름 없는 내 팀 → 이름 없는 아무 팀 → 첫 StartPos. 없으면 null. */
export function findSpawn(placement: unknown, team: Team): SpawnPoint | null {
  const list = actors(placement).filter((a) => typeName(a) === "StartPos");
  if (list.length === 0) return null;
  const want = team >= 0 ? TEAM_NAME[team] : "";
  const pick =
    list.find((a) => paramName(a) === "" && teamOf(a) === want) ??
    list.find((a) => paramName(a) === "") ??
    list[0];
  const t = vec(pick.Translate ?? pick.translate ?? pick.pos ?? pick.position) ?? [0, 0, 0];
  const r = vec(pick.Rotate ?? pick.rotate ?? pick.rot) ?? [0, 0, 0];
  return { pos: t, yaw: r[1], source: `StartPos ${teamOf(pick) || "?"} ${paramName(pick) || "(이름 없음)"}` };
}
