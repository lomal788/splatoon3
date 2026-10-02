# 04. 플레이어 상태 동기화 (`spl::PlayerNetState`, `spl::PlayerNetControl`)

[목차](network.md)

## 1. 개요

각 플레이어 기기는 자기 플레이어의 상태를 **4프레임마다** `spl::PlayerNetState`(546비트 고정)로 보냅니다. 다른 기기의 `spl::PlayerNetControl`은 이 상태를 받아 송신 프레임 스탬프로 지연을 추정하고, 과거 샘플과 자기 쪽 표시 이력을 비교한 오차를 여러 프레임에 걸쳐 조금씩 반영합니다.

## 2. 자료

| 대상 | 주소 |
|---|---|
| `spl::PlayerNetState` 등록 | 0x710241782c, 엔트리 0x71058b9db0, 생성자 0x7102417a50, vtable 0x710562e018, 객체 0x1c8(456) B |
| write / read | 0x7102418788 / 0x710241923c (`net_core.c` / `net_player.c`) |
| 송신(플레이어 넷 갱신) | 함수 0x7102483134 안, 상태 작성 0x71024873c8~0x7102488000, 플래그 검사 0x71024890d8~0x71024890f4. 디컴파일 `analysis/decomp/network/net_player_send.c`(8,028줄, `player_bigdecomp.sh`) |
| PlayerNetControl 생성 | 팩토리 0x71026583ac (`net_sync.c`) |
| 수신·보정 | 0x7102658bb4 (`net_player.c`), 클래스 `spl::PlayerNetControl`(이름 문자열 xref 0x7102658ba4, 정적 등록 0x71026581a0 → 팩토리 0x71026583ac) |
| 액터 설정 | `SplPlayer.game__NetParam`: 요소 `spl::PlayerNetState`(IsBehaviorState, Protocol 기본 Unreliable), 이벤트 큐 128/128 |

## 3. 호출 흐름

```
[송신 기기, 매 프레임]  0x7102483134 (플레이어 넷 갱신)
  if 요소+0x20 == 1 || GameNet+0x1c4 (GameFrame%4==0):
      스택에 PlayerNetState 생성(vtable GOT 0x710579ef68) → 본체·컴포넌트 필드를 직접 복사(§4)
      → variant 1·2 채움(§4.2) → [본체+0x588]->vt+0x78, [본체+0x678]->vt+0x60 (§4.3)
      → 상태 요소 저장본에 copy, 요소+0x25=1 (§4.4) → (GameNet 송신 작업이 직렬화 0x7102418788)
  매 프레임: 로컬 이력 링버퍼(PlayerNetControl+0x3e8)에 (표시 위치, 방향, +0x1ff8) push

[수신 기기, 매 프레임]  PlayerNetControl 0x7102658bb4
  요소에서 새 상태가 왔으면(크기 0x1c8, +0x25 갱신 플래그) 이중 버퍼에 복사, +0x3e0=1
  지연 추정 갱신 → 샘플 링버퍼에 (위치, 방향, 프레임) 추가
  재생 지점(나이 < 창) 샘플과 로컬 이력 비교 → 위치 오차(+0xc78), 회전 오차(+0xc84)
  오차를 스프링 형태로 점진 반영
```

## 4. `PlayerNetState` 필드 표 [실행 + 판독]

순서·비트는 write(0x7102418788) 디컴파일과 unicorn 실행(546비트, 항목 63개 + 패딩 바이트 1개)으로 확인했습니다. 기준 객체는 `spl::PlayerNetState`(+0 vtable).

**송신측 출처**는 송신 함수 0x7102483134(28 KB, `player_bigdecomp.sh`로 디컴파일 → `analysis/decomp/network/net_player_send.c`)의 상태 작성 블록(0x71024873c8~0x7102488000)을 판독한 것입니다. 스택 상태 객체 = `sp+0x1a0`, 플레이어 본체 = `x28` = `PlayerBehavior+0x108`(이하 **본체**, [../player/movement_physics.md](../player/movement_physics.md)와 같은 기준), 컴포넌트 포인터는 본체 `+0xa650..`(`analysis/player/player_components.tsv`). 디컴파일의 `param_1`은 본체+0xa5fc입니다(`param_1+0xfc` = 본체+0xa6f8 = PlayerNetControl, `param_1-0x9a18` = 본체+0xbe4 = 스페셜 게이지 비율로 교차 확인). 주요 대응은 디스어셈블(`str .., [sp,#0x1a0+X]`)로 다시 맞춰 봤습니다 **[판독]**. "의미" 열의 해석은 출처 필드가 다른 문서에서 밝혀진 경우만 적고, 그 외는 출처만 적습니다.

