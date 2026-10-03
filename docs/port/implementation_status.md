# 현재 소스와 원본 분석의 반영 차이 점검표

## 1. 기능 개요와 사용자에게 보이는 동작

Lby_Lobby00 1인 스플래시슈터 연습의 이동·물리·충돌·카메라·총·타격·표적·칠·그래픽·이펙트·소리를 구현 지시 단위로 정리한다. [port 요약의 A~I 묶음](README.md)으로 작업을 요청하면 된다. 새 원본 분석 결과를 만드는 문서가 아니라 **기존 분석과 현재 소스의 차이**를 기록한다.

## 2. 분석 대상 원본·버전·자료 위치

점검일 2026-10-03. C:/dev/splatoon3/web/games/splatoon3/core·client의 TS 87개를 목록화하고 실제 경로의 함수/호출자/데이터를 정적 판독했다. 87개 모두 실행·전수 판독했다는 뜻은 아니다. 근거는 최신 docs 본문과 r8/r9 정정, [analysis_completion.md](../analysis_completion.md), [r9 보고](../completion_r9_report.md)다. 원본 분석 분모 986와 구현 요약 분모는 별개다.

impl은 질문 목록으로만 읽고 상태는 실제 소스로 판정했다. 초기 점검은 port MD만 수정했다. 이후 카메라·그래픽·탄총 포팅으로 code/assets/impl과 이 표를 갱신했다. 원본·analysis 노트/inventory는 변경하지 않았다.

소스 보호 기준은 games/scripts/docs/impl/package.json의 파일 592개와 아래 SHA256 집계다. 상대 경로를 정렬하여 path UTF-8 byte와 각 파일 SHA256 raw digest를 이어 해시했다. 이번 시작/종료 사이 불변 검사이며 기존 변경의 작성자를 판정하는 값은 아니다.

```text
protected files: 592
SHA256: 81a91be8a8abe7991920c52a8a05406de99fcdff46faa9ce4d0365c7cef4ad4e
```

git rev-parse/status는 대상이 Git 저장소가 아니라 실패했으므로 commit SHA를 기준으로 사용하지 않는다.

## 3. 진입점과 전체 호출 흐름

현재 app fixed loop→World.step→collision/range/camera/player/weapon/paint→client Render/Range/Paint/FX/Audio/Camera 경로다. 이 웹 순서가 원본 전체 actor/physics scheduler와 같다는 뜻은 아니다(SYS02).

player→camera/weapon, weapon→DamageInfo→target→Damage/ELink/SLink, weapon→paint.request→발밑 잉크/시각 material을 연결해 확인했다. EventTap은 queue.clear 전에 frame별 이벤트를 보존한다.

## 4. 구조체·필드·상수·열거형 표

| 상태 | 정적 소스 판정 기준 | 반영률 점수 |
|---|---|---:|
| 반영 확인 | 항목에 명시한 한정 범위의 데이터/식/경로가 실제 소스에 있고 원본문서와 대응. 웹 원본 실행/화면 동등성은 별도 검증 필요 | 1 |
| 일부 반영 | 기반은 있으나 알려진 식·분기·필드·caller 연결 중 차이/누락이 남음 | 0 |
| 차이/미반영 | 명시한 기능이 원본과 다른 근사이거나 실제 producer/consumer가 빠짐 | 0 |
| 원본 미확정 | 전체를 원본대로 닫는 데 필요한 원본 근거가 남음. 모든 웹 차이를 원본 오류로 단정하지 않음 | 0 |

원본 근거의 [실행]/[판독]/[데이터]는 **링크한 기존 분석**의 수준이다. 이번에 Unicorn을 실행했다는 표시가 아니다. partial 실행/합성 fixture/미확정 writer의 경계를 유지한다.

반영률=반영 확인÷최초 고정 62개. 부분 점수/난이도 가중치/미확정 제외 없음. 작은 계산 함수가 반영 확인이어도 해당 영역 전체가 완료된 것은 아니다.

## 5. 상태 전이와 전체 수명

2026-10-03 잉크 표면 r7 반영 후 반영 확인13 / 일부37 / 차이·미반영9 / 원본 미확정3이다. 카메라/그래픽의 범위별 함수·웹 실행 검증은 아래와 impl 문서를 따르며 나머지는 정적 점검이다. 후속 구현에서 기존 ID의 근거·소스·검증 결과를 함께 갱신한다.

| 영역 | 반영 확인 | 일부 | 차이/미반영 | 원본 미확정 | 고정 항목 | 소스 반영률 |
|---|---:|---:|---:|---:|---:|---:|
| 물리 | 0 | 2 | 2 | 1 | 5 | 0/5 = 0.00% |
| 충돌 | 1 | 2 | 1 | 0 | 4 | 1/4 = 25.00% |
| 이동 | 1 | 3 | 1 | 0 | 5 | 1/5 = 20.00% |
| 카메라 | 2 | 5 | 0 | 0 | 7 | 2/7 = 28.57% |
| 탄·총 | 3 | 3 | 0 | 0 | 6 | 3/6 = 50.00% |
| 피격·판정 | 1 | 3 | 0 | 0 | 4 | 1/4 = 25.00% |
| 표적 | 2 | 2 | 0 | 0 | 4 | 2/4 = 50.00% |
| 도색 | 1 | 4 | 1 | 0 | 6 | 1/6 = 16.67% |
| 그래픽 | 0 | 7 | 2 | 1 | 10 | 0/10 = 0.00% |
| 이펙트 | 0 | 3 | 1 | 0 | 4 | 0/4 = 0.00% |
| 효과음 | 1 | 3 | 1 | 0 | 5 | 1/5 = 20.00% |
| 공통 | 1 | 0 | 0 | 1 | 2 | 1/2 = 50.00% |
| **전체** | 13 | 37 | 9 | 3 | **62** | **13/62 = 20.97%** |

## 6. 계산식·조건·상세 의사코드

요약 적용 지시이며 수식 전문은 근거 MD를 따른다. 소스 링크 라벨의 숫자는 점검일의 1-based 행이다. P0는 핵심 체감, P1은 이후 인게임 수명/표현, P2는 성능·후속이다.

### 물리

| ID | 우선 | 현재 상태 | 항목 | 현재 차이 → 반영할 것 | 실제 소스 | 원본 근거·수준 |
|---|---|---|---|---|---|---|
| PHY01 | P0 | 일부 반영 | 플레이어 캡슐·몸체 pose | 인간 기본 반경·끝점 상수는 있음. Y 오프셋은 radius로 고정하고 인간/오징어/잠복 형상·pose 갱신 계약 전체가 연결되지 않음. 원본 변환·COM와 게임 위치를 분리할 것. | [core/player/body.ts:10](../../games/splatoon3/core/player/body.ts)<br>[core/player/body.ts:43](../../games/splatoon3/core/player/body.ts) | [physics/character_controller.md §3.1~3.3.1](../physics/character_controller.md)<br>[physics/phive_controller.md §6.10.5](../physics/phive_controller.md)<br>[판독+실행+데이터] |
| PHY02 | P0 | 차이/미반영 | 침투 target·순차 normal impulse | 4회 overlap push와 4회 slide로 접촉을 해소함. 확정된 old/carry/depth 분기·압축 inverse mass·접촉 행 순차 갱신과 sub8/micro1을 구현할 것. 단순히 반복 숫자만 8로 바꾸면 안 됨. | [core/player/body.ts:66](../../games/splatoon3/core/player/body.ts)<br>[core/player/body.ts:95](../../games/splatoon3/core/player/body.ts) | [physics/phive_controller.md §6.10.4](../physics/phive_controller.md)<br>[판독+실행] |
| PHY03 | P0 | 차이/미반영 | carry·최종 속도·COM 적분 | game displacement에 충돌 보정을 바로 더함. native current/baseline, 7 carry/1 finalize, 저장 속도와 위치용 속도를 분리하고 f32 곱 뒤 double COM 적분·body origin 잔차를 보존할 것. | [core/player/body.ts:95](../../games/splatoon3/core/player/body.ts)<br>[core/player/index.ts:234](../../games/splatoon3/core/player/index.ts) | [physics/phive_controller.md §6.10.5](../physics/phive_controller.md)<br>[판독+실행] |
| PHY04 | P0 | 일부 반영 | 접지·계단·경사·착지 후보 선택 | 접지 probe가 horiz×1.1963+.02/공중 .001이고 첫 허용 normal을 채택하는 근사임. 원본 후보 분류·필터·최종 normal 생산과 player 접촉 후처리를 연결할 것. | [core/player/body.ts:127](../../games/splatoon3/core/player/body.ts)<br>[core/player/contact.ts:1](../../games/splatoon3/core/player/contact.ts) | [physics/character_controller.md §5~7](../physics/character_controller.md)<br>[판독+실행(부분)] |
| PHY05 | 보류 | 원본 미확정 | 실제 Lby 메시의 전체 TOI·접촉 생성 | 웹은 custom TriMesh sweep 사용. 원본 scalar/primitive/solver 일부는 확정됐지만 실제 Lby 전체 native query·codec·manifold까지 동등성은 미확정. 확정된 부분만 이식하고 전체 Havok 재현 완료로 표시하지 말 것. | [core/collision/mesh.ts:1](../../games/splatoon3/core/collision/mesh.ts)<br>[core/collision/world.ts:125](../../games/splatoon3/core/collision/world.ts) | [physics/phive_controller.md §6.10~6.10.5·§11](../physics/phive_controller.md)<br>[physics/character_controller.md §11](../physics/character_controller.md)<br>[미확정(whole)] |

