# 정지 상태 마우스 시점 뒤돌기·후행 보정 분석 — 2026-10-03

## 1. 기능 개요와 사용자에게 보이는 동작

사용자 조건은 **“그냥 가만히 있는 상태로 시점만 변경할 때”**다. 걷기·벽 타기·변신·Esc/Alt+Tab을 실제 원인으로 가정하지 않았다. 현재 웹 소스를 읽고 실행해 다음을 구분했다.

| 증상 경로 | 이번에 확인한 것 | 수준·실제 사건 판정 |
|---|---|---|
| 큰 수평 입력 뒤돌기/반대 보간 | 한 fixed step에 −210°를 전달하면 같은 시작/종료 방향의 **+150° 최단 경로**로 렌더가 보간한다. 5step catch-up이면 그 전 방향 이력도 사라져 큰 endpoint로 즉시 보인다 | [웹 판독]+[웹 실행], 입력 조건부 재현. 사용자의 실제 dx/설정/프레임 간격은 [미확정] |
| 손을 멈춘 뒤 수직 시점 변화 | ds0에서도 `p += (targetP−p)*pFollow`. 기본 설정의 dy−200 한 번 뒤 화면 고각이 추가15.983365° 이동했다 | [웹 판독]+[웹 실행], 실제 현재 구현의 후행. 사용자 사건과의 일대일 대응은 [미확정] |
| atan2의 ±π 숫자 경계 | dx10씩240step의 한 바퀴에서 scalar yaw는 −π/+π 경계를 넘지만 실제 시선은 step당 최대1.500004°로 연속이다 | [웹 실행], 이 조건의 숫자 wrap은 뒤돌기 원인이 아님 |
| 평지 정지의 원본 자동 yaw | 일반 평지/속도0/특수 gate 비활성에서 원본 auto-yaw 계수는0. 현재 웹 input은 특수 auto-yaw를 호출하지 않는다 | 기존 원본 [판독] 재사용, [원본 제어 경로](mouse_original_controls.md). 실제 사건에 특수 정책을 붙이지 않음 |

**웹 코드·impl·original은 수정하지 않았다.** 수정 지시 요약은 [port/mouse_camera](../port/mouse_camera.md), 입력 수명은 [mouse_input_lifecycle](mouse_input_lifecycle.md).

## 2. 분석 대상 원본·버전·자료 위치

Splatoon 3 v0의 Lby_Lobby00 1인 스플래시슈터. 이번 재현은 현행 웹의 정지·사람 형태·평지 법선(0,1,0)이다. 실제 마우스 이벤트·저장 설정을 사용자 PC에서 수집한 것은 아니다.

원본 중복 확인은 SHARED.md/FUNCS.tsv와 `decomp_index.py --no-build 24d9ae8 24d6e84 24d6598 24e0178 24e64f0 1252ff0 1017434 3589d74`로 했다. 원본 피치/기저/리그와 기존 Unicorn 표본은 재사용했다. 아래 Node 결과를 원본 [실행]으로 계상하지 않는다.

- 현재 입력 [client/input.ts](../../games/splatoon3/client/input.ts), 루프 [client/app.ts](../../games/splatoon3/client/app.ts).
- [core/camera/camera.ts](../../games/splatoon3/core/camera/camera.ts), [pitch.ts](../../games/splatoon3/core/camera/pitch.ts), [native_math.ts](../../games/splatoon3/core/camera/native_math.ts), [client/camera/index.ts](../../games/splatoon3/client/camera/index.ts).
- 원본 `0x71024e0178` 입력, `24e64f0` 피치 매핑, `24d6e84` 리그, `24d9ae8` 최종 출력. 주소는 기본0x7100000000을 포함해 해석한다.
- 자료: `analysis/mouse_camera/render/view_probe.mjs`, `view_execution.json`, `view_stdout.json`, `commands.md`. 각 실행 결과에 현재 source SHA256을 저장했다.

## 3. 진입점과 전체 호출 흐름

```text
mousemove (locked만 허용, client/input.ts164)
 → dx/dy += movementX/Y (166~167)
 → app.frame: 최대5 fixed step, 매 step input.sample() (app.ts62~70)
 → sample: mouseToLook(누적량), 즉시 dx/dy=0 (input.ts113~114)
 → PlayerCamera.step/input (camera.ts218/273)
 → yaw 전량 rotateY + pitch s/p 갱신
 → rig → verticalFollow → boom → finishOutput/basis (480)
 → renderer: q(prevBasis) → q(nowBasis), slerpQuaternions (client/camera/index.ts27~29)
```

원본은 스틱/자이로 입력이며 마우스 픽셀 누적은 없다. 원본의 입력 계수·피치·리그를 웹 mouse delta와 연결한 방식 및 렌더 보간은 웹 설계다.