| # | 오프셋 | 비트 | 형식([03](03_serialization.md#4-양자화-공식-판독--실행)) | 송신측 출처 [판독] | 의미 |
|---|---|---|---|---|---|
| 1~3 | +0x20, +0x24, +0x28 | 17×3 | Q17 | 본체+0x10..+0x18 | **위치**(수신 PlayerNetControl 샘플 위치) |
| 4 | +0x2c | 33 | VEL33 | 본체+0x114 + 본체+0xa2c (성분별 합). 단 PlayerStartLaunch(+0xa6a8)+0xb4 ≠ 0이면 StartLaunch+0xc8..+0xd0 | 속도 A. 본체+0x114 = 이동 속도 [추정, player] |
| 5 | +0x38 | 33 | VEL33 | 본체+0xfc..+0x104 | 속도 B (의미 미확정) |
| 6 | +0x44 | 21 | DIR21 | 본체+0x34..+0x3c | 방향 A = 수신 샘플 방향(§5). 재시작 때 카메라가 이 값으로 방향을 맞춤([../camera/player_camera.md](../camera/player_camera.md)) — 몸 정면 방향 [추정] |
| 7 | +0x50 | 21 | DIR21 | 본체+0x198..+0x1a0 | 방향 B |
| 8 | +0x5c,+0x64 | 13 | yaw13 | 본체+0x538..+0x540 (x,z만 씀) | **조준(카메라) 수평 방향** — 카메라 종료 시 dir=본체+0x538([../camera/player_camera.md](../camera/player_camera.md)), 머즐 xlink `MuzzleShotDirXZDot`가 이 벡터와 내적([../effect_sound/effect_sound.md](../effect_sound/effect_sound.md)) [판독: 사용처], 이름 [추정] |
| 9 | +0x68 | 12 | s12 [-1,1] | 본체+0x544 | **카메라 피치 정규값 p**(−1 아래~+1 위) — 카메라가 종료 시 p=본체+0x544로 복원, 범위가 리그 p(+0x16c)와 같음 [판독: 사용처], 이름 [추정] |
| 10 | +0x6c | 10 | u | PlayerDamage(+0xa8a0)+0x7c. 상태 생성자 기본값 **1000** | **HP** [판독]: PlayerDamage+0x30 HP 홀더의 +0x4c(hp)([../combat/player_life.md](../combat/player_life.md)). 수신측 0x7102475a54가 PlayerDamage+0xee0(원격 HP)에 그대로 씀(§5.2) |
| 11 | +0x70 | 13 | u | PlayerArmor(+0xa8c0)+0x84 | **아머 HP** [판독]: 아머 HP 홀더(Armor+0x38)의 +0x4c. 수신측은 #13이 참이고 값 ≥ 0이면 Armor+0xee8에 씀(§5.2) |
| 12 | +0x74 | 2 | u | PlayerArmor+0xefc | 아머 관련 2비트 값. 수신측: #13이 거짓이고 이 값이 자기 Armor+0xefc와 다르면 Armor+0xee8=0 후 값을 복사(§5.2) — 아머 부여 회차 카운터로 보임 [추정] |
| 13 | +0x78 | 1 | bool | PlayerArmor+0xf18 (byte) | **아머 활성** [판독]: player_life.md의 `armor.active(+0xf18)` |
| 14 | +0x7c | 7 | u | 본체+0xbe4(f32 r): r ≥ 1이면 100, 아니면 min((u32)(r·100), 99) | **스페셜 게이지 %** (본체+0xbe4 = 게이지 비율, [ui] 판독) |
| 15 | +0x80 | 11 | u11 [0,1] | 본체+0x698 (f32) | 무기 쪽이 잉크 소비 판정에 쓰는 값(0x7102492120 인자). 본체 생성(0x71024575bc)이 **1.0**으로 초기화, 수신측은 본체+0x6a0에 씀 — 잉크 탱크 잔량 비율 [추정] |
| 16 | +0x84 | 15 | u | 본체+0xc0 | **공중 프레임 수**(airFrames) [판독: [camui]/[physics] 사용처 — 4 이상 공중 취급, 3 이상 중력]. 수신측은 본체+0xd8에 씀 |
| 17 | +0x88 | 19 | 프레임(INT_MIN↔0x7FFFF) | PlayerNetControl(+0xa6f8)+0x1ff8 = 플레이어 갱신(0x71024a2c98, 쓰기 0x71024a527c) 때의 max(GameFrame, 0) | **송신 프레임 스탬프** |
| 18 | +0x8c | 1 | bool | 본체+0xbf0 > 0 | **스페셜 사용 중** [판독]: 본체+0xbf0 = 스페셜 남은 프레임([../paint/special_gauge.md](../paint/special_gauge.md)) |
| 19 | +0x90 | 3 | u | PlayerStepPaint(+0xa688)+0x30 | **발밑 분류** [판독]: 0/1 아군, 2/3 적, 4/5 없음([../player/player_state.md](../player/player_state.md)). 생성자 기본 4. 수신측이 원격 StepPaint+0x30에 그대로 씀 |
| 20 | +0x94 | 3 | s8 +1 (−1~6) | PlayerStepPaint+0x34 (byte) | **발밑 잉크 팀 번호** [판독]: 수신측이 StepPaint+0x34(값이 같지 않을 때) 또는 +0x38에 씀, −1 = 없음 |
| 21 | +0x98 | 3 | u | 본체+0xd00 | **점프 기록 회차 카운터(mod 8)** [판독]: 점프 적용 0x7102459630(0x7102459d80)과 0x71024827a8이 `(c+1)&7`로 올리면서 본체+0x748(Jump +0x24)·+0x74c(Jump +0x38 = 그때 액터 y)를 같이 갱신. 이름은 [추정] |
| 22 | +0x9c | 3 | u | 본체+0xcfc | 본체+0xcfc 구조체(#21·#23·#25·#37과 한 묶음: +0/+4/+8/+0xc/+0x10)의 첫 값. writer 미발견 [미확정] |
| 23 | +0xa0 | 3 | u | 본체+0xd04 | **1회성 동작 이벤트 카운터(mod 8)** [실행+판독]: 0x7102469fac(구조체 본체+0xcfc, 상태 번호)가 +8(=본체+0xd04)을 `(c+1)&7`로, +0x10(=본체+0xd0c)에 종류를 씀(§4.5) |
| 24 | +0xa4 | 3 | u | **송신 쪽 writer 없음 → 항상 0** [판독, §4.6] | 수신측은 이 값을 소유자 LifeNumber(넷 객체 +0x28)와 비교: 다르고 쓰러짐 구조체 첫 값(본체+0xd58) > 0 이면 **그 상태 적용을 통째로 건너뜀** [판독]. 이름(생명 번호 칸) [추정] |
| 25 | +0xa8 | 4 | u | 본체+0xd0c | **1회성 동작 종류**(#23과 짝) [실행]: 1 ThrowMiss 계열, 2 Shoot/Shoot_Stringer, 3 Shoot_Shelter_Automatic, 4 Shoot_Jetpack, 5 Shoot_Blower_Exhale, 6 Damage(+SuperHook 벽 피격 3종), 7 Surprise, 8 Repelled, 9 ThrowMiss_CoopIkura (§4.5) |
| 26 | +0xac | 3 | u | 본체+0x7f0 | **점프 시작 카운터(mod 8)** [판독]: 로컬은 점프 적용 0x7102459630(x0=본체+0x7b8)이 `(c+1)&7`, +0x7f4/+0x7f5=1, +0x7f7=오징어 이동 상태 여부, +0x7ec=2. 수신측(0x710248142c)은 값이 다르고 수직 속도(+0x73c) > 0.001이면 카운터를 하나 올리고 같은 플래그를 만들어 점프 시작을 재현 |
| 27 | +0xe0 | 1 | variant 1 인덱스 → 값 +0xb0, **10비트로 패딩** | §4.2 | 0 Squid, 1 Human |
| 28 | +0x128 | 2 | variant 2 인덱스 → 값 +0xe8, **108비트로 패딩** | §4.2 | 0 Jump, 1 DokanWarp, 2 RespawnLand |
| 29 | +0x160 | 4 | variant 3 인덱스 → 값 +0x130, **14비트로 패딩** | 본체+0x588 객체의 vt+0x78(메인 InkAction 컴포넌트, §4.3)이 채움 | InkAction 0~12 |
| 30 | +0x188 | 1 | bool | 내장 하위 객체 `PlayerNetState_InkActionSuperHook`(+0x168)의 +0x20. `[본체+0x678]->vt+0x60`이 `PlayerSubActionSpSuperHook`일 때 0x71026a8968 = `this+0x3952 \|\| this+0x3953` [실행] | **슈퍼후크 벽 부착 상태** (§4.6) |
| 31~33 | +0x190,+0x194,+0x198 | 17×3 | Q17 | 룰별(대전 설정+0x3c `Rule`): **5 Tcl(트리컬러)** → 본체+0x92c0..+0x92c8, **3 Vgl(호코)** → 본체+0x9280..+0x9288, 그 외 0 | 룰 오브젝트 관련 두 번째 위치 [판독], 룰 값 이름 [실행] |
| 34 | +0x19c | 1 | bool | Rule 5(Tcl) → 본체+0x92e0, Rule 3(Vgl) → 본체+0x92a0 (byte) | 〃 |
| 35 | +0x1a0 | 4 | u | 같은 vt+0x78 (슈터 0x7102586e14: [this+0x38] 없으면 2, [[this+0x38]+0x384]==0xf면 [..+0x320], 그 외 조건별 1/2) 생성자 기본값 0xf | 메인 무기 동작 상태로 추정 [추정] |
| 36 | +0x1a4 | 3 | u | 같은 vt+0x78 (슈터: [this+0x38]+0x37c) | |
| 37 | +0x1a8 | 2 | u | 본체+0xd08 | 본체+0xcfc 구조체 +0xc. writer 미발견 [미확정] |
| 38 | +0x1ac | 16 | u | PlayerGrapple(+0xa7a0): +0x130c ≠ 0 이고 +0x30 객체 있으면 그 객체 +0x228, 아니면 0 | 그래플(슈퍼후크 줄) 연결 대상 값. Grapple+0x130c = 연결 중 플래그(SuperHook 갱신 0x710269f0cc가 0이면 벽 부착 래치를 끔) [판독], 대상 값의 뜻 [미확정] |
| 39 | +0x1b0 | 3 | u | PlayerGrapple+0x38 | 그래플 회차 값. 수신측(0x7102476874 근처): #38 ≠ 0 이고 이 값이 자기 Grapple+0x38과 다르면 연결 중이던 그래플을 해제(0x71025249b4)하고 위치를 PlayerNetControl+0x2060으로 맞춤 [판독], 이름 [추정] |
| 40 | +0x1b4 | 1 | bool | PlayerInkRail(+0xa668)+0x1b8 ≠ −1 이고 레일 상태값(+0x80 객체 +0x24) −7 > 4 (부호 없는 비교) | 잉크레일 관련 |
| 41 | +0x1b8 | 32 | u | 위 조건일 때 0x710262c9e4(PlayerInkRail) 반환값, 아니면 0 | 〃 |
| 42 | +0x1bc | 2 | u | (s8)본체+0xb60 | |
| 43 | +0x1c0 | 2 | u | (s8)본체+0xb61 | |
| 44 | +0x1c4 | 1 | bool | **Rule 2 Vlf(야구라)** → 본체+0x9258 (byte), 그 외 0 | 야구라 룰 전용 플래그 [판독], 뜻(탑승 등) [미확정] |
| | | **546** | | | |

룰 값 **[실행]**: 대전 설정 객체(`[[0x71058e42f8]+0xc8]+0x6548`, [05 §3.1](05_events_combat.md))의 +0x3c는 BYML 키 `Rule`로 채워집니다(0x7102aeb3c4~). 값이 문자열(BYML 0xa0)이면 0x71010c8e3c가 표 0x71010c8be8(문자열 `"Pnt , Var , Vlf , Vgl , Vcl , Tcl"` @0x7104982982를 쉼표로 잘라 만든 6개)과 차례로 비교해 **위치 = 값**을 씁니다(정수 0xd1이면 그대로). 원본 함수를 unicorn으로 실행해 `Pnt→0, Var→1, Vlf→2, Vgl→3, Vcl→4, Tcl→5`, 표에 없는 문자열은 값을 쓰지 않음을 확인했습니다(`network_rest_verify.py` [1]). 온라인 대전에서는 같은 +0x3c를 `OnlineVersusSetting` +0x84(3비트)가 채웁니다([05 §3.1](05_events_combat.md)). 따라서 **Rule 2 = Vlf(야구라), 3 = Vgl(호코), 5 = Tcl(트리컬러)** 입니다. 이전 판의 [추정]을 해소합니다.

**정정 (InkActionSuperHook)**: 이전 판은 "SuperHook은 variant 3의 인덱스 13 이상이 무효라 다른 경로가 있는지 미확정"이라고 적었습니다. 송신 함수와 생성자(0x7102417a50)가 `+0x168`에 SuperHook vtable(GOT 0x710579edd0)을 넣는 것을 확인했습니다. 즉 SuperHook은 variant가 아니라 **항상 들어 있는 내장 하위 객체**이고, 필드표 #30(+0x188, 1비트)이 그 객체의 +0x20입니다 **[판독]**. 이전 판에서 미확정으로 남긴 "+0x188에 1을 쓰는 곳"은 §4.6에서 해소했습니다(`[본체+0x678]` = `PlayerSubActionSpSuperHook` 보조 인터페이스의 vt+0x60).

패딩: 각 variant 값의 비트 수를 뺀 나머지를 8비트 단위는 writer `+0x60`(바이트 0)으로, 나머지를 `+0xa8`로 0을 씁니다. 그래서 상태 크기는 언제나 546비트(68.25 B)입니다. 4프레임마다 보내므로 플레이어 1명당 payload 약 **2,047 B/s ≈ 16.4 kbit/s**(헤더·pia 오버헤드 제외)입니다 **[계산]**.

### 4.1 variant 매핑 [실행]

원본 read에 인덱스 값을 공급하고 생성된 vtable로 판정(`network_verify.py` [4b]):

| variant | 저장 | 인덱스 → 타입 (비트) |
|---|---|---|
| 1 (+0xe0) | +0xb0 | 0 `PlayerNetState_Squid` (3), 1 `PlayerNetState_Human` (10) |
| 2 (+0x128) | +0xe8 | 0 `Jump` (108), 1 `DokanWarp` (3), 2 `RespawnLand` (64); 3은 무효(read가 0으로) |
| 3 (+0x160) | +0x130 | 0 `InkActionNone` (0), 1 `Shooter` (1), 2 `Roller` (8), 3 `Charger` (12), 4 `Spinner` (13), 5 `Slosher` (5), 6 `Brush` (7), 7 `Maneuver` (2), 8 `Shelter` (11), 9 `Stringer` (9), 10 `Saber` (10), 11 `SpChariot` (14), 12 `Gachihoko` (1); 13~15 무효 |

`PlayerNetState_InkActionSuperHook`(1비트)은 variant 3의 선택지가 아니라 `+0x168`에 고정으로 들어 있는 하위 객체입니다(§4 정정) **[판독]**.

변형별 필드(`bitlayout.txt`, 오프셋 기준 = 하위 상태 객체):

| 타입 | 필드 |
|---|---|
| Squid | +0x20 bool, +0x24 u2 |
| Human | +0x20~+0x27 bool 8개, +0x28 u2 |
| Jump | +0x20 bool, +0x24 **f32 고정소수점 24비트**, +0x28 **f32 고정소수점 24비트**, +0x2c VEL33, +0x38 **f32 고정소수점 25비트**, +0x3c bool (아래 정정) |
| DokanWarp | +0x20 u2, +0x24 bool |
| RespawnLand | +0x20/24/28 Q17 위치, +0x2c u10, +0x30 u3 |
| InkActionShooter | +0x20 bool |
| InkActionRoller | +0x20~+0x23 bool, +0x24 u4 |
| InkActionCharger | +0x20~+0x22 bool, +0x24 u9 |
| InkActionSpinner | +0x20~+0x23 bool, +0x24 u9 |
| InkActionSlosher | +0x20 bool, +0x24 u4 |
| InkActionBrush | +0x20~+0x22 bool, +0x24 u4 |
| InkActionManeuver | +0x20, +0x21 bool |
| InkActionShelter | +0x20, +0x21 bool, +0x24 u4, +0x28 u5 |
| InkActionStringer | +0x20~+0x22 bool, +0x24 u6 |
| InkActionSaber | +0x20~+0x25 bool, +0x28 u4 |
| InkActionSpChariot | +0x20 u14 |
| InkActionGachihoko / SuperHook | +0x20 bool |

**정정 (Jump 필드 형식)**: 이전 판은 `bitlayout.txt` 직선 판독대로 +0x24/+0x28을 u24, +0x38을 u25 정수로 적었습니다. Jump write(0x7102424728)를 직접 읽으니 세 필드는 f32이고 `q = (u32)((v + 100) * 65536 + 0.5)`(+0x24, +0x28: 24비트, 범위 −100~156), `q = (u32)((v + 200) * 65536 + 0.5)`(+0x38: 25비트, 범위 −200~312)로 씁니다(단위 1/65536, 반올림) **[판독]**. 같은 함수 바로 뒤(0x7102424860)에 같은 모양의 두 번째 write가 있습니다(두 번째 직렬화 인터페이스용으로 보임).

### 4.2 variant 채우기 (송신 0x7102483134) [판독]

기준: 본체 = PlayerBehavior+0x108, 하위 객체 오프셋은 variant 객체 기준.

**variant 1 (Squid/Human)**: 상태 번호 `[[본체+0xa8c8]+0xc8]`가 0x82~0x90, 0xaa~0xac, 0xed, 0xee, 0x10c 중 하나면 Squid, 아니면 Human입니다(상태 번호 이름은 [state] 담당 표 참조).

| 하위 타입 | 필드 ← 출처 |
|---|---|
| Squid | +0x20 ← 본체+0x789 (byte), +0x24 ← 본체+0x79c |
| Human | +0x20 ← 본체+0x4d8 > 0, +0x21 ← 본체+0x4ec > 0, +0x22 ← 본체+0x524 > 0, +0x23 ← 본체+0xab8 < 1 일 때 (본체+0x4e0 > 0 ∨ 본체+0x532 ∨ 본체+0x533) ? 1 : 본체+0x4f2 ≠ 0 (본체+0xab8 ≥ 1이면 0), +0x24 ← 같은 조건으로 (본체+0x518 > 0 ∨ +0x534 ∨ +0x535) ? 1 : +0x52a ≠ 0, +0x25/+0x26/+0x27 ← 본체+0xad0/+0xad4/+0xad8 > 0, +0x28 ← (s8)[[본체+0xa8c8]+0x1fe] |

**variant 2 (Jump/DokanWarp/RespawnLand)**:

```
respawnLand = 전역(*0x71057999c8)+0x3680 bit0 && +0x3681 bit0
              && !( StartLaunch(+0xa6a8)+0xb4 == 0
                    && ( 본체+0x9213 || [본체+0xa830]+0x1348 == 0xc
                         || (본체+0x9211 == 0 && 본체+0xd58 < 1 && !(본체+0xf34 ∈ {1,2,4})) ) )
if respawnLand:                       RespawnLand: +0x20..+0x28 ← 본체+0xed0..+0xed8 (Q17),
                                                   +0x2c ← 본체+0xf20 (u10), +0x30 ← 본체+0xf34 (u3)
elif [본체+0xa880(PlayerDokanWarp)]+0x30 == 3:  DokanWarp: +0x20 ← (DokanWarp+0x128) % 4, +0x24 ← 1
else:                                 Jump: +0x20 ← 본체+0x72c (byte), +0x24 ← 본체+0x748 (f32),
                                            +0x28 ← 본체+0x73c + 본체+0x754 (f32),
                                            +0x2c..+0x34 ← (본체+0x750, 0, 본체+0x758) (VEL33),
                                            +0x38 ← 본체+0x74c (f32), +0x3c ← 본체+0x780 (byte)
```

본체+0xf34는 [camera] 문서에서 "값 2~4면 카메라 yaw 느림"으로 관측된 필드이고, RespawnLand가 이 값을 그대로 보냅니다. Jump의 +0x28(본체+0x73c+0x754)은 [camera]가 "수직 속도로 추정"한 두 필드의 합입니다. 의미 이름은 **[추정]**으로 둡니다.

### 4.3 variant 3 (InkAction)·무기 필드 [판독]

변형 2까지 채운 뒤 두 번 가상 호출로 상태를 넘깁니다.

1. `[본체+0x588]->vt[+0x78](obj, &state)` — 메인 InkAction 컴포넌트가 variant 3과 +0x1a0/+0x1a4를 채웁니다. 슈터 예: `spl::PlayerInkActionShooter`(vtable 0x71056376a0) 의 0x7102586e14(vtable+0x170에 있음): +0x1a0 = 무기 정보(+0x38) 없으면 2, `[info+0x384] == 0xf`면 `[info+0x320]`, 그 밖에 1 또는 2; +0x1a4 = `[info+0x37c]`; variant 3 = Shooter(1), Shooter+0x20 ← this+0x90 (byte). 다른 무기의 같은 슬롯: Charger 0x710254398c, Roller 0x710255cff0(포인터 위치 0x7105636020/0x7105636b28) — 내용은 미판독.
2. `[본체+0x678]->vt[+0x60](obj, &state)` — 서브액션 슬롯. `PlayerSubActionSpSuperHook`이면 +0x188(#30)을 채우고, `PlayerSubActionBombThrow`는 아무것도 안 함(§4.6) **[판독+실행]**.

그 뒤 `PlayerSideStep(+0xa678)+0x38 ≠ 0`이면: variant 3이 Saber(10)면 Saber+0x24 = 1, Maneuver(7)면 Maneuver+0x21 = 1, 그 밖이면 variant 3을 Maneuver로 바꾸고 +0x21 = 1(+0x20 = 0) **[판독]**. SideStep은 회피 동작 컴포넌트라서 "회피 중" 표시를 무기 종류와 관계없이 Maneuver.+0x21로 보내는 것으로 보입니다 **[추정]**.

### 4.4 송신 조건과 요소 갱신 [판독]

```
if 요소(+0x20) == 1 || GameNet+0x1c4:            // 0x7102489080 근처
    tmp = 기본 PlayerNetState; (요소 저장본과 equals 비교 → 결과는 다른 용도)
    요소 저장본(+0x10, 크기 0x1c8) ← copy(위에서 채운 state)   // vt+0x38
    요소+0x25 = 1; 요소->vt[+0x48]()                           // 갱신 통지
```

이 블록은 송신자 모드 switch(요소 소유 `+0x48`: 0 소유 플레이어, 1/4 세션 마스터 판정, 2, 3)를 통과해야 실행됩니다 — 이벤트 송신 0x71018b7f30과 같은 모양 **[판독]**.

### 4.5 1회성 동작 카운터 묶음(본체+0xcfc 구조체) [실행 + 판독]

PlayerNetState는 4프레임마다 보내는 비신뢰 상태라서, 한 번만 일어나는 동작(점프 시작, 피격 리액션, 투척 실패 등)은 **3비트 회차 카운터(mod 8) + 종류 값**으로 실어 보냅니다. 수신측은 자기 쪽 카운터와 다르면 그 동작을 한 번 재생하고 카운터를 맞춥니다. 카운터는 모두 `c = (c + 1) − ((c+1 < 0 ? c+8 : c+1) & ~7)` = `(c+1) mod 8` 모양으로 올립니다.

| 필드(#) | 본체 오프셋 | 올리는 곳 | 같이 쓰는 값 |
|---|---|---|---|
| #26 +0xac | +0x7f0 | 점프 적용 0x7102459630 (`x0` = 본체+0x7b8, 0x71024596b8) | +0x7f4/+0x7f5 = 1, +0x7f7 = 상태 ∈ 0x82~0x90, +0x7f8 = 1, +0x7ec = 2 |
| #21 +0x98 | +0xd00 | 0x7102459630 (0x7102459d80, 스택 인자 = &본체+0xcfc), 0x71024827a8 | 본체+0x748(→ Jump +0x24), 본체+0x74c = 액터 y(→ Jump +0x38) |
| #23 +0xa0 | +0xd04 | 0x7102469fac(구조체 = 본체+0xcfc, w1 = 상태 번호), 0x71024afcb8(벽 관련, 종류 7), 0x71024b2958(상태 0xd Shoot 요청, 종류 2) | 종류 → +0xd0c(#25) |
| #22 +0x9c / #37 +0x1a8 | +0xcfc / +0xd08 | writer 미발견 | — |

0x7102469fac의 상태 번호 → 종류 표(원본 실행, `network_rest_verify.py` [6], 상태 번호 0~0x11f 전수, 나머지는 0):

| 상태 번호(이름, [../player/player_state.md](../player/player_state.md) 부록) | 종류(#25) |
|---|---|
| 0x8 ThrowMiss, 0x9 ThrowMiss_Curling, 0xa ThrowMiss_Fizzy, 0xc ThrowMiss_BothHands | 1 |
| 0xd Shoot, 0x12 Shoot_Stringer | 2 |
| 0x21 Shoot_Shelter_Automatic | 3 |
| 0x23 Shoot_Jetpack | 4 |
| 0x28 Shoot_Blower_Exhale | 5 |
| 0x2b Damage, 0x2c Damage_SuperHook_WaitOnWall, 0x2d …_Left, 0x2e …_Right | 6 |
| 0x88 Surprise(오징어) | 7 |
| 0xa5 Repelled | 8 |
| 0xb ThrowMiss_CoopIkura | 9 |

피격 리액션 상태는 0x710246e1ac가 고릅니다: 기본 0x2b(Damage), 단 슈퍼후크(본체+0x65c == 0xf = 10+SuperHook 인덱스 5)가 활성이고 `[본체+0xa798]`(SuperHook 서브액션)+0x3952가 켜져 있으면 현재 상태 0xd0(SuperHook_WaitOnWall_R)→0x2e, 0xca(…_L)→0x2d, 그 밖 0x2c **[판독]**. 이 상태를 요청(0x7102448af8)한 뒤 0x7102469fac로 카운터를 올립니다.

수신 재생 쪽은 #26만 확인했습니다(0x710248142c: `본체+0x7f0 != 상태+0xac` 이고 `본체+0x73c > 0.001`이면 카운터 +1, +0x7f4/+0x7f5 = 1, +0x7f7 = 상태 ∈ 0x82~0x90, +0x7f9 = 바닥 법선 y(+0x184) < 0.64144969). #21·#23·#25의 수신 소비 코드는 찾지 못했습니다 **[미확정]**.

### 4.6 +0xa4(#24)와 +0x188(#30) [판독 + 실행]

**+0x188 (SuperHook 하위 객체 +0x20)**: 송신 0x7102483134는 `[본체+0x678]->vt[+0x60](obj, &state)`를 부릅니다(0x7102487bfc). 본체+0x678/+0x588은 서브액션/메인 잉크액션 슬롯이고, 본체+0x678에는 각 서브액션 객체의 **보조 인터페이스(this+0x30)** 가 들어갑니다. 서브액션 클래스는 두 개뿐입니다(`main_strings`의 `spl::PlayerSubAction*`).

| 클래스 | 주 vtable | 보조 vtable(this+0x30) | 보조 vt+0x60 |
|---|---|---|---|
| `spl::PlayerSubActionSpSuperHook` | 0x710563efa0 (50슬롯) | 0x710563f160 (offset-to-top −0x30) | **0x71026a8968**: `state+0x188 = this+0x3952 \|\| this+0x3953` (this = 주 객체) |
| `spl::PlayerSubActionBombThrow` | 0x710563ec98 (44슬롯) | 0x710563ee28 | 0x710269bf98 = `ret` (쓰지 않음) |

주 vtable 슬롯 41(0x71026a8938)도 같은 식입니다. 원본 실행으로 (+0x3952,+0x3953) = (0,0)→0, (0,1)/(1,0)/(1,1)→1을 확인했습니다(`network_rest_verify.py` [2]). 받는 쪽은 슈퍼후크 서브액션 0x71026a88d8(주 vt+0x140)이 `this+0x3976 = state+0x188`로 받고, SuperHook 갱신 앞부분 0x710269ef10이 매 프레임 `this+0x3952 = this+0x3953 ? 1 : (원격 복제이면 this+0x3976, 소유 기기이면 0)`, `this+0x3953 = 0`으로 정리합니다 **[판독]**. +0x3953은 0x71026a07b4 안의 거리 범위 판정(0x71026a07ec 이후 `fVar48 < fVar39 && fVar41 <= fVar48`)으로 켜지고, +0x3952는 0x710269f0cc에서 그래플(`this+0x3a88` = PlayerGrapple)+0x130c가 0이 되면 꺼집니다. 피격 리액션이 +0x3952를 보고 `Damage_SuperHook_WaitOnWall*`을 고르므로(§4.5) **+0x3952 = 슈퍼후크 벽 부착(WaitOnWall) 래치**, #30 = "벽 부착 중(또는 이번 프레임 부착 판정)"입니다 — 구조 [판독]/[실행], 이름 [추정].

**+0xa4 (#24)**: 송신 상태 블록(0x71024873c8~0x7102489200)은 `str xzr, [sp,#0x240]`(0x7102487488)로 +0xa0/+0xa4를 0으로 만든 뒤 +0xa0만 다시 씁니다. 무기 vt+0x78(슈터 0x7102586e14 등)·서브액션 vt+0x60(위 표)·요소 복사도 +0xa4를 쓰지 않으므로 **보내는 값은 항상 0**입니다 **[판독 — 탐색 범위: 송신 함수 전체의 `#0xa4]`/`sp+0x244` 쓰기, 위 가상 함수들]**. 받는 쪽 0x7102475a54(0x7102476558)는:

```
state = 수신 상태(sp+0x3e0)
life  = [[[액터(본체+8)+0x208](+0x200 > 0x20 이면 [32])]+0x50]→[0] +0x28   // 이벤트 LifeNumber 와 같은 객체·필드
if (life 객체 있음 ? state.+0xa4 != life : state.+0xa4 != -1) && 본체+0xd58(쓰러짐 구조체 첫 int) > 0:
    이번 상태는 적용하지 않음(위치·HP·variant 반영 전체를 건너뜀, 0x7102476d4c)
```

즉 수신측은 "+0xa4 = 송신 시 생명 번호"를 기대하는 모양인데 송신측이 채우지 않습니다. 관측 결과: **원격 플레이어가 쓰러져 있는 동안(본체+0xd58 > 0) LifeNumber가 0이 아니면 그 플레이어의 PlayerNetState는 반영되지 않습니다** [판독에서 도출]. 웹은 원본 동작을 유지하려면 +0xa4를 0으로 보내고 같은 조건으로 무시하면 되고, 의도된 동작(생명 번호 비교)이 필요하면 별도 기록으로 남깁니다.

### 4.7 수신 적용 일부 (0x7102475a54, 수신 상태 = sp+0x3e0) [판독]

| 상태 필드 | 수신측 기록 |
|---|---|
| #10 +0x6c HP | `[PlayerCoopZombie(+0xa7c0)+0xeec] == 0`이면 PlayerDamage+0xee0 = hp, 그리고 예측 HP PlayerDamage+0xee4 = min(+0xee4, min(1000, (s32)(1000.0 × (f32)max(d, 0) × 0.016666668 + hp))) (d = max(GameFrame,0) − 스탬프(#17), u32 뺄셈을 s32로 보고 음수면 0; 999 초과면 1000); 아니면 PlayerCoopZombie+0xee0 = hp |
| #11 +0x70, #12 +0x74, #13 +0x78 | #13 거짓: Armor+0xefc ≠ #12 이면 Armor+0xee8 = 0, Armor+0xefc = #12. #13 참: #11 ≥ 0 이면 Armor+0xee8 = #11 |
| #14 +0x7c | 스페셜 비율 평활([../paint/special_gauge.md](../paint/special_gauge.md)) → 본체+0xbe4 |
| #15 +0x80 | 본체+0x6a0 |
| #16 +0x84 | 본체+0xd8 |
| #19, #20 | PlayerStepPaint+0x30, +0x34/+0x38 |
| #26 +0xac | §4.5 |
| #24 +0xa4 | §4.6 (적용 전체를 건너뛰는 조건) |

예측 HP 식의 1000.0은 `0x71058bcccc`(player_life.md의 PlayerDamage 상수 1000.0)이고, "받은 HP에서 송신 이후 경과 프레임 × 1000/60만큼 회복될 수 있다고 보고 예측 HP 상한을 정한다"는 해석은 [추정]입니다.

## 5. 수신·지연 보정 (`PlayerNetControl` 0x7102658bb4) [판독]

기준 객체 = PlayerNetControl(`this`).

| 오프셋 | 의미(판독 근거) |
|---|---|
| +0x3d0 / +0x3d8 | 상태 이중 버퍼(새 상태 수신 시 swap), 상태 +0x1c8 = 유효, +0x1cc = 상태 +0x88(송신 프레임) 복사 |
| +0x3e0 | 이번 프레임 수신 여부 |
| +0x1ff8 | 로컬 프레임 = 플레이어 갱신(0x71024a2c98) 때 `max(GameFrame, 0)` (쓰기 0x71024a527c) **[판독]**. 송신측은 같은 값을 상태 +0x88로 보냄. GameFrame은 기기 간 공유 시계로 계산되므로([02 §5.5](02_replica_model.md#55-gameframe-기기-간-동기--netutilframestarter-판독--실행)) `+0x1ff8 − 스탬프`는 전송 지연(프레임)입니다 |
| +0x1ffc | 수신 시 = 송신 프레임, 미수신 프레임마다 +1 |
| +0x2000 | 지연 추정 D (프레임) |
| +0x2004 | 가중치 w |
| +0x2008 | 재생 오프셋 S |
| +0xa90/+0xa98/+0xa9c/+0xaa0 | 샘플 링버퍼(항목 0x1c B = 위치 xyz, 방향 xyz, 프레임) 시작·용량·머리·개수. **용량 16**(생성자 0x71026583ac: +0xa98 = 0x10, 배열 this+0xaa4, 0x1c0 B) **[판독]** |
| +0x3e8/+0x3f0/+0x3f4 | 로컬 이력 링버퍼(항목 0x1c B) 시작·용량·머리. **용량 60**(생성자: +0x3f0 = 0x3c, 배열 this+0x3fc, 0x690 B) **[판독]**. 매 프레임 송신 함수 0x7102483134(0x7102483f90 근처)가 머리를 하나 줄이며 (본체+0x8 객체의 +0x28c..+0x294 위치, +0x2a0/+0x2ac/+0x2b8 방향, 프레임 +0x1ff8)을 넣음 |
| +0x3f8 | 로컬 이력 **개수**(0에서 시작해 매 프레임 +1, 최대 60). 샘플 나이 비교의 상한 N으로 쓰임. **정정**: 이전 판은 고정 "창 길이"로 적었으나 생성자에서 0, 이력 push 때마다 증가하는 개수임 **[판독]** |
| +0xc78~+0xc80 | 위치 오차 벡터 |
| +0xc84~+0xc90 | 회전 오차(최단 회전 쿼터니언 x,y,z,w) |
| +0xc94 | 비교에 쓴 샘플 프레임 |
| +0xc6c~+0xc74 | 보정 속도(스프링) |
| +0x1fe8 | 보정 계수 W(다른 곳에서 씀) |

```
// 지연 추정 (매 프레임)
if !received: w *= 0.992
else:
    if (특수모드: G+0x194 && player+0x7b8): D = 2.0
    else: D = D + (1 - w) * ((float)(u32)(this+0x1ff8 - stamp) - D)
    w = 1.0
T = (D > 5) ? D - 5 : (D < 2) ? D - 2 : 0
S += (T - S) * 0.03

// 샘플 선택
수신했으면 (pos, dirA, stamp) 를 링버퍼에 push (가득 차면 가장 오래된 것 덮음)
가장 새 샘플부터: age = (int)((float)(this+0x1ff8 - sample.frame) - S)   // 특수모드면 this+0x1ffc - frame
   age >= N 이면 그 샘플은 버림(개수 감소), 0 <= age < N 인 가장 새 샘플을 선택
선택 샘플 vs 로컬 이력[age]:
   posErr = sample.pos - hist.pos
   rotErr = shortestArc(hist.dir → sample.dir)   // d = a·b+1 <= 1.19e-6 이면 180° 처리
```

지연 추정은 **샘플을 받은 직후 w가 1로 돌아가므로, 매 프레임 받으면 D가 움직이지 않습니다.** 4프레임 주기에서는 직전 가중치가 0.992³ ≈ 0.976이라 수신마다 약 2.4%씩 따라갑니다. 재구현 시뮬레이션(지연 8프레임 고정): 60프레임 후 D≈2.43, 300프레임 후 D≈6.69, S≈1.37, 599프레임 후 D≈7.78, S≈2.73 (`verify_result.json` `delay_estimator_sim`) **[재구현]**. "2~5프레임은 그대로 두고 그 밖의 초과분만 천천히 반영한다"는 해석은 **[추정]**입니다.

### 5.1 오차 반영 [판독, 의미는 추정]

```
e = |posErr|;  r = clamp((e - 5) / 10, 0, 1);  k = 1 - r          // 오차 5 이하 k=1, 15 이상 k=0
gain = 0.1~0.3 (오차 방향과 어떤 축(player+0x108 객체 +0x34..0x3c)의 내적으로 결정, 특정 상태에선 0)
a1 = k*0.0005 + 0.0005;  a1 += W*(0.002 - a1)
damp = k*0.045 + 0.9;    damp += W*(0.85 - damp)
velCorr = damp * (velCorr + gain * a1 * posErr)      // 0x710265b504/0x710265b7ec 로 제약 후
a2 = k*0.02 + 0.01;      a2 += (0.07 - a2) * W
step = gain * (a2 * posErr + velCorr)
posErr -= step;  표시 위치 += step
```

`0x710265b504`, `0x710265b7ec`(벡터 보정 함수)는 판독하지 않았습니다 **[미확정]**. 오차가 클수록 계수가 작아지는 점(5→15 구간)은 판독 그대로이며 이유는 모릅니다. 큰 오차를 순간이동으로 처리하는 경로가 따로 있는지 **[미확정]**.

## 7. 표현과의 연결

위치·방향 외 필드(variant, InkAction 하위 상태)는 수신측 애니메이션·무기 표현(잉크 탱크, 차저 충전, 롤러 상태 등)에 쓰일 것으로 보이며, 소비 함수는 InkAction 타입별 GOT 사용처(`vtable_got_users.tsv`, 예 Shooter 0x7102586ec4, Charger 0x7102543a40)입니다 **[추정 — 소비 함수 미판독]**.

## 9. 웹 포팅

- 서버(또는 상대 클라이언트)에 보낼 플레이어 상태는 위 44개 항목 + variant 3개가 원본 기준 집합입니다. 의미가 밝혀진 위치·속도·방향·프레임 스탬프·상태 종류(Squid/Human, Jump/DokanWarp/RespawnLand, InkAction 종류)부터 구현하고, 나머지는 [player](../player/movement_physics.md)·무기 문서에서 의미가 밝혀지는 대로 채웁니다.
- 송신 주기: 60 fps 고정 스텝 기준 **4스텝마다** 1회. 웹에서 표시 프레임이 달라도 게임 스텝 번호로 판정합니다.
- 수신 보정: 위 지연 추정(0.992, 0.03, 창 2~5)과 오차 스프링(계수 표)을 그대로 옮기면 원본과 같은 "원격 캐릭터 따라붙는 느낌"을 재현할 수 있습니다. 로컬 표시 이력은 최대 60프레임(1초), 받은 샘플은 최대 16개를 보관하며, 나이 ≥ 이력 개수인 샘플은 버립니다 **[판독]**.
- 프레임 스탬프와 `+0x1ff8`은 모두 공유 시계로 계산한 GameFrame이어야 지연 D가 전송 지연이 됩니다. 웹에서는 서버 시계 동기 후 `frame = floor((now − startClock) * 60 / 1000)`로 같은 의미를 유지합니다([06](06_web_port.md)).
- 필드 출처(§4, §4.2, §4.3)는 원본 본체 오프셋입니다. 웹 상태 객체 권장 이름(원본 이름 아님): `pos`, `velA`, `velB`(미상), `dirA`, `dirB`(미상), `aimDirXZ`(#8), `cameraPitch`(#9), `hp`(#10), `armorHp`/`armorGen`/`armorActive`(#11~13), `specialPercent`(#14), `inkTank`(#15), `airFrames`(#16), `stamp`(#17), `specialActive`(#18), `footInkKind`/`footInkTeam`(#19/#20), `jumpRecordSeq`(#21), `body_0xcfc`(#22), `actionSeq`/`actionKind`(#23/#25), `lifeSlot`(#24, 항상 0), `jumpStartSeq`(#26), `superHookOnWall`(#30), `rulePos`/`ruleFlag`(#31~34, Rule 3/5), `grappleTarget`/`grappleSeq`(#38/#39), `yaguraFlag`(#44, Rule 2). 의미 미상 필드는 원본 오프셋 이름(`body_0xd08` 등)으로 보존합니다.
- 1회성 동작은 3비트 회차 카운터(mod 8)로 보냅니다(§4.5). 웹 수신측은 "자기 카운터 ≠ 받은 값이면 한 번 재생 후 맞춤"을 지켜야 4프레임 주기 사이의 동작이 빠지지 않습니다(카운터 차이가 8의 배수면 변화가 보이지 않음. #26 수신측은 조건이 맞는 프레임마다 1씩 따라감 — 판독에서 도출).

## 10. 검증 기대값

| 입력 | 기대 | 확정 |
|---|---|---|
| 기본 생성 PlayerNetState write | 546비트, 항목 63 + 패딩 바이트 1 | [실행] |
| read에 variant3 인덱스 3 공급 | `InkActionCharger` 생성, 총 비트 546 | [실행] |
| 위치 10.5 | 2687 → 10.49625 | [실행] |
| 지연 8프레임 고정, 4프레임 주기 | D: 0.19(4f) → 2.43(60f) → 6.69(300f) → 7.78(599f) | [재구현] |
| 매 프레임 수신 | D 불변(0), S → −2.0 | [재구현] |
| 기본 PlayerNetState를 원본 writer(0x7103582678)로 직렬화 | 546비트 = 68바이트 + 대기 2비트, 바이트열이 LSB 우선 재구현과 같음(`network_bitpack.py`) | [실행] |
| Jump +0x24 = 1.5 | (u32)((1.5+100)·65536+0.5) = 6651904 | [판독 — 식] |
| 스페셜 비율 0.995 / 1.0 | +0x7c = 99 / 100 | [판독 — 식] |
| `Rule` 문자열 Pnt/Var/Vlf/Vgl/Vcl/Tcl (0x71010c8e3c) | 0/1/2/3/4/5, 그 밖 문자열은 쓰지 않음 | [실행] (`network_rest_verify.py` [1]) |
| SuperHook (+0x3952,+0x3953) = (0,0)/(0,1)/(1,0)/(1,1) → +0x188 | 0/1/1/1 (주 vt 0x71026a8938, 보조 0x71026a8968 같음) | [실행] [2] |
| 0x7102469fac(구조체, 상태 0xd) | 본체+0xd04: 7→0, 본체+0xd0c = 2 (표 §4.5) | [실행] [6] |

## 11. 미확정

| 항목 | 상태 | 근거가 필요한 곳 |
|---|---|---|
| 필드별 **출처** | 해소 [판독] — §4·§4.2·§4.3 (0x7102483134 디컴파일 `net_player_send.c`) | — |
| 출처 필드의 **게임 의미** | **부분 해소(3차, [netrest])** — 판독/실행으로 이름 붙임: #8 조준 수평 방향·#9 카메라 피치 p(사용처 판독, 이름 추정), #10 HP·#11 아머 HP·#13 아머 활성·#16 공중 프레임·#18 스페셜 사용 중·#19 발밑 분류·#20 발밑 팀 [판독], #21 점프 기록 카운터·#26 점프 시작 카운터 [판독], #23/#25 1회성 동작 카운터·종류 [실행], #30 슈퍼후크 벽 부착 [실행+판독], #24 항상 0 [판독], #15 잉크 탱크·#12 아머 회차 [추정]. **남음**: #5 속도 B(본체+0xfc), #7 방향 B(본체+0x198), #22 본체+0xcfc·#37 본체+0xd08(writer 미발견), #38 대상 값, #42/#43 본체+0xb60/+0xb61, #44 야구라 플래그 뜻, #4의 본체+0xa2c 항, #35/#36 무기 값 | 남은 필드의 writer(본체 기준 `str`/`add #off` 스캔으로 플레이어 코드 범위에서 못 찾음 → 다른 기준 레지스터 경로), [move]/[respawn] 판독 |
| #24(+0xa4), #30(+0x188 SuperHook) 를 1로 쓰는 곳 | **해소** — #30: `PlayerSubActionSpSuperHook` 보조 vt+0x60 0x71026a8968 [실행]. #24: 송신 writer 없음(항상 0), 수신측은 LifeNumber와 비교해 쓰러짐 중 상태를 버림 [판독] (§4.6) | — |
| 무기별 InkAction 채우기(Charger 0x710254398c 등) | 미판독 | 각 함수 |
| `Rule` 값 2/3/5 ↔ 룰 이름 | **해소 [실행]** — 0x71010c8e3c 원본 실행: Pnt 0, Var 1, Vlf 2, Vgl 3, Vcl 4, Tcl 5 → 2 야구라, 3 호코, 5 트리컬러 | — |
| +0x1ff8 프레임 출처 | 해소 [판독] — max(GameFrame,0), 0x71024a527c | — |
| 이력 창 N(+0x3f8), 링버퍼 용량 | 해소 [판독] — 이력 60, 샘플 16, N = 이력 개수 (정정) | — |
| `요소+0x20 == 1`(매 프레임 갱신 모드) 의미 | [추정] Protocol=Reliable(1)일 가능성 | 요소 생성 코드에서 NetEnlElementParam+0x44(Protocol) 를 요소+0x20에 쓰는지 |
| InkActionSuperHook 사용 경로 | 해소 [판독] — 내장 하위 객체 +0x168 (정정) | — |
| #21·#23·#25 카운터의 수신 재생 코드 | 미확정 — #26(점프 시작)만 0x710248142c에서 판독 | 0x7102475a54 안 상태 +0x98/+0xa0/+0xa8 를 레지스터 기준으로 읽는 곳 |
| 수신측이 쓰러짐 중 상태를 버리는 조건(#24)의 실제 빈도 | 미측정 — LifeNumber 증가 시점([respawn]) 필요 | 소유 넷 객체 +0x28 writer |
