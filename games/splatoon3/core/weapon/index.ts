// 담당: [weapon] — docs/impl/weapon.md 에 구현 상태·미확정을 기록한다.
import type { System } from "../world.ts";

export function createWeaponSystem(): System {
  return { id: "weapon", step() {} };
}
