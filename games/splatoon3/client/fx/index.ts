// 담당: [fx] — docs/impl/fx.md 에 구현 상태·미확정을 기록한다.
import type { ClientContext, View } from "../context.ts";

export function createFxView(_ctx: ClientContext): View {
  return { update() {} };
}
