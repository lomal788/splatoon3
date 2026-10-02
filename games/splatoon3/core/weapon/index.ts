// 담당: [weapon] — docs/impl/weapon.md 에 구현 상태·미확정을 기록한다.
// 메인 무기(스플래시슈터) 사격과 탄(BulletShooterBase·BulletSplashShooter·BulletWallDrop).
import type { System, World } from "../world.ts";
import { WeaponRuntime } from "./runtime.ts";

export { Bullet, type BulletKind, type SpawnInfo } from "./bullet.ts";
export { WallDrop } from "./wall_drop.ts";
export type { BulletView } from "./runtime.ts";

export function createWeaponSystem(): System {
  let rt: WeaponRuntime | null = null;
  return {
    id: "weapon",
    init(w: World) {
      rt = new WeaponRuntime(w);
    },
    step(w: World) {
      rt ??= new WeaponRuntime(w);
      rt.step(w);
    },
  };
}
