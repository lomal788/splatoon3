// 담당: [paint] — docs/impl/paint.md 에 구현 상태·미확정을 기록한다.
import type { System } from "../world.ts";

export function createPaintSystem(): System {
  return { id: "paint", step() {} };
}
