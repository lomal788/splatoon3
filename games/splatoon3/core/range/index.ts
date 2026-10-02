// 담당: [range] — docs/impl/range.md 에 구현 상태·미확정을 기록한다.
import type { System } from "../world.ts";

export function createRangeSystem(): System {
  return { id: "range", step() {} };
}
