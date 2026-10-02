# 02. 레플리카 모델·송신 주기·송신 권한

[목차](network.md)

## 1. 개요

게임 쪽 네트워크 단위는 **레플리카**(넷 액터 또는 전역 관리자)입니다. 레플리카는 (a) **상태 요소**(NetState, 값)를 여러 개, (b) **이벤트 요소**(송신·수신 큐)를 하나 가질 수 있습니다. 어떤 기기가 상태·이벤트를 보낼 수 있는지는 **SenderPolicy**가 정합니다. 설정은 전부 데이터 파일에 있고, 코드는 이름으로 타입을 찾아 붙입니다.

사용자에게 보이는 결과: 다른 플레이어 캐릭터는 4프레임마다 오는 상태로 움직이고, 발사·특수 시작·사망 같은 순간 동작은 이벤트로 즉시(다음 송신 때) 재생됩니다.

## 2. 자료

| 자료 | 위치 |
|---|---|
| 액터 넷 설정 72개 | 액터 팩 `Component/Net/*.game__NetParam.bgyml` → `analysis/network/netparams.json`, 요약 `netparams_summary.txt` |
| 전역 레플리카 설정 | `Pack/Bootup.Nin_NX_NVN.pack.zs` 의 `Net/*.game__NetEnlReplicaParam.bgyml`(26), `Net/NetEnlValueParam/*.game__NetEnlValueParam.bgyml`(10) → `analysis/network/bootup_net.json` |
| 파라미터 기본값 | `param_reflect.py` 판독 (아래 표) |
| 코드 | `analysis/decomp/network/net_core.c`, `net_send.c`, `net_player.c` |

## 3. 진입점과 흐름

```
[로드] 액터 생성 → ActorParam.Components.Net → game__NetParam
        ├ ActorType (Player/PlayerGenerate/MapObject/Enemy/EnemyGenerate/PlayerSystem)
        └ ReplicaSetting = game__NetEnlReplicaParam
            ├ Elements[]: BehaviorStateName → 등록 표(0x71012f8db8)에서 상태 타입 생성, Protocol, (값 요소면 Value)
            ├ HasEventElement, EventSendQueueSize, EventRecvQueueSize
            └ SenderPolicy
       전역 레플리카: 0x710129cbfc("Net/" + 이름 → game__NetEnlReplicaParam 로드 → 0x710129cdc4 생성)
            예) "StageBullet"(0x71018b78f0), "HitEffect", "PaintRequest"
       레플리카 등록: 0x710129b08c — 레플리카 ID 범위별 3개 트리(<1000, 1000~1999, ≥10000)

[매 프레임]
  게임 로직 → 이벤트 송신 함수(예 0x71018b7f30) → 권한 검사 → 송신 큐(프레임 스탬프, LifeNumber 첨부)
  GameNet:Send 작업(0x710129193c) → 하위 송신 → [GameNet+0x1c4] = (frame % 4 == 0)
  상태 소유 기기: 플래그가 켜진 프레임에만 상태 객체 작성(예 PlayerNetState, 0x71024890f0)
  수신 기기: 각 소비자가 자기 갱신에서 수신 큐를 훑어 타입 hash로 골라 처리(폴링)
```

## 4. 구조체·필드·열거형

### 4.1 `game::NetParam` [데이터/판독]

| 필드 | 타입 | 기본값 | 근거 |
|---|---|---|---|
| `ActorType` | 열거 `Player , PlayerGenerate , MapObject , Enemy , EnemyGenerate , PlayerSystem` | 0 = Player | 방문 함수 0x7100f4a448, 생성자 0x7100f4a194(+0x38=0) |
| `ReplicaSetting` | `game::NetEnlReplicaParam`(내장 또는 `$parent`) | — | |

열거형 문자열은 sead 방식(쉼표 분할, 위치 = 값)으로 잘라 씁니다(0x710127856c, 0x710127628c 판독) **[판독]**.

### 4.2 `game::NetEnlReplicaParam` [판독 — param_reflect]

방문 함수 0x710127687c, 생성자 0x71012766f4.

