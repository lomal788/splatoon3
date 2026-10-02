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
    createRangeSystem(), // 사격장 표적·구역(표적 이동은 플레이어보다 먼저: 추정)
    createCameraSystem(), // 입력 → 조준 yaw/pitch, 카메라 리그
    createPlayerSystem(), // 이동·점프·오징어·사격 입력 → 발사 요청
    createWeaponSystem(), // 발사 → 탄 생성, 탄 갱신(나이·이동·적분·충돌 콜백)
    createPaintSystem(), // 도색 요청 처리(큐 → 텍스처/격자), 집계
  ];
}
