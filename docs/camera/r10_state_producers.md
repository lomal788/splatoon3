# 카메라 상태·자동 회전·수직 추종 입력 생산자 (r10)

## 1. 기능 개요와 사용자에게 보이는 동작

Splatoon 3 v0의 카메라는 입력을 읽는 것 외에도 몸체 상태, 이동 기믹 및 수몰 타이머를 읽어 조준·리그를 바꾼다. 이 문서는 고정 camera106 질문 중 6·9·10·11·19·20·21·22·33·35·36·37을 다룬다. 기준 분모는 `analysis/camera_100_r10/baseline_inventory.json`의 106이며 이번 조사로 질문을 분할하거나 분모를 줄이지 않는다.

**2026-10-03 새 근거:** B9314의 실제 변환 생산자, 입력 차단 predicate 전체, WaterFall 타이머·충돌 높이 생산자와 카메라의 법선 소비를 확인했다. IkuraShoot/Gachihoko의 번호도 컴포넌트 바인딩 writer로 확인했다. 추가로 B9315 요청의 GateManhole/MissionGateway 생산자와 B9210/B9212의 실제 구독 채널을 확인했다. 합성 입력으로 실행한 구간의 일치가 실제 Lby_Lobby00 프레임·이벤트 도달을 증명하지는 않는다.

**2026-10-03 후속 근거:** PlayerDemo의 `CanControlCamera`와 `Time`을 원본 파라미터·receiver·tick까지 연결하고 922사례를 추가 실행했다. 피치 자동복귀의 reader는 입력 차단24c99f0과 조건이 다르다. B9211/9213의 실제 Ready/Result 채널 및 기존 Scene_Versus 로비 태그0을 해당 분기와 연결했다(§6.9·6.10). 값12의 enum 이름 연결 등 남은 계약은 §11에 구분한다.

**2026-10-03 차량 후속 마무리:** VehicleSpectacle의 `Cockpit` contact, 원본 `State::Controlled`, owner ActorRef를 실은 메시지, PlayerVehicleSpectacle의 command queue 및 기존 C1918 writer를 연결했다(§6.11). 새 원본 실행은288사례이며 기존6071과 별도로 기록한다. 사용자 종료 요청에 따라 여기까지 문서를 갱신하며 Coop enum12·수직 목표 공급자 추가 조사는 진행하지 않았다.

## 2. 분석 대상 원본·버전·자료 위치

- 원본: `original/`의 Splatoon 3 v0 main 및 원본에서 생성한 `analysis/main.reloc.img`. 원본은 읽기 전용이다.
- 기존 판독 재사용: `analysis/decomp/camera/batch1.c`, `analysis/decomp/camrest/cam_main_full.c`, `analysis/decomp/camera/camui_batch3.c`, `analysis/decomp/state/state_core.c`, `analysis/decomp/life/big1.c`, `analysis/decomp/gimmick/gimmick_b2.c`, `analysis/decomp/move/move_cam1918.c`.
- 신규 C: `analysis/decomp/camera_100_r10/state/input_sources.c`, `affine_source.c`, `fall_sources.c`, `collision_height.c`, `pipeline_receiver.c`, `request_sources.c`, `event_metadata.c`, `vehicle_supplier.c`, `demo_sources.c`, `demo_receiver.c`, `demo_timer_params.c`, `auto_pitch_flags.c`. scratch 사본과 SHA256가 같은 것을 확인하고 기존 파일을 덮어쓰지 않고 복사했다.
- 차량 후속 C: 같은 durable 폴더의 `next_vehicle_receiver.c`(7함수), `next_vehicle_sender.c`(4함수). `analysis/camera_100_r10/state/`의 scratch와 SHA256가 같은 신규 사본이며 기존 파일을 덮어쓰지 않는다. 기존 Controlled entry/exit·Pipeline·Dokan C는 재사용했다.
- 기존 근거: [player_camera.md](player_camera.md) §5·6.2·6.6·6.8·7.2, [r9_state_sources.md](r9_state_sources.md), [r9_collision_spring.md](r9_collision_spring.md), [r9_reset_contexts.md](r9_reset_contexts.md), [damage_hit.md](../combat/damage_hit.md) §4.7.3, [movement_physics.md](../player/movement_physics.md) §6.4.6, [mouse_original_controls.md](mouse_original_controls.md).
- 실행·명령·실패: `analysis/camera_100_r10/state/native_results.json`, `water_results.json`, `request_results.json`, `event_source_audit.json`, `classifier_data.json`, `classifier_results.json`, `demo_results.json`, `demo_source_audit.json`, `commands.md`.
- 차량 후속 기록: 같은 scratch 폴더의 `next_vehicle_emu.json`, `next_vehicle_source_audit.json`, `next_question_results.json`, `next_notes_proposed.md`, `next_funcs_proposed.tsv`, `next_commands.md`, `next_validation.json`. `next_*`는 이전6071의 결과를 바꾸거나 재합산하지 않는다.

SHARED.md・FUNCS.tsv・decomp_index를 먼저 확인했다. 함수 내부 PC를 decomp_index에 넣으면 기존 함수가 없다고 나올 수 있다. `func_lookup.py`로 시작을 찾은 뒤 다시 조회했으며 249257c는 기존 `state_core.c`를 재사용했다.

## 3. 진입점과 전체 호출 흐름

```text
PlayerBehavior slot18 2353ad0
  → 2353bf4..2353d00에서 S=B+92f8을 2475a54에 공급
  → 247b0f4..247b5a8: request/actor 유효성 확인·S 갱신
    → 247b43c..247b4e4: actor 변환 × S.local, SDK12548f0
    → S.active(B9314)=1, S.position(B92f8), S.forward(B9304)
  → 카메라 입력24e0178의 B9314 자동 yaw/pitch 분기

PlayerCollision 24f7d84
  → 선택 contact의 Water tag(bit2), 높이 → PC+1d8
PlayerBehavior slot19 2483134
  → 248a89c..: PC 높이 → T+9c(Bdf4) 래치
  → 조건 충족 시 24618fc(kind=1) → T+98(Bdf0) WaterFall 타이머
PlayerCamera 24d9ae8
  → 24da0b0..24da160: Bdf0/Bdf4로 surface-normal 목표 조정
  → 기존 SDK1252ff0으로 C138 법선 평활

2470bc0 → 2471940(x1=B+588) → 249257c
  → W+a1f0 / W+a208의 실제 컴포넌트에 actor 바인딩
  → W+d4(B65c)=0x13 / 0x16
  → 24d9ae8·24e0178의 특수 번호 소비

VehicleSpectacle contact2238460: Cockpit 및 state2의 gate
  → actor FSM state3(State::Controlled) → enter22337bc
  → 메시지6fe76000, payload+b0=owner ActorRef → sender17adcec
  → PlayerVehicleSpectacle receiver24341ac
  → component+78 ActorRef /+90 위치 /+a8 command queue
  → 1256b40 → command26b18d8 → FSM Controlled1
  → 기존 entry26b0bd4 → camera C1918=1
메시지6fe76001 → command26b1964 → FSM Free0
  → 기존 exit26b0ebc → camera C1918=0 /ActorRef 정리
```

24c99f0은 카메라가 호출하는 입력 차단 predicate이다. 모든 입력 이벤트·전체 slot18/19·전체 카메라를 이번에 원본 실행한 것은 아니다.

## 4. 구조체·필드·상수·열거형 표

기준: `B=PlayerBehavior+108의 플레이어 본체`, `C=PlayerCamera`, `S=B+92f8`, `T=B+d58`, `PC=[B+a690]=PlayerCollision`, `W=B+588`, `D=[B+a880]=PlayerDokanWarp`, `Demo=[B+a650]=PlayerDemo`.