`out.yaw=atan2(aim.x,aim.z)`(camera.ts482)는 출력 숫자다. 현재 입력·렌더의 다음 회전 계산은 그 scalar를 선형 보간하지 않고 방향 벡터와 기저/쿼터니언을 사용한다. 따라서 숫자의359° 차이만 보고 물리적으로359° 돌아갔다고 해석하지 않는다.

## 4. 구조체·필드·상수·열거형 표

| 필드·상수 | 단위/초기값 | writer → reader | 확인 범위 |
|---|---|---|---|
| InputDevice.dx/dy | 이벤트 누적px, 0 | onMouseMove166/167 → sample113/114 | 실제 웹 실행. finite/상한 검사는 없음 |
| MOUSE_BASE_DEG_PER_PX | .15°/px | input.ts8 → mouseToLook61~63 | 웹 선택값, 원본 상수 아님 |
| settings.sens/mouseScale | 기본0/1, loadScale .05..20 | localStorage 또는 setSettings → mouseToLook | 테스트 입력값. 실제 사용자의 저장값은 미수집 |
| Camera.out.aimForward | 수평f32 벡터 | reset/input → rig/finish/탄/이동 | 정지 fixture에서 입력에만 yaw 반응 |
| Camera.s | 도, reset0 | ds/clamp/correction → pitchAngleToP | 원본 C+150c 소비식과 연결한 웹 adapter |
| Camera.pFollow | reset .2(일반)/1(restart) | ds의 yEq로 증가 → p 추종 | 작은 입력/무입력 상태에서도 남는 상태 |
| Camera.p | f32 정규피치 | mix(old,target,pFollow) → rig/aim | mouse stop 뒤에도 변함 |
| prevBasis/currentBasis | X/Y/Z 3열 | 매 fixed step 앞에서 snapshot → renderer quaternion | 엔드포인트만 저장, 그 사이 누적 회전수/부호의 경로는 저장 안 함 |
| STEP/MAX_STEPS | 1/60초 / 5 | app.ts18~19 → frame loop | 마우스 데이터와 dropped time을 같은 비율로 줄이지 않음 |

## 5. 상태 전이와 전체 수명

locked 중 여러 mousemove가 한 fixed step까지 쌓인다. 첫 `sample`이 전체량을 소비하고 이후 catch-up sample의 yaw/pitch는0이다. core는 각 step 시작에 prevBasis를 currentBasis로 바꾼다. 따라서 **첫 step에서 큰 회전을 하고 나머지4step이0이면, 마지막 렌더의 prev/current 모두 회전 이후 방향**이다. alpha0/0.5/1 모두 같은 endpoint를 보였다.

수직 입력은 별도의 상태다. `s`는 입력 후 저장되고 `p`는 그 s로 구한 targetP를 여러 step에 걸쳐 따라간다. `ds=0`은 pFollow나 p를 reset하지 않는다. 정지 상태에서도 “마우스를 멈췄는데 시점이 더 움직임”이 가능하다. 그 자체가 외부 액터가 카메라를 강제로 돌렸다는 증거는 아니다.

blur/잠금 해제/KeyR에는 별도 수명 위험이 있다([입력 수명](mouse_input_lifecycle.md)). 사용자가 이 상황을 보고하지 않았으므로 이번 정지 마우스 증상의 직접 원인으로 승격하지 않는다. 실제 respawn count 변화와 최초 player 획득 외에는 평상시 step이 player.forward를 따라 yaw를 reset하지 않는다.

## 6. 계산식·조건·상세 의사코드

### 6.1 큰 yaw와 최단 경로 보간 [웹 판독]+[웹 실행]

```text
k = clamp(sens/5, −1, 1)
yawPerPxDeg = .15 * mouseScale * yawMaxDeg(k)/4
g = clamp(FOV/55, 0, 1)
coreDeltaYawDeg = −sumMovementX * yawPerPxDeg * g * invertSign
```

일반 사람 FOV55에서 회전180°에 필요한 누적량:

| 설정 | yaw°/px | 180° 임계 |
|---|---:|---:|
| sens0/scale1(기본) | .15 | 1200px |
| sens0/scale20 | 3 | 60px |
| sens5/scale20 | 5.25 | 240/7≈34.285714px |

180°보다 큰 회전은 최종 방향 두 개만으로 입력이 택한 긴 경로를 표현할 수 없다. **현재 actual Three slerp**에서 다음을 재현했다.

