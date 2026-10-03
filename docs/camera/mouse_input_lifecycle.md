# 마우스 시점 입력 수명 — 잠금·누적·고정 스텝 분석

2026-10-03. Lby_Lobby00 1인 연습 웹 구현의 마우스 입력 경로를 조사했다. 사용자 추가 설명은 **“그냥 가만히 있는 상태로 시점만 변경할 때”** 갑자기 뒤를 보거나 의도와 다른 조정이 발생한다는 것이다. 포커스 이탈·벽·이동·변신은 실제 증상의 원인으로 확정하지 않는다.

## 1. 기능 개요와 사용자에게 보이는 동작

[웹 소스 판독]+[웹실행] 현재 입력 장치는 잠금 상태의 `movementX/Y`를 제한 없이 합산하고, 다음 60Hz 고정 스텝 하나에 전량 전달한다. 프레임 안의 두 번째 이후 스텝에는 0을 전달한다. 잠금 상실/blur는 이미 누적한 회전량을 취소하지 않으며, 고정 루프는 잠금 여부와 무관하게 이를 소비한다.

이는 **입력 수명의 확인된 경로**다. 실제 사용자가 보고한 평상시 정지 조준에서 큰 입력이 들어왔는지, 렌더 보간이 반대 방향을 골랐는지, 피치의 원본 곡선/웹 연결에 다른 문제가 있는지는 이 문서만으로 확정하지 않는다. 보통 정지 조준의 core→렌더 결합은 [시점 급변 분석](mouse_view_jumps.md)을 따른다.

- [웹실행] 합성 `dx=1200px`는 기본 감도에서 한 스텝 `lookYaw=-180°`다. `mouseScale=20`이면 `60px`, 감도+5와 배율20이면 `240/7≈34.285714px`가 같은 회전량이다.
- [웹실행] 이 값들은 **재현에 주입한 값**이다. 사용자 실제 이벤트/저장 설정의 관측값이 아니다.
- 원본 카메라 입력은 스틱·자이로다. 웹 마우스 픽셀의 수명·배율·잠금 처리는 웹 이식 선택이며 원본 [실행]/[판독]/[데이터]로 승격하지 않는다.

## 2. 분석 대상 원본·버전·자료 위치

| 자료 | 사용 범위 |
|---|---|
| `web/games/splatoon3/client/input.ts` | 실제 입력 listener·누적·sample·localStorage 설정 |
| `web/games/splatoon3/client/app.ts` | 실제 60Hz accumulator/frame callback |
| `web/games/splatoon3/core/input.ts` | PadState·Reset64·Fire1 비트 |
| `web/games/splatoon3/core/camera/index.ts` | 첫 플레이어/respawns 변경 reset의 실제 소비자 |
| `web/games/splatoon3/core/player/index.ts` | Reset→respawn 및 facing 재기록 순서 |
| [impl/camera.md](../impl/camera.md) | 기존 웹 입력 선택 기록. 읽기만 수행 |
| [player_camera.md](player_camera.md), [r9_reset_contexts.md](r9_reset_contexts.md) | 기존 원본 근거 재사용 |
| `analysis/mouse_camera/input/lifecycle_execution.json` | 실제 웹 모듈/저장 callback의 30건 결과·소스 SHA256 |
| [mouse_input_lifecycle.mjs](../../tools/mouse_input_lifecycle.mjs) | 재실행 가능한 분석 전용 도구 |

새 원본 분석 전에 SHARED.md/FUNCS.tsv와 `decomp_index.py --no-build`로 `24e0178`, `24d6598`, `24a73b8`, `24e4bc8`의 기존 등록을 확인했다. 원본 함수를 다시 디컴파일하거나 기존 결과를 신규 확정 수로 세지 않았다.

## 3. 진입점과 전체 호출 흐름

[웹 소스 판독] 아래 줄번호는 2026-10-03 저장 소스 기준이며 SHA256은 결과 JSON에 저장했다.

