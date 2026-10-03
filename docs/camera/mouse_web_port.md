# 정지 마우스 시점 웹 반영 — 2026-10-03

## 1. 기능 개요와 사용자에게 보이는 동작

사용자가 우선순위 1을 web에 반영하도록 요청해, **가만히 서서 시점만 조작할 때** 재현된 경로를 수정했다. 큰 마우스 회전을 반대쪽 최단호로 표시하던 보간, catch-up의 회전 이력 소실, 마우스를 멈춘 뒤 피치의 후행을 처리한다. 이 문서의 검증 수준은 **[웹 실행]**이다.

사용자의 실제 raw delta·감도·프레임 기록이 없으므로 그 사건의 단일 원인은 **[미확정]**으로 유지한다. 원본 스틱/자이로에는 mouse px·pointer lock이 없어 PC adapter 정책을 원본 확정값으로 부르지 않는다. 원본 분석 inventory의 확정 수를 올리지 않았다.

## 2. 분석 대상 원본·버전·자료 위치

원본 근거는 Splatoon 3 v0, Lby_Lobby00 1인 스플래시슈터의 기존 [player_camera](player_camera.md)·[시점 급변 분석](mouse_view_jumps.md)·[입력 수명](mouse_input_lifecycle.md)을 재사용한다. 새 디컴파일·원본 함수 실행은 0건이다.

변경 소스: [client/input.ts](../../games/splatoon3/client/input.ts), [core/camera/camera.ts](../../games/splatoon3/core/camera/camera.ts), [client/camera/index.ts](../../games/splatoon3/client/camera/index.ts), [신규 회귀 테스트](../../games/splatoon3/tests/camera_mouse.test.mjs). 조정자 연결: [core/input.ts](../../games/splatoon3/core/input.ts)와 [client/app.ts](../../games/splatoon3/client/app.ts).

[원형 before](../../../analysis/port_priority_r4/mouse/view_before.json)·[수정 후 view](../../../analysis/port_priority_r4/mouse/view_after.json)·[입력 및 실제 app callback](../../../analysis/port_priority_r4/mouse/input_after.json)·[commands](../../../analysis/port_priority_r4/mouse/commands.md)에 수치·소스 SHA256·실패와 실행 경계를 남겼다. 기존 분석 결과를 수정 후 정책에 맞춰 덮어쓰지 않았다.

## 3. 진입점과 전체 호출 흐름

```text
locked/focused/visible mousemove → finite movementX/Y 누적
 → app.frame floor(acc/STEP) → sample(남은 step 수)
 → pending/N 소비 → PadState.lookMode="mouse"
 → yaw FOV비율·원본 sead 표 회전 → mouseYawDelta 저장
 → 원본 s→p 보정/곡선, mouse에서 p=목표p
 → 기존 native 리그·붐·최종 기저
 → signed yaw·native 기저 잔차 보간 → three camera
```

게임 시스템 순서는 유지한다. 실제 서로 다른 mouse 이벤트의 시간별 궤적은 복원하지 않으며 프레임의 pending displacement를 균등 배분하는 웹 선택이다.

## 4. 구조체·필드·상수·열거형 표

| 계약 | writer → reader | 현재 의미 |
|---|---|---|
| PadState.lookMode? | InputDevice → PlayerCamera | `"mouse"`이면 displacement adapter. 미지정 pad는 기존 native pFollow 유지 |
| InputDevice.sample(remainingSteps=1) | app → input | pending/N을 소비하고 나머지를 보존. N은 finite 정수≥1 |
| CameraShared.mouseLook | core → view | 이번 step의 입력이 mouse adapter인지 |
| CameraShared.mouseYawDelta | core → view | FOV 비율 적용 후 signed yaw rad. endpoint에서 역산하지 않아 완전한 회전도 보존 |
| prevBasis/currentBasis | core → view | 기존 native X/Y/Z 기저. 원본 reset/퇴화 보존 규칙 유지 |
| focused·locked·visibility | DOM → InputDevice | 세 소유 조건이 유효할 때만 게임 입력을 수집 |
| prevHold | sample → 다음 sample | 입력 취소 뒤에도 한 번 release를 전달하고 이후0 |
| 감도/배율/반전 | 기존 설정 → mouseToLook | .15°/px 기준·원본 감도 비율·축 반전 유지. setSettings도 load와 같은 범위 검증 |

