// 시스템 등록·실행 순서. 순서 근거와 미확정은 DESIGN.md "프레임 순서" 절.
// 각 영역은 자기 index.ts 의 create*System 만 고친다. 이 파일은 조정자만 고친다.
import { createCameraSystem } from "./camera/index.ts";
import { createCollisionSystem } from "./collision/index.ts";
import { createPaintSystem } from "./paint/index.ts";
import { createPlayerSystem } from "./player/index.ts";
import { createRangeSystem } from "./range/index.ts";
import { createWeaponSystem } from "./weapon/index.ts";
import type { System } from "./world.ts";

export function createSystems(): System[] {
  return [
    createCollisionSystem(), // 지형 충돌 세계 구축(init), 동적 충돌체 갱신
    createRangeSystem(), // 사격장 표적·구역(표적 SplObj Before(2) 그룹이 플레이어 Default(3)보다 먼저 [판독] phive_controller.md §6.7)
    createPlayerSystem(), // 슬롯18 이동 → 몸체 물리 → 접촉 → write-back → 슬롯19. 이동은 직전 프레임 카메라를 씀
    createCameraSystem(), // 카메라 메인은 플레이어 슬롯19 안, 물리 뒤 [판독] phive_controller.md §6.7
    createWeaponSystem(), // 발사 → 탄 생성, 탄 갱신(나이·이동·적분·충돌 콜백)
    createPaintSystem(), // 도색 요청 처리(큐 → 텍스처/격자), 집계
  ];
}