```text
scripts/app/games/splatoon3/main.ts:5 boot(root)
  → client/app.ts:44 new InputDevice(canvas)
    → client/input.ts:88~94 global/element listener 등록
mousemove (locked 일 때만)
  → input.ts:164~168 dx/dy += movementX/Y
requestAnimationFrame
  → app.ts:62 deltaTime 최대 5/60초 추가
  → app.ts:66~68 while(acc >= 1/60)
    → input.ts:101 sample()
      → 113 mouseToLook(누적 dx/dy, 현재 settings)
      → 114 dx=dy=0
      → 120~122 hold/trigger/release 갱신
    → core/world.ts:59~63 모든 system.step
  → app.ts:70~73 alpha 보간 렌더
```

`client/app.ts:64`의 `input.locked`는 시작 안내 표시, 65행은 audio.resume에 쓰인다. 66~68행의 월드 스텝 조건에는 쓰이지 않는다. `scripts/main.ts` 안에 별도 입력 처리 루프가 있는 것이 아니다.

## 4. 구조체·필드·상수·열거형 표

| 기준 객체/값 | writer | reader·실제 의미 |
|---|---|---|
| InputDevice.keys:Set | onKey141~144, onBlur148 | sample103~116. 잠금 여부와 무관한 전역 keydown/up |
| InputDevice.mouseButtons | locked mousedown157, mouseup161, blur149 | sample117~118. Fire/Sub hold |
| InputDevice.dx/dy | locked mousemove166~167 | sample113; sample114에서만 0 대입 |
| InputDevice.prevHold | sample122 | sample120~121. blur/lock 변화에서 지우지 않음 |
| document.pointerLockElement | 브라우저/합성 DOM | locked97~99. 이 소스에는 change listener가 없음 |
| settings.sens | load33, setSettings127 | mouseToLook60. k=clamp(sens/5,-1,1) |
| settings.mouseScale | load34, setSettings127 | mouseToLook61. load만 .05~20 clamp; setSettings에 검증 없음 |
| settings.invertX/Y | load35~36, setSettings127 | mouseToLook62~63. 축별 부호 |
| MOUSE_BASE_DEG_PER_PX | 상수8 = .15 | 픽셀→회전의 웹 선택 |
| STEP | app18 = 1/60초 | app66~70 고정 스텝/alpha |
| MAX_STEPS | app19 = 5 | app62 elapsed time 추가 상한. 입력 회전량 상한이 아님 |
| Btn.Reset | core/input.ts10 = 64 | KeyR74→trigger; player188→respawn |
| Btn.Fire | core/input.ts4 = 1 | mouse button0→hold |

[미확정] 실제 사용자의 `splatoon3.camera.*` 값은 이 합성 실행에서 읽지 않았다. 저장 기본값1은 존재하지만 현재 사용자 설정이1이라는 뜻은 아니다.

## 5. 상태 전이와 전체 수명

### 5.1 생성·유지·소비

[웹실행] 기본 환경은 settings(감도0, 배율1, 반전 없음), 빈 keys/buttons/delta/prevHold다. locked 이동 이벤트가 `(30,10)`과 `(-10,-4)` 순서로 오면 첫 sample은 yaw−3°/pitch−.405°, 두 번째 sample은0/0이다. unlock 상태로 전달한 이동은 무시한다.

[웹실행] locked가 아닌 첫 mousedown은 `requestPointerLock()`를 **인자 없이** 호출한 뒤 return하므로 그 클릭은 Fire hold로 기록하지 않는다. actual raw/processed 브라우저 입력 선택 정책은 이 소스만으로 정하지 않는다.

### 5.2 잠금 상실·blur·복귀

[웹 소스 판독]+[웹실행] `pointerlockchange`/`visibilitychange` handler는 없다. locked 시점의 pending dx1200을 놓고 잠금 해제/visibilitychange 후 sample하면−180°가 남는다. keys와 buttons도 잠금 해제만으로 지워지지 않는다. 이후 mouseup/keyup 또는 blur가 오면 각 handler가 지운다.

