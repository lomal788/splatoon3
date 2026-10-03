# 잠영 캐릭터 표시 수명과 웹 입력 연결 r8

## 1. 기능 개요와 사용자에게 보이는 동작

아군 잉크에서 오징어가 잠영할 때 보이는 모델은 `swimming` 즉시값만으로 켜고 끄지 않는다. 원본 `B7a0` 숨김 래치와 `B794/B798` 지연·경과 카운터가 먼저 갱신되고, 같은 프레임의 상태 갱신 뒤 SM과 holder가 body/`_Hlf`/squid 표시를 정한다. 이번 반영은 이 ordinary 경로와 실제 웹 표시 입력을 연결한다. 바닥 모서리·벽·특수 상태의 미공급 입력은 전체 원본과 같다고 주장하지 않는다.

**[실행: 입력 공급/블록·whole 구분]** 기존 [squid_ink_visibility_r2.md](squid_ink_visibility_r2.md)의 생산→표시 근거를 재사용하고, 실제 데이터의 벽 충전 상한45/18/5와 플래그·NaN·signed 정수 경계, 모서리 probe 기하·반경·0 생산의 새 입력군을 대조했다. 기존 질문의 부분 결과를 전체 확정으로 승격하거나 분석 inventory 분모를 변경하지 않는다.

## 2. 분석 대상 원본·버전·자료 위치

- Splatoon 3 v0, `extracted/exefs/main.reloc.img`; SHA256은 `games/splatoon3/tests/fixtures/player_display_r8.json`에 기록한다. 원본과 키 파일은 변경하지 않았다.
- 중복 확인: `analysis/notes/SHARED.md`의 기존 B7a0/접촉/SM/holder 사실, `FUNCS.tsv`의 `248c16c/243e2dc/14595b0/24abcf0`, `decomp_index.py 24abcf0/2458cfc/243e2dc/249648c/3a72e1c/24f2e5c`를 먼저 확인했다. 기존 C가 있는 함수는 재디컴파일하지 않았다. `249648c`는 기존 판독·이번 명령 확인을 사용한다.
- 기존 본문: [player_state.md §6.1.4·7.3](../player/player_state.md), [gear_skills.md §4.3·5](../player/gear_skills.md), [character_controller.md §3](../physics/character_controller.md), [player_camera.md §6.8.2](../camera/player_camera.md). EntityWorld+21c=.01의 등록 사슬은 기존 r5 실행 근거이며 신규 발견으로 재계상하지 않는다.
- 원문: `analysis/decomp/player/player_slot19.c`, `analysis/decomp/move/move_full_main.c`, `analysis/decomp/render/r4_disp.c`, `r4_holder.c`, `analysis/decomp/player/playerparam_gear.c`, `analysis/decomp/completion/camera_shape.c`. 새 `24f0dbc` factory는 `analysis/port_character_r8/display/player_collision_factory.c`에 디컴파일했다. Ghidra unreachable 경고가 반경 clamp를 생략하므로 c1358..140c 명령/실행이 해당 식의 근거다.
- 신규: `web/tools/player_display_r8_emu.py`, `analysis/port_character_r8/display/native_summary.json`, `query_scan.json`, `commands.md`, 독립 `core/player/display.ts`와 native fixture 테스트.

## 3. 진입점과 전체 호출 흐름

```text
Player 슬롯19 2483134
  24abcf0: Phive 접촉 정리 / StepPaint 입력
  248c16c..c7dc: ordinary 후보 → B794/B798/B7a0
    2458cfc + GrindRail getter 2531028는 원본 실행
  248c97c: 243e7d0 상태 갱신
  248dd94: 249648c 표시 진입
    24964a0: life+31을 display arg로 읽음
    24964b0: 243e2dc SM display
    24964e8: 14595b0 holder display
```

**[판독]** 위 호출 순서는 원본 명령과 기존 C의 연결이다. 새 하네스는 생산 블록→SM whole→holder whole을 수동 순차 호출한다. 전체 `2483134/249648c`를 엔진 액터·Phive·GPU와 자동 연결해 실행한 시험은 아니다.

