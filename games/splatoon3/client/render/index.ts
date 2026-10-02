// 담당: [render] — docs/impl/render.md 에 구현 상태·미확정을 기록한다.
import type { ClientContext, View } from "../context.ts";

export function createRenderView(_ctx: ClientContext): View {
  return { update() {} };
}
