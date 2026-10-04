# 카메라 웹 반영 상태

2026-10-04 · 현재 구현 기준. r10 입력/투영/상태/쉐이크 반영 상세는 [port/camera_r10.md](../port/camera_r10.md). 사용자의 “카메라부분 web에 반영” 지시에 따라 코드와 문서를 수정했다.
아래 §1~§11이 현재 상태이며, 이전 설명은 §11에 원문 보존한다. 원본 분석 완료율은 변경하지 않았다.

## 1. 기능·범위

Lby_Lobby00 1인 연습의 mode0 사람/오징어 카메라, 조준, 법선 추종, 붐 충돌 회피와 렌더 기저를 반영한다.
이동과 탄이 같은 최종 기저를 읽는다. ELink 이름이 지정된 카메라 쉐이크를 연결한다.
UI·다른 무기·장면·네트워크 구현은 변경하지 않았다.

## 2. 재사용한 원본 근거

| 근거 | 이번 소비 |
|---|---|
| [player_camera.md §6.1~6.8](../camera/player_camera.md) | mode0 리그·수직 추종·X/Y/Z 기저·두 붐 질의·복귀/축소 식 |
| [movement_physics.md §6.3.3](../player/movement_physics.md) | 1252ff0 방향 slerp와 sead 사인/아탄 표 |
| [r9_boom_query.md §6.1](../camera/r9_boom_query.md) | Sphere 반경 .3, layer7/mask8, 상대 camera 허용, iterator bit0 법선 |
| [r9_collision_spring.md §6](../camera/r9_collision_spring.md) | C144 damping·B210 소비·C120 보정 |
| [r9_state_sources.md §6](../camera/r9_state_sources.md) | LobbyVersus의 G143d0=0, 점프 분모의 실제 f32 |
| [r9_reset_contexts.md §6](../camera/r9_reset_contexts.md) | reset 소비와 장면 공급자의 남은 경계 |
| [shake_rumble.md §3.2](../camera/shake_rumble.md) | ELink 이름/frame·곡선·거리 15/25·월드 위치 합산 |

r10 근거는 [입력](../camera/r10_input_response.md), [상태](../camera/r10_state_producers.md), [투영/렌더](../camera/r10_render_projection.md), [쉐이크](../camera/r10_shake_shooter.md)를 추가 소비했다. 이번 원본 호출은 이식 회귀 fixture 생성이다. 새 분석 확정 건수로 합산하지 않는다.

## 3. 구현 점검률

[port 고정 점검표](../port/implementation_status.md)의 CAM01~07 기준 **2/7 = 28.57%**.
반영 확인 CAM01·CAM02, 일부 반영 CAM03~07이다. 이전 1/7 = 14.29%에서 **+14.29%p**.
부분 기능의 fixture가 통과했다고 전체 행을 완료로 승격하지 않았다. 전체 원본 카메라의 “100% 동등”을 뜻하지 않는다.

## 4. 달라진 동작