웹은 `contactCleanup → updateStepPaint → updateCling → updateOrdinaryDisplay → requestLandState/updateStateMachine → supported hidden counter write` 순서다. 후보는 상태 갱신 전 상태를 보고, 숨김 display counter는 갱신 후 상태를 본다. `recoverInk`도 지원된 B7a0를 받는다. 렌더의 wrapper tick은 계속 수행하고 display flags로 모델 visibility를 갱신한다.

## 4. 구조체·필드·상수·열거형 표

기준 `B=PlayerBehavior+108` 본체, `SM=[B+a8c8]`, `PC=[B+a690]`, `PP=[B+a658]`, `Q=PC+14a8`다.

| 원본 필드 | 의미/초기값 | writer → reader / 웹 이름 |
|---|---|---|
| B+7a0 u8 | 지연된 숨김0 | c6fc → SM/카메라/회복, `display.hidden` |
| B+794 s32 | 지연0 | ctor/restart → c16c tail, `display.delay` |
| B+798 s32 | 경과9999 | ctor/restart → c16c tail, `display.age` |
| B+c0 s32 | 공중 프레임 | contact → 후보, `airFrames` |
| B+774 s32 | 벽 충전 프레임 | 이동 → 후보, `wallJumpCharge` |
| PP+13c f32 | WallJumpChargeFrm | 2665590 AP 보간 → 후보, `gear.wallJumpChargeFrames` |
| B+180 / +198 vec3 | 바닥 법선 / 원 법선 | 24abcf0 → 일치/지연 factor, `floorN/floorNRaw` |
| B+1b4 f32 | 보간하지 않는 support normal Y | contact → upward 조건, 웹 별도 공급 없음 |
| B+a74 / +a78 f32 | 모서리 blend / target | 접촉/probe → factor, raw 값 또는 조건부 zero witness |
| SM+f0 s32 | 형태 counter | SM tick/display → `_Hlf`61 경계, `transform/f0` |
| SM+f4/f5/f6/f8 | body/hlf/squid/rail | SM display → holder flags |
| SM+1b0/1b8/1c0/1c8 | body/hlf/commonHuman/squid binder | off reset → material setter, 현재 `displayResets` 기록 |
| Q+10 / +1c | 구 캐스트 시작/끝 | contact → 3a5f36c |
| Q+f8 / +110 / +114 | flags / layer tag / hitMask | `flags\|=c`, constructor layer1, main mask8 |

**[데이터]+기존[판독]** PP+13c 실제 데이터의 low/mid/high는45/18/5다. 생성자60/40/20을 로비 실제값으로 쓰지 않는다. 기존 `GearAP.actionUp → apRate → gearLerp`와 같은 계산으로 캐시를 공급한다. 기존 logf/expf 대체 구현의1ulp 한계는 그대로 남는다.

## 5. 상태 전이와 전체 수명

초기화는 hidden=false/delay0/age9999다. 후보와 hidden이 같으면 경과를 signed32로+1하고 delay를 감소시킨 뒤 각 최소값으로 유지한다. 후보가 달라지면 상태군과 force 조건으로 delay 상한을 줄이고, 0이 되는 프레임에만 hidden을 교체한다. 숨겨지는 동안 wrapper command·재생 진행을 중단하지 않는다.

SM ordinary/invalidrail에서 hidden이면 body/hlf/squid/rail을 전부 끈다. `life+31==0`이고 human 두 표시가 모두 꺼졌으면 counter를90으로, 갱신된 상태가96이면140으로 쓴다. holder는 별도로 생존·타이머·특수·양 모델 동시 표시 우선순위를 적용한다. 숨김 종료는 후보가 false로 바뀐 뒤 native delay를 지나 표시 경로로 복귀한다.

웹의 미지원 프레임은 latch를 변경하지 않고 reason을 기록한다. 미지원 동안 native hidden counter/회복 입력을 새 확정값으로 소비하지 않으며 회복은 기존 swimming adapter로 돌아간다. 렌더는 현재 readPlayer가 마지막 display latch를 계속 공급한다. 지원 구간 밖에서 보존된 숨김/나이를 실제 원본 현재값이라고 주장하지 않는다.

## 6. 계산식·조건·상세 의사코드