| 객체·필드 | 타입·역할 | writer | reader·수준 |
|---|---|---|---|
| S+0..8 = B92f8 | f32×3, 합성 변환 위치 | 247b4c4/247b4c8 | body/카메라 연출 입력 [판독]+[실행:생산 구간] |
| S+c..14 = B9304..930c | f32×3, 합성 변환 Z축, 정규화하지 않음 | 247b4d8/247b4e0 | 자동 yaw 목표의 x/z [판독]+[실행] |
| S+18 = B9310 | s32, 연출 진행 카운터 | 247b0f4 이후 | 24bfb88 [판독] |
| S+1c = B9314 | u8, 위 actor 변환 공급 활성 | 247b4b8=1,247b290=0,23547bc reset=0 | 24c99f0/카메라 [판독]+[실행] |
| S+1d = B9315 | u8, 요청 | GateManhole2153a6c/MissionGateway21b9f6c=1, 초기화/reset/247b5a8 종료 | [판독]+[실행:쓰기 구간], 전체 supplier는 [미확정] |
| S+20..37 = B9318..932f | ActorRef, handle/gen 및 enable byte | 요청 callback→3c838dc, 초기화·종료3c837c8 | [판독]+[실행:mode0/초기gen−1] |
| S+34 = B932c | u8, 위 ActorRef 내부+14의 enable | 기존 초기화·바인딩 계약 | 요청 callback은0이면 binder를 건너뜀 [판독]+[실행] |
| S+38 = B9330 | local affine 3×4 | GateManhole2153a8c/MissionGateway21b9f8c의48B 복사 | SDK12548f0 [판독]+[실행:생산·소비] |
| T+98 = Bdf0 | s32, WaterFall 타이머 | 24618fc(kind1) | HUD/model의 WaterFall, 카메라24da0b0 [판독]+[실행:초기 쓰기] |
| T+9c = Bdf4 | f32, 선택 Water contact 높이 래치 | 248a89c.., 원천PC+1d8 | 카메라24da0bc [판독]+[실행] |
| PC+1d8 | f32, Water contact 높이 max, reset −FLT_MAX | 24f4440 reset /24f84ec..24f862c | slot19의 T+9c 공급 [판독]+[실행] |
| PC+1d4 | u32, 선택 contact 재질 id | 24f84ec..24f862c | max 갱신 여부와 별도로 씀 [판독]+[실행] |
| B+180..188 | f32×3, 몸 표면 법선 | 기존 이동·충돌 근거 | WaterFall 카메라 목표 입력 [실행:소비] |
| C+124 | f32, 추종 주시점 y | 기존 카메라 근거 | WaterFall 높이 차; camera position y가 아님 [판독] |
| W+a1f0 = B+a778 | PlayerInkActionSpIkuraShoot 포인터 | 기존 component 자료 | 2494380..의 typed actor 분기 [판독]+[데이터] |
| W+a208 = B+a790 | PlayerInkActionSpGachihoko 포인터 | 기존 component 자료 | 24944c8..의 typed actor 분기 [판독]+[데이터] |
| W+d4 = B65c | s32, 바인딩된 특수 actor 종류 | 249257c의 분류 writer | 직접 0x13/0x16 대응 확정; 보편적인 10+enum 식은 아래 정정 |
| Demo+33/+34/+35 | u8, CanMove/CanControlCamera/CanDraw | typed 파라미터2363ff4 → receiver23613ec | 입력 차단/피치/표시; [판독]+[실행:선택 메시지] |
| Demo+be4..bec | f32×3, timed Dir | payload+44의12B 복사2361cb0/2361cb4 | timed 연출 입력 [판독]+[실행] |
| Demo+bf4 | f32, Time 초 단위 잔여 | receiver2361cf4/tick250b9a4 | 입력 차단24c99f0; 피치 복귀 reader에 직접 검사 없음 [판독]+[실행] |
| Demo+bf8/+32 | u8, timed IsSquid/이번 틱 래치 | receiver2361cdc/tick250b9b8 | timed 표시 상태 입력 [판독]+[실행] |
| B9211 | u8, SplVersusReady 채널의 latched flag | 기존24cb4cc 끝24cbb08 | Scene_Versus 피치 복귀 조건 [판독]+[데이터] |
| B9213 | u8, SplVersusResultSelector 채널의 latched flag | 24cbcb8 끝24cbf08 | 같은 조건 [판독]+[데이터] |
| [B+a830]+1348 | u32, PlayerCoopSeq 구독의 메시지+18 값 | typed key5861808/functor2500fe4 | 카메라가 literal12와 비교; enum 자연어 이름은 [미확정] |
| V=[B+a6d8] | PlayerVehicleSpectacle 포인터, VT563f428 | 기존 component 생성 자료 | receiver slot16=24341ac [기존 데이터]+[판독] |
| V+78..8f | ActorRef, 차량 owner 참조 | start payload+b0에서3c837c8→3c83bc4(mode0), self alias면 skip | 기존 Controlled entry26b0bd4; empty/invalid ref 경로만 [실행] |
| V+90..98 | f32×3 raw 몸 위치 캐시 | start receiver가 B+10..18의12B를 복사 | 차량 제어 시작 저장; raw bytes [실행] |
| V+a8/+b0 | command queue의 sentinel·head/tail | 1256c54/1256b40 | 실제 native queue 연결 [실행:선택경로] |
| V+b8/+c0/+d0 | queue count/free pool/capacity | generic command queue | capacity1 합성 fixture, 모든 capacity 경계는 미실행 |
| C1918 | u8, VehicleSpectacle Controlled 카메라 분기 활성 | 기존 enter26b0bd4=1/exit26b0ebc=0 | 카메라 리그·입력의 차량 소비 [기존 판독]; writer 도달 전까지 새 [실행] |

원본 상수 데이터: `58bbf88=160`, `58bbf8c=300`, `58bbf90=160`, `58bc078=0.5`, contact normal 기준 `58bc7a0=0.6414496898651123`。정적 생성자에서 복원된 기존 `analysis/player/bss_consts_58bb000.json`을 재사용했다. 원본 런타임을 관측해 얻은 새 상수로 재계상하지 않는다.

## 5. 상태 전이와 전체 수명

S 생성·리스폰: 원본234b580/23547bc가 active/request를 0으로 만들고 local forward의 초기 Z축을 둔다. slot18은 S.count와 요청, 24bfb88 predicate, ActorRef 세대 및 actor 상태 유효성을 확인한다. 유효 actor는 상태+24가7..11 밖이다. 최초 카운터0에서 SM 요청0xed(Dive_St), 후속0xee(Dive_Ed)의 기존 상태 이름 자료를 사용한다. 활성 구간은 actor physical transform과 local affine를 곱해 position/forward를 쓰고 active를1로 한다. 양수 count 종료 쪽247b280..247b294는 active0, 종료247b5a8 쪽은 request와 ActorRef를 정리한다.

**2026-10-03 정정:** 이전 결론 “어떤 이벤트가 request와 actor를 공급하는지는 아직 미확정”을 보존하고 범위를 좁힌다. GateManhole/MissionGateway의 실제 contact callback 두 개는 owner actor와 `player_point` local transform을 요청에 공급한다(§6.6). 전체 supplier·scene activation은 여전히 미확정이다. 요청 쓰기만으로 active가 켜지지는 않으며 가만히 마우스를 돌릴 때 이 연출이 켜진다고 단정하지 않는다.

WaterFall: PC reset의 −FLT_MAX에서 시작한다. contact 소비가 선택 Water 높이를 최대값으로 기록한다. 다른 낙하 타이머가 꺼져 있고 유효 PC 높이가 있으면 T9c를 그 높이로 갱신한다. 높이가 없을 때 몸 y가 기존 높이보다 위면 T9c를 −FLT_MAX로 돌린다. 활성 타이머가 있으면 이전 높이를 유지한다. 몸 y가 `T9c−0.5` 아래이거나 다른 기존 낙하 조건이 켜지면 여러 actor/death gate를 지나24618fc(kind1)에 들어간다. kind1은 WaterFall 타이머 및 시작 높이·초기 수직속도를 설정한다. 카메라는 이 타이머가1 이상인 동안 법선 목표를 바꾼다.

WaterFall의 전체 사망·리스폰 연속 실행은 기존 [player_life.md](../combat/player_life.md)와 [damage_hit.md](../combat/damage_hit.md)에 남긴 범위를 따른다. 이번 초기화 블록 실행을 전체 낙하 수명 검증으로 확대하지 않는다.

PlayerDemo ctor250b22c는 D+10부터0xcd8B를0으로 만든 뒤 D33/34/35를1로 초기화한다. D30/31/32 및 Dbf4는0이다 [판독]. `CanControlCamera` 파라미터 기본값0은 **메시지 객체의 기본값**이며 component의 초기 D34=1과 다르다. 메시지6e9f8200이 허용되면 파라미터의 세 byte를 D33..35에 복사하고,6e9f8201은 D30을0으로 하고 D33..36을1로 돌린다. timed 메시지6e9f8228은 Dir/IsSquid/Time을 쓰고 tick은 양수 잔여만 감소시킨다(§6.9).

reset250b81c는 D36 및 queued command/holder를 정리하지만 이 함수에서 D34나 Dbf4를 직접 쓰지는 않는다 [판독]. 이것을 모든 reset의 보존 계약으로 확대하지 않는다. postupdate250b9f8의 D38 가산·clamp 및 애니메이션/이펙트 호출도 D34/Dbf4의 직접 producer가 아니다. allocator·전체 ctor·queue dispatch·scene sender를 원본 실행한 것은 아니다.

차량은 actor 쪽의 Controlled3과 player component 쪽의 Controlled1이 서로 다른 FSM이다. start 메시지는 참조·위치를 저장하고 delay0 command를 queue에 넣으며, 이후 tick이 player FSM을 전환한다. `125a178`은 이전 상태 exit를 호출한 뒤 새 상태·counter를 쓰고 enter를 호출한다. 따라서 stop의 exit 진입점에서 실행을 멈췄을 때 이전 Controlled1이 아직 남는 것이 원본 순서다. actor exit2234ce8은 다음 actor 상태7이면 즉시 stop 발행을 건너뛰며 별도 state7 exit2236800에도 stop 발행이 있다. 상태7의 자연어 이름이나 그 모드 전체 동작을 추측해 채우지 않는다(§6.11).

## 6. 계산식·조건·상세 의사코드

### 6.1 B9314 변환 생산자

원본247b43c..247b4e4 [실행]。actor+28c..2b8의 물리 변환을 `translation3, axisX3, axisY3, axisZ3`로 재배치한다. actor의 원래 행에 놓인 basis를 전치해 SDK12548f0의 column affine 형태로 공급한다. 결과는 `actorWorld × localAffine`이며 SDK 각 항은 별도 FMUL/FADD의 f32이다. FMA를 쓰지 않는다. 호출 후 **247b4b8에서 active=1을 먼저 쓰고**,247b4c4/4c8에서 결과 translation을 S.position에,247b4d8/4e0에서 결과 Z-axis를 S.forward에 복사한다. 방향을 다시 unit vector로 만드는 명령은 없다.

### 6.2 전체 입력 차단 predicate 24c99f0

아래 순서에서 처음 해당하는 조건이 blocked=1을 반환한다 [판독]+[실행:2175건]。

```text
if !(B9210 || B9212 || [B+a650].34): return 1
if MissionTicketGate+38 ∉ {0,5}: return 1
frame = SM wrapper+30 + 4*(global58bb8f4가0/1이면그값, 아니면0)
if SM∈{ef,f0} && frame<=95: return 1
if SM==f1: return 1
if SM==f2 && frame<=50: return 1
if MissionSeqPinch+38∈{3,4}: return 1
if [B+a830].38∈{5,6,7,8}: return 1
if Demo+34==0: return 1
if Demo+bf4>0: return 1
if D+30∈{1,2} || S+1c!=0: return 1
if uint(Coopptr+38)>9: return 1
return (0x1fc >> Coopptr+38) & 1
```

