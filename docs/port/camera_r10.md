# 카메라 r10 원본 근거 웹 반영 — 2026-10-04

## 1. 기능 개요와 체감 변화

사용자의 “카메라 분석한거 web에 적용” 요청으로 입력·피치, 투영, 상태 소비, 쉐이크를 병렬 이식했다. 마우스 감도 계산과 누적각→피치 곡선은 원본 f32를 사용한다. 기존 큰 마우스 회전의 방향·회전수 보간과 입력 중단 후 후행 방지 정책은 보존했다.

이 문서는 구현 기록이다. 원본 분석률 **93/106=87.74%**, 구현 고정 점검률 **2/7=28.57%**는 그대로다. CAM03~07에는 실제 공급자·전체 경로가 남아 있으므로 작은 함수 이식만으로 완료로 바꾸지 않았다.

## 2. 원본·웹·자료 위치

Splatoon 3 v0, Lby_Lobby00 1인 스플래시슈터. [카메라 r10 분석](../camera/analysis_100.md)과 아래 확정 근거를 재사용했다. 원본 파일·웹 에셋·package.json·이동/무기 로직은 수정하지 않았다. commit/push 없음. 빌드 출력은 `web/dist/`에 생성했다.

재현·명령·실패·SHA·브라우저 기록은 `analysis/port_camera_r10/`에 저장했다. 기존 r10 분석 결과·동결 분모를 덮어쓰지 않았다.

## 3. 호출 흐름과 실제 연결

```text
mouse px → 기존 InputDevice/sample → f32 감도·pitchAngleToP → PlayerCamera
명시적 PadState.cameraStick → snap/bias/yawVel/pitchVel → 동일 PlayerCamera
player.displayBinding(supported) / display.hidden → B7a0 붐 소비
명시적 cameraNative.control/autoPitch/waterFrames/waterHeight → 상태 소비
ELink nonempty CameraRumbleName → admission gain → instance tick → 종료필터 → world offset
PlayerCamera basis/pose → CameraView → logical Projection/inverse → 렌더·그림자/depth 소비
```

브라우저의 현재 입력은 마우스다. 새 `cameraStick`은 명시적 gyro-off 입력 계약이며 브라우저 gamepad 기능을 추가한 것은 아니다. core 시스템 순서는 그대로다.

## 4. 필드·정밀도 계약

| 경로 | 원본 대응·반영 |
|---|---|
| `stick.ts` 상태 | C180/184 delta 필터, C188 저장 하한−1·pow 지수 하한0, 길이 복구 |
| `pitch.ts` | yaw/pitch 감도 상수 비트, 24e64f0 f32·상한180·베지어 항 합산 순서 |
| `PadState.cameraStick` | post-remap 일반 스틱 입력·raw delta·감도/tilt/cap/state를 명시 공급 |
| `cameraNative.control` | 전체24c99f0 입력. 없으면 기존 ordinary 웹 adapter |
| `cameraNative.autoPitch` | 별도 자동복귀 조건과 이미 생산된 native s9 rate. blocked bool로 대체하지 않음 |
| `cameraNative.waterFrames/Height` | Bdf0/Bdf4, followpoint C124와의 차를 B180 법선 목표에 적용 |
| `Hit.nativeSeparation` | raw point일 때만 query1 bit0=0의 point+separation×normal; 이미 교정된 웹 접점에는 생략 |
| `CameraProjectionState` | logical matrix, ctor aspect4/3, viewport-valid 래치·행렬 뒤 aspect 저장 |
| `ShakeParameterRef/owner/serial` | generation·재사용 slot·stale handle, admission gain 래치 |

## 5. 초기화·갱신·종료

카메라 reset은 새 스틱 필터·속도를 비운다. 입력이 공급되면 C168은 deadzone 이전 remapped Y로 갱신하고, 스냅/길이 응답/속도/누적각/피치 매핑을 소비한다. 마우스 픽셀을 스틱 속도로 간주하지 않는다.

법선은 원본 표 slerp 뒤 `length>.001 && abs(length−1)>.01`일 때만 길이를 교정한다. B7a0는 검증된 supported 표시 producer에서 읽으며 wallCling으로 대체하지 않는다.

쉐이크는 계산→루프 owner 검사→counter 증가→루프 reset→finished 검사→합산이다. 종료 직전 계산한 샘플도 끝 필터에서 제외될 수 있다. 유한 shake 때문에 시각 이미터 수명을 늘리지 않는다.

## 6. 반영 식·원본 근거

| 적용 | 확정 근거 |
|---|---|
| snap 누산·복원, f32 yaw/pitch 최대·속도·누적, 피치각 매핑 | [r10_input_response §4~6](../camera/r10_input_response.md), 기존 player_camera §6.5, 원본 회귀 fixture |
| 전체 blocked·별도 auto-pitch·WaterFall 법선 | [r10_state_producers §6.2/6.4/6.10](../camera/r10_state_producers.md) |
| query1 접점 교정과 query2 법선 구분 | [r10_boom_stage_fade §7](../camera/r10_boom_stage_fade.md) |
| logical projection·후행 aspect·View row layout | [r10_module_projection §6](../camera/r10_module_projection.md), [r10_render_projection §3~6](../camera/r10_render_projection.md) |
| Hermit 곱/합 순서, `curve*(gain*Scale)`, owner/serial/종료 | [r10_shake_shooter §4~8](../camera/r10_shake_shooter.md) |

생산자가 없는 상태를 웹 bool로 임의 활성화하지 않았다. Bad0 전체 프레임 공급이 남아 있으므로 단순 “사격 후82프레임” 타이머도 만들지 않았다.

