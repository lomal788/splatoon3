# 정지 상태 마우스 시점 이상과 원본 카메라 제어 경계 (2026-10-03)

## 1. 기능 개요와 사용자에게 보이는 동작

사용자 증상은 **플레이어가 가만히 있는 상태에서 마우스로 시점만 바꾸는데 갑자기 뒤를 보거나 뜻과 다르게 보정되는 경우**이다. 현재 사건의 브라우저 mousemove·고정 스텝·카메라 상태 로그가 없으므로 특정 원인을 실제 사용자 사건으로 확정하지 않는다.

[판독: 웹 소스] 현재 일반 웹 카메라는 `lookYaw`로 `aimForward`를 직접 회전한다. `Math.atan2`의 ±π 경계는 `out.yaw`라는 출력 scalar에 생기며, 실제 화면 회전은 `right/up/viewZ → Quaternion → slerpQuaternions`를 소비한다. 이 경계만으로 화면이 180° 돌아간다는 설명은 근거가 부족하다.

[판독: 원본 재사용] 원본에는 상황별 자동 yaw와 reset이 있지만 조건이 있다. 일반 평지·정지 입력에 임의의 180° 회전을 넣는 규칙은 확인되지 않았다. 원본에는 마우스 픽셀 입력이 없으므로 마우스 수집·델타 폭·포인터 잠금·렌더 보간은 웹 대응 경로로 검증해야 한다.

## 2. 분석 대상 원본·버전·자료 위치

Splatoon 3 v0의 PlayerCamera, Lby_Lobby00 1인 연습의 일반 시점이 대상이다. C는 `spl:PlayerCamera`, B는 `PlayerBehavior+0x108` 본체다. 주소는 main 기준 `0x7100000000`를 포함한다.

| 자료 | 원본 또는 현재 코드 | 수준·이번 사용 |
|---|---|---|
| 원본 입력·일반 출력 | `analysis/decomp/camrest/cam_main_full.c`, 입력 `0x71024e0178`, 메인 `0x71024d9ae8` | 기존 디컴파일 재사용, 새로 전체 실행하지 않음 |
| 원본 reset·피치 매핑·타입 바인딩 | `analysis/decomp/camera/batch1.c`, `0x71024d6598/0x71024e64f0/0x71023555f0` | 기존 판독 재사용 |
| 자동 yaw 대상의 새 타입 식별 | `analysis/decomp/mouse_camera/native/type_identity.c` | 4함수 신규 디컴파일, [판독]+[데이터] |
| 원본 기저·붐·reset 기존 검증 | [solo_completion.md](solo_completion.md), [r9_collision_spring.md](r9_collision_spring.md), [r9_reset_contexts.md](r9_reset_contexts.md) | 이전 [실행] 결과를 인용, 이번 새 실행 건수 아님 |
| 현재 웹 입력 소비·출력 | `web/games/splatoon3/core/camera/camera.ts`, `native_math.ts`, `index.ts`, `client/camera/index.ts` | [판독: 웹 소스], 원본 실행 수준과 구분 |
| 이번 원본 감사 | `analysis/mouse_camera/native/type_identity.json`, `*.asm.txt`, `commands.md` | 실제 main bytes/vtable/name 연결, 원본 GPU·전체 프레임 실행 아님 |

지침 `web/README.md`, `web/분석.txt`, `web/docs/README.md`, `web/docs/tools.md`와 SHARED/FUNCS를 확인했다. 새 분석 전에 `decomp_index.py --no-build`로 기존 주소를 조회했고 기존 main/reset/atan/slerp/피치 매핑을 재디컴파일하거나 재실행하지 않았다. `docs/impl/camera.md`는 기존 구현의 질문·경계 목록으로 읽고 변경하지 않았다.

## 3. 진입점과 전체 호출 흐름