### 6.1 ordinary 후보와 지연 [실행: 블록/입력 공급]

기존 r2의 식은 [§6](squid_ink_visibility_r2.md)에 있다. 이번 웹 leaf도 원본 f32 순서·upper-only factor와 signed32 값을 유지한다.

```text
S = 82..90 | aa..ac | ed,ee,10c
upward = air>=1 && supportNormalY<.6414496898651123 && finalY>.05
T = B781 ? 2 : (B7f4&&B7f9)||railLatch ? 1 : upward ? 2 : 4
q = native piecewise ratio(s32(charge−10), low0, PP13c)
candidate = native2458cfc && air<T && q<.25     // finite gear inputs
match = all axes inclusive −2^-23 <= f32(N−Nraw) <= 2^-23
f = match ? fmin(1, f32(f32(1−Ny)+ (a74>a78?a74:a78))) : 1
```

상한/하한 역전·상한0의 q도 원본 전용 분기로 실행 대조했다. 웹 leaf는 유한 gear 입력을 요구하고 비유한 PP13c는 unsupported로 돌려준다. `B1b4=NaN`은 `248c1d4 B.PL`에서 upward false가 되며 factor의 edge NaN은 원본 FCSEL/FMIN/FCVTZS 결과를 유지한다. NaN을 임의의 안전값으로 채우지 않는다.

stable true의 최소 `trunc(f*4+1)`, true 교체 후 `trunc(f*7+3)`에는 하한 clamp가 없다. false 최소5/교체 후10, 상태군 밖 delay 상한3, force 상한1이다. 다른 후보에서 감소하는 명령은 native `SUBS/CSEL GT`이므로 INT_MIN overflow를 단순한 `max(wrapped(delay−1),0)`로 바꾸면 안 된다. 새 fixture는 이 경계를 포함한다.

### 6.2 모서리 probe [판독]+[실행: 기하/반경·query 결과 입력]

**2026-10-03 정정:** 기존 문서의 “모서리 레이”라는 줄인 표현을 point ray로 읽으면 안 된다. `24f141c/1428`은 `PC14b0`에 `3a72e1c` sphere wrapper, Q에 VT559ad88을 기록한다. 이 질의는 sphere cast이며 등록된 EntityWorld21c=.01을 쓰는 일반 반경은 `.01`이다. singleton 없는 fallback 반경은 `.05`이고 원본 반경식은 `min(fmaxnm(worldTolerance,.01),2000)`다.

raw actor 위치 A, PC 접점 P, B108 플랫폼 속도 V, `d=(A.x−P.x,0,A.z−P.z)`를 쓴다.

```text
L = sqrt_f32(d.x² + 0 + d.z²)
dir = L>0 ? d * f32(1/L) : d
start = f32(P+V) + (L<.01 ? (0,.05,0) : dir*.05)
end = start + (0, bits(0xbd74f023)=−.059799324721097946, 0)
Q.flags |= 0xc; Q.hitMask = 8; sphere query result hit bit → a7c branch
```

`24ac784..c7cc`은 pre-a7c>.01 && hit이면 a7c=0, pre<=.01&&hit이면 그 값을 보존한다. 유한 a7c<=lo이면 `24acc10..ccb4`는 a78=0을 만들고 비음수 `f32(priorBlend+increase)`이면 `24afe48..fe5c`는 a74=0을 만든다. 원본 lo=.06.. .3, increase=.01.. .05와 DC 상한1/초기0에서 시작하는 비음수 latch 조건은 기존 접촉식을 사용한다. 질의 결과 자체는 fixture 입력이다.

Q+110은 constructor `24f12b4`에서1, main은 Q+114에8을 쓴다. 24f0dd4..24fffffc의 고정 오프셋 store scan에서는 PC15b8의 다른 writer를 찾지 못했다. 계산된 기준 주소나 다른 caller의 active writer가 없다고 증명한 것은 아니다.

## 7. 애니메이션·이펙트·소리·카메라·에셋 연결

