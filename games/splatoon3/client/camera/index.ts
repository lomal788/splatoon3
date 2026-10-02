// 담당: [camera] — docs/impl/camera.md 에 구현 상태·미확정을 기록한다.
// core 카메라(shared "camera") → three PerspectiveCamera. 렌더 보간은 직전 스텝 값과 alpha 로 선형 보간(웹 선택).
// 카메라 쉐이크: fx 가 camera.userData.shakeOffset({x,y,z}, 월드)을 두면 위치·주시점에 같이 더한다
// (원본은 쉐이크 합을 포즈 위치(월드)에 더하고 회전은 그대로 — docs/camera/shake_rumble.md §3.2a).
import type { CameraShared } from "../../core/camera/index.ts";
import type { World } from "../../core/world.ts";
import type { ClientContext, View } from "../context.ts";

export function createCameraView(ctx: ClientContext): View {
  const cam = ctx.camera;
  cam.up.set(0, 1, 0);
  return {
    update(w: World, alpha: number) {
      const c = w.shared.get("camera") as CameraShared | undefined;
      if (!c) return;
      const a = alpha < 0 ? 0 : alpha > 1 ? 1 : alpha;
      const lerp = (p: number, q: number): number => p + (q - p) * a;
      const sh = cam.userData.shakeOffset as { x: number; y: number; z: number } | undefined;
      const sx = sh?.x ?? 0, sy = sh?.y ?? 0, sz = sh?.z ?? 0;
      cam.position.set(lerp(c.prevPos[0], c.pos[0]) + sx, lerp(c.prevPos[1], c.pos[1]) + sy, lerp(c.prevPos[2], c.pos[2]) + sz);
      cam.lookAt(lerp(c.prevTarget[0], c.target[0]) + sx, lerp(c.prevTarget[1], c.target[1]) + sy, lerp(c.prevTarget[2], c.target[2]) + sz);
      const fov = lerp(c.prevFov, c.fov);
      if (cam.fov !== fov || cam.near !== c.near || cam.far !== c.far) {
        cam.fov = fov;
        cam.near = c.near;
        cam.far = c.far;
        cam.updateProjectionMatrix();
      }
    },
  };
}