- 법선의 선형 보간/재정규화 → 원본 1252ff0의 표 기반 방향 slerp(.1). 거의 반대 방향은 원본의 null 축 동작을 보존한다.
- mode0 곡선·로드리게스 회전은 명령의 f32 연산/덧셈 순서와 원본 사인·코사인 표를 사용한다. SQ 음수 높이 제어점은 축약값 1.275가 아닌 **1.2750000953674316**이다.
- 카메라 최종 기저는 Z=normalize(pos−at), X=normalize(up×Z), Y=Z×X. 길이0 또는 |Z.y|>0x3f7ffffe면 **세 열 모두 이전 값 유지**. right와 viewForward(−Z)를 공유한다.
- 붐 반경 .2 → 원본 f32(.3). near .2와 구분한다. query1·C14ec 전진 계수·query2 시작점/거리, 미적중 법선 초기화, 정상 거리 복귀 및 축소 하한 min(…, .35)을 반영한다.
- C144 오프셋 소비, 피벗 xz 및 최소거리의 dot 보정, C1760 질의 생략/ratio 혼합, Bde0 위치 보존 게이트와 후속 포즈 혼합을 추가한다. 공급자가 없는 값은 §9대로 남긴다.
- 수직 속도 비율은 F(F(vy+jump3dY)/**0.11499999463558197**), 원본 분모 0x3deb851e이다. 보통 수직 추종·누산·FOV·근접 보정에 f32 연산을 적용한다.
- 렌더 회전은 lookAt 재계산 대신 원본 기저로 만든 쿼터니언을 사용한다. 이전/현재 쿼터니언 보간은 웹 선택이다.
- ELink CameraRumbleName/Frame, 거리 감쇠, Axis·곡선·Scale의 합을 실제 shakeOffset에 공급한다. 회전을 유지하고 월드 위치만 이동한다. 이름이 빈 슈터에 별도 발사 쉐이크를 만들지 않는다.

r10 추가: 원본 f32 감도·pitchAngleToP, native 스틱 scalar 소비, whole blocked/별도 auto-pitch·WaterFall 법선, conditional normal normalize, 검증된 B7a0 공급, query1 separation 교정, logical Projection/inverse·후행 aspect, admission gain·owner/serial/finished 순서를 반영했다. 마우스 픽셀을 원본 스틱으로 취급하지 않는다.

## 5. 웹 갱신 순서

코어의 기존 시스템 순서는 변경하지 않았다. 원본 actor↔physics 전체 순서의 미확정은 유지한다.

카메라 내부: 이전 렌더값 저장 → 몸 위치/법선 추종 → C144 소비 → 입력 → 오징어/FOV/고각 누산 → 리그 → 수직 추종 → 붐 정의 → 두 질의/복귀·축소/위치 게이트·혼합 → 근접 보정 → 최종 기저.

client/fx는 기존 고정 step 이벤트 배출에서 쉐이크를 계산하고, 마지막 camera view가 위치 offset과 기저 회전을 반영한다. 유한 쉐이크가 시각 이미터보다 오래 살아도 ELink 시각 핸들의 수명을 늘리지 않는다.

## 6. 영역 간 계약

| 필드/경로 | 원본 대응·현재 상태 |
|---|---|
| camera.right/up/viewZ | X/Y/Z 기저, 이전 값 prevRight/prevUp/prevViewZ도 공유 |
| camera.viewForward | −Z. weapon이 재정규화한 pos/at 축보다 우선 사용 |
| player.final → CameraPlayerInput.finalVel | B+e4. C14ec와 spring의 최종 속도 |
| player.vel → moveVel | B+114. 축소 속도 계산용; final과 혼동하지 않음 |
| player.cameraNative → CameraPlayerInput.native | 명시적 원본 소비 필드 계약. 현재 player는 이를 생산하지 않음 |
| native.springDelta/bodyResidual/springHold | D/B210/B e0c. B1f8의 unexplained를 B210으로 대입하지 않음 |
| native.wall7a0/ad0/d9/blend1760/positionGateDe0 | 이름을 추정해 web wallCling/사격 bool로 대체하지 않음 |
| native.skipQueries/skipBoom/minimumQueryOffset/humanFov | 특수 게이트/offS/B6dc 소비 입력. 공급자가 없으면 기존 보통 경로 유지 |
| SphereQueryFilter | query layer7/sub0, hitMask8/subMaskFFFFFFFF. 웹 Layer와 별개 |
| Hit.nativeEntryFlags | native point normal일 때 bit0=1 그대로/0 반전. 일반 웹 outward normal은 카메라 inward로 한 번 변환 |
| PadState.cameraStick | 명시적 gyro-off post-remap/delta·감도·cap/state 소비. 현재 브라우저는 mouse 공급이며 gamepad 추가 아님 |
| cameraNative.control/autoPitch/waterFrames/Height | 원본 blocked/별도 피치 reader·s9 및 Bdf0/Bdf4 입력. 실제 player/event 생산자는 미연결 |
| player.displayBinding/display.hidden | supported producer의 B7a0를 wall7a0에 연결. wallCling을 대입하지 않음 |
| Hit.nativeSeparation | raw query1 point 교정에만 사용. 웹 surface point에는 생략 |
| 지형 sweep | 원시 재질 mask의 camera 허용과 sub0을 검사. camera-only 장벽을 기존 bullet용 web Layer=0이라도 유지 |

mesh 쪽은 현재 Ground 지형 컨테이너 전제를 사용한다. 실제 body LP의 레이어·Default/Same/Other 표·typed shape/태그·skip 목록 전체를 이식한 것이 아니다. 현재 Object 표적을 camera Ground query의 대상으로 확대하지 않았다.

## 7. 입력·렌더 이식 선택

마우스의 px→회전량·감도 설정과 PC 버튼 표현은 유지한다. yaw 회전은 sead 표를 쓴다.
전체 원본 gyro/device posture·모듈 pose 공급은 미반영이다.
60Hz·렌더 alpha·three 쿼터니언 정규화/역행렬은 웹 선택이다. 투영은 원본 logical f32 식·후행 aspect를 이식했고 SDK tanf는 JS adapter다. viewport 래치 호출 주기는 웹 render frame이다. 카메라의 native 기저를 이동·탄·렌더에 전달한 범위와 실제 GPU 화면의 동등성은 구분한다.

## 8. 원본 실행 fixture 회귀

[생성 도구](../../tools/camera_port_fixtures.py)는 기존 확정 함수·블록을 unicorn에서 실행하고
[fixture](../../games/splatoon3/tests/fixtures/camera_native.json)에 원본 비트를 저장한다.
[camera_native.test.mjs](../../games/splatoon3/tests/camera_native.test.mjs)가 TS 결과와 직접 비교한다.

| 범위 | 원본 경우 수 | TS 비교 |
|---|---:|---|
| 최종 X/Y/Z 및 수직/길이0 보존 | 260 | 전부 비트 일치 |
| 1252ff0 null 축 slerp | 131 | 전부 비트 일치 |
| C144/C120 소비 블록 | 128 | 전부 비트 일치 |
| Bde0 위치 게이트·C1760 postmix | 128 | 전부 비트 일치 |
| 붐 under/angle/speed/rate/target/ratio | 128 | 전부 비트 일치 |
| C14ec 전진 계수 | 128 | 전부 비트 일치 |
| mode0 사람/오징어 리그 값·최종 pose | 128 | 전부 비트 일치 |
| **합계** | **1,031** | **표본 전부 일치** |

합성 입력에서 원본 명령을 호출했다. whole 원본 카메라/actor·physics·query/frame은 실행하지 않았다.
SDK logf/expf와 JS Math의 일반적인 마지막 비트 차이가 알려져 있으므로 이 128개 표본 일치를 모든 입력으로 확대하지 않는다.
앞 표는 이전1,031건의 회귀 범위다. r10 추가 검증은 입력1,280사례/3,328필드, 기존 blocked2,175+WaterFall512, 투영421×16, 쉐이크162trace/6,318틱이다. 합성 pre-block/SDK boundary/전체scene 경계는 [현재 검증](../port/camera_r10.md#10-검증실제-명령실패)에 명시한다. 투영은 captured SDK tanf 공급 시0불일치, 실제 JS tanf는380/421완전일치·139필드차이·최대관측19ULP이다. 원본 분석 건수로 재계상하지 않는다.

## 9. 남은 차이·다음 지시

| 항목 | 상태와 다음 작업 |
|---|---|
| spring 실제 생산 | 소비는 이식됐지만 player가 D/B210/e0c를 공급하지 않아 보통 실행은 0 입력이다. 원본 rig/head 차이 생산자와 B210 실제 컴포넌트를 physics 계약으로 연결해야 한다. |
| formHeight/B6dc/상태 게이트 | formHeight는 아직 미공급(기존 기본0), humanFov는 미공급시 기존55. wall7a0는 supported B7a0 표시 producer를 연결했다. ad0/d9/blend1760/de0와 희귀 offS/장면 게이트 생산자, WaterFall live writer는 남는다. |
| query 전체 | 웹 custom mesh sweep/다면체 근사·Ground 컨테이너 전제는 남는다. native LP·양방향 표·typed 태그·real stage TOI를 이식해야 한다. |
| reset/모듈 | 첫 player·respawns 웹 매핑은 유지했다. 원본 First/Warp/Recorder 조건·module quaternion/상태 리그의 실제 장면 공급은 후속이다. |
| 조준 scalar/libm | pitchAngleToP는 원본f32로 정정했다. aimPitchDeg/aimDirection의 일부 double 계산 및 SDK math 차이는 남는다. 전체 조준 함수를 모든 입력에서 비트 동일하다고 주장하지 않는다. |
| 쉐이크 수명 | native MaxX/frame-limit 종료·generation/follow·serial·종료후합산 소비를 이식했다. 실제 pool capacity/초기serial·XLink delay·event-owner 공급은 미연결이고 visual handle fallback은 웹adapter다. |
| 쉐이크 listener | 현재 unshaken shared camera.pos를 사용한다. 모듈 listener+1c8의 장면 공급 동등성은 별도 확인 필요. |
| 실제 체감·화면 비교 | 현행 웹 실행은 확인했다. 원본 플레이 녹화/동일 입력의 전체 화면·조작감 대조는 하지 않았다. |

다음에는 CAM04~05의 실제 physics→camera 공급과 CAM03의 지형 질의 계약을 먼저 연결하면 된다.
위 경계 때문에 CAM03~07은 일부 반영으로 유지한다.

## 10. 실제 검증·명령

이전 포팅 명령은 [analysis/port_camera/commands.md](../../../analysis/port_camera/commands.md), 최신 r10은 [commands.md](../../../analysis/port_camera_r10/commands.md)에 기록한다. 전체359/359, typecheck/build PASS. 실제 화면/크기 변경은 확인했으나 자동화 pointer lock WrongDocumentError로 실제 마우스·오징어 조작은 미검증이다.
기존 이식 선택 테스트의 .2 벽 기대값과 배정밀도 리그 기대값은 원본 .3/표 결과를 기대하도록 정정했다.
float32의 미분 잡음을 원본 오차로 판정하던 C1 유한차분 검사는 원본 경계 fixture 직접 비교로 바꿨다.

## 11. 변경·정정 기록

2026-10-04 r10: 이전 “pitchAngleToP 일부 double”, “비루프 종료 미확정/MaxX 웹정책”, “loop fade 웹종료” 설명은 원본 f32 매핑과 native 수명 이식으로 정정했다. 당시 표현을 여기 보존하며 현재 잔여는 실제 supplier/전체event·SDK/GPU 경계다. 일부 함수 회귀로 CAM03~07 전체를 완료로 승격하지 않았다.

2026-10-03: 이전 본문의 “질의1/C14ec 생략”, “법선 선형”, “near=.2에서 반경 추정”, “normalize(at−pos)만 출력”,
“쉐이크 producer 없음”은 이번 구현으로 변경됐다. 기존 분석 결론을 삭제하지 않고 아래 당시 구현 기록을 보존한다.
원본 MD의 분석 inventory·확정 수와 SHARED/FUNCS는 새 분석으로 계산해 수정하지 않았다.

<details>
<summary>이전 구현 기록 — 2026-10-03 카메라 포팅 전 상태</summary>

### [camera] 카메라·조준 입력 구현 기록

담당 폴더: `games/splatoon3/core/camera/`, `games/splatoon3/client/camera/`, `games/splatoon3/client/input.ts`.
근거 문서: [../camera/player_camera.md](../camera/player_camera.md), [../camera/camera_feel.md](../camera/camera_feel.md), [../camera/aim_swerve.md](../camera/aim_swerve.md), [../camera/shake_rumble.md](../camera/shake_rumble.md).
원문 디컴파일: `analysis/decomp/camrest/cam_main_full.c`(메인 0x71024d9ae8 = 1~3652행, 입력 0x71024e0178 = 3653~6297행), `analysis/decomp/camera/batch1.c`(리셋 0x71024d6598, 리그 0x71024d6e84, 붐 정의 0x71024d8f94), 이번에 추가한 `analysis/decomp/camimpl/aim.c`(0x7102551fe0, 0x7102551640), `aim2.c`(0x7102551780).

### 1. 구현한 것

### 1.1 파일

| 파일 | 내용 |
|---|---|
| `core/camera/curves.ts` | bias 곡선(camera_feel §4.2), 조각 3차 베지어 `pieceBez`(리그·조준 곡선 공용 꼴), invLerp |
| `core/camera/rig.ts` | 상수 블록(0x71024d63f0), 기본 리그 H/F/D/S, 오징어 블록(+0x1764), 고각 회전(`rigPose`) |
| `core/camera/pitch.ts` | 감도→회전 속도(0x71024d6598), `pitchAngleToP`(0x71024e64f0), 조준 피치 곡선(0x7102551780), 조준 방향 회전(0x7102551fe0) |
| `core/camera/camera.ts` | `PlayerCamera`: 리셋·프레임 갱신·출력. shared `camera` 객체(`CameraShared`) |
| `core/camera/index.ts` | `createCameraSystem`, shared `player` 어댑터(`readPlayer`), 오징어 상태 집합 `isCameraSquidState` |
| `client/camera/index.ts` | shared `camera` → three `PerspectiveCamera`(위치·lookAt·FOV·near 0.2/far 2000), 렌더 보간, 쉐이크 오프셋 연결점 |
| `client/input.ts` | 마우스 → `lookYaw/lookPitch` 대응식, 감도·반전 설정(localStorage `splatoon3.camera.*`) |

### 1.2 shared `camera` (`CameraShared`, 쓰기: camera)

| 필드 | 원본 | 내용 |
|---|---|---|
| `aimForward` | +0x18c | 조준 수평 단위벡터. yaw 회전 대상 |
| `rigForward` | +0x1a4 | 리그 수평 시선. 일반 경로에서 매 프레임 `= aimForward`(입력 함수 끝 6226~6227행). 탄 조준 기준(0x71024aff7c param_4=1) |
| `yaw` | — | `atan2(aimForward.x, aimForward.z)` (forward = (sin, 0, cos)) |
| `pitchNorm` | +0x16c | p, −1(아래)..+1(위) |
| `pitchAngleDeg` | +0x150c | 피치 누적각 s(도), 스틱 범위 −28..+44 |
| `pitch` | — | 조준 피치(라디안, 위 +) = `aimPitchDeg(p)` 기본 곡선 |
| `aimDir` | 0x71024aff7c 반환 | `rigForward`를 `pitch`만큼 올린 3D 단위벡터(흔들림 회전 전). f32 |
| `pos` / `target` | *(+0x60) / +0x70 | 최종 카메라 위치·주시점 |
| `fov` / `near` / `far` | +0x7c / +0x80 / +0x84 | 수직 FOV(도) [수직인지는 추정: sead PerspectiveProjection fovy], 0.2, 2000 |
| `prevPos` / `prevTarget` / `prevFov` | — | 직전 스텝 값(렌더 보간용, 웹) |
| `squidBlend` / `boomRatio` | +0x1764 / +0x14c4 | 표시·디버그용 |

`world.shared.debug` 에 `camera.p`, `camera.s`, `camera.squid`, `camera.boom` 을 씁니다.

### 1.3 프레임 순서 (0x71024d9ae8 와 같은 순서)

1. 추종 위치 +0x120 = 플레이어 위치(+0x10), 이전 값 +0x12c 보관. 카메라 바닥 법선 +0x138 → 플레이어 +0x180 쪽으로 0.1 (228~360행).
2. 입력(0x71024e0178): yaw → 피치 누적 s → p → `rigForward = aimForward` (§2 이식 차이).
3. 오징어 가중치 +0x1764 (500~545행): 조건 = 상태 ∈ Sq(0x82..0x90, 0xaa..0xac, 0xed, 0xee, 0x10c). 누산기 +0x1768/+0x176c 에 프레임마다 0.025(공중 프레임 ≥ 4 이면 0.001) 더하고 상한 0.2, 반대쪽은 0, `w += r·(목표 − w)`.
4. FOV·고각 목표(1056~1126행): 오징어면 FOV 60, 고각 (A, B↑, B↓) = (0, 20+40u, −60−15u), 아니면 FOV 55(본체+0x6dc, §3), (−7.5, 60, −75). u = min(1 − 법선 y, 1). 비율 = min(+0x1768 또는 +0x176c, +0x1558), +0x1558 은 같은 증가량으로 0.2 까지(+0x155c = 0.2, 리셋 batch1.c 363행).
5. 리그(0x71024d6e84 mode 0): §6.1 베지어 + 오징어 블록(아래) + H += 본체+0xcf0 → 주시점·카메라, 고각 −θ° 로드리게스 회전.
6. 수직 추종(1660~1850행): 비율 = (vy + 3D점프 y)/0.115(0x71058bbc60), 목표 0.25/0.7/0.25−0.45r, 오를 때 0.25 + q·r·g (q −0.22, g = 바닥 법선 y 로 bias(·,0.3)·0.7+0.3), +0x1518 은 커질 때 0.01 비율, +0x151c ×0.9 를 하한으로. rate = max(+0x1518, 0.3 − 0.3·+0x14f0). 주시점 y 만 지연, 카메라 y 는 같은 차이만큼 내림.
7. 붐(§6.8): 붐 정의 0x71024d8f94(피벗·방향·길이·minDist 0.8·e) → 질의 2 → +0x14f0 → 복귀 속도 spd → 목표 비율 +0x14c8 → 평활 rate(늘 때 3071~3086행, 줄 때 3087~3241행 전사) → `pos = 피벗 + dir·len·비율`, `pos.y −= e·(dR − dA)/dR` → 주시점 = 리그 주시점, 비율 < 0.999 이면 주시점 y 보정(3534~3566행).
8. 근접 보정(2363~2378행): `(pos − at)·aimForward > −0.16` 이면 조준 방향으로 0.16 뒤까지 민다.
9. 시선 방향(*(+0x68)+0x18 = normalize(at − pos), |y| ≤ 0.9999999 일 때만 갱신, 2392~2405행) → 다음 프레임 +0x14bc(시선 회전 변화) 입력.

### 1.4 오징어 블록 (+0x1764 > 0, batch1.c 1031~1460행 직접 판독)

player_camera.md 가 "표로 옮기지 않았다"고 남긴 부분을 이번에 읽어 옮겼습니다.

- 곡선(접선 계수 +0x1820 = 0.5): 거리 (7.2, 6.8, 5.2), 높이 (1.45, 1.45, 2.35), 전방 (0, 0.5, 0.5), 위 오프셋 0.
- 바닥 법선으로 섞기 u = min(1 − +0x13c, 1): 높이 → 상수 곡선 p≤0 [1.45, 1.275, 1.45, 1.45] / p>0 [1.45, 1.625, 1.8, 1.8], 거리 → [7.5, 7.5, 10, 10], 전방·위 오프셋 → 0.
- 그 뒤 +0x1550(0x1834~0x1848 곡선)·+0x1570(높이 0.2·전방 0.5·거리 [8.8, 9.8|7.8, 9.2|7.2, ..]) 가중을 섞지만, 두 가중치는 전역 `0x71058bbb9a`/본체+0xa5f4 와 +0x16ec(특수 재시작) 모드에서만 켜지므로 웹에서는 0으로 두고 생략했습니다.
- FOV 목표 정정: player_camera.md §6.2 의 "lerp(…, 45, wSq)"의 가중치는 +0x1764 가 아니라 **+0x1550** 입니다(1113행 `fVar32 = this+0x1550`). 오징어 FOV 목표는 60 입니다.

### 1.5 조준 방향 (0x71024aff7c) — 이번 분석

- 탄 생성(param_4=1)은 방향 = 카메라 +0x1a4(특정 조건이면 본체+0x54c), 각 인자 = 0x71024e4fec(카메라) = p(+0x16c, 특정 조건이면 본체+0x558) [판독: batch1.c 8665행, asm 0x71024b0060~0x71024b00dc].
- 각 = (스페셜 활성 시 본체+0x678 vt+0xb8) / (본체+0x588 vt+0xe0) / 둘 다 없으면 **0x7102551640(p)**. 0x7102551640 은 0x71058bdeb0+0x14..+0x28 의 값으로 임시 파라미터를 만들어 0x7102551780(param, p, 1) 을 부릅니다 [판독: asm].
- 0x7102551780: 조각 베지어 p≤0: P0=mid, P1=mid−kMid(up−down), P2=down+2kDown(mid−down), P3=down; p>0: P1=mid+kMid(up−down), P2=up−2kUp(up−mid), P3=up. 결과(도) × π/180 [판독: aim2.c].
- 기본값(정적 초기화 0x710257ff00, `analysis/player/bss_consts_58bb000.json`): up 75, mid 5, down −70, kMid 0.17, kUp 0.152, kDown 0.178 [실행(에뮬)]. 즉 p=0 에서 조준은 수평보다 5° 위입니다.
- 0x7102551fe0: 축 normalize(−h.z, 0, h.x) 둘레 쿼터니언 회전(cosf/sinf, 사인표 아님), 양의 각 = 위 [판독].
- 슈터의 vt+0xe0 은 0x710258868c: `this+0x270`(InkActionShooter 객체 +0x2a0)의 파라미터 객체로 0x7102551780 을 부릅니다. 그 객체가 어느 GameParameter 인지·값은 [미확정] — 웹은 기본 곡선을 씁니다(§3).

### 2. 원본과 다른 점

### 2.1 입력 이식 차이 (필수 표)

| 원본 (조이콘) | 웹 (마우스·WASD) | 근거·이유 |
|---|---|---|
| 오른쪽 스틱 x → yaw 각속도 목표 `yawMax(k)·bias(m,0.8)·(−x)`, 속도 평활 α=lerp(0.8,0.3,m'), 주축 스냅 e, 데드존 0.15 | 마우스 dx → `lookYaw`(rad)를 **각속도 평활 없이** `aimForward` 에 바로 Y축 회전. 데드존·bias 응답곡선·주축 스냅·α 평활은 **마우스에 적용하지 않음** | 마우스는 위치 입력이라 원본 자이로처럼 직접 각도에 대응. 스틱 응답곡선은 "스틱 기울기 → 속도" 변환이라 마우스에는 의미가 없음 |
| 오른쪽 스틱 y → 피치 속도 → 누적각 s(+0x150c) += 속도·57.29578·bias(t,0.45) 기울기 | 마우스 dy → `lookPitch`(rad)를 **도 단위로 s 에 직접 더함**(bias 기울기 곱 없음). 그 뒤 원본 그대로 ±90 클램프 → `pitchAngleToP(s−75, gk=0, stick=1)` → s += 보정량 → `p += r·(pT − p)` | 원본 자이로도 자세 절대각을 s 에 더하는 꼴(§6.9). 스틱 매핑(gk=0, stick=1) 곡선과 범위 −28..+44 는 원본 그대로 |
| p 추종 비율 r(+0x168) += (1−r)·\|y\|·0.2 (\|y\| = 스틱 세로 크기) | \|y\| 대신 `min(|Δs°| / pitchMax(0)=1.8, 1)` (그 프레임 Δs 를 내는 데 필요한 스틱 세로 크기, 감도 0 기준) | 마우스에는 스틱 크기가 없어 등가 크기로 환산 [웹 선택]. r 은 리셋 0.2, 재시작 1.0 은 원본 그대로 |
| 감도 세이브 0..20 → k=(v−10)/10, yaw 4+k·(3\|1.6)°/f, pitch 1.8+(k\|0.8k)°/f | 설정 `splatoon3.camera.sens` = UI −5..+5(0.5 단위), k = sens/5. 마우스 yaw = 0.15°/px · yawMax(k)/yawMax(0), 피치 = 0.15°/px · pitchMax(k)/yawMax(0) (× `mouseScale`) | 원본 감도 단계의 **비율**과 **yaw:pitch 비(=pitchMax/yawMax, k=0 에서 0.45)** 를 그대로 유지. 기준 0.15°/px 는 "감도 0 스틱 최대 yaw 4°/f = 240°/s 를 마우스 1600px/s 에" 맞춘 웹 선택(px 단위는 원본에 없음). DPI 차이는 `splatoon3.camera.mouseScale`(기본 1) |
| IsReverseLR / IsReverseUD (세이브 +0x4002/+0x4001, 스틱에만, 0x71024a73b8) | `splatoon3.camera.invertX` / `invertY` ("1"/"0") 를 마우스에 적용 | 원본은 자이로에 반전을 안 걸지만 웹에는 마우스뿐이라 스틱 반전 설정의 의미로 둠. 원본 특이점(차이값 = 원시 − 반전 후 지난값)은 주축 스냅 입력이라 마우스 경로에는 없음 |
| FOV 비율 clamp(FOV/55, 0, 1) 를 피치 속도에 곱함(yaw 는 [추정]) | lookYaw·lookPitch 둘 다에 곱함 | 피치는 원본 그대로, yaw 는 문서 §8 추정과 같게 |
| 자이로(자세 절대 피치 + 각속도 yaw, 작은 움직임 억제) | 없음 | 마우스가 대신함. 자이로 경로는 원본 판독-부분 |
| 왼쪽 스틱 | WASD, 대각선 길이 1 로 정규화(`client/input.ts` 그대로) | 응답 곡선(\|v\|^4 등)은 physics 가 적용 |
| 감도·반전 설정 UI | localStorage 만(설정 화면 없음). `InputDevice.setSettings()` 로 바꾸면 저장 | UI 는 범위 밖 |

부호 규약: `lookYaw` 양수 = 원본 rotateY 양의 방향(+Z → +X) = 오른손 Y-up 에서 왼쪽 회전. 마우스 오른쪽(dx>0) → 음수(오른쪽 회전). `lookPitch` 양수 = 위. 원본 스틱 오른쪽(x>0) → 음의 각속도와 같은 방향입니다(좌표계 좌우 부호는 원본에서 [미확정], three 오른손 좌표계로 봄).

### 2.2 미구현·단순화 (원본 기능 중 연습장 범위 밖이거나 입력이 없는 것)

| 항목 | 처리 | 근거 위치 |
|---|---|---|
| 붐 질의 1(피벗 근처)·전진 오징어 계수 +0x14ec | 생략 → 질의 2 시작 오프셋 = 0.8 고정(+0x14ec = 0 일 때 원본 식과 같은 값) | 2150~2860행 |
| 복귀 속도의 `bVar9` 항(\|이동량\|·0.5) | 0 으로 둠 [조건 미확정] | 2970~2984행 |
| 본체+0xad0 > 0 일 때 이동량 항 | 생략(필드 의미 미상) | 3029~3040행 |
| 충돌 밀림 오프셋 +0x144..+0x14c (본체+0x210 누적 변위 스프링) | 0 (추종은 완전 즉시) | 436~498행 |
| 대체 리그 7종(NiceBall·Jetpack·IkuraShoot·다운·GrindRail·Pipeline·+0x1918), +0x1550/+0x1570, 다운·수몰(+0xdf0/+0xe0c), 슈퍼점프(DokanWarp), 사망 메시지, 연출 모드 1, 오징어 벽 자동 회전(+0x14e8), 경사 거리 보정(+0x13c < 0.6414) | 생략 — 연습장 1인에서 발생 조건 없음 또는 의존 컴포넌트 없음 | §6.2, §7 |
| 수직 추종의 특수 목표(0.6/0.2/0.03/0.1/0.3, SuperLanding 0.025, DashPanel) | 생략, +0x744/+0x782 플래그 = 0 (q = −0.22) | 1660~1720행 |
| 플레이어 조작 불가 시 p → 0 복귀 등 | 항상 조작 가능으로 봄 | 4940~5050행 |
| sead 사인표 | yaw 회전·고각 회전에 `Math.sin/cos` 사용(표 최대 오차 7.5e-5). 조준 방향 0x7102551fe0 은 원본도 cosf/sinf | camera_feel §4.3 |
| 바닥 법선 추종 0x7101252ff0 | 선형 보간 후 정규화로 근사 | 312행 |
| 카메라 쉐이크 | 계산은 fx 담당. `camera.userData.shakeOffset`(월드) 를 위치·주시점에 같이 더하는 연결점만 둠 | shake_rumble §3.2a |
| 렌더 보간 | 직전 스텝과 alpha 선형 보간(웹) | DESIGN §3 |

### 2.3 형상 질의 근사

원본 질의 형상·반경·필터는 [미확정]입니다(player_camera.md §6.8). 웹: `world.collision.sweepSphere(시작, 끝, 0.2, Layer.Ground)`, 적중 거리 = `t·|끝−시작|`(원본 Q+0x54 와 같은 의미), 법선은 `hit.normal` 부호 반전을 원본 hitN 으로 씀. 반경 0.2 는 near 와 같게 둔 웹 선택(근평면이 벽을 덜 파고들게), 레이어 Ground 만은 [추정](맵 오브젝트·표적에 카메라가 걸리지 않게; 원본 충돌 태그 22 `SplKeepOutPlayerAndCamera` 는 지형 쪽). `BOOM_PROBE_RADIUS`/`BOOM_PROBE_MASK` 로 export.

### 3. 미확정·추가 분석 필요

| 항목 | 풀리는 곳 |
|---|---|
| 사람 FOV 목표 본체+0x6dc (writer 미발견, 55 로 둠) | 플레이어 본체 생성자·파라미터 적용 함수에서 +0x6dc 쓰기 |
| 슈터 조준 피치 곡선(InkActionShooter+0x2a0 파라미터 객체) — 기본 곡선과 다를 수 있음 | PlayerInkActionShooter 생성자/초기화에서 +0x2a0 writer, 객체 vtable 0x7105633c30 계열의 타입 이름 |
| 복귀 속도 `bVar9` 조건 | cam_main_full.c 2960~2985행 해당 asm |
| 붐 질의 형상·반경·충돌 필터 | 팩토리 0x71024d5c6c, 형상 준비 0x7103a66ea4 |
| FOV 가 수직각인지 | sead::PerspectiveProjection 설정(0x7101016d0c 이후) |
| 본체+0x1cc 의미(웹은 physics `surfN.y` = 본체+0x1c8 의 y 로 봄) | physics player_state.md 표면 법선 |
| 카메라·플레이어 시스템 순서 | DESIGN §3 [미확정] 그대로 |

### 4. 검증

- `tests/camera_rig.test.mjs` (9): 리그 끝점·표 값·C1 연속·끝 기울기·고각·카메라 위치가 `web/tools/camera_rig.py selftest`/`table`/`camera_pose` 출력과 1e-4~1e-6 안에서 일치. `pitchAngleToP`(−28→−1, 0→0, +44→1, 단조, 보정량 12/−6, 중간값 3개 일치), 감도 속도(2.4/4/7, 1.0/1.8/2.8), bias(0.5,0.8)=0.5^0.3219, 조준 곡선 끝점(−70/5/75)과 회전 방향.
- `tests/camera_system.test.mjs` (8): 정지 시 카메라 = 리그 위치(0, 3.1376, −6.2418), 수평 즉시·주시점 y 0.25 비율 지연, lookYaw 부호, 피치 끝(s 44/−28, 조준 75°), 오징어 가중치 0→0.9 접지 14·공중 67 프레임(`camera_rig.py altrig` 와 일치), 오징어 FOV 60·거리 6.8·높이 1.45, 벽 회피(첫 프레임부터 줄고 벽 − 반경에서 멈춤, 이동 시 천천히 복귀), 마우스 대응식 비율.
- 헤드리스(Chrome, 개발 서버): 콘솔 오류 없음, three 카메라 = core 카메라, 조준 입력 주입(yaw 30°, s +20°) 후 p 0.5365·조준 43.8°·붐 질의 동작 확인. physics 가 shared `player` 를 아직 쓰지 않아 원점 기준으로만 확인.
- 원본 실행 대조는 없습니다(카메라 메인 함수 에뮬 미실시).

### 5. 조정 요청

1. **[physics] shared `player` 필드**: 카메라는 `core/camera/index.ts` 의 `PlayerLike` 이름으로 읽습니다 — `pos`(+0x10), `facing`(리셋 방향, 원본은 본체+0x34), `floorN`(+0x180), `surfN`(+0x1c8, y 가 +0x1cc), `vy`(+0x73c), `jump3d`(+0x750, y 사용), `vel`(+0x114), `airFrames`(+0xc0), `airRatio`(+0xdc), `state`(상태 번호 → Sq 판정), `respawns`(바뀌면 재시작 리셋, 원본 isRestart=1). 현재 PlayerState 와 같은 이름입니다. 추가로 본체+0xcf0(형태별 주시점 추가 높이)을 `formHeight` 로 주면 리그에 더합니다. 카메라 상대 이동에는 shared `camera.rigForward`(원본 본체+0x538 = 카메라 +0x1a4 사본, 0x7102458630)를 쓰면 됩니다.
2. **[weapon]** 탄 조준 = shared `camera.aimDir`(0x71024aff7c 결과, 흔들림 전). 무기별 곡선이 확정되면 `aimPitchDeg(camera.pitchNorm, curve)` + `aimDirection(camera.rigForward, rad, out)` 로 직접 계산 가능(core/camera/index.ts export).
3. **[fx]** 카메라 쉐이크는 `ctx.camera.userData.shakeOffset = {x,y,z}`(월드) 로 넘겨 주세요. 카메라 뷰가 마지막에 위치·주시점에 같이 더합니다(원본: 위치에 더하고 회전 불변).
4. **[조정] `core/input.ts` 주석**: `lookPitch` 의 의미를 "피치 누적각(+0x150c) 변화량(라디안, 위 +)"으로, `lookYaw` 를 "양수 = +Z→+X(왼쪽) 회전"으로 적어 주세요. DESIGN §6 마우스 행 비고에 "대응식 docs/impl/camera.md §2.1" 링크 추가를 제안합니다.
5. **[조정] 시스템 순서**: 지금 순서(camera → player)에서는 카메라가 직전 스텝의 플레이어 위치를 따라가 1스텝 늦습니다. 원본 순서 근거는 없으나, 플레이어가 카메라 +0x1a4 사본을 매 프레임 읽는 구조(0x7102458630)와 맞추려면 현재 순서 유지, 표시 지연을 없애려면 player 뒤로 옮기는 것을 검토해 주세요(결정은 조정자).

</details>
