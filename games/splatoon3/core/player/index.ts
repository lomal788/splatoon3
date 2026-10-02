// 담당: [physics] — docs/impl/physics.md 에 구현 상태·미확정을 기록한다.
import type { System } from "../world.ts";

export function createPlayerSystem(): System {
  return { id: "player", step() {} };
}