[판독: 원본, 기존 근거] 원본 한 프레임에서 플레이어 슬롯18 → 물리 → 플레이어 슬롯19 안 카메라 메인 `24d9ae8`이 돈다. 카메라 메인은 입력 `24e0178` → 상태 리그 → 수직 추종 → 붐 질의와 위치 → 근접 보정 → 기저/포즈 출력을 실행한다. 상세 프레임 그래프는 [player_camera.md §3](player_camera.md#3-호출-흐름)에 둔다.

[판독: 웹 소스] 현재 카메라 시스템은 `readPlayer`와 reset 조건 확인 → `PlayerCamera.step` → `input(pad)` → 리그·붐·`finishOutput`을 수행한다. 렌더 소비자는 `prevRight/prevUp/prevViewZ`와 현재 기저로 두 쿼터니언을 만들고 alpha로 보간한다. `out.yaw`를 선형 보간해 화면에 적용하는 경로가 아니다.

따라서 조사할 시점은 mousemove 수집, `PadState.lookYaw/lookPitch`, core `aimForward/p/s`, `pos/target/basis`, 렌더 쿼터니언을 순서대로 구분한다. 다른 문서의 입력 이벤트·실제 웹 재현 결과는 [mouse_view_jumps.md](mouse_view_jumps.md)에 통합된다.

## 4. 구조체·필드·상수·열거형 표

| 기준 | 필드·단위 | writer → reader 및 이번 해석 |
|---|---|---|
| C | `+0x18c..194` vec3 | reset·입력 Y회전 → 리그/조준. 일반 조준 수평 방향 |
| C | `+0x1a4..1ac` vec3 | 입력 후단 → 리그. 일반 조건에서 `= aimForward` |
| C | `+0x14f8` rad/f, `+0x14fc` rad/f | 스틱 응답·감도 → 원본 yaw 적분. 웹 마우스 direct delta와 같지 않음 |
| C | `+0x150c` 도, `+0x16c` −1..1, `+0x168` 비율 | 피치 누적·매핑·추종 → 리그. 목표 s와 화면 p가 다른 수명 |
| C | `+0x1510/1514` 비율 | reset 0/1 → 자동 yaw 도입 제한. `+0.011111111`/f |
| C | `+0x1500/14dc` 도 | 내부 보정각 → 각각 .15/.03 비율 소비 후 차감 |
| B | `+0x9314` u8, `+0x9304/930c` f32 | 생성 초기화는 판독됨, 활성 runtime writer는 미확정 → 자동 yaw 덮어쓰기 |
| C | `+0x1940` ptr | `23555f0`가 태그 `58c0080`로 바인딩 → 자동 yaw state1/2/4. 아래 새 타입 식별 |
| 출력 | `dot(pos−at, aim)` 한계 −.16 | 메인 일반 근접 보정 → 최종 기저. near .2와 다른 값 |
| 기저 | Z=`normalize(pos−at)`, X=`normalize(up×Z)`, Y=`Z×X` | `24df4e8..24df6d4` → 이동/탄/화면. 실제 viewForward는 −Z |

[판독]+[데이터: 신규] `23555f0`의 컴포넌트 writer, 타입 판정 함수의 태그, 원본 vtable slot2 name getter를 연결했다. 모든 숫자에 base `0x7100000000`를 더한다.

| C 필드 | 태그 | 타입 판정 | vtable / name getter | 원본 이름 |
|---|---|---|---|---|
| 1930 | 58c0c08 | 268aa70 | 563ea38 / 26895b4 | `spl::PlayerStartLaunch` |
| 1940 | 58c0080 | 2656038 | 563db40 / 2655338 | `spl::PlayerMissionTicketGateAction` |
| 1948 | 58bd5d0 | 2530cc0 | 5635660 / 2525bb4 | `spl::PlayerGrindRail` |
| 1950 | 58c0608 | 2674798 | 563e1b0 / 2671678 | `spl::PlayerPipeline` |

2026-10-03 정정: 기존 [player_camera.md §7](player_camera.md#7-연출-카메라와의-연결)의 C1940 “컴포넌트 의미 미확정” 중 **타입 정체**는 MissionTicketGateAction으로 확정한다. 그 컴포넌트의 state1/2/4가 사격장 마우스 사건에서 활성이라는 뜻은 아니다. 임무 실제 동작은 이번 범위 밖이므로 추가 분석하지 않았다.

## 5. 상태 전이와 전체 수명

[판독: 웹 소스] reset은 처음 유효 플레이어를 읽은 때, respawns 카운터가 바뀐 때, 카운터가 없는 경우 Reset 버튼 fallback 뒤에 수행된다. `reset`은 s/p=0, aim=dir 또는 player.facing, 리그·이전 포즈를 함께 초기화한다. 단순 마우스 회전·평지 정지·인간/오징어 boolean만으로 reset을 호출하지 않는다.

[판독: 원본 재사용] 원본 reset은 재시작 종류·설정 메시지·모듈 저장 포즈·수신 카메라 복구 조건에서 발생한다. `First` 종류의 −180° 선택은 시작 방향 반전 predicate를 가진다([player_camera.md §7.1](player_camera.md#71-첫-재시작의-방향-반전-조건--8차2026-10-03-판독실행)). 매 mousemove 또는 yaw scalar의 ±π 경계에서 reset하는 규칙으로 옮기지 않는다.

피치 수명은 s를 목표로 p가 따라가는 형태다. 웹에서는 마우스 dy가 0이 되어도 `p = p + (pTarget−p)*pFollow`가 계속 실행된다. 따라서 수직 이동을 멈춘 직후 시점 고각이 이어서 바뀌는 현상은 현재 식으로 가능하다. 이것은 실제 사용자 사건의 원인 확정이나 수평 180° 뒤돌기의 설명이 아니다.

## 6. 계산식·조건·상세 의사코드

### 6.1 yaw 단위와 wrap

[판독: 원본 재사용] 원본은 angle index `atan2Idx(cross,dot)`의 u32 결과를 f32로 바꿔 `bits0x30c90fdb`를 곱한다. 부호 범위 처리는 `r>π ? max(r−2π,−π) : r`이며 π 값은 `bits0x40490fdb`이다. vector가 바뀌는 것은 wrap scalar의 저장 자체가 아니라 **rate와 gate를 곱한 Y회전**이다.

[판독: 웹 소스] 마우스 일반 입력은 다음과 같다. 연산 함수 add/mul/mix는 매 단계 `Math.fround`를 적용한다.

```text
fovRatio = clamp(FOV/55, 0, 1)
dyaw = lookYaw * fovRatio
if dyaw != 0:
    aimForward = normalize(rotateY(aimForward, dyaw))
ds = (lookPitch * 57.29578) * fovRatio
pFollow += (1−pFollow) * min(abs(ds)/1.8,1) * .2
s = clamp(s + ds, −90,+90)
(pTarget,corr) = pitchAngleToP(s−75, gk=0, stick=true)
s += corr
p += (pTarget−p) * pFollow
rigForward = aimForward
out.yaw = atan2(aimForward.x,aimForward.z)   # 화면 회전 입력이 아닌 출력 scalar
```

원본 최대 스틱 yaw 2.4..7°/f는 원본 스틱 속도 변환의 값이다. 마우스 픽셀 delta가 이 최대값으로 자동 제한된다는 뜻이 아니다. 실제 웹 수집·포인터 잠금·큰 delta는 별도 웹 대응 규칙이다.

### 6.2 일반 자동 yaw와 덮어쓰기 우선순위

[판독: 원본 명령] 기존 입력 `24e0178`에서 자동 yaw rate 후보를 만들고 `24e3264..32d8`은 스틱 yaw 속도 비율에 따라 이를 누른 뒤 C1510/1514 도입 제한을 적용한다. 일반 rate 기본은 이어서 ×.03이다. `24e35f4..3758`의 뒤쪽 우선순위는 **기본/Dokan → B9314 → C1940**이다. 뒤 조건이 활성하면 앞의 target angle과 rate를 덮어쓴다. 새로 저장한 raw 명령은 `auto_override.asm.txt`다.

```text
if B9314:
    y = (B9304 * aim.z) − (B930c * aim.x)
    x = (aim.z * −B930c) − (B9304 * aim.x)
    angle = signed_atan_index(y,x)
    rate = Bdc * .04 + .03
if C1940.state in {1,2,4}:       # MissionTicketGateAction
    y = C1940.f4 * aim.x − C1940.ec * aim.z
    x = aim.x * C1940.ec + C1940.f4 * aim.z
    angle = signed_atan_index(y,x)
    rate = .15
rotation = inputGate * (rate * −angle)
aim = table_rotateY(aim, rotation)
```

여기서 B9314의 x 식에는 목표 벡터의 **음수 부호**가 있다. 이 조건을 “목표9304/930c 쪽”이라고 단순히 이름만 옮기면 방향을 반대로 이해할 수 있다. 상황 의미·활성 writer를 확인하기 전 일반 자동 추종으로 구현하지 않는다.

[판독: 조건부] 일반 평지 Ny=1이면 경사 가중 local_b4=0이고 이동 속도0이면 이동 비율도0이다. B9314=0, Dokan inactive, Mission gate state0, 관련 특수/수신 flags 비활성·유한 입력의 기본 조건에서는 이 자동 회전 후보가0이다. **가만히 있다고 실제 모든 native flags가0이라는 주장이나 원본 전체 프레임 실행 확인은 아니다.** 현행 웹 `input()`에는 이 자동 yaw 경로 자체가 이식되지 않았다.

### 6.3 최종 기저와 뒤쪽 반구 제한

[판독: 원본, 기존 실행 재사용] 일반 출력은 `d=dot(pos−at,aim)`가 −.16보다 크면 `pos -= aim*(d+.16)`으로 민다. 수평 단위 aim과 유한 정상 값이라는 조건에서 이것은 카메라가 주시점의 aim 반대쪽에 남도록 한다. dot half-plane 설명은 [재구현: 조건부 대수], raw 명령과 기저 자체는 기존 [실행] 근거다. f32 오차·0길이·비정상 입력·모드 제외까지 전체 불변식으로 확대하지 않는다.

`updateBasis`는 길이0 또는 |Z.y|>bits0x3f7ffffe이면 이전 세 기저를 그대로 보존한다. 웹이 `atan2` 출력을 ±π 경계에서 초기화하거나 viewZ 대신 aimDir를 화면 Euler로 쓰게 바꾸면 기존 원본 출력과 달라진다.

## 7. 애니메이션·이펙트·소리·카메라·에셋 연결

원본 FOV/거리/고각의 인간·오징어 리그 전환은 현재 일반 yaw를 초기화하는 호출과 구분된다. 정지 인간 상태의 mouse-only 재현에서는 squid/state/floor normal을 고정해야 한다. 총 사격 입력과 움직임이 없는 현재 증상에 발사 쉐이크·벽 잠영 특수 분기를 원인으로 단정하지 않는다.

현재 웹 카메라 view의 shakeOffset은 위치에만 더해 기저 회전을 유지한다. 이 경로만으로 수평 180° 회전을 직접 넣는 식은 없다. 다만 실제 사건에서 어떤 값이 공급됐는지는 사건 로그가 필요하다.

## 8. 다른 기능과의 상호작용

정지 상태에서도 입력 수집과 고정60Hz 스텝은 서로 다른 주기다. 사건 한 번의 mousemove delta와 그 delta가 몇 step에 소비되었는지를 함께 기록해야 한다. renderer는 alpha와 두 기저를 보간하므로 core aim이 정상인지, 표시만 반대로 보간되는지 분리한다.

`core/player/index.ts`는 카메라 방향을 가져올 때 rigForward/aimForward가 있으면 vector를 쓰고, 없을 때 yaw의 sin/cos로 fallback한다. 현재 camera.out에는 vectors가 항상 있다. yaw scalar 경계를 넘는 것 자체가 리셋 원인은 아니다. 실제 player respawns 변경 또는 shared player 재생성은 reset trace에서 확인한다.

## 9. 웹 포팅 구조와 구현 순서

현재 요구는 분석+MD이므로 웹 코드는 변경하지 않았다.

| 우선 | 웹 대응 작업 | 완료 판단 근거 |
|---|---|---|
| P0 | 정지·무발사·form 고정으로 raw mouse delta → step 소비값 → aim/basis → 렌더 각도를 연결 기록 | 사용자 사건 또는 현재 코드 재현을 통해 어느 경계에서 큰 회전이 생겼는지 확인 |
| P0 | yaw scalar wrap, 큰 누적 delta, pointer-lock 진입/복귀, 여러 catch-up step을 각각 재현 | synthetic 웹 검증과 실제 브라우저 입력을 구분, 원본 최대 스틱 속도로 mouse delta를 임의 제한하지 않음 |
| P0 | mouse dy 정지 뒤 pFollow 수렴과 큰 s 경계의 보정량을 기록 | s/p/고각 별도 수명 확인. 큰 입력은 s89.5 근처 분기 포함 |
| P1 | reset이 발생한 경우 reason과 direction source를 기록 | firstPlayer/respawns/Reset과 원본 First/모듈 상태를 혼동하지 않음 |
| P1 | finite state의 final basis 및 Quaternion 보간 점검 | vector와 화면 delta를 독립 비교, 포즈의 Z/−Z 부호 일관 |
| 후속 | 원본 B9314 runtime writer·정지 관련 native gate 공급 | native 장면 입력이 확보되기 전 임의의 auto yaw를 추가하지 않음 |

C1940 MissionTicketGateAction의 임무 실제 동작은 이번 사격장 우선 수정 대상이 아니다. 원본 일반 자동 yaw를 웹 마우스 고치기의 대체물로 추가하면 사용자가 보고한 문제를 가릴 수 있으므로 입출력 원인을 먼저 닫는다.

## 10. 검증 코드·실행 결과·기대값

새 원본 실행은 **0건**이다. 이미 실행한 atan/Dokan/reset/기저 함수를 중복 계상하지 않았다. 이번 신규 원본 성과는 자동 yaw target override의 raw ARM 순서·C1940 타입 연결 [판독]+[데이터]다.

- `decomp_index.py --no-build 24e0178/24d6598/1252998/1252ff0/24e64f0`: 모두 기존 파일 확인, 재디컴파일·재실행 생략.
- `xref.py addr 58c0080/58c0608/58c0c08/58bd5d0`: camera binder와 타입 판정 참조 확인.
- `effect_ptrscan.py`: 타입 판정 주소마다 실제 vtable 1개 발견.
- `combat_vtname.py`: 4개 vtable slot2 원본 문자열 확인.
- `full_decomp.sh .../type_identity.c 2656038 2655338 268aa70 26895b4`: 신규4함수 성공, index6181. 기존 함수 재디컴파일 없음.
- `.venv/Scripts/python.exe web/tools/mouse_native_camera_audit.py`: 원본 태그·vtable·getter4사슬 불일치0, 원본 main SHA256과 raw instruction 기록.
- 실패1: 최초 감사가 첫 `add x8,x8`를 타입 태그로 가정해 guard 주소를 잡아 AssertionError. 같은 명령 창에서 실제 태그 즉치가 존재하는지 검사하도록 수정 후 성공. guard 바이트와 타입 객체를 구분한다.
- 검색 실패: 존재하지 않는 `core/player/physics.ts` 경로를 포함한 rg는 os error2를 냈다. 실제 `core/player/index.ts`와 카메라 디렉터리를 읽어 수정했다.
- 함수 경계 함정: func_lookup가 26747b8을 선행26744e0, 2530ce0을 선행25308e4로 보고했다. 실제2674798/2530cc0에 별도 prologue·RET가 있어 vtable pointer와 원본 명령으로 정확한 타입 판정 진입을 사용했다. 선행 함수의 크기만으로 타입 판정 함수 경계를 추정하지 않았다.

기존 기저260건·Dokan yaw448건·module reset 활성2048/무효64건은 근거 문서에서 재사용했다. 이 수치를 이번 실행 증가율로 적지 않는다. 이번 웹 합성·브라우저 재현은 [mouse_view_jumps.md](mouse_view_jumps.md)의 실제 명령·결과를 기준으로 한다.

## 11. 미확정 사항과 추가 분석에 필요한 근거

| 항목 | 지금 남긴 이유 | 다음 근거 |
|---|---|---|
| 실제 사용자 사건의 직접 원인 | 사건 mousemove/step/basis 로그 없음. 웹 재현은 가능한 경로를 확정할 뿐 과거 사건 원인이 아님 | 동일 브라우저/포인터 잠금·delta timestamp와 core/render 동시 trace |
| B9314 활성 writer·상황 | 전체 기존 decomp 검색은 생성 초기화0과 reader만 찾았다. B9300 구조체 alias 쓰기는 전수증명하지 못함 | B9300 주변 주소 생성·복사 source, B9314 data watch 또는 구간 store scanner |
| Lby 일반 실행의 native auto yaw 입력 전체 | 본체 flags·각도 후보·상태 공급이 실제 장면 값으로 연결되지 않음 | 원본 main/actor slot19 live 입력, ordinary rate whole-function harness |
| 큰 pitch delta의 원본 수치 전부 | 현재 `pitchAngleToP`와 일부 SDK 계산은 판독/웹 재구현 경계, whole input emu 아님 | 24e64f0 경계 입력과 기존 native state의 공급 연결 |
| 최종 원본 화면 부호 | logical basis/projection은 검증됨, device posture live 값과 whole scene 출력은 별도 | 5997898/M2ac writer·실제 active poser/runtime capture |

고정 inventory 전체 질문·분모·확정률을 이 보조 문서의 부분 결과로 올리지 않았다. 웹 소스·docs/impl·original·키·git commit/push는 변경하지 않았다.