## 7. 렌더·이펙트 연결

일반 renderer에 **logical** projection을 공급한다. device posture/NVN 부호를 혼용하거나 미확정 GPU 화면을 이유로 X 반전을 넣지 않았다. projection inverse와 View12 f32 rows도 갱신해 shadow/depth 소비를 유지한다. `app.ts` resize의 즉시 aspect/Three 재계산을 제거하고 CameraView가 행렬 계산 뒤 새 크기를 래치한다.

일반 스플래시슈터 발사·표적 명중의 빈 CameraRumbleName은 admission에서 제외한다. 진동이 없다는 근거를 총구 이펙트·탄 spread·효과음 부재로 확대하지 않는다.

## 8. 웹 adapter와 미연결 공급자

viewport 래치는 현재 **render frame** adapter이며 원본 module tick와 동일한 scheduler 구현은 아니다. Three 쿼터니언 보간/역행렬·마우스 px 정책은 웹 선택이다. 실제 SDK tanf와 JS Math.tan은 별도 경계다.

D/B210/e0c, formHeight/B6dc, 상태 리그·gyro absolute pose, Water contact/timer의 live player writer, Bad0 전체 frame, Fade metadata→model/shader binding, native LP/typed filter/초기 지형 pose는 아직 추가 연결이 필요하다. 새 상태 소비 API가 실제 Lby 이벤트를 자동 생산한다는 뜻은 아니다.

쉐이크는 native SafePtr 소비를 지원하지만 실제 Module capacity/초기serial/listener+1c8·event-owner producer는 미연결이다. dynamic pool·initialserial0·shared camera.pos·visual XHandle lifetime fallback을 웹 adapter로 남겼다.

## 9. 다음 우선 반영

| 우선 | 작업 | 남은 경계 |
|---|---|---|
| P0 | 실제 physics→camera spring/formHeight/상태 공급 | B1f8을 B210으로 대입하지 않기, 타이머 variant/stackbyte 실제 공급 |
| P0 | 실제 지형 native query 계약 | Default/Same/Other·Entity LP·typed tag, 최초 pose→native writer 연결 |
| P0 | Module pose·SDK math·최종 화면 대조 | gyro/선택 pose 공급, SDK tanf·실제 HDR target/window/GPU 부호 |
| P1 | 모델 카메라 Fade | 별도 FadeType metadata와 material `fade_dither_alpha`, GrindRail 파라미터 혼용 금지 |
| P1 | 실제 ELink owner/listener/pool 공급 | 현재 소비 수학과 실시간 event/handle 수명 구분 |

## 10. 검증·실제 명령·실패

| 검증 | 결과·경계 |
|---|---|
| 입력 신규 원본 포팅 fixture | 1,280사례/3,328필드, native SDK 호출·TS arithmetic 전비트 일치. production JS math도 이 표본은 모두 일치. 전체 입력/scene 아님 |
| blocked/WaterFall 기존 원본 출력 | 2,175반환 +512법선 triple 모두 일치. 새로운 분석 건수로 재계상하지 않음 |
| 투영 기존 원본 출력 | 421×16=6,736 f32, captured SDK tanf 입력이면 모두 일치. runtime JS adapter는380/421 완전일치·139필드 차이·최대 관측19ULP. 일반 오차상한 아님 |
| 쉐이크 원본 포팅 fixture | 162 trace/6,318고유tick의 offset·counter·valid·finished 비트 일치, whole original selected module/instance 수명. 전체 Lby 이벤트 공급 아님 |
| 기존 native camera 회귀 | 기존1,031 함수/블록 fixture 유지·통과 |
| `npm run typecheck`, `npm test`, `npm run build` (`web` cwd) | typecheck PASS, 전체359/359 PASS, build PASS |
| 실제 브라우저 | 화면·1280×720/900×900 canvas와 복구 확인. 실제 마우스/오징어 조작은 pointer lock 거부로 미검증 |

첫 전체 테스트는351/352로 실패했다. 새 Fx 통합 테스트의 JSON 직접 import가 Node24 attribute 오류였고, 기존 방식의 esbuild bundle 테스트로 고친 뒤359/359를 통과했다. 감도 f32 변경으로 마우스13.5/-1.35 기대가 달랐던 검사는 원본 `bits3FE66666`×기존 px 정책으로 정정했으며 tolerance는 그대로다.

부모의 첫 fixture 명령은 잘못된 cwd의 `.venv` 경로로 실패하고 fixture ENOENT가 이어졌다. 올바른 root cwd에서 생성 후 통과했다. 입력 담당의 첫 pitchMap1ULP는 raw 명령의 항 묶음으로 정정했다. 브라우저 IAB 생성 timeout 후 기존 Chrome 탭을 사용했으나 pointer lock은 `WrongDocumentError`로 거부됐다. 이 실패를 조작 성공으로 기록하지 않는다. texture-unit 경고도 관측했으며 카메라 작업에서 그래픽을 수정하지 않았다. 상세는 `analysis/port_camera_r10/commands.md` 및 담당 하위 기록이다.

## 11. 완료 판정과 변경 이력

2026-10-04: 분석된 camera 소비 계약을 웹에 반영하고 MD를 갱신했다. 일부 원본 함수 회귀 성공은 GPU/화면/전체 tick 100% 동등을 뜻하지 않는다. 원본 분석 완료율과 고정 implementation62/카메라7 분모는 유지했다.

[impl/camera](../impl/camera.md), [구현 점검표](implementation_status.md), [카메라 원본 분석](../camera/analysis_100.md)의 웹 반영 기록이 현재 이 문서와 대응한다. 후속 대상은 §9의 실제 공급자 연결이다.