### 충돌

| ID | 우선 | 현재 상태 | 항목 | 현재 차이 → 반영할 것 | 실제 소스 | 원본 근거·수준 |
|---|---|---|---|---|---|---|
| COL01 | 유지 | 반영 확인 | 변환 지형 메시·재질 데이터 읽기 | collision bundle의 positions/indices/material과 원본 filterRaw 하위·상위 32bit를 읽는 경로가 있음. 데이터 입력 경로만 반영 확인이며 전체 query/primitive 정합을 포함하지 않음. | [core/collision/world.ts:273](../../games/splatoon3/core/collision/world.ts)<br>[core/collision/world.ts:392](../../games/splatoon3/core/collision/world.ts) | [gimmick/collision_mesh.md §3.3~3.4](../gimmick/collision_mesh.md)<br>[데이터+판독] |
| COL02 | P0 | 일부 반영 | 양방향 layer/subLayer·shape/tag 필터 | bodyFilter는 상대 hitMask/subMask의 내 layer bit만 검사하고 query는 web Layer로 단순화함. 양쪽 허용식·하위층·비교 그룹·typed shape/tag 조건과 잠복 subLayer 전환을 공통 계약으로 만들 것. | [core/collision/world.ts:68](../../games/splatoon3/core/collision/world.ts)<br>[core/collision/filter.ts:1](../../games/splatoon3/core/collision/filter.ts) | [physics/character_controller.md §3.5~3.6](../physics/character_controller.md)<br>[camera/r9_boom_query.md §6.1](../camera/r9_boom_query.md)<br>[판독+실행+데이터] |
| COL03 | P0 | 차이/미반영 | 플레이어 ↔ 표적 Main 동적 충돌 | range는 Main capsule을 Layer.KeepOut으로 등록하지만 sweepBody/overlapBody는 mesh만 사용함. 플레이어 질의에도 Main을 포함하고 원본 pair 조건·kinematic 상대속도를 전달할 것. | [core/collision/world.ts:124](../../games/splatoon3/core/collision/world.ts)<br>[core/range/index.ts:223](../../games/splatoon3/core/range/index.ts) | [range/shooting_range.md §4.3·§9.3](../range/shooting_range.md)<br>[physics/phive_controller.md §6.10.4](../physics/phive_controller.md)<br>[판독+실행+데이터] |
| COL04 | P0 | 일부 반영 | 탄·카메라 sphere/capsule 질의 계약 | 원시 형상의 일부를 12분할/4링 메시로 바꾸고 custom sweep으로 처리함. 확정된 sphere/capsule 결과·t/point/normal 방향과 query filter를 소비자별로 보존할 것. 미확정 native TOI 전체는 PHY05에 남김. | [core/collision/world.ts:1](../../games/splatoon3/core/collision/world.ts)<br>[core/collision/geom.ts:1](../../games/splatoon3/core/collision/geom.ts) | [physics/sphere_quad_toi.md §6](../physics/sphere_quad_toi.md)<br>[camera/r9_boom_query.md §6.1](../camera/r9_boom_query.md)<br>[판독+실행(부분)] |

### 이동

| ID | 우선 | 현재 상태 | 항목 | 현재 차이 → 반영할 것 | 실제 소스 | 원본 근거·수준 |
|---|---|---|---|---|---|---|
| MOV01 | P0 | 일부 반영 | 일반 이동·가속·사격 이동 속도 | updateMove는 원본식과 f32 연산을 상당 부분 사용함. slerpDir은 Math.sin/acos 근사이고 aimFold를 shooting으로 대신함. 확정된 공급자·sead 수학과 나머지 경로를 구분하여 보완할 것. | [core/player/move.ts:10](../../games/splatoon3/core/player/move.ts)<br>[core/player/move.ts:164](../../games/splatoon3/core/player/move.ts) | [player/movement_physics.md §6.1~6.5](../player/movement_physics.md)<br>[판독+실행(부분)] |
| MOV02 | 유지 | 반영 확인 | 보통 점프·수직 감쇠·중력 계산 | verticalUpdate의 jump3d/vy 분리·공중 카운터 조건과 보통 jumpSpeed/tryJump 식이 존재하고 연산별 f32를 사용함. 특수 상태·물리 결과 생산자·벽 전체 동작의 완료 판정은 제외함. | [core/player/vertical.ts:15](../../games/splatoon3/core/player/vertical.ts)<br>[core/player/vertical.ts:44](../../games/splatoon3/core/player/vertical.ts) | [player/movement_physics.md §6.4·§6.7](../player/movement_physics.md)<br>[physics/phive_controller.md §4.2](../physics/phive_controller.md)<br>[판독+실행] |
| MOV03 | P1 | 차이/미반영 | 오징어 목표 속도 k | targetSpeed가 k=1로 고정하고 아직 미판독이라 주석 처리함. 266c6e4의 인자 bit0 우선·능력104 bit4일 때 .9 식은 이미 확정됨. 현재 기본 장비에서 1인 경우와 적용 대상 장비를 구분할 것. | [core/player/move.ts:114](../../games/splatoon3/core/player/move.ts) | [player/movement_physics.md §6.1.1](../player/movement_physics.md)<br>[판독+실행] |
| MOV04 | P0 | 일부 반영 | 발밑 잉크 분류·이전 결과 재사용 | stepPaint는 own/enemy 보간식을 갖지만 매번 새 sample을 읽고 재사용=false/texels=0으로 둠. 원본 재사용 조건·owner/mode 및 sample 결과를 연결할 것. GroundPaintMonitorRadius 미확정 값은 .6을 확정값으로 승격하지 말 것. | [core/player/contact.ts:1](../../games/splatoon3/core/player/contact.ts)<br>[core/player/index.ts:250](../../games/splatoon3/core/player/index.ts) | [player/player_state.md §8·§11](../player/player_state.md)<br>[paint/paint_and_score.md §6.3](../paint/paint_and_score.md)<br>[판독+실행(부분)] |
| MOV05 | P0 | 일부 반영 | 벽 타기·벽 점프·상태 전이 | 벽 normal/벽 잉크 확인·wallKick 함수는 있으나 접촉 분류와 애니 종료값이 근사 입력에 의존함. PHY04/PT05/GR02의 실제 출력을 연결하고 본체 상태 writer와 대조할 것. | [core/player/index.ts:250](../../games/splatoon3/core/player/index.ts)<br>[core/player/vertical.ts:56](../../games/splatoon3/core/player/vertical.ts)<br>[core/player/contact.ts:1](../../games/splatoon3/core/player/contact.ts) | [player/player_state.md §6](../player/player_state.md)<br>[player/movement_physics.md §6.8](../player/movement_physics.md)<br>[판독+실행(부분)] |

### 카메라

