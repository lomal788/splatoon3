// 담당: [camera] — docs/impl/camera.md 에 구현 상태·미확정을 기록한다.
import type { System } from "../world.ts";

export function createCameraSystem(): System {
  return { id: "camera", step() {} };
}