[웹실행] blur는 keys와 buttons를 지우고 dx/dy·prevHold는 유지한다. blur 다음 sample은 pending yaw−180°와 이전 Fire/Reset의 release 비트를 동시에 내보냈다. app의 실제 frame callback도 unlock/blur 뒤 이를 world.step에 전달했다. **사용자는 포커스 이탈 없이 정지 조준이라고 설명했으므로 이 경로는 별도 위험으로 기록한다.**

### 5.3 Reset·반복키·종료

[웹실행] unlock 상태 KeyR도 trigger64를 전달한다. 키 반복 이벤트는 hold가 유지되면 추가 trigger를 만들지 않는다. keyup 뒤 release64를 만든다. camera/index.ts80~86은 respawns 변경/대기 reset을 소비한다.

[웹 소스 판독] player/index.ts166의 spawnYaw→facing 기록 뒤 같은 step의200행에서 인간 facing=ctx.aim을 다시 기록할 수 있다. 따라서 **KeyR가 반드시 spawnYaw를 보는 카메라 뒤돌기라는 결론은 이 입력 테스트로 확정하지 않는다.** 실제 전체 player/camera 연결은 별도 검증 범위다.

[웹실행] dispose는 등록된 listener를 제거한다. app.boot는 이 입력 객체를 frame closure에 보관하며 현재 반환 cleanup은 없다. 다중 boot/페이지 수명 문제는 사용자 정지 조준 증상과 별도로 남긴다.

## 6. 계산식·조건·상세 의사코드

[웹 소스 판독] 원본 스틱의 최대 속도 비율을 가져오되 **현재 웹 delta는 픽셀 합에 비례하며 스틱 최대 각/프레임으로 clamp하지 않는다**.

```text
k = clamp(sens/5, -1, 1)
yawMax(k) = 4 + k * (k>=0 ? 3 : 1.6)
pitchMax(k) = 1.8 + (k>=0 ? 1 : .8) * k
base = .15 * mouseScale * PI/180
lookYaw = -sum(movementX) * base * yawMax(k)/4 * invertXSign
lookPitch = -sum(movementY) * base * pitchMax(k)/4 * invertYSign
```

기본 yaw는−.15°/px, pitch는−.0675°/px다. 180°의 합산 dx 크기는 `1200/(mouseScale*yawMax(k)/4)`다. 이는 입력 샘플 기준의 경계이며 실제 core FOV 비율·f32·렌더 결과는 별도다.

```text
frame(now):                           // 저장 callback 직접 실행
  acc += min((now-last)/1000, 5/60)
  last = now
  while acc >= 1/60:
    world.step(input.sample())       // 첫 step 누적량 전부, 뒤 step는 0
    acc -= 1/60
  view.update(world, acc/(1/60))
```

[웹실행] 8ms에는 step이 없어 누적량을 보존하고 16.6666666667ms에 첫 sample로 전달한다. 1000ms 지연은 elapsed time 상한으로5step을 실행하며 합성 dx1200은 `[-180°,0°,0°,0°,0°]`다. 시간이 clamp된다고 mouse delta도 clamp되거나5개로 나뉘는 것이 아니다.

[웹실행] setSettings로 sample 전 배율을1→20으로 바꾸면 이미 누적한 dx10도−30°가 된다. Infinity/NaN 이벤트를 합성 주입하면 finite 검사 없이 각각−Infinity/NaN을 전달한다. sample 뒤 delta0은 복구된다. 이 값이 실제 브라우저에서 발생한다는 주장은 하지 않는다.

## 7. 애니메이션·이펙트·소리·카메라·에셋 연결

[웹 소스 판독] 입력 listener는 카메라 quaternion/position을 직접 쓰지 않는다. output PadState가 camera→player→weapon/paint 시스템에 전달된다. 카메라 렌더 보간·basis·pitch 제어의 공급자는 별도 [시점 급변 분석](mouse_view_jumps.md)과 [player_camera.md](player_camera.md)를 따른다.