mouse delta 자체에 원본 스틱 최대각이나 임의 magnitude 상한을 추가하지 않았다. sample 전에 설정이 바뀌면 pending delta에 현재 설정을 적용하는 기존 정책은 유지한다.

## 5. 상태 전이와 전체 수명

pending displacement는 fixed step이 없는 렌더 프레임에서 보존한다. N step catch-up이면 각 sample이 남은 pending/N을 소비한다. 기본 dx1400의 5 step은 **−42°×5=−210°**다. 마지막 step의 prev/current에도 마지막 −42° 경로가 남는다. 낮은 렌더 빈도에서 앞선 모든 step을 별도 화면으로 표시하는 것은 아니다.

blur·pointerlockchange·hidden·dispose는 pending dx/dy와 keys/buttons를 지운다. blur 뒤 focus가 돌아오기 전 mouse/keydown은 무시한다. 잠금 상실 뒤 다음 sample은 마지막 hold의 release를 한 번 전달한다. unlocked KeyR는 무시한다. 첫 잠금 요청 클릭은 Fire로 소비하지 않는다. 이 경계 정책은 PC 이식 선택이다.

nonfinite 축은 이벤트 합산에서 제외하되 valid 축은 보존한다. setSettings의 nonfinite 감도/배율은 기존 유효값을 유지한다. finite 설정은 감도 −5..5(0.5 간격), 배율 .05..20으로 맞춘다.

## 6. 계산식·조건·상세 의사코드

원본 yaw 표·s 누적/보정·s→p 곡선·리그는 유지한다. `lookMode="mouse"`에서 **p=F(targetP)**로 즉시 적용한다. 기존 등가 스틱 pFollow가 목표에 계속 따라가던 연결만 우회한다. 미지정 pad는 **p=mix(p,targetP,pFollow)**다.

렌더 회전은 다음 웹 식이다. Y는 월드 Y축 yaw quaternion이며 a는 렌더 alpha다.

```text
yaw = 실제 core에 적용한 signed mouse delta (FOV 비율 포함)
residual = (Y(yaw) · Qprev)^-1 · Qnow
Q(a) = Y(yaw*a) · Qprev · slerp(I,residual,a)
```

±210/270/450/720°가 택한 방향·전량을 Y에서 보존하고 피치·법선·붐 등의 기저 잔차만 최단호로 보간한다. alpha0/1은 이전/현재 기저에 일치한다. scalar yaw의 ±π wrap으로 long path를 재구성하지 않는다.

position은 target의 보간값에 `Y(yaw*a)`로 회전한 이전 relative position 및 최종 relative residual을 더한다. 큰 yaw에서 선형 chord가 플레이어를 가로지르는 문제를 피한다. 렌더 보간 도중 별도의 연속 지형 sweep을 새로 실행하지는 않는다.

## 7. 애니메이션·이펙트·소리·카메라·에셋 연결

camera.aimDir·rigForward·right·viewForward 계약은 유지한다. native 리그와 최종 기저를 이동·탄·renderer가 읽으며 mouse 피치의 목표 p를 같은 fixed step에 소비한다. camera shake는 위치에만 합산하고 quaternion을 보존한다. 사격 이펙트의 emitter 애니메이션 반영은 별도 담당이 처리했다.

## 8. 다른 기능과의 상호작용

reset은 mouseYawDelta를0, mouseLook을false로 초기화하고 prev/current 기저를 맞춘다. native/stick 미지정 pad의 원본 피치 추종을 없애지 않았다. 법선·오징어 FOV·이동 위치·shake 변경과 signed yaw가 함께 있어도 alpha endpoints가 native 출력에 맞는지 검사했다.

일반 ±π 숫자 경계는 원래도 시선이 연속이었다. 이를 뒤돌기의 원인으로 바꾸지 않는다. 사용자 설명에 없는 이동·벽·변신·Alt+Tab을 실제 사건의 원인으로 단정하지 않는다.