| ID | 우선 | 현재 상태 | 항목 | 현재 차이 → 반영할 것 | 실제 소스 | 원본 근거·수준 |
|---|---|---|---|---|---|---|
| CAM01 | 유지 | 반영 확인 | mode0 기본 사람/오징어 리그 곡선 | 기본 테이블 범위 유지. 이번에는 곡선 f32 덧셈 순서·sead 사인/코사인 표·정확한 SQ 제어점을 적용했다. 원본 128경우의 리그 값과 pose 비트 일치. mode1/특수 리그/장면 선택은 이 행 범위에 넣지 않음. | [core/camera/rig.ts:1](../../games/splatoon3/core/camera/rig.ts) | [camera/player_camera.md §6.1~6.2](../camera/player_camera.md)<br>[판독+데이터+실행(표본)] |
| CAM02 | 유지 | 반영 확인 | 최종 카메라 기저·이동 방향·법선 추종 | 원본 X/Y/Z 및 세 열 동시 보존, right/viewForward 공유, 이동·탄·렌더 기저 소비, 1252ff0 null 축 방향 slerp를 연결했다. 기저260·법선131 원본 표본 비트 일치. 렌더 alpha와 three 쿼터니언 보간은 웹 선택으로 유지. | [core/camera/native_math.ts:1](../../games/splatoon3/core/camera/native_math.ts)<br>[core/player/index.ts:1](../../games/splatoon3/core/player/index.ts)<br>[core/weapon/actors.ts:1](../../games/splatoon3/core/weapon/actors.ts)<br>[client/camera/index.ts:1](../../games/splatoon3/client/camera/index.ts) | [camera/player_camera.md §6.7](../camera/player_camera.md)<br>[player/movement_physics.md §6.1](../player/movement_physics.md)<br>[판독+실행] |
| CAM03 | P0 | 일부 반영 | 붐 반경·활성 query filter·적중 법선 | 반경 .3, 명시적 layer7/mask8/sub0, 상대 재질의 camera/sub0 허용, native entry bit0 법선 부호를 반영했다. camera-only 장벽도 유지한다. 실제 body LP의 양방향 Default/Same/Other 표·typed 태그·skip 목록과 whole native mesh query는 아직 미반영. | [core/camera/camera.ts:1](../../games/splatoon3/core/camera/camera.ts)<br>[core/collision/world.ts:1](../../games/splatoon3/core/collision/world.ts) | [camera/r9_boom_query.md §3.1·§6.1](../camera/r9_boom_query.md)<br>[판독+실행] |
| CAM04 | P0 | 일부 반영 | 붐 두 질의·충돌 오프셋 spring·출력 혼합 | 두 질의/C14ec/시작점, 복귀·축소 하한, C144 소비/피벗/최소거리, C1760 ratio·pose 혼합, Bde0 이전 위치 보존 게이트를 반영했다. 해당 원본 블록 표본은 비트 일치. 실제 D/B210/e0c/상태 weight 생산자는 player가 공급하지 않아 native 소비 입력 기본0이 남는다. B1f8 unexplained를 B210으로 대입하지 않았다. | [core/camera/camera.ts:1](../../games/splatoon3/core/camera/camera.ts)<br>[core/camera/boom.ts:1](../../games/splatoon3/core/camera/boom.ts) | [camera/player_camera.md §6.8·§6.11](../camera/player_camera.md)<br>[camera/r9_collision_spring.md §6](../camera/r9_collision_spring.md)<br>[camera/r9_boom_query.md §6](../camera/r9_boom_query.md)<br>[판독+실행] |
| CAM05 | P0 | 일부 반영 | 점프·낙하 수직 추종·formHeight | 보통 수직 추종을 f32로 옮기고 점프 분모를 원본 0x3deb851e로 정정했다. player.final과 moveVel을 분리해 카메라에 전달했다. formHeight/Bcf0는 아직 player 실제 공급이 없고 특수 상태 목표/게이트 연결도 남는다. | [core/camera/camera.ts:1](../../games/splatoon3/core/camera/camera.ts)<br>[core/camera/index.ts:1](../../games/splatoon3/core/camera/index.ts) | [camera/player_camera.md §6.6·§7.7](../camera/player_camera.md)<br>[camera/r9_state_sources.md §6](../camera/r9_state_sources.md)<br>[판독+실행(부분)] |
| CAM06 | P1 | 일부 반영 | 생성·리스폰 reset·상태 리그 선택 | 보통 reset과 G143d0=0의 LobbyVersus 리그는 유지했다. 이번에 spring/전진 계수 초기화를 추가했지만 First/Warp/Recorder·모듈 quaternion·실제 상태 리그 공급은 기존 후속 항목이다. 마우스는 PC 이식 선택. | [core/camera/index.ts:1](../../games/splatoon3/core/camera/index.ts) | [camera/r9_lifecycle.md §6](../camera/r9_lifecycle.md)<br>[camera/r9_reset_contexts.md §6](../camera/r9_reset_contexts.md)<br>[camera/r9_state_sources.md §6](../camera/r9_state_sources.md)<br>[판독+실행(부분)] |
| CAM07 | P1 | 일부 반영 | ELink 쉐이크 시작·수명·포즈 출력 | 실제 ELink CameraRumbleName/Frame, 원본 10종 곡선/Axis/Scale 및 15/25 거리식으로 producer를 연결하고 월드 위치만 이동한다. 빈 이름에 임의 발사 shake 없음. 비루프 종료는 MaxX 웹 정책이며 listener+1c8·owner generation/follow·ELink 전체 수명/Delay는 아직 미검증. | [core/camera/shake.ts:1](../../games/splatoon3/core/camera/shake.ts)<br>[client/fx/index.ts:1](../../games/splatoon3/client/fx/index.ts)<br>[client/camera/index.ts:1](../../games/splatoon3/client/camera/index.ts) | [camera/shake_rumble.md §3.2~3.2c](../camera/shake_rumble.md)<br>[판독+데이터(부분)] |

### 탄·총

| ID | 우선 | 현재 상태 | 항목 | 현재 차이 → 반영할 것 | 실제 소스 | 원본 근거·수준 |
|---|---|---|---|---|---|---|
| BUL01 | 유지 | 반영 확인 | 탄 생성·age·pre/physics/post 단계 | 프레임 시작 활성 목록·pre/physics/contact→player19 group3 사격→기존 bullet19/21 group4를 연결했다. 새 메인/분열 탄·방울은 생성 프레임 갱신 제외, age=-1→다음 pre0. 통합 fixture 검증. 전체 actor scheduler는 SYS02에 남는다. | [core/weapon/bullet.ts:1](../../games/splatoon3/core/weapon/bullet.ts)<br>[core/weapon/runtime.ts:1](../../games/splatoon3/core/weapon/runtime.ts)<br>[core/weapon/body.ts:1](../../games/splatoon3/core/weapon/body.ts) | [weapon/shooter_bullet.md §3.2~3.3·§5.3~5.4](../weapon/shooter_bullet.md)<br>[판독+실행(부분)] |
| BUL02 | 유지 | 반영 확인 | 탄 나이에 따른 데미지·두 반경 계산 | shooterDamage/radius의 원본 보간·정수화/상한 식이 분리 구현돼 있음. 계산 함수 반영 확인이며 실제 접촉·receiver·최종 HP를 포함하지 않음. | [core/weapon/damage.ts:1](../../games/splatoon3/core/weapon/damage.ts) | [combat/damage_hit.md §6](../combat/damage_hit.md)<br>[weapon/shooter_bullet.md §3.3.5](../weapon/shooter_bullet.md)<br>[판독+실행] |
| BUL03 | P0 | 일부 반영 | 연사·PreDelay·분산 RNG·조준 | native main 우선 입력/차단·s32 카운터와 abc/ab4 countdown, fresh Lobby seed(1,0,0,0)/합13 및 공유 조준 축을 반영했다. 연사6 확인. a90/4d4/원점/일부 reset·GameFrame 공급은 남는다. | [core/weapon/shooter.ts:1](../../games/splatoon3/core/weapon/shooter.ts)<br>[core/weapon/runtime.ts:377](../../games/splatoon3/core/weapon/runtime.ts) | [camera/aim_swerve.md §6.1~6.4](../camera/aim_swerve.md)<br>[weapon/shooter_bullet.md §3.5~3.5.1](../weapon/shooter_bullet.md)<br>[판독+실행] |
| BUL04 | P0 | 일부 반영 | 발사원점·스플래시·벽 낙하 접촉 | 초기 t=0 sphere overlap·벽 자식 접촉점 재질의 구 질의·WallDrop .2 sphere 접촉 및 칠 불가 거름, 분열 탄 WallDrop 표 연결을 반영했다. 원점·native 두 shape TOI/typed filter·후보순서/천장 flag는 남는다. | [core/weapon/shooter.ts:1](../../games/splatoon3/core/weapon/shooter.ts)<br>[core/weapon/runtime.ts:163](../../games/splatoon3/core/weapon/runtime.ts)<br>[core/weapon/runtime.ts:347](../../games/splatoon3/core/weapon/runtime.ts) | [weapon/shooter_bullet.md §3.3.6·§5.5](../weapon/shooter_bullet.md)<br>[paint/paint_and_score.md §3.0](../paint/paint_and_score.md)<br>[판독+실행] |
| BUL05 | 유지 | 반영 확인 | 슈터 잉크 소비 수치·허용 오차 | consumeInk의 잔량 허용 오차·1/600 경계와 원본 소비 수치가 구현돼 있음. 이 항목은 소비 수치 판정만이며 세 회복 정지 카운터의 수명은 BUL06임. | [core/weapon/shooter.ts:1](../../games/splatoon3/core/weapon/shooter.ts) | [weapon/shooter_bullet.md §5.5](../weapon/shooter_bullet.md)<br>[판독+실행] |
| BUL06 | P0 | 일부 반영 | 잉크 회복·소비 시 정지 카운터 | 세 정지 카운터·음수 진행·이전 max 판단·B6b4/6b8/6bc·600/180 선택을 연결했다. 원본 실행 fixture와 웹 경계 확인. 실제 B7a0 지연 writer/상위 회복 게이트/gear 소비자 전체는 남는다. | [core/player/index.ts:264](../../games/splatoon3/core/player/index.ts)<br>[core/weapon/runtime.ts:397](../../games/splatoon3/core/weapon/runtime.ts) | [weapon/shooter_bullet.md §5.5](../weapon/shooter_bullet.md)<br>[판독+실행] |