큰 입력과 finite 여부는 camera/weapon 조준 양쪽으로 이어질 수 있으나 이 하네스의 world fixture는 PadState만 캡처하므로 실제 총구/탄 생성 결과를 검증하지 않았다. 잠금 상태는 audio.resume의 조건이지만 원본 오디오/효과 동등성은 범위 밖이다. 이번 조사에 에셋 추출은 필요하지 않았다.

## 8. 다른 기능과의 상호작용

| 상호작용 | 확인한 경계 | 증상 특정 여부 |
|---|---|---|
| 정지 상태 마우스→조준 | input에는 이동키가 필요하지 않음. 합산 회전량 자체는 이동 여부와 독립 | ordinary core→render 검증은 부모 문서 |
| 화면 갱신 지연 | 누적 input은 첫 fixed step에 일괄 전달 | 실제 사용자 frame delay/이벤트 크기는 미확정 |
| unlock/blur | 이미 누적한 look은 다음 step 소비 | 이번 사용자 설명에서 주원인으로 미지정 |
| KeyR | 잠금과 무관한 trigger64→respawn/reset 소비자 | 실제 사용 중 KeyR 여부와 연결 최종 방향 미확정 |
| localStorage 설정 | load의 clamp·setSettings sample 시점 사용 | 사용자 현재 값 미확정 |
| 렌더 quaternion 보간 | 입력은 회전의 연속 경로를 PadState 하나로만 전달 | 큰 각/최단호 선택의 실제 결합은 부모 문서 |

## 9. 웹 포팅 구조와 구현 순서

이 문서는 변경 지시를 구체화하기 위한 분석이며 구현 코드를 고치지 않았다. 사용자의 ordinary stationary 증상에 우선순위를 둔다.

1. **P0: 정지 조준 core→렌더 결합 원인부터 검증/반영.** [시점 급변 분석](mouse_view_jumps.md)의 실제 재현을 우선한다. 입력 수명의 focus/Reset 후보만 고쳐 사용자 증상이 해결됐다고 보고하지 않는다.
2. **P0: 합산 mouse delta와 렌더 회전 경로의 계약을 함께 정한다.** event/sample/frame별 raw dx/dy·설정·lookYaw/Pitch·alpha·basis/quaternion을 기록할 수 있어야 한다. 현재 무상한 회전과 최단 quaternion 보간을 연결할 때 경로 손실이 가능한지 검증한다. 숫자 상한을 원본 스틱 최대각에서 임의 차용하지 않는다.
3. **P1: 입력 소유 기간을 정의한다.** pointer lock 변경·blur·visibility 변경의 pending dx/dy/keys/buttons/prevHold 처리, unlock 동안 세계 진행/입력 허용을 분리한다. 다음 첫 frame에 의도하지 않은 look이 전달되지 않는 구체 조건을 정한다. Switch에 마우스 잠금이 없으므로 이것은 웹 전용 정책이다.
4. **P1: 설정과 이벤트 경계의 검증.** load와 setSettings 모두 finite/허용 범위를 일관되게 다루고 pending delta에 어느 설정을 적용하는지 정한다. 실제 사용자 설정 확인 없이 기본1로 덮어쓰지 않는다.
5. **P2: 종료 수명.** 필요 시 boot cleanup에서 InputDevice.dispose·frame·resize 수명을 같이 처리한다. 현재 증상 해결의 선행 조건으로 승격하지 않는다.

## 10. 검증 코드·실행 결과·기대값

명령은 [analysis/mouse_camera/input/commands.md](../../../analysis/mouse_camera/input/commands.md)에 성공/실패와 함께 저장했다.

```powershell
cd C:\dev\splatoon3
node web/tools/mouse_input_lifecycle.mjs
```

결과: **30/30 PASS, fail0, exit0**. Node v24.13.0, `stripTypeScriptTypes` ExperimentalWarning 1회. 소스 import/저장 callback 실행 수준은 **[웹실행]**이다.