마지막 Coop 상태2..8은 차단하고0·1·9는 허용한다. 실제 caller는 Coopptr에 `[B+a830]`를 넘긴다. 도구의 raw ABI fixture는 두 포인터를 분리하는 경우도 포함하여 함수 자체 계약을 검사했으므로 그 조합을 실제 caller 도달로 주장하지 않는다. frame의 FCMP+B.LS와 DemoBF4의 FCMP+B.GT는 NaN에서 해당 분기로 가지 않는다. C 디컴파일의 `DemoBF4<=0`를 JS의 같은 비교로 옮기면 NaN 계약이 달라진다.

**2026-10-03 정정:** 이전 §5의 “B9210/9212/…가 모두0이면 조작 불가”만으로 전부 설명하는 문장은 Demo+34와 뒤의 gate를 생략한다. 단순한 두 byte OR가 아니라 위 predicate 및 별도 카메라 branch를 공급해야 한다. B9210/9212 이벤트 의미는 §11에 남긴다.

### 6.3 Water 높이·초기 타이머

선택 Water contact의 tag bit2를 확인한 뒤, `pairflag == (entry8==entry9)`이면 후보 높이는 `f32(rawContactY+f32(contactDistance*contactNormalY))`, 아니면 rawContactY이다. 후보가 현재 PC1d8보다 클 때만 높이를 쓴다. 선택 재질 id는 높이 max가 바뀌지 않아도 쓴다. contact normal-Y 기준으로 선택하는 전체 loop와 material conversion은 [판독]이며 실행 fixture는 선택 contact block에 입력했다.

일반 모드의24618fc(kind1)은 기존 RespawnTime 보간266c838의 두 결과를 각각 정수 절삭하고 `58bbd2c + trunc(index16) + trunc(index17) + RefereeCorrection`을 구성한다. WaterFall 타이머는 이 합을160..300에 제한한다. 별도 전역58e87a4가 켜진 가지는58bbf90=160을 쓴다. Mission branch의 실제 동작은 범위 밖이며 원본에 별도 가지가 있다는 판독만 유지한다. 초기 T+a0은 몸 위치y, T+a4는 원본 FMAX(velY,−0.1), T+ac는 −10 또는 CoopZombie+eec 입력에 따른1이다. FMAX는 NaN을 전파하며 FMAXNM으로 바꾸지 않는다.

### 6.4 WaterFall은 카메라 위치가 아닌 법선 목표를 바꾼다

```text
n = B.surfaceNormal
if Bdf0 >= 1:
  n.y = f32(n.y + f32(max(0, f32(Bdf4 - C124)) * f32(0.4)))
  length = native f32 SQRT(f32(f32(nx*nx + ny*ny) + nz*nz))
  if length > 0: n *= f32(1/length)
  if length < 0.01: n = B.surfaceNormal
기존 native1252ff0(n, C138, rate=0.1)의 소비로 이어짐
```

**2026-10-03 정정:** 기존 §7 “본체+df4 높이(카메라 y와의 차×0.4)만큼 주시점 방향을 위로 기울임, 수몰·낙하 추정”을 그대로 삭제하지 않고 남긴다. 원본24da0b0..24da160은 `C124=followpointY`와의 양수 높이 차로 **표면 법선 목표**를 바꾼다. WaterFall 이름은 기존 damage_hit §4.7.3의 HUD/model writer에서 이미 확정됐고 새 성과로 재계상하지 않는다. 이번에는 물리 Water contact 높이 및 원본 카메라 소비까지 새 근거로 연결했다.

### 6.5 IkuraShoot/Gachihoko의 직접 번호 writer

`2471940 add x1,x21,#588 → 2471970 BL249257c`로 W의 기준을 확정한다. 함수의 `249347c..3484`는 W+a1f0=Ba778을, `2493498..349c`는 W+a208=Ba790을 읽는다. 실제 actor virtual IsA(token58d6a28)가 true이면 **24943a4에서 B65c=0x13**을 쓰고 IkuraShoot+30에 actor를 바인딩한다. token58d6858이 true이면 **24944f0에서 B65c=0x16**을 쓰고 Gachihoko+30, native25a9ce4에 actor를 공급한다. 이는 특수 동작 자체를 분석한 것이 아니라 카메라 입력 번호의 typed producer 판독이다. 원본 명령 snapshot은 `source_audit.json`에 남겼다.

**2026-10-03 정정:** 기존 §6.2의 두 이름 [추정—강함]을 직접 writer의 [판독]+기존 component 표의 [데이터]로 정정한다. 이 조사 시점에는 “모든 B65c 값은10+열거 인덱스”를 보편식으로 확정하지 않았고 NoSpecial/FullGauge의0xa/0xb 공급을 미확정으로 남겼다. 후속 §6.8에서 이 classifier의 전체 조건부 표와 실제 원본 실행을 연결해 기존 보편식 추정을 대체한다. 다른 writer/모든 runtime 상태까지 닫은 것은 아니다.

### 6.6 B9315 요청의 실제 owner와 local transform 생산자

새 `request_sources.c`의 실제 시작은 **215363c**, **21b9c8c**이다. native prologue/RET와 원본 VT slot22를 대조했다. func_lookup의 가까운 함수2152a74/21b8504는 해당 PC를 포함하지 않아 그대로 시작으로 사용하지 않았다. VT560dbf8의 slot22=215363c는 원본 getName2151438의 **spl::GateManhole**, VT56123f0의 slot22=21b9c8c는 getName21b5554의 **spl::MissionGateway**이다 [판독]+[데이터]. 가까운 다른 기믹 이름을 owner로 쓰지 않는다.

GateManhole은 contact에서12d4228로 PlayerBehavior를 얻고 B1054·Ba5f8·2f63cac·원본 `Progress` 상태 및 manager gate를 확인한다.12d485c가 승인한 contact의 side에 따라 접점에 `distance×normal`을 더하거나 원래 접점을 쓴다. owner physical translation을 빼고 owner X/Z축에 투영한 거리 `sqrt(localX²+localZ²)`를 원본 resource+30 반경과 비교한다. component+150의 timer gate도 통과해야 한다. 원본 `player_point` 문자열488e785로 component+188의 named transform을 찾아0f61bbc가 local3×4를 공급한다. 없으면 기존 SDK identity5823b50을 쓴다. identity의 생성 근거는 기존 [stage_misc.md](../gimmick/stage_misc.md) §1.5를 재사용하며 신규 상수로 세지 않는다.

MissionGateway는 component+160·+1e4, PlayerBehavior/B1054, 선택2f7a4e0 및12d485c gate를 확인한다. 같은 contact side와 local X/Z 투영을 사용하지만 **sqrt가 아닌 거리 제곱과 반경 제곱**을 비교한다(resource+50). owner component 배열+208에서 원본 인덱스26의 component를 얻고 원본 record56123d8→문자열488e785의 `player_point`를0f61bbc로 읽는다. 없으면 같은 기존 SDK identity를 쓴다. 두 기믹의 전체 동작을 이 카메라 입력 생산자 판독으로 확정하지 않는다.

```text
Gate2153a6c / Mission21b9f6c: B9315=1 먼저 씀
if B932c != 0:
  native3c838dc(B9318 ActorRef, component+10 ownerActor, mode=0)
Gate2153a8c..ac4 / Mission21b9f8c..fc4: local48B → B9330..B935f
Mission21b9fc8: component+1ef=1
B9314는 이 구간에서 쓰지 않음; 후속 slot18의 변환 생산자가 활성화
```

원본3c838dc의 initial generation−1/mode0 경로는 owner+1a8 handle이 유효하고 owner+24 state가7..11 밖이면 ActorRef+8에 handle, +10에 owner+10 generation, +15에0을 쓴다. 그 밖에는 이전 ref를 유지한다. B932c는 이 ref 내부+14이므로 독립 bool 구조체로 분리하지 않는다. 이전 유효 참조의 release/rebind 및 manager 유지 경로는 이번 실행에 포함하지 않았다.

**[실행]768건:** Gate2153a5c..2153ac8과 Mission21b9f60..21b9fcc를 각각384건 실행했다. B932c=0/1/255, owner state0/6/7/8/9/10/11/12, handle null/유효, raw local48B의 NaN 비트 패턴을 포함했다. 실제3c838dc 호출512회이며 함수·SDK·PLT·수학 stub0이다. request·ref·local bytes·Mission flag 모두 일치했고 active의 이전값도 보존됐다. scene/contact/named lookup 전체는 실행하지 않았다.

### 6.7 q21 플레이어 필드 의미와 실제 이벤트 채널

q21의 고정 질문은 아래 플레이어 필드의 의미이다. 이미 확정된 속도·spring·입력 producer를 재분석하거나 신규 실행으로 세지 않고 새 B9210/B9212 구독 연결과 합친다.