| 누적dx/설정 | core raw 회전 | 최종 수평 방향차 | alpha .25~.75의 진행 방향 |
|---|---:|---:|---|
| 1200/기본 | −180° | −180° | 반구 선택은 경계값으로 보관 |
| 1400/기본 | −210° | +150.000015° | raw 입력과 반대 방향 |
| 1800/기본 | −270° | +90° | raw 입력과 반대 방향 |
| 70/scale20 | −210° | +150.000015° | 동일 |
| 40/sens5·scale20 | −210° | +150.000015° | 동일 |

큰 raw delta가 **실제로 사용자에게 들어왔는지**, 정상 빠른 움직임인지·OS/브라우저 이상 값인지·누적/설정 문제인지는 이번 결과로 확정하지 않았다. 임계는 현재 코드의 조건부 값이며 사용자의 감도를 기본값이라고 단정하지 않는다.

### 6.2 수직 입력 중단 후 후행 [웹 판독]+[웹 실행]

```text
ds = f32(f32(lookPitch*57.29578)*g)
yEq = min(abs(ds)/pitchMaxDeg(0),1)
pFollow += (1−pFollow)*yEq*.2
s0 = clamp(s+ds,−90,90)
[targetP,corr] = pitchAngleToP(s0−75,0,false,0,0,true)
s = s0+corr
p = p+(targetP−p)*pFollow  // ds=0이어도 실행
```

기본 설정 dy−200 한 번은 ds≈13.500001°, pFollow≈.36, targetP≈.369985이다. 첫 p≈.133195, 다음 .218439→.272996→…→.369985. 실제 카메라 뷰의 첫 고각 변화8.990624° 뒤, 무입력60step에서 추가15.983365°가 진행했다. 이 수치는 조준 pitch scalar 대신 렌더 카메라의 3D 시선으로 측정했다.

피치 큰 입력에서도 수평 뒤돌기는 재현되지 않았다. requested s=89.49/89.5는 보정 후44, 89.51은44.020004, 90/120은clamp·보정 후45다. 이어 targetP1로 추종한다. 이 특이한 correction은 기존 원본 `24e64f0` 판독을 재사용하며 “자연스럽게” 값45를44로 바꾸지 않았다. dy±200/600/1000/1400/2000을 각각120step 관찰한 수평 heading 변화는0이었다.

### 6.3 확인된 반례·제외 조건

- dx10×240step: scalar ±π wrap1회, 실제 최대 수평 변화1.500004°/step. 일반 wrap을 원인으로 확정하지 않음.
- 정착 뒤600step, mouse0·position0 고정이고 player.forward만 바꿔도 aim/렌더 방향 변화0. 평상시 facing 따라가기나 reset을 재현하지 않음.
- 최종 근접 보정(camera.ts474~479)은 `dot(pos−at,aim)>−.16`이면 aim 반대쪽으로 카메라를 이동한다. 정상 유한 입력에서 카메라가 aim 앞쪽으로 지나가 뒤를 보는 경로를 억제한다. 실제 stage 모든 collision을 이 fixture에서 실행한 것은 아님.

## 7. 애니메이션·이펙트·소리·카메라·에셋 연결

이번 fixture는 ASB/캐릭터·탄·그림자·GPU를 실행하지 않았다. 동적 광원/오징어 변신으로 시점이 바뀐다고 설명하지 않는다. camera.out의 basis/viewForward/aimDir은 실제 웹의 이동·탄·렌더 소비 계약에 쓰이므로, mouse 입력만 수정할 때도 core 조준 방향과 렌더 시선을 함께 검증해야 한다.

shake는 현재 renderer 위치에만 추가하고 회전은 basis로 유지한다. 이번 재현에서는 shakeOffset이 없었다. 따라서 확인된 역방향 보간을 발사 shake 탓으로 돌리지 않는다.

## 8. 다른 기능과의 상호작용

정지 조건의 사용자 보고는 실제 runtime telemetry가 아니다. 움직임이 없더라도 input 누적·렌더 catch-up·피치 추종은 실행된다. 디버그에서 `camera.yaw`의 −180→+180 숫자만 관찰하면 실제 기저가 연속인 경우도 뒤돌기로 오판할 수 있다.

`camera.p/s`는 현행 debug에도 있지만 raw movement·pending dx/dy·settings·step 수·pre/post basis·reset reason은 함께 기록하지 않는다. 이 자료가 없으면 큰 delta, 보간 경로, reset 사건을 같은 증상으로 묶어 확정할 수 없다.

## 9. 웹 포팅 구조와 구현 순서

**아래는 다음 수정 작업의 명세/설계 과제이며 이번에 구현하지 않았다. 원본에 마우스·PC 렌더 alpha 정책은 없다.**

