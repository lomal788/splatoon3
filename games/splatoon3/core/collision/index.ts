// 담당: [physics] — docs/impl/physics.md 에 구현 상태·미확정을 기록한다.
// 지형 충돌 세계를 init 에서 만들고 world.collision 에 둔다. 동적 충돌체는 각 영역이 setDynamic 으로 갱신한다.
import type { System, World } from "../world.ts";
import { fallbackPlane, loadCollision, MeshCollisionWorld } from "./world.ts";

export { MeshCollisionWorld, fallbackPlane, loadCollision, playerBodyFilter } from "./world.ts";
export type { MaterialInfo, BodyFilter } from "./world.ts";
export { TriMesh } from "./mesh.ts";
export type { SweepResult, Penetration } from "./mesh.ts";
export { LAYER_HIT_MASK, SUB_LAYER_HIT_MASK, PhiveLayer, PhiveSubLayer } from "./filter.ts";

/** world.data.collision → 충돌 세계. 에셋이 없거나 읽기 실패면 y=0 평면(경고). */
export function buildCollision(data: unknown): MeshCollisionWorld {
  const d = data as { meta?: Record<string, unknown>; bin?: ArrayBuffer | null } | null;
  if (d && d.meta && d.bin) {
    try {
      return loadCollision(d.meta, d.bin);
    } catch (e) {
      console.warn("[physics] collision 읽기 실패 — 평면으로 대체:", e);
      return fallbackPlane();
    }
  }
  console.warn("[physics] collision 에셋 없음 — y=0 평면으로 대체(placeholder)");
  return fallbackPlane();
}

export function createCollisionSystem(): System {
  return {
    id: "collision",
    init(w: World) {
      w.collision = buildCollision(w.data.collision);
    },
    step() {},
  };
}