| 플레이어 필드 | 원본 의미·writer/consumer | 원본 근거·확정 수준 |
|---|---|---|
| B9210/B9214 | BeforeGameSelector가 생성하는 typed 채널 구독 callback24cb3ec에서1을 쓰는 latched flag | nodeBaa18/key58963e8,2457ff4→245800c,등록2352fec→0f3de98; 새 [판독]+[데이터] |
| B9212 | GameEndSelector가 생성하는 typed 채널 구독 callback24cbca8에서1을 쓰는 latched flag | nodeBab78/key5853238,2458170→2458184,등록235303c→0f3de98; 새 [판독]+[데이터] |
| Bf34 | RespawnLand phase: T=Bd58, T+178=Bed0의+64 | 기존245fd38 초기1,2475a54 상태 writer,246292c phase5→0; [player_life.md](../combat/player_life.md) §6.8.1·6.8.4 [판독] |
| B73c | 일반 점프·중력의 프레임당 수직 이동량 | 기존24a7d00/점프 writer와245aed8 최종 합; [movement_physics.md](../player/movement_physics.md) §4.1·6.4·6.7 [판독]+기존 [실행] |
| B754 | B750 3D 점프 벡터의 Y 성분; 벽·경사·공중 전이 입력을 포함 | 같은 문서 §4.1·6.4 및 [r9_state_sources.md](r9_state_sources.md)의 수직 consumer; 기존 [판독] |
| Bcf0 | 카메라 추가 높이 spring 출력: Bcd0+Bce4 | 기존248e14c..248e638의 상태 적분·합, [movement_physics.md](../player/movement_physics.md) §6.4.6; 기존 [판독]+[실행] |
| Ba9c/Baa0 | UD/LR reverse 옵션을 적용한 오른쪽 스틱 X/Y | 기존24a73b8 writer와249f494 caller; [player_camera.md](player_camera.md) §4.1·6.4; 기존 [판독]+[실행] |

Bf34를 PlayerStartLaunch의 phase로 명명하지 않는다. RespawnLand의 초기1 및2..5 writer는 기존 life 문서에 있고 당시 추정으로 둔 각 phase의 자연어 이름을 새 확정 이름으로 옮기지 않는다. B754 또한 벽 차지 수직 impulse만으로 축소하지 않는다.

새 이벤트 대응은 원본 ctor의 **node+48=typekey**, node+28=functor VT, +30=context/body, +38=callback에 따라 분리했다. B9210 nodeBaa18의 key는58963e8(guard58963f0), B9212 nodeBab78의 key는5853238(guard5853240)이다. actual thunk24cc16c/24cc404는 context/callback/adjust를 읽고 callback으로 tail branch한다. 생성 메시지의 실제 VT56aceb0/56ad828 slot0/1은 각각 IsA308937c/key getter30894e0와 IsA3094198/key getter30942fc이며 각각 같은 원본 key를 읽는다. 이 함수 pointer 대응은 원본 qword로 직접 대조했다.

원본 getName3089364/3094178의 문자열은 **SplVersusBeforeGameSelector/SplVersusGameEndSelector**이고 VT56acd58/56ad6d0과 위 generated channel을 잇는다. BeforeGame의 actual node3082158은3083158에서 node+60과 virtual+138 결과 byte가 달라질 때30831ac의 message VT56aceb0을 queue에 넣는다. GameEnd의 actual node309377c는3093910의 message VT56ad828을 같은 queue에 넣는다. 두32B message는 global582b7c0의 allocator+d0, tail+e0, mutex+108을 사용하고 +8/+10/+18에 원본 VT 및 interface pointer를 쓴다. 이는 원본 발행 구간 [판독]이며 실제 Lby phase 활성화를 실행한 결과는 아니다. node+60의 의미를 이름으로 추측하지 않는다.

clear callback24cb3d4는 B9208의8B와B9210/9211의2B 및B9214를0으로 쓰며 **B9212는 지우지 않는다**. 이 구독 nodeBa9c0/key5896978은 원본 SplVersusFreeTest(getName308a8e8/IsA308a900)의308a0fc enqueue와 대응한다 [판독]+[데이터]. 초기화/reset의 다른 writer는 기존 상태 근거를 재사용한다.

**2026-10-03 정정:** 이전 r9_state_sources §11 및 이 문서 §11의 “245800c/2458184에서 callback과 typed token58bc348을 등록”을 보존하고 바로잡는다.58bc348은 **다음 nodeBabd0/다른 callback24cbcb8**, 원본 SplVersusResultSelector 채널이다. ctor는 callback을 설치한 뒤 다음 node의 key를 읽으므로 인접 load를 같은 구독 key로 연결한 것이 오인의 원인이다. 실제 B9210/B9212 key·node·writer는 위 표와 다르다. `event_source_audit.json`에 실제 명령·VT·getName·queued message 대응을 보존했다.

이 표로 q21의 **필드 의미**는 [판독]+[데이터] 해소를 권고한다. queued message→global5801908 bus의 실제 delivery와 모든 상태 event 도달은 별도 미확정이다. 당시 미확정으로 남긴 Demo+34/+bf4의 직접 producer는 후속 §6.9에서 해소했고 script/scene sender 전체는 분리해 남긴다.

### 6.8 q10의 보편 번호식 정정과 실제 전체 classifier 표

**2026-10-03 후속 정정:** 기존 “P65c는10+특수 열거 인덱스”는 무조건적 생산 규칙으로 쓰면 틀린다.249257c는 enum 산술을 실행하는 대신 **변경된 비null special actor의 실제 WeaponSp IsA를 순서대로 검사하고 아래 literal 코드를 저장**한다. `W=B588`의 `W+d4=B65c`이다. 새 actor가null이면2493430→249353c, 이전 primary actor와같으면2493438/3440→2493554로 이 분류 쓰기를 건너뛴다. 뒤의 함수 전체 update가 B65c를 영구 보존한다는 별도 주장은 하지 않는다.