## 9. 웹 포팅 구조와 구현 순서

원형 재현값을 먼저 보존한 뒤 input sampling 계약 → core mouse-only p → signed yaw/residual/orbit → 입력 소유 수명 → 신규 회귀를 연결했다. 조정자가 공통 PadState/app 연결을 완료했다.

원본 전체 조작감·원본 GPU 동등성은 별도다. 현재 변경은 확인된 웹 경로의 반영이며 broad CAM 행/원본 분석 퍼센트를 이 부분 검사로 자동 승격하지 않는다. **impl 문서는 수정하지 않고 이 허용된 camera MD에 완료 기록을 남겼다.** 자동 승인 검토가 최초 impl 수정 금지를 이유로 그 갱신을 거절했다.

## 10. 검증 코드·실행 결과·기대값

| 검증 | 결과 | 실행 경계 |
|---|---|---|
| `node --test web/games/splatoon3/tests/camera*.test.mjs` | **42/42 PASS** (기존30+신규12) | 실제 TS core/input/view + Three CPU |
| 기존 view_probe 재사용, mouse adapter 지정 | **268 checks PASS** | 정지 사람/평지 fixture, original/OS/GPU 실행 없음 |
| 실제 InputDevice 및 app frame callback | **30/30 PASS** | DOM·world/render 호스트 합성, callback 소스 타입만 제거 |
| dx1400 한 step partial alpha | 역방향 보간 false | 기존 +150° 최단호의 반대 방향 재현을 제거 |
| dy−200 후60 무입력 | p 변화0, 시선 잔여 **1.9090959e−6°** | 기존 잔여15.9833651°와 비교. f32 잡음을 물리적 후행으로 과장하지 않음 |
| 5 step dx1400 | −42°×5, 마지막 yaw 경로 보존 | 무상한 finite 누적량 전량 |
| ±210/270/450/720° | 각64 render sample 방향·회전 합 통과 | 전체 회전을 endpoint 방향차로만 검증하지 않음 |

신규 테스트 첫 실행은 **8 PASS/4 FAIL**이었다. 네 실패는 무입력 `-0`을 strict `0`과 비교한 테스트였다. 0 허용오차 비교로 수정해12/12 통과했고 동작 기대값은 완화하지 않았다. 최초 잘못된 `web/DESIGN.md`·`.agents` 조회, native_math rotateY 검색의 exit1도 commands에 기록했다. 구현 위치는 DESIGN의 정식 경로 및 weapon/swerve import로 확인했다.

[before/after 수치](../../../analysis/port_priority_r4/mouse/closeout.json). 형검사·전체 게임 테스트·브라우저 통합은 조정자 최종 기록을 따른다. 이 담당의 Node 검증을 실제 사용자 마우스 기기 또는 원본 실행이라고 부르지 않는다.

## 11. 미확정 사항과 추가 분석에 필요한 근거

| 항목 | 남은 이유 | 다음에 볼 곳 |
|---|---|---|
| 사용자의 실제 사건이 어느 경로였는가 | raw movement·감도·render timing 미수집 | 실제 이벤트→sample→basis/alpha trace |
| 실제 OS·브라우저 입력의 체감 | 합성 스트레스 입력과 actual TS CPU 검사 | 실기 마우스 정지 조준·고감도·프레임 지연 대조 |
| 원본 전체 camera 동등성 | 모듈 pose/gyro·native spring/특수 writer 공급은 기존 미반영 | 기존 player_camera/r9 문서의 미확정 표 |
| 렌더 보간 중 모든 지형 접촉 | orbit/residual 표시 경로에 연속 sweep을 추가하지 않음 | 실기 벽/모서리 render 경로와 기존 boom 계약 |

2026-10-03 정정: 이전 분석 MD는 당시 **분석-only/코드 미반영**의 결과로 보존한다. 이번 완료 기록이 mouse adapter 현재 상태를 명시한다. 원본 값으로 mouse 정책을 정당화하지 않았으며 원본 inventory 증가0·commit/push0이다.