1. **P0 큰 delta→회전 경로 계약:** mouse event raw 값·누적량·감도·시간·FOV·각도·fixed step 수를 재현 로그에 연결한다. 긴 회전은 입력 부호와 전체량을 보존하며 소비 구간과 렌더 구간에 분할해 경로를 유지할 것. endpoint-only shortest slerp로 ≥180° 긴 입력의 진행 방향을 결정하지 않는다. 임의 .x 상한으로 정상 입력을 잘라 없애는 값은 원본 근거가 없다.
2. **P0 mouse pitch adapter:** native s/p 매핑·리그를 유지하면서 마우스 delta와 `pFollow`를 어떤 방식으로 연결할지 명시한다. 기존 스틱 속도 평활 제거와 p의 목표 추종 제거는 다른 선택이다. “마우스 입력 끝=즉시 화면 정지”를 원한다면 mouse adapter/visual sampling의 별도 정책이며 원본 확정값으로 pFollow1을 발명하지 않는다.
3. **P1 입력 수명:** lock/blur/visibility epoch, pending 누적량·hold/release 정리, reset reason 기록을 [입력 수명](mouse_input_lifecycle.md)의 구체 범위대로 다룬다. 사용자 보고의 주원인으로 단정하지 않는다.

검증 기준: stationary 작은 마우스·±π 양쪽·같은 총dx의 여러 이벤트/fixed step 분할·catch-up1~5·sens/scale 조합·pitch stop와 양쪽 경계·잠금 재진입·reset을 분리하고 basis/aim/화면 진행 방향을 확인한다. native rig/basis 기존 비트 fixture를 유지한다.

**2026-10-03 정정:** [player_camera §9](player_camera.md)의 기존 “렌더 보간은 웹 선택(원본 동등성 영향 없음)”은 무조건적 결론으로 사용할 수 없다. 큰 mouse 입력에서 역방향 보간/이력 소실 반례가 있다. 또한 “스틱 속도 평활을 마우스에 적용하지 않음”은 p 목표 후행까지 없다는 뜻이 아니다. impl 본문은 읽기 전용으로 유지하고 이 분석에서 차이를 기록한다.

## 10. 검증 코드·실행 결과·기대값

`node analysis/mouse_camera/render/view_probe.mjs`를 Node24.13.0으로 실행했다. 실제 source 모듈의 `mouseToLook`, `PlayerCamera`, `createCameraView`, 실제 Three CPU Matrix/Quaternion/PerspectiveCamera를 사용했다. **268 assertion 통과**, 불일치0. fake player/World.shared/ClientContext, collision=null, 평지/정지 입력 공급. original Unicorn·원본 실기·브라우저 mousemove·GPU 픽셀 검증이 아니다.

입력 agent의 `node web/tools/mouse_input_lifecycle.mjs`는 InputDevice와 저장된 actual app frame callback 30건을 fakeDOM/호스트 fixture에서 실행했다. 이 결과는 원본 [실행] 건수에 합산하지 않는다.

실제 명령·실패는 `analysis/mouse_camera/render/commands.md`, 각 결과 JSON에는 코드 SHA256과 조건을 저장했다. 사용자 실제 이벤트를 스텁으로 만들어 확정한 것이 아니라 **지정한 입력에 현재 웹이 어떻게 반응하는지** 확인한 것이다.

## 11. 미확정 사항과 추가 분석에 필요한 근거

| 남은 질문 | 시도·불가 이유 | 다음 확인 |
|---|---|---|
| 사용자의 실제 sudden turn 단일 원인 | stationary 조건은 확보, 실제 raw delta·저장 설정·frame/reset 기록 미수집 | mousemove movementX/Y/시간, pending sum, settings, FOV, sample 각도, step count, aim/pre/post quaternion/reset reason을 같은 사건으로 기록 |
| 큰 delta의 발생원 | 현행 코드가 무상한 소비함은 확인했으나 실제 브라우저/OS 데이터를 확인 안 함 | 원래 실행 브라우저의 실제 이벤트 trace. 특정 기기/브라우저 버그로 단정 금지 |
| 평지 정지 이외의 전체 stage 동작 | fixture는 position·floor normal 고정/collision null | 실제 Lby floor/Phive output과 two query·cameraNative를 동일 사건으로 기록 |
| 원본 B9314 자동 yaw 상위 의미/wholeframe | 기존 asm에서 소비 조건 확보, 현 웹 일반 입력에는 없음 | [원본 제어](mouse_original_controls.md) §11의 writer/scene 경로. 사용자 증상과 별도 |
| mouse adapter 최종 제품 정책 | 원본에 PC 마우스가 없음, 현재 정책의 반례만 확인 | 위 §9의 입력량·진행 방향 보존/수직 정지 정책을 구현 후 실제 조작 검증 |

고정 원본 inventory 질문을 웹 재현으로 승격하지 않는다. 기존 CAM01/02의 원본 리그/기저 계산 확인과 이번 마우스 전체 체감 문제의 완료는 별도다.