### 피격·판정

| ID | 우선 | 현재 상태 | 항목 | 현재 차이 → 반영할 것 | 실제 소스 | 원본 근거·수준 |
|---|---|---|---|---|---|---|
| HIT01 | 유지 | 반영 확인 | receiver 배율 적용 위치·HP 전달 | 송신자 선배율을 제거하고 raw damage→target receiver 한 번 배율→HP를 연결했다. 실제 gun+range rate .344에서 raw360→123/HP877 확인. 다른 receiver 모드/히트 표시 범위는 HIT02~04 별도. | [core/weapon/runtime.ts:194](../../games/splatoon3/core/weapon/runtime.ts)<br>[core/range/target.ts:280](../../games/splatoon3/core/range/target.ts) | [combat/damage_hit.md §6.4](../combat/damage_hit.md)<br>[range/shooting_range.md §6.1](../range/shooting_range.md)<br>[판독+실행] |
| HIT02 | P1 | 일부 반영 | critical ring·히트 종류 | critical은 항상 false. 원본 ring 수명/ID/count와 HitEffect 선택 계약의 확정 부분을 전달할 것. 스플래시슈터 ordinary/critical 모두 Shooter 행인 사실을 유지하고 임의 headshot 데미지 배율을 추가하지 말 것. | [core/weapon/runtime.ts:202](../../games/splatoon3/core/weapon/runtime.ts) | [combat/critical_ring_lifecycle.md §6](../combat/critical_ring_lifecycle.md)<br>[combat/damage_hit.md §6](../combat/damage_hit.md)<br>[판독+실행(부분)+데이터] |
| HIT03 | P0 | 일부 반영 | 결과 enum·착탄 효과/소리 정보 전달 | target.computeResult는 일부 team/extra/rate 경로만 구현함. 실제 sender가 사용하는 확정 경로부터 결과·HitEffect row·충돌 분류를 FX/SFX에 전달할 것. 미확정 sender 모드/이력을 모두 활성화하지 말 것. | [core/range/target.ts:292](../../games/splatoon3/core/range/target.ts)<br>[core/weapon/runtime.ts:200](../../games/splatoon3/core/weapon/runtime.ts) | [combat/damage_hit.md §6.4](../combat/damage_hit.md)<br>[combat/hit_effect_pipeline.md §6](../combat/hit_effect_pipeline.md)<br>[판독+실행(부분)] |
| HIT04 | P1 | 일부 반영 | 낙하·물·사망/복귀 수명 | 현재 fellOut이면 즉시 respawn 경로임. 원본 로컬 사망 상태·시간·카메라/모델 전환의 확정 부분을 붙일 것. 적 잉크 HP·무적 계산은 1인 기본 환경에서 사용 경로 확인 후 적용하며 네트워크/다른 모드는 제외함. | [core/player/index.ts:270](../../games/splatoon3/core/player/index.ts) | [combat/player_life.md §6.8·§6.11](../combat/player_life.md)<br>[판독+실행(부분)] |

### 표적

| ID | 우선 | 현재 상태 | 항목 | 현재 차이 → 반영할 것 | 실제 소스 | 원본 근거·수준 |
|---|---|---|---|---|---|---|
| TGT01 | 유지 | 반영 확인 | 원본 배치·파라미터·Main/ColBullet 크기 입력 | Lby actor/rail 배치·원본 Sighter param과 두 capsule 크기를 읽어 초기화하는 경로가 있음. 데이터 연결만 확인하며 실제 player collision은 COL03, 상태별 크기/pose 검증은 TGT02임. | [core/range/index.ts:125](../../games/splatoon3/core/range/index.ts)<br>[core/range/index.ts:222](../../games/splatoon3/core/range/index.ts) | [range/shooting_range.md §4.1~4.3](../range/shooting_range.md)<br>[데이터+판독] |
| TGT02 | P1 | 일부 반영 | HP·6상태·파괴/복귀·몸체 활성 | Wait/DamageShot/Burst/BurstWait/Expand/Flick와 복귀식은 있음. 최신 HP0 helper/event, 재피격 재방출 및 애니 종료/몸체 활성 시점을 원본과 대조하고 static target의 cached collision pose를 확인할 것. | [core/range/target.ts:103](../../games/splatoon3/core/range/target.ts)<br>[core/range/target.ts:149](../../games/splatoon3/core/range/target.ts)<br>[core/range/target.ts:237](../../games/splatoon3/core/range/target.ts)<br>[core/range/index.ts:221](../../games/splatoon3/core/range/index.ts) | [range/shooting_range.md §5·§6.2·§7.1](../range/shooting_range.md)<br>[combat/player_life.md §3.6.1](../combat/player_life.md)<br>[판독+실행+데이터] |
| TGT03 | 유지 | 반영 확인 | 명중 휨 충격의 실제 연결 | damage와 별도 물리 접촉 callback으로 body center·접촉 전 stepVelSec·y=0·BulletImpulsScaler를 전달했다. 실제 gun+range 휨과 Through 무손상 물리 접촉 검증. target 전체 애니/재질 표현은 별도. | [core/range/index.ts:188](../../games/splatoon3/core/range/index.ts)<br>[core/weapon/runtime.ts:200](../../games/splatoon3/core/weapon/runtime.ts) | [range/shooting_range.md §6.3·§11](../range/shooting_range.md)<br>[실행+판독(수치),미확정(일부 공급)] |
| TGT04 | P1 | 일부 반영 | 이동 표적 레일·회전·충돌 동기화 | 배치 rail과 curve/속도 갱신은 있음. 원본 parametric 상태·회전 writer·매 프레임 Main/ColBullet pose 갱신을 연결해 방향 전환/피격 중 움직임을 검증할 것. | [core/range/rail.ts:1](../../games/splatoon3/core/range/rail.ts)<br>[core/range/index.ts:229](../../games/splatoon3/core/range/index.ts) | [range/shooting_range.md §6.5·§11](../range/shooting_range.md)<br>[데이터+판독(부분)] |

### 도색

| ID | 우선 | 현재 상태 | 항목 | 현재 차이 → 반영할 것 | 실제 소스 | 원본 근거·수준 |
|---|---|---|---|---|---|---|
| PNT01 | 유지 | 반영 확인 | InkTexInfo·원본 R8 스탬프 로드 | common에 InkTexInfo 50행·R8 stamp 52개가 있으며 StampLibrary 원본 데이터 경로를 사용함. 이번 검사에서 52개 모두 w×h와 decode byte 수 일치. analytic fallback·pattern 선택 정합은 PNT03에 남김. | [core/paint/index.ts:1](../../games/splatoon3/core/paint/index.ts)<br>[core/paint/inktex.ts:128](../../games/splatoon3/core/paint/inktex.ts) | [paint/paint_and_score.md §3.4](../paint/paint_and_score.md)<br>[paint/ink_texture_loader.md §6](../paint/ink_texture_loader.md)<br>[데이터+판독] |
| PNT02 | P0 | 차이/미반영 | ColPaint panel·basis·atlas 구성 | custom plane chart/page packing을 사용함. 원본 prism/slab/panel basis·패턴/그룹·연결·3200 limit의 확정 부분을 적용할 것. 전체 allocator/raster 최종 미확정을 확정된 것으로 확대하지 말 것. | [core/paint/surface.ts:1](../../games/splatoon3/core/paint/surface.ts) | [paint/colpaint_atlas.md §3~6](../paint/colpaint_atlas.md)<br>[paint/panel_groups.md §6](../paint/panel_groups.md)<br>[paint/panel_connections.md §6](../paint/panel_connections.md)<br>[판독+실행+데이터(부분)] |
| PNT03 | P0 | 일부 반영 | 칠 크기·방향·seed 좌표계 | 탄→paint.request, 폭/깊이/지연 및 RNG helper는 있음. paintSeed 호출은 world pos에 의존하며 원본 target-space 변환·pattern/center offset·Floor/Col/Obj 순서와 묶어 대조할 것. | [core/paint/inktex.ts:1](../../games/splatoon3/core/paint/inktex.ts)<br>[core/paint/paintworld.ts:1](../../games/splatoon3/core/paint/paintworld.ts)<br>[core/weapon/runtime.ts:367](../../games/splatoon3/core/weapon/runtime.ts) | [paint/paint_shape.md §4~7](../paint/paint_shape.md)<br>[paint/colpaint_atlas.md §7.1](../paint/colpaint_atlas.md)<br>[판독+실행(부분)] |
| PNT04 | P0 | 일부 반영 | 칠 가능 flag·면/접촉 후보 선택 | isPaintableMaterial는 태그명 blacklist 중심이고 chartsInSphere는 독자적인 후보/normal 조건 사용. 원본 raw 32/16B 재질 flag·typed contact 분류를 사용하고 원본 최대/정렬/조기 종료 조건을 보존할 것. | [core/paint/surface.ts:1](../../games/splatoon3/core/paint/surface.ts)<br>[core/paint/paintworld.ts:1](../../games/splatoon3/core/paint/paintworld.ts) | [paint/paint_and_score.md §3.3](../paint/paint_and_score.md)<br>[paint/paint_shape.md §7.1~7.2](../paint/paint_shape.md)<br>[gimmick/collision_mesh.md §3.4.3](../gimmick/collision_mesh.md)<br>[판독+실행+데이터] |
| PNT05 | P0 | 일부 반영 | owner/mode·stencil·alpha·잉크 sample | OWN mode4/5/6과 alpha 처리·sample은 있음. 원본 패스/조건·raster 경계·texel count를 접촉 결과와 함께 대조하고, 발밑 판정 MOV04와 같은 데이터를 사용하도록 연결할 것. 미확정 GPU 전체 경계는 표시할 것. | [core/paint/paintworld.ts:1](../../games/splatoon3/core/paint/paintworld.ts) | [paint/paint_and_score.md §3.5·§6.3](../paint/paint_and_score.md)<br>[판독+실행(부분)] |
| PNT06 | P0 | 일부 반영 | 화면에 보이는 잉크·모델 ColPaint UV | 2026-10-03 r7에서 띄운 collision overlay를 제거하고 실제 visual triangle draw에 packed UV/switch/tangent·InkBright/rim/normal/thickness/.05/.015·공통 조명을 연결했다. bake UV1/변환 보존, 실제 Lby4단계·GPU오류0. 현재 chart/page와 seam/환경 BRDF·live 공급은 web adapter여서 원본 전체는 남는다. [현재 검증·잔여](ink_surface_r7.md). | [client/paint/index.ts](../../games/splatoon3/client/paint/index.ts)<br>[client/paint/visual_geometry.ts](../../games/splatoon3/client/paint/visual_geometry.ts)<br>[client/render/ink_surface.ts](../../games/splatoon3/client/render/ink_surface.ts) | [paint/model_panel_mapping.md §6](../paint/model_panel_mapping.md)<br>[graphics/ink_visual_geometry_r7.md](../graphics/ink_visual_geometry_r7.md)<br>[graphics/ink_surface_web_r7.md](../graphics/ink_surface_web_r7.md)<br>[판독+실행(기재범위)+데이터] |