| 검증 묶음 | 건수 | 실제 결과 |
|---|---:|---|
| 누적1회 소비/다음0 | 2 | yaw−3°/pitch−.405°, 다음0 |
| unlock 이동·첫 클릭 | 3 | 이동0, request 인자 없음, Fire0 |
| lock 상실/재획득 | 3 | pending−180°, key/button 유지, Fire 추가 trigger0 |
| blur | 3 | pending−180°, key/button0, release65 |
| unlock Reset/반복/해제 | 3 | trigger64, 반복trigger0, release64 |
| 회전량/감도/배율 | 3 | dx1200, scale20dx60, sens5scale20dx240/7 각각−180° |
| sample 시 설정/finite/복구 | 4 | queued dx10→−30°, −Infinity, NaN, 다음0 |
| load 설정 clamp | 1 | 감도5/배율20 |
| 실제 frame: substep/pending | 2 | 8ms0step, 뒤 첫step−180° |
| 실제 frame: 1초 resume | 3 | 5step, 첫−180°+뒤0, alpha0..1 |
| 실제 frame: unlock/blur | 1 | world에 pending−180°/hold0 전달 |
| 실제 frame: unlock Reset | 1 | world trigger64 |
| dispose | 1 | 새 mouse/key listener 호출 없음 |

fixture/제외 경계:

- 실제 TS 모듈 InputDevice/mouseToLook/loadCameraSettings를 호출했다. 복사한 재구현 클래스를 테스트하지 않았다.
- app.ts 실제 frame callback은 소스에서 추출해 타입만 지우고 실행했다. DOM event delivery·world.step·render/audio/requestAnimationFrame 호스트는 합성 캡처 fixture다.
- 실제 사용자 browser/OS mouse, screen focus, GPU, 전체 player/camera/frame은 이 실행에 포함하지 않았다.
- 원본 실행·새 디컴파일0건. 원본 inventory 분모/확정 수를 바꾸지 않는다.
- 초기 rg에 없는 port/camera.md가 포함돼 exit2가 났다. 올바른 port/implementation_status.md를 후속으로 읽었다. 실패를 명령 기록에 남겼다.

## 11. 미확정 사항과 추가 분석에 필요한 근거

| 항목 | 수준·남은 이유 | 다음에 볼 곳 |
|---|---|---|
| 사용자의 정지 조준 중 실제 dx/dy·설정·프레임 타이밍 | [미확정] 합성 이벤트는 원인 존재 조건만 보여 줌 | 실제 브라우저 event→sample→alpha trace, localStorage camera 설정 |
| ordinary yaw/pitch와 렌더가 의도와 다르게 도는 직접 원인 | [미확정] 이 문서는 입력 소유 수명만 실행 | [mouse_view_jumps.md](mouse_view_jumps.md), core/camera/camera.ts, client/camera/index.ts |
| lock/blur가 이번 증상에 관여했는가 | [미확정] 사용자 “가만히 시점만” 설명에서 이탈은 확인되지 않음 | 사용 환경/이벤트 trace. 주원인으로 선승격 금지 |
| 큰 입력의 발생 빈도·기기/브라우저 정책 | [미확정] raw 합산은 소스 확인, 합성1200px는 실제 관측 아님 | 실제 movement 이벤트 로그. requestPointerLock() 옵션/브라우저 정책은 별도 |
| KeyR의 전체 player→camera 최종 방향 | [미확정] respawn의 facing은 같은 step 후속에 덮일 수 있음 | player/index.ts163~203, camera/index.ts74~86 연결 실행 |
| 입력 수명 정책의 원본 동등성 | [미확정] Switch 원본에 pointer lock/mouse 픽셀 경로가 없음 | 웹 이식 계약으로 명시. 기존원본24e0178/24d6598/24a73b8 재사용 |

코드·impl·package·original은 변경하지 않았다. 이 문서와 분석 전용 하네스/결과만 저장했다.