| 오프셋 | 필드 | 타입 | 기본값 |
|---|---|---|---|
| +0x58 | `EventRecvQueueSize` | s32 | 32 |
| +0x5c | `EventSendQueueSize` | s32 | 32 |
| +0x60 | `SenderPolicy` | 열거 | 0 (Invalid) |
| +0x64 | `HasEventElement` | bool | false |
| — | `Elements` | 배열 | 비어 있음 (도구가 배열을 못 읽음) |

`SenderPolicy` 열거(`game::NetSenderPolicy`, 문자열 @0x710493accb): **0 Invalid, 1 PlayerIdBased, 2 SessionMasterOnly, 3 Atomic, 4 Anyone, 5 SessionMasterOrEvent** **[판독 — 분할 함수, 값 = 위치]**.

### 4.3 `game::NetEnlElementParam` [판독]

방문 함수 0x7101274ea4, 생성자 0x7101274bd4.

| 오프셋 | 필드 | 기본값 |
|---|---|---|
| +0x30 | `BehaviorStateName` | (문자열) |
| +0x40 | `BehaviorStateArySize` | -1 |
| +0x44 | `Protocol` (`game::NetEnlProtocol` = `Unreliable , Reliable`) | 0 = **Unreliable** |
| +0x48 | `IsBehaviorState` | true |
| +0x49 | `IsBehaviorStateAry` | false |
| — | `Value` (`game::NetEnlValueParam`: `Name`, `ValueType`, `ParamU64/S64/F32{min,max}`, `SeadEnumName`) | |

### 4.4 데이터 표본 [데이터]

액터(72개 NetParam 중 대전 관련):

| 액터 | ActorType | SenderPolicy | 상태 요소 | 이벤트 큐(송/수) |
|---|---|---|---|---|
| `SplPlayer`, `SplLivePlayer` | (기본 Player) | (기본 Invalid) | `spl::PlayerNetState` (Protocol 기본 Unreliable) | 128/128 |
| `BulletBeacon`, `BulletShield`, `BulletSprinkler`, `BulletSpGreatBarrier` | PlayerGenerate | Anyone | — | 기본 32 |
| `BulletBombRobot` 16, `BulletBombTorpedo` 32, `BulletShelterCanopy*` 64, `BulletSpMicroLaserBit` 256 | PlayerGenerate | Anyone | — | (괄호 숫자) |
| `BulletSpBlowerInhale` | PlayerGenerate | Anyone | `spl::BlowerInhaleNetState` | 256 |
| `Gachihoko` | MapObject | SessionMasterOrEvent | `spl::GachihokoNetState` | 32 |
| `Gachiyagura_*` | MapObject | SessionMasterOrEvent | `spl::GachiyaguraNetState` | 이벤트 없음 |
| `PaintTargetArea_*` | MapObject | SessionMasterOrEvent | `spl::PaintTargetAreaNetState` | 8 |
| `InkRailOnline` | MapObject | SessionMasterOrEvent | `spl::InkRailNetState` | 기본 |
| `Sponge*_VS` | MapObject | ($parent `Net/SpongeInfo` = SessionMasterOrEvent) | `spl::SpongeNetState` | — |
| `GachihokoGoal`, `WallaObj*`, `Obj_Yagara*` | MapObject | Anyone | — | 기본 |
| `CoopTurret` | MapObject | **Atomic** | `spl::CooTurretRiderState` | 기본 |
| `SplPhotographer` | PlayerSystem | SessionMasterOnly | `spl::PhotographerNetState` | — |

**일반 탄(`BulletShooterBase` 등)과 대부분의 무기 액터에는 Net 컴포넌트가 없습니다**(3,572개 액터 팩 중 ActorParam `Net` 참조가 있는 것 72개). 탄은 넷 객체가 아니라 이벤트로 복제합니다([05](05_events_combat.md)) **[데이터]**.

전역 레플리카(Bootup `Net/`):