### 그래픽

| ID | 우선 | 현재 상태 | 항목 | 현재 차이 → 반영할 것 | 실제 소스 | 원본 근거·수준 |
|---|---|---|---|---|---|---|
| GR01 | P0 | 일부 반영 | 몸·장비·무기 조립·_Hlf 표시 | r8 B7a0 지연 표시·_Hlf 복귀와 r9 실제 Weapon_R→Root→Muzzle pose 공급을 연결했다. 접지/벽/상승 공중 producer·기어 가림/전체 pose는 남음. [r9 현재 검증](graphics_priority_r9.md). | [client/render/player.ts](../../games/splatoon3/client/render/player.ts)<br>[client/render/model.ts](../../games/splatoon3/client/render/model.ts) | [graphics/player_assembly.md §6](../graphics/player_assembly.md)<br>[graphics/part_suffix_runtime.md §6](../graphics/part_suffix_runtime.md)<br>[graphics/calc_thickness_runtime.md §6](../graphics/calc_thickness_runtime.md)<br>[판독+실행+데이터(부분)] |
| GR02 | P0 | 일부 반영 | ASB·blackboard·애니 속도·끝 프레임 | r9 raw FMAA reader·type11 전용 metadata·full-weight 눈 패턴/SRT 공급을 연결했다. weighted type11/몸CP·현재skin idx/type18·binder reset·첫 tick/event/holder 전체 수명은 남음. [r9 현재 검증](graphics_priority_r9.md). | [core/player/index.ts:255](../../games/splatoon3/core/player/index.ts)<br>[client/render/anim/animator.ts:49](../../games/splatoon3/client/render/anim/animator.ts)<br>[client/render/player.ts:65](../../games/splatoon3/client/render/player.ts)<br>[client/render/anim/asb.ts:1](../../games/splatoon3/client/render/anim/asb.ts) | [player/player_state.md §6.1.3](../player/player_state.md)<br>[graphics/anim_state_machine.md §4·§11.8~11.11](../graphics/anim_state_machine.md)<br>[graphics/asb_typed_tags.md §6](../graphics/asb_typed_tags.md)<br>[graphics/animation_weapon_blackboard.md §6](../graphics/animation_weapon_blackboard.md)<br>[판독+실행+데이터] |
| GR03 | P0 | 일부 반영 | 캐릭터 재질·팀색·셰이더 | r8 피부/머리/오징어에 이어 r9 탱크·하네스·병 film 분기, owner texture3개와 calc22 발광을 연결했다. 실제 Maya0/rotation0 UV6lane도 적용. live CP/skin·다른 SRT mode/rotation·native cube/BRDF/SPP/전체GPU는 남음. [r9 상세](graphics_priority_r9.md). | [client/render/hoian.ts](../../games/splatoon3/client/render/hoian.ts)<br>[client/render/forward.ts](../../games/splatoon3/client/render/forward.ts)<br>[client/render/teamcolor.ts](../../games/splatoon3/client/render/teamcolor.ts) | [graphics/shaders.md §3](../graphics/shaders.md)<br>[graphics/shader_uv_selection.md §6](../graphics/shader_uv_selection.md)<br>[graphics/light_rig_runtime.md §6](../graphics/light_rig_runtime.md)<br>[graphics/team_color.md §5](../graphics/team_color.md)<br>[판독+실행(부분)+데이터] |
| GR04 | P0 | 일부 반영 | 스테이지 베이크 조명·AO/그림자 재질 | 원본75mesh bake/AO/light 유지. 2026-10-03 common_render_r5에서 AO·bake+dynamic+projection 가산 occlusion과2shadow supply를 연결했다. r6에서 동적SPP/fade 계산을 연결했다. r7 actual visual/bakeUV1과 잉크 조명을 연결했다. native whole ColPaint/vertex·hemiFix·static/fullSPP는 남음. | [client/render/bake.ts](../../games/splatoon3/client/render/bake.ts)<br>[client/render/forward.ts](../../games/splatoon3/client/render/forward.ts)<br>[client/render/map.ts](../../games/splatoon3/client/render/map.ts) | [graphics/stage_rendering.md §5~6](../graphics/stage_rendering.md)<br>[graphics/bake_material_binding.md §6](../graphics/bake_material_binding.md)<br>[판독+실행(부분)+데이터] <br>[공통경로 현재구현](common_render_r5.md) |
| GR05 | P0 | 일부 반영 | 방향광·하늘·SH·환경맵 | r8에 MainLight A×Intensity=10 및 실제 spot RGBA.w×강도를 캐릭터 역광에 연결했다. 기존 capture2/SH/sky 유지. cube12/Illuminate/BRDF/live capture/actor 경계는 남음. [r8 현재 검증](character_graphics_r8.md). | [client/render/lighting.ts](../../games/splatoon3/client/render/lighting.ts)<br>[client/render/dynamic_lights.ts](../../games/splatoon3/client/render/dynamic_lights.ts)<br>[client/render/sky.ts](../../games/splatoon3/client/render/sky.ts) | [graphics/common_lighting_r6.md](../graphics/common_lighting_r6.md)<br>[graphics/stage_rendering.md §4·§5.4~5.7](../graphics/stage_rendering.md)<br>[판독+실행(부분)+데이터] <br>[공통경로 현재구현](common_render_r6.md) |
| GR06 | P0 | 일부 반영 | 동적 그림자·투영 그림자 | 2×1024 depth·stage/player/paint receiver·Density0 유지. r6에서 기본1tap 및native1/4/9/16커널·strict20 경계·SPP/farFade/PCFWidth CPU식 및Default fade40~60을 연결했다. native projection/compare sampler·live overrides·caster등록·range표적shadowflag는 남음. | [client/render/shadows.ts](../../games/splatoon3/client/render/shadows.ts)<br>[client/render/forward.ts](../../games/splatoon3/client/render/forward.ts)<br>[client/render/index.ts](../../games/splatoon3/client/render/index.ts) | [graphics/common_shadow_r6.md](../graphics/common_shadow_r6.md)<br>[graphics/projected_shadow_runtime.md §6](../graphics/projected_shadow_runtime.md)<br>[판독+실행+데이터(부분)] <br>[공통경로 현재구현](common_render_r6.md) |
| GR07 | P0 | 일부 반영 | HDRCompose·톤매핑·팀색 산술 | linearhalf HDR에서native Bloom mask/reduce/Gaussian/역합성→HDR×EV2+Bloom→Tone4→원본8³LUT→선택gamma 연결. DefaultDay old_calc=false 및CPUpacket/합성계수·native blend값 검증. LUTrounding/sampler·Bloom live gates/깊이변형·DOF master enable·gamma/팀색행은 남음. | [client/render/post.ts](../../games/splatoon3/client/render/post.ts)<br>[client/render/bloom.ts](../../games/splatoon3/client/render/bloom.ts)<br>[client/render/teamcolor.ts](../../games/splatoon3/client/render/teamcolor.ts) | [graphics/common_post_r6.md](../graphics/common_post_r6.md)<br>[graphics/stage_rendering.md §3.1~3.4](../graphics/stage_rendering.md)<br>[판독+실행(부분)+데이터] <br>[공통경로 현재구현](common_render_r6.md) |
| GR08 | P1 | 차이/미반영 | 머리카락·cloth 실행 경로 | 스켈레탈 클립으로 파츠를 움직이며 native cloth link/감쇠·constraint 경로가 없음. r9 확정 감쇠/effectiveDt·강성·link 식을 단계별로 붙일 것. 최초 frameInfo/실제 scene writer 미확정은 그대로 남김. | [client/render/player.ts:145](../../games/splatoon3/client/render/player.ts) | [graphics/cloth_damping_runtime.md §6](../graphics/cloth_damping_runtime.md)<br>[graphics/cloth_link_runtime.md §6](../graphics/cloth_link_runtime.md)<br>[graphics/cloth_frame_runtime.md §11](../graphics/cloth_frame_runtime.md)<br>[판독+실행(부분)+데이터] |
| GR09 | P2 | 차이/미반영 | 모델 LOD·거리 bias/hysteresis | 플레이어 mesh는 frustumCulled=false이고 원본 LOD 선택 경로가 없음. 확정된 view-space Z·bounding radius·전역 bias·hysteresis를 적용할 것. 단순 유클리드 거리/일률 3LOD로 바꾸지 말 것. | [client/render/player.ts:130](../../games/splatoon3/client/render/player.ts) | [graphics/lod_runtime.md §6](../graphics/lod_runtime.md)<br>[판독+실행] |
| GR10 | 보류 | 원본 미확정 | 실제 Lby 팀색 행·최종 GPU 활성 바인딩 | render/paint는 OrangeBlue 고정. RSDB typed loader/행 데이터 확정은 실제 Lby 행 선택 확정이 아님. 최종 GPU/LUT·활성 variant/자원 전체 연결과 장면별 selector 근거가 필요한 부분은 원본 조사 대기. | [client/render/index.ts:13](../../games/splatoon3/client/render/index.ts)<br>[client/paint/index.ts:1](../../games/splatoon3/client/paint/index.ts) | [graphics/teamcolor_rsdb_source.md §11](../graphics/teamcolor_rsdb_source.md)<br>[graphics/stage_rendering.md §11](../graphics/stage_rendering.md)<br>[graphics/shaders.md §6](../graphics/shaders.md)<br>[미확정(실제 선택·whole)] |

