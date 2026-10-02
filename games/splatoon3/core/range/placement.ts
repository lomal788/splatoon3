// 배치 데이터(world.data.placement) → 사격장이 쓰는 형태.
// 받는 형식: [assets] placement.json(docs/impl/assets.md: actors[]/rails[], 해시 = 10진 문자열)
// 또는 원본 Banc JSON(Actors[]/Rails[], Gyaml·Hash·Translate·Rotate·Scale·TeamCmp).
import type { RailData } from "./rail.ts";

export interface PlacedActor {
  hash: string;
  /** 액터 이름(Gyaml 짧은 이름, 예: "SighterTarget_Move") */
  name: string;
  pos: [number, number, number];
  rot: [number, number, number];
  scale: [number, number, number];
  team: string;
  params: Record<string, Record<string, unknown>>;
}

type Obj = Record<string, unknown>;

function vec(v: unknown, d: number): [number, number, number] {
  if (Array.isArray(v) && v.length >= 3) return [Number(v[0]), Number(v[1]), Number(v[2])];
  if (v && typeof v === "object") {
    const o = v as Obj;
    if ("X" in o) return [Number(o.X), Number(o.Y), Number(o.Z)];
  }
  return [d, d, d];
}

function hashStr(v: unknown): string {
  if (typeof v === "string") return v;
  if (typeof v === "number" || typeof v === "bigint") return String(v);
  return "";
}

function shortName(g: string): string {
  const base = g.slice(g.lastIndexOf("/") + 1);
  const dot = base.indexOf(".");
  return dot >= 0 ? base.slice(0, dot) : base;
}

export function readActors(placement: unknown): PlacedActor[] {
  if (!placement || typeof placement !== "object") return [];
  const p = placement as Obj;
  const list = (p.actors ?? p.Actors) as Obj[] | undefined;
  if (!Array.isArray(list)) return [];
  return list.map((a) => {
    const gy = String(a.gyml ?? a.Gyaml ?? a.name ?? a.Name ?? "");
    const name = shortName(String(a.name ?? "") || gy);
    const params: Record<string, Record<string, unknown>> = {};
    const src = (a.params as Obj | undefined) ?? a;
    for (const [k, v] of Object.entries(src)) if ((k.startsWith("spl__") || k.startsWith("game__")) && v && typeof v === "object") params[k] = v as Record<string, unknown>;
    const teamCmp = a.TeamCmp as Obj | undefined;
    return {
      hash: hashStr(a.hash ?? a.Hash),
      name,
      pos: vec(a.pos ?? a.Translate, 0),
      rot: vec(a.rot ?? a.Rotate, 0),
      scale: vec(a.scale ?? a.Scale, 1),
      team: String(a.team ?? teamCmp?.Team ?? "Neutral"),
      params,
    };
  });
}

export function readRails(placement: unknown): RailData[] {
  if (!placement || typeof placement !== "object") return [];
  const p = placement as Obj;
  const list = (p.rails ?? p.Rails) as Obj[] | undefined;
  if (!Array.isArray(list)) return [];
  return list.map((r) => {
    const pts = ((r.Points ?? r.points) as Obj[] | undefined) ?? [];
    return {
      hash: hashStr(r.hash ?? r.Hash),
      closed: Boolean(r.IsClosed ?? r.closed ?? false),
      rotation: vec(r.Rotation ?? r.rotation, 0),
      points: pts.map((q) => {
        const node = (q.game__LiftGraphRailNodeParam as Obj | undefined) ?? {};
        return {
          hash: hashStr(q.hash ?? q.Hash),
          pos: vec(q.Translate ?? q.pos, 0),
          rotDeg: vec(node.Rotation, 0),
          breakTime: typeof node.BreakTime === "number" ? node.BreakTime : 0,
        };
      }),
    };
  });
}
