// 담당: [paint] — docs/impl/paint.md 에 구현 상태·미확정을 기록한다.
// 도색 시스템: init 에서 충돌 메시 → 도색 표면(아틀라스) → PaintWorld(world.paint), shared "paintSurfaces".
// step 은 프레임 마지막(무기 뒤)에 요청을 처리한다(core/systems.ts).
import type { System, World } from "../world.ts";
import { PaintWorldImpl } from "./paintworld.ts";
import { playerPoint, teamPoint } from "./score.ts";
import { PaintSurfaces, readCollisionTriangles } from "./surface.ts";

export { PaintKind, PaintWorldImpl, type InkSampleEx, type PaintSurfacesShared } from "./paintworld.ts";
export * from "./shape.ts";
export { playerPoint, teamPoint } from "./score.ts";

/** 에셋 표 이름(data/<이름>.json → world.data.tables). 앞에 있는 이름을 먼저 찾는다. */
const INKTEX_TABLES = ["InkTexInfo", "ink_tex_info", "inktex_info"];
const STAMP_TABLES = ["ink_stamps", "InkTexture", "inktex"];

export function createPaintSystem(): System {
  let pw: PaintWorldImpl | null = null;
  return {
    id: "paint",
    init(w: World) {
      const surf = new PaintSurfaces(readCollisionTriangles(w));
      pw = new PaintWorldImpl(w, surf, pick(w, INKTEX_TABLES), pick(w, STAMP_TABLES));
      w.paint = pw;
      w.shared.set("paintSurfaces", pw.shared);
      debug(w)["paint.surface"] = `${surf.tris.source} 차트 ${surf.charts.length} 텍셀 ${surf.totalInside} 마스크 ${pw.stamps.hasOriginal ? "원본" : "근사"}`;
    },
    step(w: World) {
      if (!pw) return;
      pw.step(w);
      const c = pw.counts();
      const dbg = debug(w);
      dbg["paint.p"] = playerPoint(pw.playerTexels[0] ?? 0);
      dbg["paint.teamP"] = `${teamPoint(c.team[0])} / ${teamPoint(c.team[1])} (max ${teamPoint(c.total)})`;
    },
  };
}

function pick(w: World, names: string[]): unknown {
  for (const n of names) if (w.data.tables[n] !== undefined) return w.data.tables[n];
  return null;
}

function debug(w: World): Record<string, unknown> {
  let d = w.shared.get("debug") as Record<string, unknown> | undefined;
  if (!d) w.shared.set("debug", (d = {}));
  return d;
}