| 이름 | SenderPolicy | 요소 | 큐(송/수) |
|---|---|---|---|
| `StageBullet` | Anyone | — | 32/64 |
| `HitEffect` | Anyone | — | 32/64 |
| `PaintRequest` | Anyone | — | 256/256 |
| `PaintRequestForEmulation` | Anyone | — | 2/256 |
| `ClampDownManager` | Anyone | — | 기본 |
| `VersusRefereePaint`, `VersusRefereeTricol`, `VersusGachiasariDirector` | SessionMasterOrEvent | — | 기본(32/64 등) |
| `VersusRefereeVArea` | SessionMasterOrEvent | `spl::VersusRefereeVAreaNetState` | 32/32 |
| `VersusRefereeVClam/VGoal/VLift` | SessionMasterOrEvent | — | 32/32 |
| `VersusSetting` | SessionMasterOrEvent | 값 `is_valid`, `participant_num`, `require_sequence_id`, `start_clock`(U64) + 상태 6종(StationIdArray, AtomicManage, …) 전부 Reliable | 16/16 |
| `StationInfo` | (기본) | 값 `sequence_id`, `is_valid`, `desired_start_clock`(U64 0~86,400,000), `is_ready`, `user_setting_cnt`, `station_update_count` + `spl::StationNetState` 등, 대부분 Reliable | 8/8 |
| `DebugTransition` | SessionMasterOnly | — | 기본/64 |
| `TestAtomic` | Atomic | 값 `test_value` | — |

값 파라미터: `U32_GameFrame`(0~8,388,607), `U32_LifeNumber`(0~15), `F32_default`(-256~255), `S32_default`, `U64_default`, `Bool_default` **[데이터]**.

### 4.5 이벤트 메시지 스키마 [판독]

0x710129ad24가 `U32_GameFrame`·`U32_LifeNumber` 값 파라미터를 읽고, 등록된 **모든 이벤트 타입마다** 요소 3개짜리 메시지 스키마(0x50 B)를 만들어 GameNet 레지스트리에 넣습니다.

| 순서 | 요소 | 범위 | 송신측 값 |
|---|---|---|---|
| 0 | 이벤트 payload | 타입별 비트([03](03_serialization.md)) | 이벤트 객체 |
| 1 | GameFrame | 0 ~ 8,388,607 | 송신 시 GameFrame 싱글턴(`*0x710580e758`, GOT 0x7105790610) +0x148 (음수면 0) (0x71018b7f30) |
| 2 | LifeNumber | 0 ~ 15 | 송신자 소유 객체의 `+0x28` & 0xF (슈터 0x7102584238) |