`nativeSmDisplay`는 모델 visibility와 counter를 쓰고 command wrapper를 stop하지 않는다. 웹 animator는 실제 ASB bundle의 wrapper를 tick한 뒤 SM/holder leaf에 전달한다. 숨김 중 wrapper 시각 진행과 command 유지는 부모의 `player_visual_supply.test.mjs`에서 검증한다. 숨김 동안 PlayerView.draw가 applyLeaves를 수행하지 않으므로 이 시험을 모든 mesh pose의 진행 검증으로 확대하지 않는다.

off reset 순서는 body→hlf→squid→commonHuman이다. 각 binder의 team0/1/2 cache+8/+c/+10은 `0x7fc00000`, vt10 setter의 **S0는0**이다. GPU에 NaN을 썼거나 Wrapper.stop으로 대체했다고 해석하지 않는다. 웹은 `displayResets`에 기록하지만 type11/live material setter reset 미구현은 유지한다. modelKind18 시험이 material shader type18 전체 경로 확정을 뜻하지 않는다.

원본 카메라는 B7a0를 소비하지만 현재 웹 카메라가 이 display latch를 읽는 연결은 확인되지 않았다. 이번 실제 공급은 렌더의 `displayHidden`과 잉크 회복 `inkFastStealth`다. 카메라 B7a0 입력 연결은 미연결 항목으로 남긴다. 소리/VAT/수영 물결의 새 식·타이밍을 이 표시 leaf에서 추측하지 않는다.

## 8. 다른 기능과의 상호작용

Phive support/StepPaint cls는 후보 입력이며 이번 표시 leaf 대조가 원본 sampler/CCT까지 동일하게 만든 것은 아니다. 특히 현재 웹 StepPaint는 근사 sampler와0/2/4 분류를 쓰고 원본에는 홀수 cls 분기도 있다.

world 벽 접촉, CeilTimer, charge, launch는 표시 후보와 force 조건을 바꾼다. 상태 갱신 후 counter90을 유지하면 `_Hlf` 전환에도 영향을 준다. 일반 모델이 보이지 않는 이유를 단순 shader색이나 squid 축소로 채우지 않는다. dead/life/holder timer는 독립 gate이므로 렌더 쪽의 life fixture adapter를 명시한다.

## 9. 웹 포팅 구조와 구현 순서

`core/player/display.ts`는 raw 입력을 받는 독립 leaf 모듈이다. `createPlayerDisplayState/stepPlayerDisplay`의 단일 `DisplayBinding`에 supported, hidden/candidate/factor/threshold, latch 또는 unsupported reason을 돌려준다.

| 공급 지점 | 반영 내용 | 동등성 경계 |
|---|---|---|
| core/player/index.ts | updated StepPaint 후·SM 전 후보, supported hidden counter는 SM 후 | raw producer는 웹 adapter |
| core/player/gear.ts | ActionUp AP에 따른 실제 triplet45/18/5→+13c | log/exp 기존1ulp 한계 |
| core/player/state.ts / client/render/shared.ts | latch/binding→snap displayHidden | unsupported 이유 보존 |
| client/render/anim/animator.ts | SM+holder flags/counter/reset 기록 | holder life/timer/special은 일반 practice adapter |
| client/render/player.ts | body/hlf/squid visibility 소비 | 원본 model/material 전체 shader 동등성은 별도 |

현재 ordinary static floor adapter 조건은 `!collision.fallback && onGround && gtri>=0 && floorN.y>=FLOOR_NY && !wallCling`이다. res.gp를 PC 접점 대체로 쓰고 실제 구 sweep hit에서 zero witness(.01,.06,0,0)를 얻는다. 이 bounds는 raw a7c/a74 캡처값이 아니다. B108 플랫폼 속도는 현재0인 static adapter다. `nativeCornerProbe` 기하/반경 leaf를 재사용하고 필터 layer1/mask8/sub0/subMaskffffffff를 명시하지만 native 후단 filter/CCD 전체 동등성은 미확정이다.

equal normal에서 true를 유지/진입할 때 a74/a78이 미공급이면 unsupported다. 법선 불일치는 f=1로 edge 입력과 독립이며 false 유지도 edge가 필요 없다. 상승 공중에서 B1b4가 필요하면 별도 입력이 없으므로 unsupported다. B781/B7f4/B7f9/rail/special 등 미구현 기능은 일반 practice adapter에서 불활성이라고 명시한다.

