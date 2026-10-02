// 화면·소리 뷰 등록. 각 영역은 자기 index.ts 만 고친다. 이 파일은 조정자만 고친다.
import { createAudioView } from "./audio/index.ts";
import { createCameraView } from "./camera/index.ts";
import type { ClientContext, View } from "./context.ts";
import { createFxView } from "./fx/index.ts";
import { createPaintView } from "./paint/index.ts";
import { createRangeView } from "./range/index.ts";
import { createRenderView } from "./render/index.ts";

export function createViews(ctx: ClientContext): View[] {
  return [
    createRenderView(ctx), // 맵·캐릭터·무기 모델, 애니메이션, 팀 컬러
    createRangeView(ctx), // 표적 모델·피격 연출
    createPaintView(ctx), // 도색 텍스처 표시
    createFxView(ctx), // 탄·착탄·머즐 파티클 (core 이벤트 소비)
    createAudioView(ctx), // 효과음 (core 이벤트 소비)
    createCameraView(ctx), // core 카메라 → three 카메라 (마지막)
  ];
}