와이어 비트 폭은 GameFrame **23비트**, LifeNumber **4비트**(값 요소 write 0x71012a4080: `nbits = 64 − clz(max − min)`, 범위 밖은 포화)이고 payload 다음에 이 순서로 붙습니다 **[실행]** — [03 §3.5](03_serialization.md#35-이벤트-메시지-헤더-비트-폭-판독--실행).

수신 디코드: 0x71018b84d4(스키마, 버퍼, 비트수, &payload, &frame, &life) **[판독]**.

### 4.6 수신 큐 [판독]

수신 큐 객체(레플리카 이벤트 요소 `+0x60`): `+0x38` 항목 배열(항목 0x30 B), `+0x40` 용량, `+0x44` 시작 인덱스, `+0x48` 개수. 항목 `+0x00` = 메시지 스키마 포인터(`스키마+8` = 이벤트 hash32, `스키마+0x48` = payload 객체 크기 상한), `+0x18` = 비트 버퍼(`+0`=포인터, `+0xc`=비트 수).

소비자는 원형 큐를 `i = 0..count-1`, `idx = start + i (용량 넘으면 −용량)` 순서로 훑으며 hash가 맞는 항목만 디코드합니다(슈터 0x7102586af0, DamageHelper 0x7101e421a4, HitEffect 0x71027b7938, 플레이어 0x71024c17d8 공통 패턴). 소비자마다 같은 큐를 따로 훑습니다. 큐를 비우는 시점은 확인하지 않았습니다 **[미확정]**.

## 5. 상태 전이와 수명

### 5.1 송신 주기 — 4프레임 [판독]

GameNet 싱글턴(전역 `0x7105825fd0`, 생성 0x71012916e4, 0x270 B, 작업 이름 `GameNet:Send`):

```
// 0x710129193c  (GameNet:Send 작업 본체)
if (this+0xc8):
    this+0xd0 ->vt[0x88]()            // 하위 송신
    0x710128d200(this+0xd8)
    0x710129bc30(this+0xe8)          // 레플리카 트리 순회, 활성(+0x75) 레플리카마다 0x710129e630
    0x71034bdb3c(this+0xd0)
    frame = *([0x710580e758] + 0x148)
    this+0x1c4 = (frame % this+0x1c0 == 0)    // this+0x1c0 생성자 기본값 4
```

`+0x1c0`에 4 외 값을 쓰는 코드는 찾지 못했습니다(GameNet 포인터 근처 `str [..,#0x1c0]` 검색 결과 없음) **[판독 — 다른 writer 미발견]**.

`+0x1c4`를 읽는 곳 29군데: 플레이어(0x71024890f0), 게임 모드 레플리카(0x7101fe4b04, 0x71020052d0, 0x7103049e20 등), 연어런·미니게임. 플레이어 쪽:

```
// 0x71024890d8 근처 (플레이어 넷 갱신, 함수 0x7102483134 안)
if (element+0x20 == 1 || GameNet+0x1c4):
    PlayerNetState 를 스택에 만들고 채워서 요소에 기록
```

`element+0x20 == 1`은 요소 모드 값으로 보이며(예: Reliable 설정) 의미는 **[미확정]**. 대전 플레이어는 Protocol 기본값(Unreliable)이라 **4프레임마다 = 15 Hz(60 fps 기준)** 로 보냅니다 **[판독 + 데이터, 의미 연결은 추정]**.

### 5.2 이벤트 송신 권한 검사 — 0x71018b7f30 [판독]

```
bool sendEvent(sender, event, lifeNumber):
    if sender+0x70 == 1: return false                      // 비활성
    if sender+0x70 == 2 && [0x7105801cb0]+0x140: return false
    if !sender+0xc: return false
    switch sender+0x28:
      0: require sender+0x24 != -1 && sender+0x24 == localPlayerIdx   // 소유 플레이어만
      1: require session->vt[0x90]()                                   // 세션 마스터 등
      2: if localPlayerIdx >= 0: require sender+0x78 == localPlayerIdx
      3,4: 누구나
      default: return false
    if session->stationCount(vt[0x48]) < 2: return true     // 혼자면 실제로 안 보내고 성공 처리
    frame = max(globalFrame, 0)
    lock(sender+0x50); ok = enqueue(queue, schema(event), event, frame, lifeNumber); unlock
    return ok
```

`localPlayerIdx` = `[[0x7105801cc0]+0xc70]+0x18`. `sender+0x28` 값(0~4)은 NetSenderPolicy(0~5)와 개수가 달라 같은 열거형이 아닙니다. 모드 0이 "소유 플레이어 기기만"이라는 것은 비교 대상(로컬 플레이어 번호)으로 확정, 모드 1의 `vt[0x90]`이 "세션 마스터인가"인지는 **[추정]**.

### 5.3 SenderPolicy 의미 [추정 — 이름·데이터 배치]

| 값 | 이름 | 쓰는 곳 | 의미(추정) |
|---|---|---|---|
| 1 | PlayerIdBased | MiniGame, TestScenePrivate | 플레이어 번호 슬롯별 송신 |
| 2 | SessionMasterOnly | DebugTransition, SplPhotographer | 세션 마스터만 상태·이벤트 송신 |
| 3 | Atomic | CoopTurret, TestAtomic | 잠금 요청(`spl::AtomicRequestNetEvent`)→관리 상태(`spl::AtomicManageNetState`)→해제(`spl::AtomicFinalizeNetEvent`)로 한 번에 한 기기만 소유 |
| 4 | Anyone | 플레이어 생성물, 전역 StageBullet/HitEffect/PaintRequest | 누구나 이벤트 송신 |
| 5 | SessionMasterOrEvent | 게임 모드 오브젝트(호코·야구라·에리어·아사리), Referee | 상태는 마스터가, 다른 기기는 이벤트(요청)로 |

### 5.4 수명

- 레플리카는 액터 생성 시 만들고 ID 범위별 트리에 넣습니다(0x710129b08c: `id < 1000` → `+0x20` 트리, `1000 ≤ id < 2000` → `+0x40` 트리(잠금 `+0xe0`), `id ≥ 10000` → `+0x60` 트리(잠금 `+0xa0`)). ID 부여 규칙은 **[미확정]**.
- 이벤트는 LifeNumber가 다르면 수신측이 버립니다(슈터 0x7102586c84 `cmp w8, w24`, DamageHelper `iStack_1b8 == iVar11`). 리스폰 전 생명의 이벤트를 무시하는 장치로 보입니다 **[추정]**.

### 5.5 GameFrame 기기 간 동기 — NetUtilFrameStarter [판독 + 실행]

**결론**: 온라인 대전의 GameFrame(`*0x710580e758`+0x148)은 매 프레임 1씩 더하는 카운터가 아니라, **세션 공통 시작 시각(start_clock, ms)과 넷 관리자 시계의 차이로 매 갱신마다 다시 계산하는 값**입니다. 그래서 모든 기기의 GameFrame이 시계 동기 정밀도 안에서 같습니다. 이전 판의 "갱신 0x71010286e0이 델타를 더한다"는 기본 델리게이트(0x7101028850)일 때만 맞고, 대전 시작 처리 후에는 아래 델리게이트로 바뀝니다(정정).

GameFrame 싱글턴은 +0x108(값 갱신 델리게이트: vtable, 인자 2개)과 +0x128(시계→프레임 변환 델리게이트)를 가지고, 갱신 0x71010286e0이 `+0x108` 델리게이트 슬롯 0을 `(&frame(+0x148), delta)`로 호출합니다. 델리게이트 교체는 `NetUtilFrameStarter`(vtable 0x7105572810, getName 0x710126d034) 가 합니다.

| 델리게이트 vtable | 슬롯 0 | 동작 | 설치 |
|---|---|---|---|
| 0x7105555638 (기본) | 0x7101028c30 → 0x7101028850 | `frame = (s32)((float)frame + delta)` | 생성 0x7101028344 |
| 0x7105572910 (대기) | 0x710126d2ac | `frame = INT_MIN(0x80000000)`, `starter+0x4c += delta`(경과 프레임 누적) | 리셋 0x710126bb78(w1=1: frame=0 후 교체), 호출자 0x7103099400 등 |
| 0x71055728a0 (**공유 시계**) | 0x710126d0ec | `clock = [넷관리자(*0x7105790be8)+0x60]->vt[+0x20] (&out,0)`; 유효하면 `frame = base(+0x118) + (s32)((float)(s32)(clock − start(+0x110)) / 1000 * 60)`, 무효면 INT_MIN | 0x710126c02c |
| 0x71055728d8 (+0x128, 시계→프레임) | 0x710126d1fc | `base + (s32)((float)(s32)(clk − start) / 1000 * 60)` | 〃 |
| 0x7105572868 (로컬 시작) | 0x710126d040 | `frame == INT_MIN ? base : (s32)((float)frame + delta)` | 0x710126c02c (`+0x31` 경로) |

`NetUtilFrameStarter` 갱신 0x710126c02c(매 프레임, 시작 전까지):

```
if !started(+0x28):
  clockOk = 넷관리자시계.get(&now(+0x38))
  [로컬 기기] 자기 StationInfo 레플리카(ID = 로컬 번호+2)의 값 요소(0x71058252b4, 8 B) ← now + offsetMs(+0x2c)
             // offsetMs = (float)프레임수/60*1000, 0x710126bd8c 가 설정 (desired_start_clock 로 추정)
  [모든 기기] VersusSetting 레플리카(ID 1)의 값 요소(0x71058252ac, 8 B) 가 0이 아니면:
             GameFrame +0x108 ← 공유 시계 델리게이트(start = 그 값, base = 0), +0x128 도 같이; started = 1
  [세션 마스터(넷관리자+0x58 vt+0x90)] 시계 유효하고 아직 시작 전이면:
             스테이션 0..9 의 StationInfo 에서 값(0x71058252b0, 4 B) 과 (0x71058252b4, 8 B) 를 읽어
             max(desired) 를 구하고, 값(b0) != 5 인 스테이션이 있으면 +0x44++
             (max != 0) && (모두 5 || 갱신 횟수(+0x54) > 600) 이면 VersusSetting.(0x71058252ac) ← max
if started && !done(+0x50):
  남은 = −min(GameFrame, 0) 프레임;  if 남은/60*1000 < 3000 ms: 넷관리자(*0x7105801cb0)+0x140 = 0, done = 1
```

- 값 요소 ID(0x71058252ac/b0/b4)는 런타임에 채우는 bss 값이라 이름은 크기와 데이터(`VersusSetting.start_clock` U64, `StationInfo.desired_start_clock` U64 0~86,400,000, `StationInfo` 의 4바이트 값)로 대응시켰습니다 **[추정 — 이름 대응]**. 값(b0) == 5 조건은 "준비 완료 단계"로 보입니다 **[추정]**.
- 시작 시각 = 모든 스테이션이 원한 시각의 **최댓값**을 세션 마스터가 정해 Reliable 값으로 배포 → 각 기기가 같은 start로 GameFrame을 계산 **[판독]**.
- 시작 전 GameFrame은 INT_MIN, 시작 시각 이전(음수 프레임)도 계산됩니다. 이벤트 스탬프·PlayerNetState 스탬프는 `max(GameFrame, 0)`을 쓰므로 0으로 눌립니다.
- 넷관리자+0x140은 이벤트 송신 함수(0x71018b7f30)가 `sender+0x70 == 2`일 때 송신을 막는 플래그입니다. 시작 3초 전(GameFrame > −180)에 풀립니다 **[판독]**.
- **프레임 건너뜀**: GameFrame이 시계에서 매번 다시 계산되므로 한 게임 갱신 사이에 2 이상 오르거나 그대로일 수 있습니다. 상태 송신 판정 `GameFrame % 4 == 0`도 이 값으로 하므로, 프레임이 건너뛰면 그 주기의 송신이 빠질 수 있습니다 **[판독에서 도출, 실제 빈도 미측정]**.
- 넷 관리자 시계(`+0x60` 객체 vt+0x20, ms 단위)는 **pia `clone::ClockProtocol`의 공유 시계**입니다(§5.6에서 해소, 이전 판 [추정]).

검증 **[실행]**: `web/tools/network_clock.py` — 0x710126d1fc를 무작위 (start, base, clock) 3,000건 실행한 결과와 재구현 `base + trunc(f32(f32(s32(clock−start)/1000)·60))`이 모두 일치(불일치 0). 0x710126d040(로컬) 1,000건 불일치 0. 0x710126d2ac를 delta 1.0으로 10회 → frame 0x80000000, starter+0x4c = 10.0. 결과 `analysis/network/clock_result.json`.

### 5.6 공유 시계 = pia `clone::ClockProtocol` [판독 + 실행]

**결론**: GameFrame 델리게이트가 읽는 `[*0x7105790be8(넷 관리자)+0x60]->vt[+0x20](&ms, 0)`은 매 프레임 pia `ClockProtocol::GetClock()`에서 받아 둔 값(µs ÷ 1000 = ms)을 돌려줍니다. 이전 판의 [추정]을 해소합니다.

연결 경로(기준 객체를 함께 적음):

| 단계 | 함수 | 내용 |
|---|---|---|
| ClockProtocol 생성·등록 | 0x71034e48ac (넷 관리자+0x60 객체 = 이하 **C**의 클론 설정) | pia 프로토콜 관리자(`*0x71057d4b08`+0x10)에서 0x80 B를 할당해 **0x710076e224**(ClockProtocol 생성자, vtable = `[0x7105777ea0]+0x10` = 0x7105406010 = RTTI `N2nn3pia5clone13ClockProtocolE`의 vtable)로 만들고 ID `0x77000064`로 등록, 핸들을 `[C+0x38]+0x140`에 저장, 0x710076e2dc(시작)·0x710076dfb0 호출 |
| 매 프레임 갱신 | 0x71034e3908(`[C+0x38]`, 1) ← 0x71034d97d8(넷 관리자 메서드) | dt = (현재 틱 − `+0x148`)을 µs로 환산, `+0x148` = 현재 틱. `0x710076eb08(proto, dt, 1, 2·dt)`(시계 진행), `+0x158 = 0x710076ebd4(proto) & 1`(동기 상태), 동기 안 됐다가 이전 플래그(+0x1a4 bit0)가 있으면 0x710076e78c, 그다음 **`0x710076ebf8(&res, proto, &clk)` = GetClock** → 성공이면 `+0x150 = clk / 1000`, 실패면 `+0x150 = −1`(오류 종류에 따라 재시도 처리 0x71034d9038) |
| 게임 쪽 읽기 | **C vt+0x20 = 0x71034e56c0** (C 생성자 0x71034e3d20, vtable 0x710571d840) | `e = (idx < C+0x30) ? C+0x38 배열[idx] (stride 0x1a8) : 배열[0]`; `e+0x150 != −1`이면 `*out = e+0x150`, 1 반환, 아니면 0 반환(out 그대로) |
| pia GetClock | 0x710076ebf8 | ClockProtocol +0x5a(상태) == 4 이면 −1·오류 0x6c88, +0x68 == −1(미동기) 이면 −1·오류, +0x78 != 0 이면 `*out = +0x70`, 결과 0 |

원본 실행(`network_rest_verify.py` [3][4]): 0x71034e56c0에 (개수 2, idx 0/1/5)를 넣어 각각 배열[0]/[1]/[0]의 +0x150을 돌려주고, 값이 −1이면 0 반환·out 불변. 0x710076ebf8은 (상태 2, +0x68 0, +0x78 1, +0x70 5,000,000) → 5,000,000, 상태 4 또는 +0x68 = −1 → −1. 즉 **ClockProtocol 시계는 µs 단위, 게임은 ms로 받아 GameFrame = base + (s32)((float)(s32)(ms − start)/1000·60)** 를 계산합니다.

남은 것: pia ClockProtocol 내부의 동기 알고리즘(세션 마스터 기준 시계 배포·RTT 보정, 0x710076eb08/0x710076e78c) **[미판독]**. 웹은 서버 시계를 기준으로 한 시계 동기(NTP 방식 왕복 측정)로 같은 역할을 대신합니다([06](06_web_port.md)).

## 6. 의사코드 (원본 동작 요약)

```
// 송신측 (매 게임 프레임, 고정 1/60 s)
onGameplayAction(evt):            // 발사, 특수 시작, 사망 ...
    sendEvent(ownerSender, evt, owner.lifeNumber)      // 권한 검사 후 큐잉, 스탬프=globalFrame
onNetUpdate():
    if gameNet.sendFlag (= globalFrame % 4 == 0):
        state = buildPlayerNetState()                  // 546 bit
        replica.stateElement.set(state)

// 수신측 (매 게임 프레임)
for consumer in replicaConsumers:  // 무기, DamageHelper, PlayerNetControl, HitEffect ...
    for entry in replica.recvQueue:
        if entry.schema.hash != consumer.wantedHash: continue
        (evt, frame, life) = decode(entry)
        if life != owner.lifeNumber: continue
        consumer.apply(evt, frame)
```

## 8. 다른 기능과의 상호작용

- 탄 발사·피격: [05](05_events_combat.md), 탄 계산 자체는 [../weapon/shooter_bullet.md](../weapon/shooter_bullet.md).
- 도색: `PaintRequest` 레플리카(Anyone, 큐 256)로 `spl::paint::*PaintEvent`가 오갑니다. 도색 계산은 [../paint/paint_and_score.md](../paint/paint_and_score.md).
- 게임 모드 오브젝트(호코·야구라·에리어): SessionMasterOrEvent 상태 + 요청 이벤트. 기믹 쪽은 [../gimmick/stage_gimmicks.md](../gimmick/stage_gimmicks.md).

## 11. 미확정

| 항목 | 이유 | 다음 단계 |
|---|---|---|
| GameFrame 기기 간 동기 | **해소 [판독+실행]** — §5.5. 넷 관리자 시계 = pia ClockProtocol GetClock(µs)/1000 **해소 [판독+실행]** — §5.6. 남은 것: `VersusStartClockEvent`(32비트) 사용처, ClockProtocol 내부 동기 알고리즘 | 0x710307e1c0/0x710307e468, 0x710076eb08 |
| `element+0x20 == 1`(매 프레임 송신 조건) 의미 | 플레이어 쪽 동작은 판독([04 §4.4](04_player_state.md)): 1이면 매 프레임 상태 저장본 갱신. 값 1 = Reliable 인지는 [추정] | 요소 생성 함수에서 Protocol/모드 기록 위치 |
| Unreliable 상태 손실 시 재전송 여부, Reliable 상태 송신 조건(`equals` 슬롯으로 변경 감지?) | 미판독 | 0x710129e630 디컴파일 |
| 큐 비우기 시점·오버플로 처리 | 미판독 | 큐 클래스 |
| 모드 1 `vt[0x90]`의 정확한 의미 | 미판독 | 세션 객체 vtable |