## 10. 검증 코드·실행 결과·기대값

명령과 실패는 `analysis/port_character_r8/display/commands.md`에 기록했다. native fixture 생성은 `python web/tools/player_display_r8_emu.py`, 독립 웹 대조는 `node --test web/games/splatoon3/tests/player_display.test.mjs`다.

| 검증 | 새 입력 수 | 결과/경계 |
|---|---:|---|
| original c16c..c7dc→2458cfc/2531028 | 2,048 | candidate/match/3 latch 불일치0, PLT0/fault0 |
| whole SM display | 384 | flags/counter/off 순서, reset capture1,992·cacheNaN/setter0 |
| whole holder | 384 | timer/life/priority, 원본 내부 stubs0 |
| corner query-result→target0→blend0 블록 열 | 512 | 원본 target/blend bits0, query 결과 공급 |
| corner start/end block | 384 | xyz 각 f32 bits 불일치0, raw position 입력 |
| corner radius block | 10 | singleton 없음/.01/경계/±inf/NaN, descriptor S0 bits 일치 |
| producer→SMwhole→holderwhole 연속 | 288 frames | 45/18/5 각각96프레임, flat→wall-like→charge→air→exit |
| 독립 웹 tests | 7 | 7/7 PASS |

native SM의4 material setter callback은 캡처/return fixture다. 나머지 일반 native 의존성은 원본을 실행하며 PLT0/fault0이 이 제한을 없애지는 않는다. r2의10800/8192/4096/272 등은 이번 새 입력 수에 더하지 않는다. 수치 테스트 통과를 실제 게임 전 프레임·GPU 화면 일치로 확대하지 않는다. 작업 중 `tsc -p games/splatoon3/tsconfig.json`도 PASS했다. 부모의 전체 검사/브라우저 검증은 별도 기록한다.

## 11. 미확정 사항과 추가 분석에 필요한 근거

| 미확정 | 시도/이유 | 다음에 볼 곳 |
|---|---|---|
| 전체 raw corner producer | 원본 query 소비·0분기·geometry/radius 실행. 웹은 PC110*PC124/B108/원본 접촉을 모두 공급하지 않음 | 24abcf0 c5xx..c7cc, 24f7410→actualCCT/Entity query |
| active Q 전체 filter producer | constructor1/mask8, 제한된 고정 오프셋 store scan. 다른 caller/계산 base alias 제외 불가 | 24f0dbc 내부 init/slot7/13·Q메타tag 갱신·3b19dd4/3b1a114 |
| equal-normal 벽/edge와 공중 support normal | unknown field를0으로 채우지 않고 unsupported 보존 | Ba74/Ba78 전체 framewriter, B1b0/+1b4 contact→air 유지 |
| valid 특수 상태 후보OR | ordinary 입력 fixture만 실행. warp/validrail/geyser/periscope/pipeline/vehicle/debug는 별도 범위 | 248c418..c5c0 실제 handle producer |
| GPU binder reset/type11/type18 전체 visibility | 원본 reset cache/setter 인수 캡처, 웹은 기록만 | 243e488..e644에서 live binder/vt10→material updater |
| wrapper/life/holder 전체 frame 공급 | 원본 whole consumer 대조와 웹 bundle 시험을 구분. life/timer 일반 adapter | 249648c 전체 caller·1459284/243a434·actor scene 제출 |
| 카메라 B7a0 웹 소비 | 원본은 기존 판독/실행 근거가 있으나 현재 웹은 display latch 소비를 확인하지 못함 | client camera 입력 생성→native boom hidden/stealth 입력 계약 |
| 원본 화면과 완전 일치 | fixture/browser 웹 검사가 원본 GPU frame과의 이미지 차분은 아님 | 같은 조건 Lby v0 frame capture와 color/depth/material/effect 비교 |

이 문서는 제한된 표시/입력 연결을 반영한 기록이며 물리·카메라·그래픽 전체 inventory 완료율을 여기서 늘리지 않는다. 전체 표/SHARED/FUNCS 갱신과 브라우저/전체 검사는 부모 통합 작업에서 관리한다.