### 이펙트

| ID | 우선 | 현재 상태 | 항목 | 현재 차이 → 반영할 것 | 실제 소스 | 원본 근거·수준 |
|---|---|---|---|---|---|---|
| FX01 | P1 | 일부 반영 | XLink·탄/명중/상태 trigger | 원본 ELink/SLink trigger와 r9 owner별 실제 Muzzle 행렬 공급을 연결했다. reader +3c4/+3c6 뼈를 Muzzle로 명명한 해석은 정정. 실제 내적 writer·trigger rule/metadata·native 평가 순서는 남음. [r9 현재 검증](graphics_priority_r9.md). | [client/fx/index.ts:1](../../games/splatoon3/client/fx/index.ts)<br>[client/audio/xlink.ts:1](../../games/splatoon3/client/audio/xlink.ts) | [effect_sound/xlink_switch_runtime.md §6](../effect_sound/xlink_switch_runtime.md)<br>[effect_sound/xlink_trigger_runtime.md §6](../effect_sound/xlink_trigger_runtime.md)<br>[combat/hit_effect_pipeline.md §6](../combat/hit_effect_pipeline.md)<br>[판독+실행(부분)+데이터] |
| FX02 | P0 | 차이/미반영 | 이미터 형상별 위치·방향·난수 | spawn은 모든 volumeType을 점으로 보고 positionRandom 단위벡터를 사용함. 이미 확정된 형상별 위치/방출·난수 소비 순서와 지정방향/크기 식을 이식할 것. | [client/fx/particles.ts:296](../../games/splatoon3/client/fx/particles.ts) | [effect_sound/effect_resources.md §2.2.3.1~2.2.4](../effect_sound/effect_resources.md)<br>[판독+실행(부분)+데이터] |
| FX03 | P0 | 일부 반영 | color0/1·alpha0/1 조합·탄 VAT | r4 원본키39개/known shader17개와 VAT2개를 실제 소비한다. r9 총구 pose 공급 추가. 나머지22 fallback/Custom1·dynamic color·linked alpha·VAT 시간률·native FX BRDF/env/전체 운동이 남음. [실제 FX 반영](priority_1_4.md), [r9](graphics_priority_r9.md). | [client/fx/particles.ts:1](../../games/splatoon3/client/fx/particles.ts) | [effect_sound/effect_resources.md §2.1.1·§2.2.5~2.2.5.1](../effect_sound/effect_resources.md)<br>[판독+데이터] |
| FX04 | P1 | 일부 반영 | OneEmitter 입장·개수·follow·수명 | pool은 cap에 따라 순환 덮어쓰기함. 원본 queue/admission·세대·0x60 record/n-count 계약과 follow 갱신을 연결할 것. cap을 늘려서 원본 동작이 됐다고 판정하지 말 것. | [client/fx/particles.ts:297](../../games/splatoon3/client/fx/particles.ts)<br>[client/fx/index.ts:1](../../games/splatoon3/client/fx/index.ts) | [effect_sound/one_emitter_runtime.md §6](../effect_sound/one_emitter_runtime.md)<br>[effect_sound/emitter_render_follow.md §6](../effect_sound/emitter_render_follow.md)<br>[판독+실행(부분)] |

### 효과음

| ID | 우선 | 현재 상태 | 항목 | 현재 차이 → 반영할 것 | 실제 소스 | 원본 근거·수준 |
|---|---|---|---|---|---|---|
| SND01 | 유지 | 반영 확인 | 원본 파형 변환 자산·재생 입력 | sfx bundle의 변환 .ogg와 metadata를 SoundPlayer가 읽어 bufferSource에 사용함. 자산 공급 경로만 확인하며 재생 gain/pitch/공간·XLink 선택 정합을 포함하지 않음. | [client/audio/sound.ts:87](../../games/splatoon3/client/audio/sound.ts)<br>[client/audio/index.ts:1](../../games/splatoon3/client/audio/index.ts) | [effect_sound/sound_resources.md §2~3](../effect_sound/sound_resources.md)<br>[데이터+실행(변환)] |
| SND02 | P1 | 일부 반영 | 리스너 위치·타깃 offset | 현재 listener는 camera.pos. 원본 mode3의 T+Rᵀoffset 계산은 확정되어 별도 함수로 반영 가능하지만 실제 Lby T 공급/모드 전체 연결은 미확정. camera.target을 원본 T로 확정하지 말 것. | [client/audio/index.ts:107](../../games/splatoon3/client/audio/index.ts) | [effect_sound/sound_resources.md §4.1.2](../effect_sound/sound_resources.md)<br>[판독+실행(식),미확정(실제 공급)] |
| SND03 | P1 | 일부 반영 | 거리 감쇠·DistCoef·방향성·패닝 | distance/DistCoef·AROC/AADR 일부와 단순 right projection pan 사용. 원본 directivityRate/extension flag1·FriendDistCoef 분기·전역 단위와 확정된 pan 입력/합성을 반영할 것. 최종 DSP 미확정을 별도 남김. | [client/audio/sound.ts:71](../../games/splatoon3/client/audio/sound.ts)<br>[client/audio/alto.ts:1](../../games/splatoon3/client/audio/alto.ts) | [effect_sound/sound_resources.md §4.1.3·§4.2·§4.5](../effect_sound/sound_resources.md)<br>[effect_sound/sound_global_unit.md §6](../effect_sound/sound_global_unit.md)<br>[판독+실행(부분)+데이터] |
| SND04 | P1 | 차이/미반영 | voice 필터·LPF/biquad 기본 계수 | 현재 gain→StereoPanner이며 필터 노드 없음. 원본 필터 packet·종류별 기본 계수·dist/HfGain 소비를 연결할 것. SDK의 전체 DSP 출력까지 원본 동등성을 주장하지 말 것. | [client/audio/sound.ts:104](../../games/splatoon3/client/audio/sound.ts) | [effect_sound/sound_runtime_filters.md §6·§11](../effect_sound/sound_runtime_filters.md)<br>[effect_sound/sound_resources.md §4.6·§4.8](../effect_sound/sound_resources.md)<br>[판독+실행+데이터(부분)] |
| SND05 | P1 | 일부 반영 | 그룹 제한·priority·정지 시간 | Priority×AUDC 일부와 limiterOrder는 있으나 P_D4/CC/guard/timer 계약이 빠지고 stop을 .01/.012로 통일함. 원본 제한기4종·생존 순서·duration envelope를 적용할 것. 슈터 AGST type0/limit−1와 stop .016초를 구분. | [client/audio/sound.ts:127](../../games/splatoon3/client/audio/sound.ts)<br>[client/audio/sound.ts:158](../../games/splatoon3/client/audio/sound.ts) | [effect_sound/sound_limiter_runtime.md §6](../effect_sound/sound_limiter_runtime.md)<br>[effect_sound/sound_resources.md §4.3.3](../effect_sound/sound_resources.md)<br>[판독+실행+데이터] |