원본4960049의 comma 문자열은21개 항목이며 아래index는 이 문자열 목록을0부터 센 **위치**이다 [데이터]. 실제 `spl::WeaponSp*` actor의 getName/VT slot0 IsA가 아래token을 비교한다. classifier의 해당 성공 분기는 원본MOV w8의literal 및STR w8,[x22,#d4]로 코드를 쓴다 [판독]+[데이터]. 실제 serialized enum 값의 전체 writer나 특수 동작을 분석한 표가 아니다.

| 목록 index | 원본 label·실제 WeaponSp actor 접미사 | IsA token | 저장 코드 | 코드 설정 PC → 저장 PC |
|---:|---|---|---:|---|
| 0 | NoSpecial | 이 classifier의 actor 분류 항목 아님 | 이 표에서0xa로 생성하지 않음 | 자동 `10+0`을 넣지 않음 |
| 1 | FullGauge | 이 classifier의 actor 분류 항목 아님 | 이 표에서0xb로 생성하지 않음 | 자동 `10+1`을 넣지 않음 |
| 2 | SuperShot | 58d7480 | 0xc | 24936c8→24936cc |
| 3 | UltraShot | 58d7620 | 0xd | 2493754→2493758 |
| 4 | GreatBarrier | 58d6958 | 0xe | 24937c8→24937d0 |
| 5 | SuperHook | 58d72e0 | 0xf | 24946e0→24946e8 |
| 6 | MultiMissile | 58d6ed0 | 0x10 | 2493878→2493880 |
| 7 | InkStorm | 58d6af8 | 0x11 | 24938cc→249391c |
| 8 | NiceBall | 58d6fa0 | 0x12 | 2493918→249391c |
| 9 | IkuraShoot | 58d6a28 | 0x13 | 249439c→24943a4 |
| 10 | ShockSonar | 58d7140 | 0x14 | 249442c→2494434 |
| 11 | Blower | 58d6508 | 0x15 | 24944a8→249391c |
| 12 | Gachihoko | 58d6858 | 0x16 | 24944e4→24944f0 |
| 13 | MicroLaser | 58d6e00 | 0x17 | 2494618→2494620 |
| 14 | Jetpack | 58d6d30 | 0x18 | 24947fc→2494804 |
| 15 | UltraStamp | 58d76f0 | 0x19 | 24948bc→24948c4 |
| 16 | Chariot | 58d6668 | 0x1a | 2494914→249491c |
| 17 | Skewer | 58d7210 | 0x1b | 2494a00→2494a08 |
| 18 | SuperLanding | 58d73b0 | 0x1c | 2494a50→2494a58 |
| 19 | TripleTornado | 58d7550 | 0x1d | 2494a9c→2494ad8 |
| 20 | EnergyStand | 58d6788 | 0x1e | 2494ad4→2494ad8 |
| 해당 없음 | 위19타입이 아닌 actor | 모두 불일치 | 0 | 2494b94의STR wzr |

따라서 **해당19종 분류 성공에 한해서** 결과는 이 문자열index2..20의10+index와 일치한다. 이는 발견한 원본literal 표의 규칙성이고 모든 B65c 값의 생산식을 `10+enum`으로 대체할 근거가 아니다. NoSpecial/FullGauge를 무조건10/11로 생성하지 않으며 다른 B65c writer의 부재를 주장하지 않는다. 특히 활성 상태를 확인하는 카메라의 `B678==B688≠0 OR B588==B598≠0` 조건과 이 타입 분류는 별도 계약이다.

**[실행]110건:** `r10_camera_state_classifier_emu.py`는 원본249368c부터 **실제 각 actor VT/IsA 및 공통부모26ea3a0을 실행**하고 첫 B65c store 직후 멈춘다.19종과 실제 ordinary WeaponShooter VT5652468의 불일치fallback0을 이전B65c=0/10/11/18/0xffffffff로 각각 대조하여100건 모두 일치했다. 선택 gate2493430의null/same-primary는 skip PC까지10건 실행하여 해당 구간의 이전값 보존을 확인했다. 실제RTTI 호출1045회, 함수·SDK·PLT·수학stub0이다.

원본 guarded type descriptor의24개 **ready byte=1은 초기화 후를 가정한 합성 입력**이다. 원본 guard 초기화나 전체249257c를 실행한 것이 아니다. 실제 물리 actor 생성·특수binding/동작·field writer 전수 부재 및 모든 frame상태는 미검증이다. classifier_data.json에는19개의 실제getName/VT/IsA token, literalMOV와STR를 직접assert한자료를 저장했다. 이 자료로 q10의 **보편식 추정 자체를 조건부 원본 규칙으로 정정하여 해소**하는 것을 권고하며 q35/36의 전체 상태 공급은 그대로 남긴다.

### 6.9 PlayerDemo의 실제 CanControlCamera·Time 공급

실제 PlayerDemo VT5634a68의 slot16은 **23613ec receiver**, slot20은 **250b8f0 tick**이다 [데이터]. D=[B+a650] 생성 연결은 기존234b580/SHARED95를 재사용했다. 함수 목록은23613ec를 앞 함수의 끝으로,23655a0/23655b8을 이전 함수 근처로 반환한다. 실제 VT 및 raw prologue/앞 RET로 시작을 확인하고 새 C를 저장했다. 전체 receiver에는 다른 명령이 있지만 이번 실행은 아래 세 camera 입력 명령에 한정한다.

| 원본 파라미터 | VT / typekey / 함수 | 원본 이름·필드·기본값 |
|---|---|---|
| control flags | 56228a0 / 58b4218 / default2363fe4·parser2363ff4·IsA2367088 | CanMove+40=0, **CanControlCamera+41=0**, CanDraw+42=1 |
| timed direction | 5623020 / 58b4288 / default23655a0·parser23655b8·IsA236bb14 | IsSquid+40=0, Dir+44=(0,0,1), **Time+50=−1** |

두 parser는 실제 이름 문자열을 비교하여 stride0xd0 row의+a0 scalar 또는+a0/+a8 vec3를 복사한다. 같은 이름이 여러 번 나오면 뒤 값이 이기며, count가 capacity를 넘은 반복은 첫 row를 읽는 원본 경계를 그대로 따른다. 사용자의 bool 값이라고 보고 raw byte를0/1로 정규화하지 않는다. 원본 control parser는 기존camera/batch1.c를 재사용했다.

```text
receiver23613ec, msg.id=6e9f8200:
  payload=null 또는 actual IsA58b4218 불일치 → 0
  (*580dec0)+1a9 != 0 → 1, flags는 그대로
  그 밖: D31=0, D30=1, payload40/41/42 → D33/34/35, 반환1
msg.id=6e9f8201:
  global1a9!=0 또는 D30==0 → 1, 그대로
  그 밖: D30=0, D33..36=1, 반환1
msg.id=6e9f8228:
  payload=null 또는 actual IsA58b4288 불일치 → 0
  Dir12B → Dbe4..bec
  Dbf0 = native FMAX(Bd3c, f32(.3))
  Dbf8 = payload.IsSquid byte
  Dbf4 = (Time < 0) ? FLT_MAX : Time
```

`(*580dec0)+1a9`의 실제 이름은 [미확정]이다. 이를 menu/network bool로 지어내지 않는다. timed 메시지에는 이 global gate가 없으므로 control 메시지에 있는 조건을 옮겨 붙이지 않는다. Dbf0의 FMAX는 FMAXNM이 아니다. Time의 원본 FCMP+FCSEL MI는 **−0을 −0으로, NaN을 입력 raw bits로 보존**하며 음수일 때만 FLT_MAX를 쓴다. 디컴파일의 `0<=Time ? Time : FLT_MAX`는 NaN에서 틀린 의사코드이므로 위 원본 명령식으로 정정한다.

```text
whole tick250b8f0, queueCount=0 실행 범위:
  D32=0
  if Dbf4 > 0:
    Dbf4 = f32(Dbf4 + f32 bits0xbc888889)   // −1/60초
    if 새 Dbf4 <= 0:
      Dbe4..bf8의21B를0으로 씀
    else:
      if Dbf8 != 0: D32=1
      if signed Bad0 <= 1: Bad0=2
```

만료 쓰기는 STP의16B와 +0xd 위치의 비정렬8B가 겹쳐 정확히21B를 지운다. 처음 잔여가0·음수·NaN이면 감소하지 않는다. +∞ 및 FLT_MAX는 작은1/60 가산으로 줄어들지 않는다. 새로운 양수 잔여에서만 자세 타이머Bad0 하한2를 올린다. 이 writer는 부모 [r10_posture_timer.md](r10_posture_timer.md)에도 연결했지만 **동일922사례를 부모 timer 실행 건수에 다시 합산하지 않는다**.

**[실행]922사례, mismatch0:** 기본값2, control parser64, timed parser64, receiver control192, receiver timed216, empty-queue tick384. 원본 typed IsA2367088을36회,236bb14를246회 실제 실행했다. 함수·SDK·PLT·수학 스텁0이며 constructor 초기화 guard 세 byte를 ready1로 둔 것은 합성 post-init 입력이다. D 전체0xce8B와 Bad0의 기대 bytes를 대조했다. queued command가 있는 tick/allocator/전체 ctor/script sender/실제 scene 연속 실행은 검증하지 않았다.

### 6.10 피치 자동복귀 reader와 입력 차단 predicate의 차이

**2026-10-03 정정:** 기존 “조작 불가이면 p→0”을24c99f0의 반환과 같은 조건으로 해석하면 틀린다. 피치 reader는 기존camrest/cam_main_full.c 4940~5050 및 원본24e2d80..24e2ea8/24e407c..24e4390의 별도 branch이다 [판독]. 다음 표는 원본 실행 순서이며 p=C16c, r은 이 지점까지 생산된 s9 계수이다. 기존 자동복귀 산술 근거를 새 실행 성과로 세지 않는다.

| 우선순위 | 실제 조건 | 결과·의미 |
|---:|---|---|
| 1 | !(B9212 \|\| B9210 \|\| Demo34) | p += r×(0−p); typed GameEnd/BeforeGame flags 및 **CanControlCamera** |
| 2 | [B+a6c8].38가0/5 밖 | 같은0 복귀; 실제 PlayerMissionTicketGateAction 상태 |
| 3 | SM ef/f0이며 선택 wrapper frame<=95, 또는 SM f1, 또는 SM f2이며 frame<=50 | 같은0 복귀; 기존 SM 이름 MsnAppear/MsnAppear_Landing/WorldAppear를 재사용 |
| 4 | MissionSeqPinch.38가3/4, 또는 CoopSeq.38가5..8 | 같은0 복귀; 컴포넌트·raw 상태값 판독, 해당 mode 전체 동작은 미분석 |
| 5 | B9314!=0 | p += (−.5−p)×f32(f32(Bdc×.09)+.01); §6.1/6.6의 actor affine 연출 |
| 6 | Scene_Versus && (((!B9213 && Coop1348!=12) && (B9211 \|\| Bd58>0 \|\| Bf34∈{1,2,4})) \|\| B9210) && uint(Bf34−2)>2 | p += .2×(0−p); Ready/Result/리스폰 상태 조합 |
| 7 | [C1940].38∈{1,2,4} | p += .1×(0−p); 같은 typed MissionTicketGateAction |
| 8 | 앞 조건 불충족이고 해당 계산 활성 | 일반 target blend; C1868이 켜져 있으면 한 번 지우고 p 유지 |

**중요한 차이:** 피치 branch는 Demo34를 첫 OR에만 넣는다.24c99f0 후반의 `Demo34==0`, `DemoBF4>0`, Dokan30=1/2, S1c 및 최종 Coop mask 검사를 그대로 복사하지 않는다. timed Dir가 입력을 차단한다고 해당 피치 branch가 직접0 복귀하는 것으로 바꾸지 않는다. frame NaN은 원본 FCMP+B.LS에서 문턱 복귀하지 않으며 unsigned Bf34−2와0x16 mask의 범위를 보존한다. 이후 Water/AirFall p 제한도 별도 단계이다.

**B9211 [판독]+[데이터]:** 기존cached respawn/batch1.c의24cb4cc는 끝24cbb08에서1을 쓴다. ctor2458020..2458054가 구독 nodeBaa70에 실제 key5896968을 넣고245806c에서 이 callback을 설치한다. actual getName309d440은 **SplVersusReady**, message VT56adf58/IsA309d458이 같은 key를 사용한다. 다음 node의 guard58bc330을 현재 node key로 오인하지 않는다. 이 latch를 단순한 GameStart bool로 재명명하지 않는다.

**B9213 [판독]+[데이터]:** 실제24cbcb8 끝24cbefc..24cbf08이1을 쓴다. nodeBabd0의 key58bc348은 actual **SplVersusResultSelector**(getName30aa0cc/message VT56ae348/IsA30aa0ec)와 대응한다. Ready/Result callback 전체 cleanup 및 mode 동작은 실행하지 않았으며 typed channel 의미와 flag store만 이번 질문 근거로 사용한다.

**Scene_Versus [기존 판독]+[기존 데이터]:** SHARED245의2b546e0은 전역58e877c를 Scene_Versus로 연결하며, SHARED520/r6 seed 자료가 원본 Tag.Product.100의 **LobbyVersus 행4272/태그열160 Scene_Versus=0**을 이미 확정했다. Lby_Lobby00은 shooting_range §1·2의 LobbyVersus pack 배치이므로 위.2 branch의 이 guard는 범위 내 실제 scene 자료상0이다. 원본 r6 태그 판정 실행의 스텁 경계는 기존 문서대로 유지한다. 이번 태그 재독출은 신규 실행이나 새 확정률로 다시 세지 않는다.

**Coop1348 [부분 판독]:** 실제 PlayerCoopSeq ctor2500b0c는 이u32를0으로 초기화하고 node+1370/key5861808에 callback2500fe4를 연결한다. callback 첫 명령은 **message+18 u32→component1348** 복사이다. message VT56830c0/IsA2c86a90이 같은 key를 쓰며 native2c850ac의 queue producer는 payload+18에13을 쓴다. 이로써 raw notification 값의 직접 producer는 닫았지만 카메라가 비교하는12의 enum 이름은 미확정이다. 원본16label `spl::CoopSequenceSignalType`의 Result index12와 다른12label 목록의 Result index11이 모두 존재한다. typed channel field와16label descriptor의 직접 연결을 못 닫았으므로 비슷한 문자열만으로12=Result라 쓰지 않는다. 다음 근거는3499284의16label producer와 key5861808 message의 typed field/발행자 연결이다. 다른 mode의 실제 동작까지 분석 범위를 넓히지 않는다.

### 6.11 VehicleSpectacle Controlled의 실제 참조·메시지·카메라 공급

**범위와 이름 [판독]+[데이터]:** 원본 class는 `spl::VehicleSpectacle`(VT5617bb0/getName2231114), 플레이어 component는 `spl::PlayerVehicleSpectacle`(VT563f428/[B+a6d8])이다. readonly `extracted/romfs/Pack/Actor/VehicleSpectacle.pack.zs`의 ModelInfo는 `Npc_RailKingSpace_Field.fmdb` 및 `Cockpit/Robo/Vacuum/Hatch` submodel을 지정한다. Cockpit RigidBodyEntityParam은 `ShapeName=Cockpit`, `LayerEntityGround/SubLayerGround`, `MotionType=Kinematic`, `HitAll`이다. 이 원본 이름과 cockpit 탑승 관계로 C1918의 상황 의미를 정한다. 지역화 명칭·특정 스토리 진행이나 Lby 배치 유무를 해당 이름에서 추론하지 않는다.

**actor 진입 공급 [판독]:** VT slot22 contact2238460은 pair side/body를 원본 flag로 고른다. `[component+698]+38==2`, 태그 predicate12d3e10의 실제 token58e88b0, body 가상 이름 `Cockpit`(원본 문자열49721f2), 12d485c gate, component402!=0, component60c의 원본 FCMP/B.GT gate, `[component+6b8]+38==1`을 통과하면 component39d=1 뒤223863c에서 actor FSM을3으로 전환한다. token58e88b0의 자연어 이름은 이번에 확인하지 않았다. float 비교를 JS의 `<=0`로 단순화한 NaN 계약은 주장하지 않는다.

setup22314e4..22315bc는 index3을 실제 문자열48a0a5d의 `State::Controlled`로 등록하며 enter22337bc/tick2233bf0/exit2234ce8을 둔다. enter22337bc는 원본 payload VT56730e0을 구성하고 `[component+10]`의 **차량 owner ActorRef**를 payload+b0에 넣는다. 21ac320으로 선택한 player 참조를0f81a90으로 해석하여 target ActorId+358을 얻고,2233a3c의17adcec에 `id=0x6fe76000`과 payload를 전달한다. 선택 player 참조의 전체 mode 선택 및 message bus delivery는 새 원본 실행 범위가 아니다.

**player 수신·참조 공급 [판독]+[실행:선택경로]:** 실제 receiver24341ac는 VT563f428 slot16이며 message+4의 id와 message+10의 payload 포인터를 읽는다. start6fe76000은 null payload를 거부하고 가상 slot8 IsA로 token5872a58을 검사한다. actual payload VT56730e0의 IsA2b50078을 원본 실행했다. 허용 시 몸 B+10..18의12B를 V+90..98에 복사하고, `V+78 != payload+b0`이면3c837c8으로 목적 참조를 정리한 뒤3c83bc4(mode0)로 복사한다. 이전의 직접3c838dc+ADD78 후보 검색으로 이 writer를 못 찾은 이유는 **실제 공급이 copy binder3c83bc4**였기 때문이다. empty/invalid 참조 합성 fixture만 실행했으며 유효 handle의 thread/lock/retain 수명은 미실행이다.

start command VT563f5c8과 stop command VT563f600은16B `{vt, component}`로 clone되어 V+a8 queue에 delay0으로 들어간다. stop6fe76001은 payload/type 검사 없이 수락하며 unknown id는0을 반환한다. 별도6fe76002 명령의 affine 소비는 이번 수명 범위에서 분석·실행하지 않았다. generic1256c54는 실제 SDK memset 뒤 node를 연결하고 delay를 `float(int(seconds*60))`로 저장한다. 실제1256b40 tick은 delay−1 후 command를 호출한다. start26b18d8은 원본125a178로 player FSM+30에 state1, stop26b1964는state0을 요청한다. 기존 Controlled entry26b0bd4의 C1918=1 및 exit26b0ebc의 C1918=0/ActorRef 정리를 재사용한다. 새 실행은 이 callback **진입 직전**까지만 진행했으며 physical callback 및 C1918 store를 실행한 결과로 부르지 않는다.

**종료 공급 [판독]:** actor Controlled exit2234ce8은 다음 actor state가7이 아닐 때6fe76001을3e0db84로 보낸다. next7이면 해당 발행을 건너뛰며 setup22318f4가 등록한 state7 exit2236800에서도6fe76001을 발행한다. sender의 실제 queue/bus 배송·actor tick/scene 프레임을 연속 실행한 것은 아니다. 이 경계는 종료 message의 존재와 player receiver/FSM 요청의 원본 계약을 부정하지도, 전체 runtime 완성을 뜻하지도 않는다.

**2026-10-03 결론 정정:** 이전 “VehicleSpectacle Controlled의 실제 요청 supplier와 ActorRef+78 writer 미확정”은 위 actual cockpit contact→Controlled3→typed start/ownerRef→receiver/command→Controlled1 연결로 해소한다. 고정11의 ‘무엇을 탈 때인지’와22의 ‘켜지는 상황’은 기존 Pipeline contact·Free/Start/RailMove/Finish 및 Dokan0..4 수명 근거와 합쳐 원문의 literal 의미 해소를 권고한다. **실제 Lby 배치·접촉 도달, 유효 ActorRef thread 수명, scene/bus 배송·물리 callback 전체 실행**은 별도 미검증 경계로 유지한다. 이들이 모두 확인됐다고 승격하지 않으며 원래 질문을 전 scene 동작 질문으로 확대하지도 않는다.

## 7. 애니메이션·이펙트·소리·카메라·에셋 연결

S 진행의0xed/0xee는 기존 원본 상태표의 Dive_St/Dive_Ed이다. 이 이름으로 요청 actor의 실제 종류나 일반 잠영과의 동일성을 추측하지 않는다. WaterFall은 기존 HUD/model 표시 WaterFall=1, TroubleType WaterFall=2와 연결되며 AirFall(Bde0), Dying(Bd60), respawn(Bd58)와 구별한다. 기존 Lby 원본 collision Water row14의 평면 높이−0.05는 [collision_mesh.md](../gimmick/collision_mesh.md) §3.5의 [데이터]이다. 실제 어떤 연습 경로에서 물에 빠지는지는 이번 합성 contact 실행으로 확인한 내용이 아니다.

S.forward 소비는 입력 yaw를 자동 방향에 혼합하는 기존 카메라 분기로 이어진다. 사용자의 “제자리에서 마우스로만 시점 변경 중 갑자기 돌아봄”을 이 상태 연출의 원본 정상 동작이라고 결론 내리지 않는다. 현재 웹 mouse 이벤트와 pose 소비는 [mouse_view_jumps.md](mouse_view_jumps.md)의 별도 실제 웹 재현 근거와 대조해야 한다.

## 8. 다른 기능과의 상호작용

Water 높이는 충돌 material 및 contact side 방향에 의존한다. 타이머 활성화가 뒤의 카메라 normal target을 바꾼다. B9314 활성은24c99f0을 차단하고 자동 yaw/pitch 가지가 다른 입력을 읽게 한다. 같은 오프셋이 다른 구조체에 있는 경우를 본체 필드 writer로 오인하지 않는다.

기존 DokanWarp §7.2는0/1/2/3/4 상태와 yaw 분기의 `D+c0==2 && t<=0.4`를 원본448사례 및 body 승인12사례로 이미 닫았다. 질문20의 이 미확정은 **기존 근거 정정** 후보이며 새 실행 숫자로 다시 세지 않는다. C1940은 기존 mouse_original_controls의 MissionTicketGateAction이고, rate0.15 자동 yaw의 우선순위는 Dokan→B9314→C1940이다. Mission의 실제 게임 동작은 이번에 분석하지 않았다.

수직 속도 B73c/B754·B744 Jetpack 공중 점프·B782 벽 차지 점프는 r9_state_sources와 기존 movement 근거를 재사용한다. B744를 DashPanel이라고 부르는 기존 impl의 이름은 틀렸으며, 실제 DashPanel은 `[B+a698]+f4/+39` 가지이다. 수직 특수 목표0.6은Jetpack predicate,0.2는GrindRail vt100(0),0.03은GrindRail vt110,0.1은 유효 InkRail/AttractTarget 또는 SuperLanding 상승쪽,0.3은 SuperLanding 하강 및 실제 DashPanel 공급 가지로 읽힌다. 각 actor의 전체 생산 상황을 이번 표 이름만으로 확정하지 않는다.

## 9. 웹 포팅 구조와 구현 순서

이번은 분석 전용이며 웹 source/assets/impl을 수정하지 않았다. 필요한 이식은 다음 순서로 비교한다.

1. 카메라 입력의 blocked를 B9210/B9212 두 byte만으로 대체하지 말고 raw PlayerDemo/Dokan/SM/Coop 입력과 원본 branch 순서를 보존한다. NaN·unsigned 범위 경계도 위 실행 fixture로 검사한다.
2. 자동 방향 producer를 붙일 때 S.active·position·forward·request/handle generation의 수명을 따로 둔다. 확인된 GateManhole/MissionGateway 요청을 일반 마우스 bool로 대체하지 않는다. 전체 supplier·실제 Lby 도달은 별도 미확정으로 보존한다.
3. WaterFall의 source는 물 높이 상수가 아니라 선택 collision contact와 높이 래치이다. world query 공급이 연결되지 않은 웹 경로에서 이번 결과를 raw runtime 값으로 가장하지 않는다.
4. Bdf0가 켜지면 followpointY와의 차를 surface-normal 목표에 가산한다. camera position/atY를 즉시 올리는 다른 식으로 바꾸지 않는다.
5. typed 번호0x13/0x16 이름 정정과 실제 B65c writer를 반영하되 특수 실행 동작은 이번 범위의 이식 항목이 아니다.
6. 피치 자동복귀는24c99f0 blocked 결과를 재사용하지 말고 §6.10의 실제 조건표를 따로 공급한다. Demo34는 `CanControlCamera`, BF4는 초 단위 잔여이며 메시지 객체의 기본0과 component 초기1을 섞지 않는다. 웹에서 실제 message/script 공급이 없는 상태를 임의 매프레임 bool로 채우지 않는다.
7. C1918을 일반 마우스/잠영 bool로 켜지 않는다. 원본은 VehicleSpectacle cockpit의 typed owner ActorRef와 queue/FSM Controlled 수명에서 켜고 끈다. 사격장에 동일 actor가 실제 배치됐는지 확인하지 않은 상태에서 새로운 차량 경로를 웹에 추가할 근거로 쓰지 않는다. 이번은 source 변경 없이 문서와 fixture만 제공한다.

`impl/camera.md`의 피치 자동복귀·대체 리그·수몰 법선·특수 수직 ratio 및 `impl/physics.md`의 Water contact 공급을 대조할 필요가 있다. impl 자체는 변경하지 않았다.

## 10. 검증 코드·실행 결과·기대값

| 실제 실행 도구·원본 구간 | 사례 | 결과·경계 |
|---|---:|---|
| r10_camera_state_emu.py:247b43c..247b4e4 + actualSDK12548f0 | 512 | position/forward/active f32 비트 일치 |
| 같은 도구:247b280..247b294 | 18 | active clear 일치 |
| 같은 도구:whole24c99f0 | 2175 | blocked 반환 일치, NaN/index/byte/문턱 포함 |
| r10_camera_state_water_emu.py:24f84ec..24f862c | 512 | 선택 side·Water tag·높이 max·재질 일치 |
| 같은 도구:248a89c..248e6cc/248e708 | 432 | 높이 래치/유지/−FLT_MAX reset 비트 일치, NaN 포함 |
| 같은 도구:2461d30..2461d90 | 110 | 160..300 clamp·초기 높이/속도·T+ac 일치 |
| 같은 도구:24da0b0..24da160 | 512 | 목표 normal 비트 일치,0/음수/양수 timer 및zero vector 포함 |
| r10_camera_state_request_emu.py:2153a5c..2153ac8 /21b9f60..21b9fcc | 384+384 | request/ref/local48B 및active 보존 일치, actual3c838dc512회 |
| r10_camera_state_classifier_emu.py:249368c→선택 B65c store/실제VT·RTTI | 100 | 19종 literal 및 unmatched0 일치; binding·특수동작 미실행 |
| 같은 도구:2493430→null/same-primary skip target | 10 | 해당 selection gate의 B65c 보존 일치; whole함수 보존 주장은 아님 |
| r10_camera_state_demo_emu.py:2363fe4/23655a0 기본값 writer | 2 | raw 파라미터 기본 bytes 일치; 전체 ctor 실행 아님 |
| 같은 도구:2363ff4/23655b8 전체 parser | 64+64 | named row·중복·capacity 경계 및 vec3 bytes 일치 |
| 같은 도구:whole23613ec의 선택 control/timed 명령 | 192+216 | 실제 parameter VT/IsA282회, raw flags/Dir/Time/NaN 일치 |
| 같은 도구:whole250b8f0 empty-queue tick | 384 | D 전체 bytes·expiry overlap·Bad0 하한 일치; queued command 미실행 |
| r10_camera_state_next_vehicle_emu.py:whole24341ac의 start/stop/unknown 선택 경로 | 192 | null/잘못된 실제VT/실제typed payload·empty ActorRef·raw 위치 bytes·queue clone/연결 일치 |
| 같은 도구:receiver→1256c54→1256b40→command→125a178→Controlled callback 경계 | 96 | start state1/count0/previous 보존, stop exit-before-state-store 순서 일치; callback 본체·queue 완료 이후는 미실행 |

신규 실제 ARM64 실행 총**6071사례(2705+1566+768+110+922), mismatch0**이다. 함수·PLT·SDK math 스텁0, 자동 매핑/불명 반환값 대체0이다. 비교식은 별도 NumPy f32 계산 및원본literal 표이며 입력 actor/contact/component는 합성 메모리이다. T9c 실행은 종료 PC에 stop hook만 둬 state를 쓰지 않았다. request/classifier/demo 도구도 실제 호출 구간의 명령을 실행했고 SDK/math/stub page 진입은0이었다. frame/scene/충돌 loop 전체 실행이나 최종 화면 비트 일치로 승격하지 않는다. 기존 Dokan448·body12 및 r9 ratio4096, 부모 timer10752와 input 실행은 이6071에 포함하지 않는다. Ready/Result·Coop 구독·자동복귀 조건표의 추가 [판독]+[데이터]를 새 실행 건수로 더하지 않는다.

최초 state 도구는 UC.u64 없는 API로 실패했고 직접 memwrite로 정정했다. 최초 Water 도구는 contact block 중간 진입에 불일치 flag fixture를 공급하여512 중 i=3에서 material17/예상34로 실패했다. 시작을24f84ec로 옮겨 원본 side/tag 선택 명령부터 실행하고 기대식을 바로잡은 뒤 위 최종 결과를 얻었다. 최초 request 도구도 expected ActorRef에 내부+14=B932c byte를 반영하지 않아 Gate i=0에서 실패했다. 원본 메모리와 기대 ref의 중첩 byte를 동일하게 구성한 뒤768건 모두 일치했다. 이 실패와 명령은 commands.md에 보존한다.

**차량 후속은 신규288사례(192+96), mismatch0**이다. 이전6071을 다시 실행·계상하지 않으며 담당 누계 보고값만6359이다. 기존 Pipeline/Dokan 실행도288에 넣지 않는다. 함수/SDK/PLT-return/임의 수학 스텁0이다. 합성 입력은 capacity1 pool/FSM records/invalid ActorRef 및 ready guard5872a60/5800d90/58b4220/5824530=1이다. callback PC의 stop hook은 메모리에 값을 쓰지 않는다. start의 state1 저장 뒤 enter, stop의 exit 호출 전 state1 및 queue count1을 독립 기대값과 대조했다.

SDK 연결은 `extracted/exefs/sdk.img`의 실제 dynsym `memset offset581ba8/size0xd0/section2`를 읽어 원본 main PLT3e99f10→GOT576efa8에 **RAM만** 연결했다. mapped SDK base7400000000은 fixture 주소이며 실제 부팅 module base가 아니다. 해당 original SDK memset 명령을192회 실행했다. 수학이나 PLT 반환을 만들어 대체하지 않았으며 SDK의 전체 relocation/loader 부팅을 수행했다고 주장하지 않는다. 유효 ActorRef/OS lock 및 sender·bus·physical callback·scene 전체는 미실행이다. 실제 명령, 경로·Windows glob 오류, func_lookup 경계 함정은 `next_commands.md`에 보존한다.

## 11. 미확정 사항과 추가 분석에 필요한 근거

| 고정 ordinal | 이번 판정 권고 | 남는 계약·다음 근거 |
|---|---|---|
| 6 | 발동 조건의 두 이름 추정 해소; 기존 조건 판독과 합쳐 전체 질문 검토 가능 | Pipeline/1918의 실제 상황은 별도11/22로 남음. 전체 오징어 전역 조건은 r9 근거 재사용 |
| 9 | 상태 의미 일부 해소, 부분 권고 | §6.9·6.10으로 Demo34=CanControlCamera/BF4=Time와 Ready/Result·Scene_Versus 분기를 연결. 남는 직접 의미 질문은 Coop1348 literal12와 실제 typed enum 연결 및 raw mode 상태 코드의 명명. 모든 queue/runtime를 새 완료조건으로 추가하지 않음 |
| 10 | 확정 검토 권고 [판독]+[데이터]+[실행] | §6.8의실제19타입literal분류/unknown0/null·동일skip으로보편식추정을정정.다른writer/전체runtime는35/36의별도미확정 |
| 11 | literal 상황 의미 확정 검토 권고 [판독]+[데이터]+[실행:선택경로] | §6.11의 Cockpit→Vehicle Controlled3→ownerRef/start message→Player Controlled1→기존C1918 writer와 기존Pipeline 공급으로 ‘무엇을 탈 때인지’ 해소. live Lby 배치·유효ref thread·bus/물리 전체 실행은 별도 미검증 |
| 19 | 확정 검토 권고 [판독]+[실행], 이름은 기존 근거 재사용 | 질문의 실제 식을surface-normal/followpointY로 정정. contact/query 및 전체scene 실행은 이 질문 실행 범위 밖의 미검증 경계로 명시 |
| 20 | 기존 근거 정정 권고 | §7.2의 original448+12로 D+c0==2/t<=.4 이미 해결. S/C1940의 전체 producer 질문은9/21/22로 별도 유지 |
| 21 | 확정 검토 권고 [판독]+[데이터] | §6.7의 literal 필드 의미 표: 새BeforeGame/GameEnd typed channel→latched flag와 기존Bf34/73c/754/cf0/a9c producer 연결. 모든 event 도달은 별도 실행 경계이며 literal 상태 의미 질문의 새 완료조건이 아님 |
| 22 | literal 켜지는 상황 확정 검토 권고 [판독]+[데이터]+[실행:선택경로] | C1918=VehicleSpectacle Controlled, Pipeline38=Free/Start/RailMove/Finish 수명, Dokan30=0..4의 기존요청/승인/flight/종료. 전체scene 조합 연속실행·Lby 도달은 확인하지 않음 |
| 33 | 부분·조사중 유지 | literal 이동량 항의 raw guard·Δp·수식·max·평활은r7 §6.8.1/원본640에서 이미 확정. ordinary 슈터24b28b0 및B7a0 r8 producer도 재사용. 고정 기준행에 명시된 모든state/runtime writer는 여전히 미확정 |
| 35 | 부분 유지 | WaterFall 법선·번호 대응만 새로 닫음. 모든 대체 리그/연출모드1/사망메시지/+1550/+1570/벽 자동회전 전체 계약은 미완 |
| 36 | 부분 유지 | Jetpack/GrindRail/SuperLanding/실제DashPanel의 consumer 조건은 기록. 전체 actor/기믹 공급 및 특수 목표 조합 runtime는 미확정 |
| 37 | 피치 reader 조건·직접 producer 보강, 부분 권고 | 실제 피치 branch는24c99f0과 다르며 DemoBF4 직접검사 없음. original 상태 의미 중 남은 Coop1348 enum12 연결은9와 공유. scene 전체 큐실행 미완을 이 literal 질문의 새 완료조건으로 삼지 않음 |

이전 문장 “B9210/9214는24cb3ec, B9212는24cbca8가1을 쓰며245800c/2458184에서 callback과typed token58bc348을 등록한다”는 §6.7의 **2026-10-03 정정**으로 보존·대체한다. 쓰기 callback 자체는 맞지만 두 구독 key는58963e8/5853238이며58bc348은 인접 다른 node이다. callback→flag 및 실제 typed enqueue까지 새 판독으로 닫았고 queue→bus delivery는 아직 못 닫았다. **2026-10-03 별도 정정:** r9_state_sources §11의1e9f5e4/1ea4bd8은 raw `ldr w8,[x0,#348]`로 읽힌다. xref의register page 잔존으로58bc348 참조처럼 나온 후보이며 원본 token 주소를 생성한 명령이 아니다. 이 둘을 callback 이벤트 근거나 다음 확정 후보로 사용하지 않는다.

B9314의 split 구조 writer와 S1d/ActorRef의 외부 생산자 두 개는 찾았다. bounded alias scan 결과는 roots를 모르는 후보 목록이고256byte linear dataflow이므로 “모든 writer를 찾음”의 증거가 아니다. 다음은 나머지S/B92f8 외부 요청 interface·functor body,24bbf10을 호출하는component receiver6c2b6a2b 및slot18 이전 frame단계이다. PlayerPipeline26744e0은 handle을 공급하고2674150은 FSM을 tick한다. 추가 원본 BL 전수 검색에서 incoming24299dc→2429a3c BL26744e0를 찾았다.24299dc는message id4bd02f00와payload+10의typed 검사(virtual+40,token5872a58→553dc00)를 확인한다. emitter는 기존 `gimmick_b2.c`의 **spl::Pipeline VT5613b50 slot22=21d5f88 contact callback**으로,오징어 형태·Dokan상태0·충돌 대상 gate 뒤 같은4bd02f00을17adcec로 보낸다. 실제 Pipeline의 FSM 이름은 원본 문자열 `Free/Start/RailMove/Finish`이다. 전체 sender→message dispatch→FSM tick 연속 실행 및Lby 도달 배제는 아직 미확정이다. 이 추가 판독은 Pipeline 탑승 입력의 직접 공급 연결이며 VehicleSpectacle 상황까지 함께 확정하지 않는다.

질문33의 기존 근거 정정: literal 이동량 항의 산술은r7 §6.8.1/640원본실행에서 이미 닫혔다. `Bad0>0 && !C15d9`, `Δp=현재follow−이전follow`와 `Bc0>=4` 때의 y−B73c, `length(Δp)*(0.5−0.4q)` 및max/평활/출력순서를 포함한다. **B7a0는 이ad0 항의guard가 아니라 앞의 별도wall moveTerm의guard**이다. ordinary 슈터Bad0는24b28b0의posture타이머, B7a0ordinaryproducer는r8 근거를 재사용한다. **2026-10-03 판정 정정:** 앞선 “기존 판정 정정으로 전체 확정 가능” 권고는 고정 기준행이 명시한 상태별writer/runtime 미확정을 충족하지 못한다. 산술과ordinaryproducer가 이미 확정된 사실은 유지하고 q33 전체는부분·조사중으로 남긴다. 부모가 맡은 추가writer 조사는 중복 수행하지 않는다.

6071개 원본 구간 실행·q10조건부 규칙·q21 필드 의미 해소로 위 복합 질문 전체나 camera106을100%라고 말하지 않는다. 상태별 분모·확정률 집계는 부모의 고정 inventory 판정에 따른다.

**2026-10-03 후속 시도·남는 곳:** 처음 q10의 NoSpecial/FullGauge0xa/0xb 공급을 못 찾은 결과는 §6.8의 전체classifier 규칙으로 정정한다. player/state/move cached C의 제한 검색이0건인 것은 전체 원본 writer 부재의 증거가 아니다. fallback0을 열거 index0의10으로 바꾸지 않는다. q10의 번호식추정은 해소를 권고하되 다른 B65c writer/비활성 프레임전체 및 serializedenum 공급은 별도 미검증 경계이다.

q11의 새 원본 `vehicle_supplier.c`는 PlayerVehicleSpectacle ctor26b084c와 getter26b11dc이다. ctor는 typed key5874948의 구독 functor callback26b1330을 연결한다. 실제 callback26b1330은 `component+9c=1`만 쓰며 **Controlled ActorRef+78을 바인딩하지 않는다**. getter26b11dc도 원본component+28의+28c 값과 선택transform+30 f32의 합을 반환하는 구간이므로 요청 supplier 후보에서 제외했다. 실제 VT563f428의 slot20=26b1180은 component+a8 갱신 및FSM+30 tick이다. 기존 Controlled entry26b0bd4/exit26b0ebc와 혼동하지 않는다. 다음은 ActorRef+78의 실제 외부 writer와 FSM의 Controlled 요청(원본125a178의 실제 caller)이다.

**2026-10-03 차량 후속 정정:** 위 ‘다음은 ActorRef+78 외부 writer/Controlled 요청’이라는 이전 잔여는 §6.11에서 actual receiver24341ac→copy3c83bc4→command26b18d8/26b1964→125a178 및 actor sender22337bc/2234ce8/2236800으로 해결했다. ctor callback9c/getter가 실제 supplier가 아니라는 기존 배제는 그대로 맞다. 이전 표의11/22 ‘부분 유지’는 원문 literal 상황 의미에 대해 확정 검토 권고로 바꾼다. Lby 배치·배송·유효ref·physical callback의 별도 미검증 경계는 남기며 다른 영역 확정률로 재계상하지 않는다.

`r10_camera_state_followup.py`는 native3c838dc 직접BL378개에서 직전20명령의ADD78만 검사하여7개 후보를 저장했다.22548fc/2254c20의ADD78은stack별칭용x12이며 binder의x0=stack과 달라 VehicleSpectacle writer 근거로 사용할 수 없다. 좁은 scan은 register dataflow 전수 검사나 virtual caller 부재 proof가 아니다. q36은 기존 InkRail262caf4/262c480/23538f0와 카메라consumer를 재사용했으며 실제DashPanel+f4/+39 및 전체특수 목표의 producer/runtime 조합은 미확정으로 유지한다. 특수 동작 자체나 네트워크 실제 동작으로 분석 범위를 확대하지 않았다.

B9210/B9212 typed 의미와 실제 enqueue를 닫은 뒤 남은 generic delivery는 global582b7c0 queue의head/tail 소비자, 생성 messageVT56aceb0/56ad828 interface와 기존global5801908 bus의0f3de98 등록/1323ea8 broadcast 사이의 adapter가 다음 근거이다. 이를 못 찾은 현재 상태에서 모든 event 상황을0/상수로 메우지 않는다.

**2026-10-03 q9/37 후속 판정 정정:** 이전 권고의 “Demo34/BF4 전체 공급 미확정, 모든 scene sender/queue delivery를 닫아야 질문 완료”를 그대로 보존하되 원문의 범위를 바로잡는다. 고정 q9는 피치 자동복귀의 **상태 의미**, q37은 해당 원본 피치 복귀와 웹 대응의 미확정 질문이다. Demo의 직접 파라미터/receiver/empty-queue tick은 §6.9로 닫혔고 B9211 Ready/B9213 Result 및 실제 로비 Scene_Versus0도 §6.10으로 연결됐다. 따라서 전 Scene sender/모든 queue 연속 실행을 새 완료조건으로 요구하지 않는다. 반대로 remaining literal12의 enum 이름을 유사한 문자열로 채워 전체 승격하지 않는다. 원본 조건표와 typed raw notification 생산자를 제공하고 위 실제 잔여를 부모의 고정 질문 판정에 전달한다.

**bounded 탐색 경계:** TEXT 전수의 정확한 `STR S,[...,#bf4]` 형태는2361cf4/250b9a4 두 개이고 `MOVZ #9213`는31개 후보였다. 별칭·pair store·memcpy/memset까지 다룬 writer 전수 검사는 아니므로 다른 writer 부재를 확정하지 않는다. 원본 parameter typekey 직접xref0도GOT 경유 참조의 부재가 아니다. 추가 Coop13 queue producer2c850ac와16label 메타데이터345f99c/347a2cc는 읽었지만 typed field의 enum 선언을 연결하지 못했다. 이 실패/다음 주소는 demo_source_audit.json과 commands.md에 남겼다. 다른 mode의 실제 플레이 동작 및 네트워크 실행은 이번 분석에서 수행하지 않았다.

**사용자 종료 요청에 따른 잔여:** 차량 후속 이후 q9/37의 Coop raw12 typed enum 명명, q36의 특수 수직 목표 추가 producer는 진행하지 않았다. 기존 부분 판정과 다음 근거를 그대로 유지한다. 전체 카메라100%라고 보고하지 않으며 고정106의 최종 집계·SHARED/FUNCS append는 부모가 담당한다. 본 후속은 보호 경로를 수정하지 않고 MD/analysis/분석도구만 저장했다.