### 공통

| ID | 우선 | 현재 상태 | 항목 | 현재 차이 → 반영할 것 | 실제 소스 | 원본 근거·수준 |
|---|---|---|---|---|---|---|
| SYS01 | 유지 | 반영 확인 | 60Hz core·복수 스텝 이벤트 보존 | app은 1/60 fixed step이며 EventTap이 clear 전에 frame별 이벤트를 보존하고 FX/audio가 drain함. 단순히 렌더가 마지막 queue만 읽어 발사 이벤트를 잃는 구조는 아님. 원본 actor 순서 동등성은 SYS02. | [client/app.ts:1](../../games/splatoon3/client/app.ts)<br>[client/audio/read.ts:24](../../games/splatoon3/client/audio/read.ts) | [weapon/shooter_bullet.md §3.2·§4.1](../weapon/shooter_bullet.md)<br>[physics/phive_controller.md §6](../physics/phive_controller.md)<br>[판독+데이터(60Hz),웹 소스 판독(보존)] |
| SYS02 | 보류 | 원본 미확정 | 프레임 안 actor ↔ physics 전체 순서 | 웹은 collision→range→camera→player→weapon→paint. 원본 개별 슬롯/함수 순서와 실제 engine scheduler 전체 순서는 구분해야 함. 근거 없이 system 순서를 재배열하지 말고 알려진 로컬 계약부터 검증. | [core/systems.ts:13](../../games/splatoon3/core/systems.ts) | [physics/phive_controller.md §11](../physics/phive_controller.md)<br>[weapon/shooter_bullet.md §3.2·§11](../weapon/shooter_bullet.md)<br>[미확정(whole)] |


## 7. 애니메이션·이펙트·소리·카메라·에셋 연결

- 이번에 CAM02 최종 기저를 이동·발사 축·렌더가 공유하도록 연결했다. MOV01/BUL03~04의 다른 상태/원점/물리 차이는 남는다.
- COL02~04/PHY04 contact를 MOV04~05/PT04/탄 접촉에서 소비한다. Ground 단일 mask로 각자 구현하지 않는다.
- PNT02~06 panel/owner/sample/시각 UV와 GR03~07의 조명을 연결한다. 발밑 잉크와 overlay 화면이 서로 다른 데이터를 쓰지 않도록 한다.
- HIT01/03·TGT03 결과/vel/충돌 분류를 FX/SFX에 전달한다. UI 숫자는 이후 별도 작업이다.
- GR02 SM+d4는 실제 변위·외부 벡터·명령 상한 식이다. 계산식 확정과 일부 field writer 미확정을 구분한다.
- 최초 CAM07 점검에는 writer가 없었으나 이번에 ELink/원본 곡선 producer를 연결했다. 남은 수명/listener 경계는 CAM07에 유지하며, 빈 에셋 이름에 흔들림을 넣지 않는다.

## 8. 다른 기능과의 상호작용

FillUp은 [collision_mesh §3.4.4~3.4.7](../gimmick/collision_mesh.md)와 [preset runtime](../physics/fillup_preset_runtime.md)의 r9 경계에 따른다. 확인한 Lby closure는 0건이므로 이 핵심 구현 목록의 분모/최우선 blocker로 추가하지 않는다. tag/filter 계약 자체를 없애라는 뜻은 아니다.

PC 마우스·렌더 보간·웹 렌더러/WebAudio 선택과 확정된 원본 기저/스케일/산술/필드의 미반영을 구분한다. critical을 headshot으로 해석하지 않는다. UI/메뉴·다른 모드·네트워크·다른 무기는 제외한다.

## 9. 웹 포팅 구조와 구현 순서

[README A~I](README.md)를 지시 단위로 쓴다. A/B/C가 이동·조준·벽 행동의 기반, D/E가 칠·화면, F/G가 탄·타격·시각 피드백, H/I가 나머지 인게임 수명·성능·원본 blocker다. 작은 연결 수정은 병행할 수 있다.

요청에 **묶음 또는 ID·수정 범위·근거 MD·검증 입력/출력·남길 미확정**을 명시하면 된다. PHY05/GR10/SYS02가 남아도 이미 확정된 normal impulse·붐 필터·베이크·형상별 emitter 식은 반영 가능하다.

## 10. 검증 코드·실행 결과·기대값

이번 실행은 정적 점검/문서 검증이며 원본 함수·웹 전체 테스트는 재실행하지 않았다. 기존 MD의 원본 실행 건수를 이번 실행 로그로 옮기지 않는다.

| 실제 명령/검사 | 결과 |
|---|---|
| PowerShell Get-Content / rg --files / rg -n으로 README/분석 형식/목차·impl 질문 및 실제 소스/원본 근거 조회 | caller/consumer와 최신 정정 대조. 보호 대상 쓰기 없음 |
| .venv/Scripts/python.exe - 로 1-based 소스 행/파일·근거 MD 존재 확인 | core/client TS87개 목록, 표의 파일/행 범위 확인 |
| Python json/base64 검사: ink_stamps.json / ink_tex_info.json | stamp52개/InkTexInfo50행, R8 decoded byte 수=w×h 전부 일치. 원본 byte/화면 재대조는 아님 |
| rg -n -e shakeOffset -e CameraRumbleName -e CameraRumbleFrame -e CameraRumbleParam web/games/splatoon3/client | client/camera/index.ts reader만 발견 |
| git rev-parse --short HEAD / git status --short -- web/docs/port | 둘 다 exit1: not a git repository. commit/push 없음 |
| 일부 가정 경로 조회 | phive.md/rig_follow.md/step_paint.md/ink_gauge.md 등 미존재 exit1/2. 실제 phive_controller/player_camera/player_state§8/shooter_bullet§5.5로 교정 |
| 첫 Python 출력/읽기 | cp949 stdout UnicodeEncodeError와 sincos_table.ts UTF-8 읽기 실패. stdout UTF-8 및 해당 파일 encoding 구분 후 판독 |
| 첫 문서 저장 orchestration | Markdown fence를 포함한 JS 문자열 구문 오류 SyntaxError. 도구 호출/파일 저장 전 실패했고 문자열 교정 후 저장 |
| 초기 MD 검증 parser | §11 보류 요약표의 PHY05도 점검행으로 읽어 AssertionError(cell3). §6 본점검표로 범위를 제한한 뒤 위 합계/링크 검증 성공 |
| 최종 MD·보호 파일 검사 | exit0: 고정ID62/중복0, 반영확인9·일부37·차이13·원본보류3, 12영역 합계/퍼센트 일치. 링크241/누락0·소스42파일/행 범위 이상0, 본문11절 확인. 보호파일592 SHA256 시작/종료 일치 |

후속 최소 검증: 자유 이동/바닥/벽/모서리/경사/kinematic 표적 접촉, 카메라 벽 거리·법선·수직 시선 보존·점프/낙하, 탄 첫2프레임/연사·release/감쇠거리/잉크 회복 경계, 비1 damageRate/재피격·Burst/Expand·레일/bend, floor/wall/edge/stamp/덧칠 owner/sample/UV, 동일 scene pose의 조명/캐릭터/FX와 소리 공간/그룹 수명.

기존 원본 harness의 독립 입력·출력 계약을 재사용한다. 정상 fixture나 비슷한 화면만으로 whole 항목을 닫지 않는다.

## 11. 미확정 사항과 추가 분석에 필요한 근거

| 보류 ID | 남은 원본 근거 | 다음 / 구현 가능한 경계 |
|---|---|---|
| PHY05 | 실제 Lby geometry/typed filter/native TOI/manifold 전체 연결 | phive_controller§11·character_controller§11. primitive/normal impulse/COM 확정식부터 구현하고 live 전체 별도 추적 |
| GR10 | 실제 팀색 행 selector·활성 GPU/LUT/자원 전체 binding | teamcolor_rsdb_source§11·stage_rendering§11·shaders§6. known 산술과 scene 선택을 분리 |
| SYS02 | actor scheduler와 physics의 전체 프레임 배치 | phive_controller§11·shooter_bullet§3.2/11. 알려진 로컬 슬롯 순서를 유지하고 actual scheduler 추적 |

식이 확정된 일부 항목도 scene writer/상위 요청/SDK DSP가 미확정이면 표에 남겼다. 갱신 때 근거 없는 값·분모 축소·부분 결과의 whole 승격을 금지한다. 새 원본 분석이 필요하면 기존 SHARED/FUNCS/decomp_index 중복 검사부터 별도 분석 지시로 수행한다.

### 카메라 반영 후 검증 — 2026-10-03

CAM02 일부 → 반영 확인, CAM07 미반영 → 일부. 고정 분모62/카메라7을 유지했다.
전체 **10/62 = 16.13%**, 카메라 **2/7 = 28.57%**. 새 질문을 쪼개거나 부분 결과로 whole 행을 닫지 않았다.
원본 실행 fixture 1,031건은 기저260·slerp131·spring128·위치 게이트128·붐128·전진128·리그128이며 TS 표본 전부 비트 일치.
SDK libm의 알려진 일반 ULP 차이, 미공급 상태 필드, native 질의/프레임 전체 경계는 [impl/camera.md §8~9](../impl/camera.md)에 유지했다.
최종 전체 검사와 실제 브라우저/실패 기록은 [commands.md](../../../analysis/port_camera/commands.md).
UI·그래픽 재질/광원·physics solver 자체와 다른 고정 행을 이번 카메라 수정으로 완료 처리하지 않았다.

### 그래픽 반영 후 검증 — 2026-10-03

GR04 차이/미반영→일부, 기존 GR01/03/05/07에 새 연결을 반영했다. 전체10/62=16.13%, 그래픽0/10=0.00%를 유지한다. 일부38/차이11/미확정3. 원본 전체와 다르게 남은 broad 행을 승격하지 않았다.
원본 SH/Hermit680·HSV128 비트 일치, point32×8 시퀀스/cone256 결정 일치. 전체 테스트·typecheck·build 및 actual Lby/HDR/형태 coverage는 [graphics.md](graphics.md), [render.md §8](../impl/render.md)와 [commands.md](../../../analysis/port_graphics/commands.md). 원본 inventory는 그대로다.

### 탄·총 반영 후 검증 — 2026-10-03

BUL01/HIT01/TGT03 세 고정 항목을 위 한정 범위에서 반영 확인으로 변경했다. [weapon](weapon.md), [impl/weapon](../impl/weapon.md) §10: native 1,926건/전체153개 테스트/typecheck/build/실제 Lby browser 30발 간격6·도색·NoInk/회복·error0. BUL03/04/06 일부 유지. 원본 분석 inventory 분모/상태는 변경하지 않았다.

추가 원본 시각 분석 r2(2026-10-03)는 [ink_visuals](ink_visuals.md)의 후속 표를 따른다. 바닥 UBO/잠영 표시/Flash·Ripple/로비 LUT 공급을 보강했으며 코드 반영 상태와 고정62 분모는 바꾸지 않았다.

### 정지 마우스 시점 분석 — 2026-10-03
[mouse_camera](mouse_camera.md)·[시점 급변 상세](../camera/mouse_view_jumps.md): actual 웹/Three268assert와 InputDevice/frame30건으로 large delta 역방향 보간·catch-up 이력 소실·pitch 후행을 확인했다. CAM01/02의 원본 계산 한정 확인과 마우스 전체 체감을 구분한다. 코드 수정이 없어 본표 상태/62분모·2/7카메라 점수는 바꾸지 않았다. 사용자 실제 이벤트와 설정은 미수집이므로 사건의 직접 원인은 미확정이다.

### 첨부 화면 추가 분석 — 2026-10-03

[reference_graphics](reference_graphics.md)와 [전체 원본/웹 경로](../graphics/reference_graphics_gap.md)에 키/count 유실·surface shader·캐릭터 cheapSSS/film·playerFX·CC LUT와역번역도구정정을추가했다. source/impl변경0이며고정62개및상태점수유지. 부분재질/셀/CPU실행은원본GPU전체/픽셀동등성을뜻하지않는다.


## 우선순위1·4 후속 구현 — 2026-10-03

[실제 마우스·FX 반영 결과](priority_1_4.md). 마우스 adapter와 FX 공급/소비자를 연결했다. 원본키39개 실제 전달, known shader17개와 VAT2개 GPU 활성 확인. native 전체 카메라·FX 출력 계약이 남아 기존 broad 상태와13/62분모·분자는 변경하지 않는다. 이전내용의시점별분석/정적대조를현재fullframe동등성으로읽지않는다.

## 6번 공통 조명·그림자·최종색 실제 반영 — 2026-10-03

[common_render_r5](common_render_r5.md)에 실제변경·원본128회·WebGL검증·잔여를 통합했다. GR04/05/06/07 설명을 현재source로 갱신했지만 broad 상태는 일부 유지다. **13/62=20.97%, 그래픽0/10/일부7/10** 유지. 전체252/252·typecheck/build PASS, GPUshadow13/13·post36/36·actualLby 오류0. nativeGPU/frame 전체와 표적cast/receive 정책은 미확정.


## 공통 경로 r6 후속 웹 반영 — 2026-10-03

[현재 구현·검증·잔여](common_render_r6.md). mSky cube27의 채도 .4, 원본 PCF/strict 캐스케이드/SPP·Default fade40~60, DefaultDay old_calc=false Bloom producer와 HDR 소비를 연결했다. 전체266/266·typecheck/build PASS, 실제 Lby4단계·GPU오류0. Sky21/Shadow25/Bloom18 웹 GPU 검사와 원본 writer1,024·Bloom블록/파서775건을 구분한다. native Illuminate/12layer·live sampler/SPP/HDR alpha·DOF·ColPaint·캐릭터/잠영은 남는다. 고정13/62=20.97%, GR0/10·일부7/10 및 원본556/986는 유지한다.


## 바닥·벽 잉크 표면 r7 실제 반영 — 2026-10-03

[현재 구현·검증·다음 지시](ink_surface_r7.md). 띄운 collision overlay를 actual visual triangle draw로 옮기고 packed UV/switch/tangent, InkBright·rim·normal1.8·floor/wall thickness·F0.015/roughness.05와 공통 베이크/SH/그림자/HDR 조명을 연결했다. 원본 leaf writer277/panel256/변환블록128 입력 대조, WebGL 판독slice↔포트431건, 전체285/285·typecheck/build·actualLby4단계 오류0. 전체원본GPU/atlas 동등성은 아니다.

PNT06 차이→일부이며 **고정13/62=20.97%, 일부37/차이9/미확정3**, GR0/10·일부7/10, 원본556/986=56.39% 유지. native atlas/seam·BRDF/cube12/Illuminate·W 후속writer/환경emission·캐릭터SSS/film·잠영숨김/파문이 남는다. 과거 collision overlay/.35 설명은 당시 사실로 보존하며 현재상태는 r7 링크를 따른다.


## 캐릭터 그래픽 r8 실제 반영 — 2026-10-03

[현재 반영·검증·다음 지시](character_graphics_r8.md): body/face cheapSSS·Thc 역광, hair/squid film·2cl 보정 법선, RGBA 강도, B7a0 지연 숨김/복귀, 슈터 Shtr/Shtr를 웹에 연결했다. 전체304/304·typecheck/build, WebGL 판독식512건, actual Lby12단계 오류0. 원본 NVN/전체 프레임 동등성은 아니다.

고정13/62=20.97%(일부37/차이9/미확정3), GR0/10·일부7/10, 원본556/986=56.39%·그래픽102/204=50.00% 유지. 추가 재질3개/live 몸 잉크·type11/18·SPP·cube12/BRDF·벽/상승 공중 producer·잠영 파문은 남는다. 이전 '캐릭터SSS/film/B7a0 전체 미연결' 설명은 당시 기록이고 최신 한정 반영은 r8 링크를 따른다.


## 재질·눈 패턴·총구 그래픽 r9 — 2026-10-03

[현재 반영·검증·다음 지시](graphics_priority_r9.md): 탱크/하네스/병의 native 재질·owner texture, raw type11 눈 채널, [Maya0/rotation0 UV6lane](../graphics/character_texsrt_r9.md), [실제 Muzzle 시각 행렬 및 내적 정정](../effect_sound/muzzle_attachment_r9.md)을 웹과 MD에 반영했다. FMAA 원본1,212/피부 홀더67/SRT313/내적 격리블록2,048, 선택 GLSL↔웹GPU448건은 각각 범위가 다른 검증이며 원본 NVN/전체프레임 일치가 아니다.

고정 원본556/986=56.39%·그래픽102/204=50.00%, port13/62=20.97%(일부37/차이9/원본미확정3)·GR0/10/일부7/10 유지. 신규 부분 근거를 기존 복합 질문 전체 확정으로 승격하지 않았다. 몸CP/skin idx·weighted type11/type18·다른 SRT mode/rotation·cube/BRDF/SPP·잠영 파문/Custom1/VAT·native 최종픽셀은 남는다. 최종 테스트·브라우저·보호 SHA와 실패는 r9 요약의 실행 기록을 따른다.
