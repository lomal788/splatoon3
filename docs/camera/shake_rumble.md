# 카메라 쉐이크·컨트롤러 진동·연출 카메라 자료

목차: [camera_feel.md](camera_feel.md). sead 곡선 평가식은 [camera_feel.md §4.4](camera_feel.md#44-sead-곡선-평가-판독).

## 1. 기능 개요

폭발·착지·사망·스페셜 발사 같은 순간에 화면이 짧게 흔들리고(카메라 쉐이크) 컨트롤러가 진동합니다. 둘 다 **ELink(이펙트 링크) 에셋 파라미터**로 지정됩니다. ELink 에셋이 재생되면 `CameraRumbleName`(→ `CameraModuleParam.Rumble`의 곡선 이름)과 `CtrlRumbleName`(→ `Rumble/Common.bnvib.sarc` 안 진동 파형)이 함께 시작됩니다.

## 2. 자료

| 자료 | 위치 | 수준 |
|---|---|---|
| 카메라 쉐이크 곡선 10종 | `Pack/SingletonParam.pack.zs` → `Gyml/Singleton/game__CameraModuleParam.game__CameraModuleParam.bgyml`의 `Rumble` (해제본 `analysis/camera/SingletonParam/…json`) | [데이터] |
| 카메라 보간 곡선 13종 | 같은 파일 `Interpolation` | [데이터] |
| 진동 모듈 설정 | `game__RumbleModuleParam`: `LimiterParams=[{PatternName GMBT_ToSquidMix00.bnvib, LimitFrm 8}]`, `RumbleDistFactor 1.0` | [데이터], 의미 [추정] |
| 진동 파형 115개 | `Rumble/Common.bnvib.sarc.zs` → `analysis/camera/rumble_bnvib/` | [데이터] |
| RSDB `RumbleCall` | 행 0개 (빈 표) | [데이터] |
| `RumbleAgent` 액터 | Behavior `spl::RumbleAgent`, CalcPriority After | [데이터], 코드 미판독 |
| ELink 에셋별 진동/쉐이크 | `analysis/camera/rumble_map.json` (518 에셋, 182 사용자) — [effect_sound] 파서 출력 재가공 | [데이터] |

## 3. 카메라 쉐이크

### 3.1 파라미터 `game::CameraRumbleParam` (팩토리 0x710100e6b4, vtable 0x71055542b0, 방문 0x710100e790) [판독]

| 오프셋 | 필드 | 타입 | 기본값 |
|---|---|---|---|
| +0x30 | Curve | sead 곡선 (+0x38 타입 u32, +0x3c MaxX, +0x40 개수 u8, +0x48 데이터 포인터) | 타입 0, MaxX 1 |
| +0x50 | Axis | vec3 | (0, 1, 0) |
| +0x5c | Scale | f32 | 1.0 |
| +0x60 | IsLooped | bool | false |

### 3.2 갱신 (0x71010182e8, 기준 = 쉐이크 인스턴스) [판독]

```
inst: [0] 파라미터 핸들, +0x14 frame(s32), +0x18 경과(s32), +0x28 gain(f32), 출력 +0x1c/+0x20/+0x24
t = (Curve.type < 3) ? frame / Curve.MaxX : frame
v = curve(t) * gain * Scale
out = (Axis.x*v, Axis.y*v, Axis.z*v)
frame++, 경과++
IsLooped && frame >= MaxX → frame = 0
종료 판정 0x7101018998 (비루프) [미확정: 비교식]
```

인스턴스 배치(stride 0x48, 카메라 모듈 +0x138 배열·개수 +0x130) [판독]:

| 오프셋 | 형 | 의미 | writer |
|---|---|---|---|
| +0x00/+0x08 | 핸들 | 곡선 파라미터(CameraModuleParam.Rumble 항목), 0이면 빈 칸 | 시작 0x7101010f14 |
| +0x10 | s32 | 일련번호(모듈 +0x128 증가값) — 호출자가 (포인터, 번호)로 소유 확인 | 시작 |
| +0x14 / +0x18 | s32 | 곡선 프레임 / 경과 프레임 | 시작 0, 갱신 +1 |
| +0x1c..+0x24 | vec3 | 출력 Axis·v | 갱신 |
| +0x28 | f32 | **gain** — 시작 시 1.0 | 시작, ELink·코드 호출자 |
| +0x2c | s32 | 지속 프레임 상한 — 시작 시 −1(없음), ELink `CameraRumbleFrame` ≥ 1이면 그 값 | ELink 0x710137b17c |
| +0x30 / +0x38 / +0x40 | u8 / ptr / s32 | 소유자 추적 켜짐, 소유자, 소유자 번호 | ELink 0x710137b160 |

### 3.2a 시작·종료·소유자 [판독]

```
start(name):                                   // 0x7101010f14 (this = *(0x710580c3b0)+0xe8 카메라 모듈)
  param = Rumble 표에서 name 찾기 (0x7101012e04) ; 없으면 실패
  빈 칸(isFinished) 하나 골라 {param, 번호=++serial, frame=0, elapsed=0, gain=1.0, frameLimit=−1, follow=0}
isFinished(inst):                              // 0x7101018b4c
  frameLimit ≥ 1 && elapsed ≥ frameLimit → 끝 ; 파라미터 없음 → 끝 ; 아니면 곡선 기준(비루프는 MaxX 도달) [곡선 쪽 비교식 판독-부분]
update(inst):                                  // 0x71010182e8 (§3.2)
  follow && 루프 && (소유자 사라짐 또는 번호 불일치) → 칸 비움
```

### 3.2b 출력이 더해지는 곳 — 카메라 **위치**, 월드 좌표 [판독]

카메라 모듈 갱신 0x7101010150:

```
poser = this+0x120 ; poser.vt+0x28() ; poser.vt+0x30(&pose(this+0xd4))   // 활성 카메라 포저의 포즈
for inst in shakes(+0x138, n=+0x130): update(inst)
sum = Σ_{!isFinished(inst)} inst.out                                     // x=+0x1c, y=+0x20, z=+0x24
pose' = pose (this+0x144 사본) ; pose'.pos += sum                         // pose = {pos vec3, rot quat, near 0.1, far 10000, …}
0x7101017434(&pose', this+0x190(카메라), this+0x220(투영))                 // 뷰 행렬 구성
```

- 쉐이크는 **카메라 위치만 월드 축으로 평행이동**합니다. 회전(쿼터니언)은 바꾸지 않으므로 시선 방향은 그대로이고 화면 전체가 Axis 방향으로 흔들립니다. Axis 기본 (0,1,0) = 월드 위아래 [판독].
- 플레이어 카메라(spl:PlayerCamera) 출력이 이 모듈의 활성 포저 포즈로 들어가는 연결은 [미확정]입니다(대전 카메라도 이 모듈을 거친다는 것은 [추정]). 2026-10-03 진행 [판독]: 활성 포저 설정 함수는 0x7101010de0(`this+0x120 = 포저`, 포저 vt+0x20 호출 뒤 vt+0x30(&this+0xd4)로 포즈 복사)입니다. PlayerCamera의 `+0x60`은 자기 `+0x30`을 가리키는 내부 출력이라([player_camera.md](player_camera.md) §4.2) 모듈과의 연결은 별도 포저 객체를 거칩니다. 플레이어 쪽 호출 0x710233dbd4·0x710233e050·0x710233e270(꼬리 분기 `b 0x7101010de0`)이 소유 객체+0x160의 포저를 넘기며, 이 포저는 0x710233c414가 할당합니다. 다음 근거: +0x160 포저의 클래스·vt+0x30이 PlayerCamera의 +0x30/+0x70/+0x7c를 읽는지.
- 정정(2026-10-03 6차, [r6 camweapon]) [판독]: 위의 0x710233dbd4·0x710233e050·0x710233e270과 +0x160 포저(할당 0x710233c414)는 플레이어 카메라 경로가 아닙니다. 소유 객체의 초기화 0x710233c414가 상태 `State::Control`, `State::SelfTimer`, `State::Capture`, `State::Amiibo`를 등록하므로, 이것은 촬영(사진·amiibo) 컨트롤러입니다(`analysis/decomp/r6_camweapon/poser.c`). 이전 판의 "플레이어 쪽 호출"은 주소 범위만 보고 붙인 이름이라 철회합니다.
- 모듈+0x120(활성 포저) writer 전수 [판독] (`web/tools/bl_callers.py 0x7101010de0`, 모듈 경로 자료 흐름 스캔):
  - setPoser 직접 호출은 bl/b 36곳입니다. 이 가운데 `0x7102d1f8a4`·`0x7102d1fae0`은 `Coop_Result_Default`/`Coop_FinalResult` CameraPoserFixedParam 포저(생성 0x7102d1e8b0/0x7102d1e8e0)를 넘깁니다.
  - 인라인 쓰기는 4곳입니다. `0x7100fc76ac`(요청 객체+0x28 포저, +0x40 보간 이름 → `0x7101012fac`/`0x7101017ba8` 보간, 직접 호출자 없음 = 가상 함수), `0x7102121bcc`, `0x710221e1c8`(SupplyPoint 포저), `0x71022221dc`입니다.
  - PlayerCamera vtable(0x7105633960)은 포저 인터페이스(vt+0x20 활성, vt+0x28 갱신, vt+0x30 포즈 복사)와 슬롯 의미가 다릅니다(슬롯5·6 = 소멸자). 따라서 PlayerCamera 자체가 포저로 들어가지는 않습니다.
- 다음 근거: 0x7100fc7654의 vtable과 그 요청을 만드는 쪽, 0x7102121034. PlayerCamera 포즈(this+0x88, 0x7101016d0c가 만드는 위치·쿼터니언·거리)를 읽는 포저 클래스를 찾아야 합니다.

### 3.2c gain 출처 [판독]

| 호출자 | 쉐이크 | gain |
|---|---|---|
| ELink 에셋 재생 0x710137b000 | `CameraRumbleName` | `DistanceAttenuate ≥ 1`이면 `0x710130d3a8(카메라 모듈+0x1c8, 이미터 위치)`, 아니면 1.0 |
| 스피너 잉크액션(0x71025c42b0 부근) | `SpinnerShooting` | c = 0x71025c7e98(this,0,0), s = (c − 0.15)/0.85; s ≤ 0이면 정지, 아니면 `sign(s)·|s|^0.51457`(= bias(s, 0.7)) |
| HUD 관리자 0x710275c1ac | `FootPaintEnemy`(루프) | 1.0. 관전 대상의 PlayerStepPaint(+0xa688)+0x30 ∈ {2,3}(적 잉크 밟음으로 추정) && 코옵 좀비 아님 && 다운 카운터 4개 ≤ 0 이면 유지, 아니면 정지 |

거리 감쇠 0x710130d3a8:

```
d = |listener − emitter|                    // listener = 카메라 모듈+0x1c8 (카메라 위치로 추정)
A = RumbleModuleParam.CameraMinPowerDist (+0x5c, 기본 25) ; B = CameraMaxPowerDist (+0x58, 기본 15)
A > B: gain = 1 − clamp01((d − B)/(A − B))  // d ≤ 15 → 1, d ≥ 25 → 0
A ≤ B: gain = clamp01((d − A)/(B − A))
```

`game::RumbleModuleParam`(방문 0x710130ba14, 생성 0x710130b874)의 필드: `LimiterParams`, `CameraMaxPowerDist 15 (+0x58)`, `CameraMinPowerDist 25 (+0x5c)`, `RumbleDistFactor 0.3 (+0x60)`, `RumbleMaxPowerDist 4 (+0x64)`, `RumbleMinPowerDist 30 (+0x68)` [판독]. 데이터(`game__RumbleModuleParam.bgyml`)는 LimiterParams와 RumbleDistFactor(1.0)만 덮어써서 카메라 거리값은 기본값 15/25입니다 [데이터].

### 3.2d ELink 파라미터 의미 정정

ELink 처리 함수는 시스템 파라미터 인덱스 표(`*x28 + 0x3b0..`)로 값을 읽습니다. 코드 쪽 열거 문자열은 `ForceTeam , ShaderGraphParam , DistanceAttenuate , CameraRumbleName , CameraRumbleFrame , CtrlRumbleName , CtrlRumbleGain , CtrlRumblePitch , CtrlRumbleStretch , CtrlRumbleExtra , CullingDistance`(main_strings 37224행) 11개이고, 읽는 칸이 +0x3b8(정수, ≥1 검사) / +0x3bc(문자열) / +0x3c0(정수, ≥1이면 +0x2c) / +0x3c4(문자열) / +0x3d0(실수) / +0x3d4(정수) 이므로 표 시작 +0x3b0 = ForceTeam으로 맞추면 각각 **DistanceAttenuate / CameraRumbleName / CameraRumbleFrame / CtrlRumbleName / CtrlRumbleStretch / CtrlRumbleExtra** 입니다 [판독+데이터 대응].

- 앞 판본에서 "범위/세기 단계"로 추정한 ELink 파일 파라미터 `CameraRumble`(정수, 기본 −1, ParamDefine 33번)은 이 코드 열거에 **없습니다**. 쉐이크 시작 함수는 이 값을 읽지 않습니다 [판독].
- (3차, [effect_sound]) **`CameraRumble`(33)과 `CtrlRumblePattern`(36)은 런타임이 읽지 않는 파라미터입니다** [판독]. 근거: ① 게임이 ParamDefine을 이름으로 찾는 목록은 위 11개 열거 문자열 하나뿐이고 두 이름은 없습니다. ② main 전체에 `CameraRumble `, `CtrlRumblePattern ` 문자열이 없습니다(접미사 병합으로도 못 만듦 — 둘 다 다른 이름의 접두사). ③ xlink 파라미터 비트마스크로 번호를 직접 고르는 코드(33번 = `and #0x1ffffffff`, 36번 = `#0xfffffffff`)가 0x7101300000–0x7103a00000에 없습니다. 데이터의 0~5 값(11건)과 `CtrlRumblePattern` 10002~10057은 툴 쪽 정보로 보고, 웹은 무시합니다. 거리 감쇠를 켜는 값은 `DistanceAttenuate`(ParamDefine 34번, 기본 1 — 대부분 에셋이 감쇠 켜짐) [정정].
- `CameraRumbleFrame` ≥ 1 = 지속 프레임 상한(곡선 길이와 무관하게 그 프레임 수가 지나면 종료) [판독]. 데이터 값 5/50(11건).
- 진동(컨트롤러) 쪽도 같은 함수 뒷부분이 `DistanceAttenuate ≥ 1`이면 0x710130d764(같은 모듈 +0x1c8, 이미터)로 거리 판정을 합니다. 진동 감쇠 식(RumbleMax/MinPowerDist 4/30, RumbleDistFactor)은 판독하지 않았습니다 [미확정].

### 3.3 곡선 10종 [데이터] + 재구현 샘플 [재구현 계산]

`camera_shake.py rumble` → `analysis/camera/camera_rumble_samples.json` (gain 1 기준, 프레임별 값).

| 이름 | 타입 | MaxX(프레임) | Scale | 루프 | Axis | 최대 |v| | ELink 사용 수 |
|---|---|---|---|---|---|---|---|
| Fuwa | Hermit (값0·접선 감쇠 진동 5키) | 15 | 0.2 | × | 기본 | 0.2422 | 71 |
| FuwaWeak | Hermit | 15 | 0.1 | × | 기본 | 0.0409 | 47 |
| FuwaStrong | Hermit | 15 | 0.3 | × | 기본 | 0.1228 | 26 |
| FuwaLoop | Hermit | 15 | 0.1 | ○ | 기본 | 0.0346 | 3 |
| ZigZag / ZigZagStrong | Linear 9점 | 8 | 0.2 | × | 기본 | 0.1 | 1 / 2 |
| ZigZagLoop | Linear ±0.5 교대 | 16 | 0.1 | ○ | 기본 | 0.05 | 1 |
| ZigZagStrongLoop | Linear ±0.5 교대 | 20 | 0.2 | ○ | (0,1,0) | 0.1 | 1 |
| SpinnerShooting | Sin (0.18 주기/프레임, 진폭 1) | 20 | 0.02 | ○ | 기본 | 0.02 | 1 |
| FootPaintEnemy | Hermit 9키 | 50 | 0.12 | ○ | (0,1,0) | 0.0825 | 0 (코드 직접 호출: HUD 관리자 0x710275c1ac, §3.2c [판독]) |

Fuwa 계열 Hermit 데이터는 (값, 접선) 쌍이 전부 값 0이고 접선만 있어, 키 사이에서 부호가 바뀌는 감쇠 진동이 됩니다. FuwaStrong은 첫 접선이 1.58로 Fuwa(4.58)보다 작아서, Scale이 0.3으로 더 큰데도 gain 1 기준 최대치(0.1228)가 Fuwa(0.2422)보다 작습니다. 이름과 반대이지만 데이터 그대로입니다 [데이터+재구현 계산]. 실제 세기는 gain에 따라 달라집니다.

## 4. ELink 연결

`camera_rumble_map.py SplPlayer` 발췌 (전체는 `rumble_map.json`) [데이터]:

| 사용자 / 에셋 키 | 카메라 쉐이크 | 진동 파형 (Gain, Pitch, Stretch) |
|---|---|---|
| SplPlayer / Death_00_00, Death_00_01, Death_01 | FuwaStrong, CameraRumble 2 | — |
| SplPlayer / DeathFall | FuwaWeak | PresetDoon (–, 0.5) |
| SplPlayer / 水没_インク·水·Coop | Fuwa | PresetDohoon (3.0, 0.3) |
| SplPlayer / スーパージャンプ着地点破壊_01/02 | Fuwa | REDS_Tr_PresetDon (0.5, 0.8) |
| SplPlayer / スーパージャンプ飛沫_F/FC | — | PresetGataGataLv (5.0, 0.4) |
| SplPlayer / スポナージャンプ移動線_Focused | FuwaStrong | — |
| SplPlayer / InkLand_00_0x (잉크 착지) | — | GMBT_InkDiveDeep (3.0, 0.7), Pattern 10024 |
| SplPlayer / InkLand_01_x | — | GMBT_InkDiveLight00 (5.0, 0.2), Pattern 10025 |
| SplPlayer / InkDash_00 | — | PresetGataGataLv, Gain = 곡선(MoveVelXZ 0.14→0, 0.2→0.5, 0.5→1.0) |
| SplPlayer / 敵塗り踏み振動 | FuwaStrong | PresetDon (3.0, 0.5, 2.0) |
| SplPlayer / DashPanelDash | Fuwa, CameraRumble 1 | ARMS_Grapple (0.6, 0.3, 1.2) |
| WeaponChargerNormal / マズルフラッシュ_Focused_02 | Fuwa | PresetDoon (0.5, –, 0.8) |
| WeaponSpUltraShot / マズルフラッシュ_00 | FuwaStrong | PresetDoDon |
| WeaponSpChariot / キャノンマズルフラッシュ_00 | Fuwa, CameraRumble 2 | PresetDoDon |
| WeaponSpMultiMissile / Muzzle_High_0x | FuwaWeak, CameraRumble 0, Frame 5 | PresetDott (–, 0.7), Pattern 10012 |

- **슈터(WeaponShooter*) ELink 에셋에는 진동/쉐이크 파라미터가 없습니다** [데이터]. 코드에서 컨트롤러 진동을 직접 거는 함수 0x710130f0b8(진동 재생, 인자 (0, 진동 관리자 `*0x71057954c0`, 종류, &파형 이름, 0))의 직접 호출자는 전체에서 **3곳뿐**입니다 [판독: bl 전수 스캔]: ELink 처리 0x710137b000, 플레이어 0x71024b1510(`ARMS_UIButtonDecide.bnvib`), 0x7102da1118(`GMBT_ZLZR.bnvib`, vtable 0x710568ddd8 소속 — UI/튜토리얼 쪽으로 보임 [추정]). 따라서 **대전 슈터 발사 진동은 없습니다** [판독 — 직접 호출 기준; 가상 호출로 같은 함수에 오는 경로는 별도 확인 안 함].
- `PresetDon.bnvib` 문자열 7곳(0x7103df681c, 0x7103df7064)은 발사 코드가 아니라 진동 파라미터 배열을 BYML에서 읽을 때 원소 기본값(이름 `PresetDon.bnvib`, gain 1.0)을 채우는 로더입니다 [판독].
- 코드에서 직접 거는 **카메라 쉐이크**는 `SpinnerShooting`(스피너 발사, 세기 = 충전/발사 비율 함수)과 `FootPaintEnemy`(적 잉크 밟기) 두 개입니다(§3.2c) [판독].
- `Focused`가 붙은 에셋은 자기 플레이어 시점 전용으로 보입니다 [추정].
- 사용자 이름이 해시(`#5ae56e8f` 등)로 남은 항목이 있습니다. [effect_sound]의 이름 복원 결과에 따릅니다.

## 5. CameraAnimation과 데모 카메라 [데이터]

`romfs/CameraAnimation/*.camera.bfres.zs` 25개: `D1_01 … D9_01, D5_D01`(히어로 모드 데모), `DemoCamera`, `Demo_Plaza_Overview`, `Enm_BankaraIdolCShadow, Enm_Bear, Enm_MasterShark, Enm_RailKingDesert, Enm_Utsubox`(보스), `Fld_PlayerMakeTrainInside`, `Obj_StaffRollName`, `PlayerMake_WeaponGet`.

- 대전의 **스페셜·슈퍼점프·사망·리스폰용 카메라 애니 파일은 없습니다**. 이들은 코드 카메라([player_camera.md](player_camera.md))와 ELink 쉐이크로 표현됩니다 [데이터 + 추정].
- 로더: 문자열 `CameraAnimation/%s.camera.bfres`를 0x71010193b4가 참조합니다(game::CameraAnim 계열) [판독-부분]. 애니 재생 갱신 0x7101014770은 bfres 카메라 애니(위치·회전 행렬)와 DOF 값(+0x38..+0x50, 기본 0.4/5/5/10)을 함께 보간합니다 [판독-부분].
- 대전 시작/결과 데모는 `Model/DemoCamera.bfres` 안 `Work/Model/Etc/DemoCamera/output/StageInDemo00_%sL/R.camera.fsnb`, `StartCam00_VS.camera.fsnb`, `Result_Win00.camera.fsnb` 같은 장면 이름을 씁니다 [데이터 — 문자열].
- 고정 카메라 포즈: `Gyml/*.game__CameraPoserFixedParam.bgyml` 9개(Vss_* 스테이지 뷰 등).
- bfres 카메라 애니(FSCN) 변환은 [graphics]의 BfresLibrary로 가능한지 확인하지 않았습니다. **범위 밖(2026-10-03)** [데이터]: 위 25개 파일은 히어로 모드 데모·보스·광장·스태프롤·플레이어 생성용이고, 사격장(Lby_Lobby00)과 대전에는 카메라 애니 파일이 없습니다.

## 6. 히트 피드백 연결점

- 탄이 맞았을 때의 이펙트·사운드는 `HitEffectConfig`(셀별 E1/E2 이펙트, S1/S2 사운드, `analysis/effect_sound/HitEffectConfig.json`)가 정합니다 — [effect_sound]/[combat] 범위.
- 화면 히트마커(조준선 반응)는 HUD 레이아웃 쪽이며 [ui] 범위입니다. 이 영역에서는 카메라/진동 쪽 반응(예: `敵塗り踏み振動` 쉐이크·진동)만 다뤘습니다.
- 적에게 맞힌 자기 탄의 진동/쉐이크 ELink 에셋은 이번 추출에서 찾지 못했습니다 [미확정].

## 7. 컨트롤러 진동 파형 (.bnvib)

### 7.1 구조와 디코드 — 확정(2026-10-03, [r5 camweapon]) [실행]+[판독]+[데이터]

디코더는 SDK 모듈 `extracted/exefs/sdk.img`의 `nn::hid::detail::ParseVibrationFile`(sdk+0x24aa70)과 `nn::hid::detail::RetrieveVibrationValue`(sdk+0x24ab90)입니다(동적 심볼). 두 함수 모두 다른 함수를 부르지 않는 리프입니다.

```
// ParseVibrationFile(info, ctx, file, size)  [판독]
u32 metaSize   @0   → info+0      // < 4 이면 오류
u16 format     @4   → info+4      // != 3 이면 오류
u16 sampleRate @6   → info+6      // != 200 이면 오류
if metaSize >= 0xC:  isLoop(info+0x10) = 1, loopStart(+0x14) = u32 @8, loopEnd(+0x18) = u32 @0xC   // loopStart > loopEnd 이면 오류
                     loopInterval(+0x1C) = metaSize >= 0x10 ? s32 @0x10 (음수면 오류) : 0
else:                isLoop = 0, loopStart = 0, loopEnd = 샘플 수, loopInterval = 0
u32 dataSize @ metaSize+4 → info+8 ; 샘플 수 = dataSize >> 2 → info+0xC   // 루프면 loopEnd > 샘플 수 오류
ctx+0 = file + metaSize + 8 (샘플 시작), ctx+0xC = 샘플 수 ; 8 + metaSize + dataSize > size 이면 오류

// RetrieveVibrationValue(value, i, ctx)  [판독]
b = ctx.samples + 4*i
value.amplitudeLow  = f32(b[0]) / 255f
value.frequencyLow  = T[b[1] & 31] * f32(10 << (b[1] >> 5))
value.amplitudeHigh = f32(b[2]) / 255f
value.frequencyHigh = T[b[3] & 31] * f32(10 << (b[3] >> 5))
// T = sdk+0xaceb9c, f32 32개 = 2^(k/32) 를 소수 6~7자리로 적은 값(정확한 2^(k/32) f32 와는 3개만 같음, 최대 차 4.9e-7) [데이터]
```

- 루프 칸은 **샘플 인덱스**이고, 샘플은 **{저역 진폭, 저역 주파수, 고역 진폭, 고역 주파수}** 순서이며, 진폭은 **선형(바이트/255)**입니다. 주파수는 `10·2^(code/32)`에 가깝지만 비트 일치를 위해서는 SDK 표 T를 그대로 써야 합니다. 0x80 → 160Hz, 0xA0 → 320Hz, 0x93 → 10·2·T[19] ≈ 241.83Hz.
- 원본 실행 `PY web/tools/r5_camweapon_bnvib_emu.py`: `analysis/camera/rumble_bnvib/` 115개 파일의 헤더 정보 115/115, 전 샘플 **30,240/30,240** 이 독립 디코더(위 식 + 표 T)와 비트 일치했습니다. 스텁 없음. 결과 `analysis/completion/r5/camweapon_bnvib_emu.json`. 루프 파일 15개는 모두 metaSize 0xC(loopInterval 0)입니다(예: PresetGataGataLv 7..801, Simple240HzLoop 1..5).
- 115개 전부 `8(+8) + 4 + dataSize = 파일 크기`가 맞습니다 [데이터]. 길이: 15ms(ARMS_CmnShort*) ~ 7.89s(보스 비명). 요약 `analysis/camera/bnvib_summary.json`.
- 정정(2026-10-03): 같은 날 앞 판은 "디코드가 main 밖 SDK라 판독할 수 없다 → [확정 불가]"로 적었습니다. SDK NSO 해제본(`sdk.img`)의 동적 심볼로 디코더를 찾아 실행할 수 있으므로 틀린 근거였습니다. 그보다 앞의 추정 기록: "루프 칸 = 샘플 인덱스 [추정]", "순서 [추정]", "주파수 `f = 10·2^(code/32)` [추정 — 강함]", "진폭 선형/로그 [미확정]" — 모두 위로 확정했고, 주파수는 표 기반으로 정정했습니다.

**재생(VibrationPlayer::OnNextSampleRequired, sdk+0x251908) [판독]**: 생성자(sdk+0x251338)가 재생 속도 +0x58 = 1.0, 누산기 +0x5c = 1.0을 둡니다. `SetPlaySpeed`(sdk+0x2518a4)는 음수가 아니면 +0x58에 씁니다. 매 요청마다 정지(+0x39 = 0)이거나 지연 카운터 +0x54 > 0이면 무음 `{0, 160, 0, 320}`을 내고 지연을 1 줄입니다. 그렇지 않으면 누산기 < 1이면 `누산기 += 속도`만 하고 출력은 바꾸지 않으며(직전 값 유지), 누산기 ≥ 1이면 `누산기 −= 1`마다 현재 위치 +0x40의 샘플을 꺼내고 위치를 1 늘립니다(속도 > 1이면 한 요청에 여러 샘플을 건너뛰고 마지막 값이 남음). 루프(+0x3b)면 loopEnd(+0x48) 이상에서 loopStart(+0x44)로 돌아가고(간격 +0x4c 처리 포함), 루프가 아니면 위치 ≥ 샘플 수(+0x6c)에서 재생 끝(+0x3a = 0)·무음입니다. 따라서 게임의 `SetPlaySpeed(1/Stretch)`는 샘플을 Stretch배 길게 유지합니다.

### 7.2 ELink 진동 파라미터 적용 [판독, 3차 — effect_sound]

ELink 에셋 재생 `0x710137b000`(디컴파일 `analysis/decomp/camera/camui_full1.c`)의 진동 부분:

```
시작(이벤트 처음):
  DistanceAttenuate >= 1 이면 0x710130d764(청자, 이미터) > 0 일 때만(거리 컷)
  name = CtrlRumbleName ; 비면 진동 없음
  h = 0x710130f0b8(0, 진동 관리자 *0x710582a710, CtrlRumbleExtra(bool), &name, 반복 여부)   // 반복 = 에셋 속성 바이트 bit0 또는 vt+0x38
  h.voice.vt+0x18(1 / CtrlRumbleStretch, 1.0)          // 재생 속도 = 1/Stretch  → Stretch 2 = 두 배 길게
  h+0x50 = 1, h+0x58 = 소유 이벤트, h+0x60 = 그 세대
  DistanceAttenuate >= 1 이면 h+0x14 = 1, h+0x18..0x20 = 이미터 위치(거리 감쇠용)
매 프레임(재생 중, 상태 ≠ 0·6):
  h+0x28 = CtrlRumbleGain (값 해석기로 매 프레임 평가 → 속성 곡선 Gain 이 실시간 반영)
  h+0x38 = CtrlRumblePitch
  거리 감쇠 켜짐이면 h+0x18 = 이미터 위치 갱신
```

진동 출력은 SDK `nn::hid::VibrationPlayer`(Load = bnvib 바이트, `SetPlaySpeed`(+0x74), `SetLoop`, `Play`, `SetCurrentPosition`)와 `VibrationNodeConnection::SetModulation`입니다(외부 함수 이름 [데이터: import 표]). 변조 계산 `0x7103c7afa0`:

```
G = mgr(+0x18)+0x58 * v+0x60 * v+0x64 * v+0x40         // 이득 곱
P = v+0x68 * v+0x6c                                     // 주파수 배율 곱
for 각 연결 i:  c = 컨트롤러별 이득 표[i], m = 노드 기본 변조 {gL, fL, gH, fH}
  SetModulation({ gainLow = c*G*m.gL (v+0x79 면 0), freqLow = P*m.fL,
                  gainHigh = c*G*m.gH (v+0x78 면 0), freqHigh = P*m.fH })
```

즉 **Gain은 진폭 배율, Pitch는 주파수 배율, Stretch는 재생 속도의 역수**입니다 [판독]. 핸들 +0x28/+0x38이 보이스 +0x60..+0x6c 중 어느 칸으로 복사되는지는 따라가지 않았습니다 [판독-부분]. `CtrlRumbleExtra`는 `0x710130f0b8` 셋째 인자(진동 종류 bool)이고 의미는 [미확정]입니다.

## 8. 웹 포팅

| 모듈 | 책임 |
|---|---|
| `SeadCurve` | Linear/Hermit/Step/Sin/Cos/SinPow2 (camera_feel.md §4.4) |
| `CameraShake` | 인스턴스 {param, frame, elapsed, gain, frameLimit, owner}, 매 프레임 `out = Axis·curve·gain·Scale`, 루프/종료/소유자 소멸. 살아 있는 인스턴스 out 합을 **카메라 위치(월드)**에 더하고 회전은 그대로(§3.2b). gain은 §3.2c |
| `RumblePlayer` | bnvib 디코드(§7.1 식, 진폭 = 바이트/255 [실행]) → Gamepad API `vibrationActuator.playEffect('dual-rumble', {strongMagnitude=ampLow·Gain, weakMagnitude=ampHigh·Gain, duration = 원래 길이 × Stretch})`. 원본 재생은 200Hz 샘플을 속도 1/Stretch 누산기로 유지·건너뜀(§7.1 재생) [판독]. Gain은 매 프레임 다시 평가(곡선 Gain), Pitch는 주파수 배율이라 브라우저에서는 버림(웹 선택). 저역/고역을 strong/weak에 대응시키는 것은 웹 선택입니다. `CameraRumble`·`CtrlRumblePattern`은 무시(§3.2d) |
| ELink 연결 | `rumble_map.json`을 ELink 재생 이벤트에 붙여 쉐이크·진동 동시 시작 |

웹에서 바뀌는 점: 브라우저 진동은 저/고역 세기와 길이만 지정할 수 있어 HD 진동의 주파수·피치·스트레치는 재현할 수 없습니다. 200Hz 샘플을 16.7ms 단위로 평균해 프레임마다 다시 걸면 진폭 엔벨로프는 따라갈 수 있습니다.

## 9. 검증

`camera_shake.py selftest` → 9항목 PASS (재구현·합성): Linear 중간값·끝값, Hermit 키 위 값·홀수 개수 0·EaseInOut 중간 0.5, Step, Sin 주기, Simple240HzLoop 헤더, 주파수 코드 0x93≈240Hz. `camera_shake.py bnvib` → 115개 크기 일치.

2026-10-02 추가 [재구현 계산]: `camera_shake.py selftest`에 gain 7항목 추가(총 16 PASS) — DistanceAttenuate 0 → 1.0, 거리 10/20/30 → 1/0.5/0, 스피너 비율 0.15 → 정지, 1 → 1, 0.575 → 0.5^0.51457.

검증 안 함: 실제 화면 흔들림 크기(원본 실행 없음), 진폭 해석, ELink 재생 타이밍, 진동 거리 감쇠.

## 10. 미확정

| 항목 | 필요한 근거 |
|---|---|
| (해소) 쉐이크 적용 위치·좌표계, gain 출처, CameraRumbleFrame | §3.2b~3.2d. 남은 것: 카메라 모듈 +0x1c8(청자 위치) 정체 확인, PlayerCamera 출력 → 모듈 포저 연결 |
| ELink `CameraRumble`(정수 0~5) 의미 | **해소** [판독]: 런타임이 읽지 않음(§3.2d). `CtrlRumblePattern`도 같음 |
| 스피너 0x71025c7e98 반환값 의미 | 스피너 잉크액션 판독 |
| ~~bnvib 진폭 해석~~ | **해소**(2026-10-03 [실행]): 선형 바이트/255, SDK RetrieveVibrationValue 원본 실행 30,240샘플 일치(§7.1). 정정: 앞 판 "확정 불가"는 틀림 |
| Pitch/Stretch/Gain 적용 | **해소** [판독] §7.2(주파수 배율·재생 속도 1/Stretch·진폭 배율). 핸들→보이스 칸 복사 경로만 남음 |
| (해소) 슈터 발사 진동 — 직접 호출 없음(§4). 명중 진동 ELink 에셋은 여전히 못 찾음 | 피격자 쪽 진동은 SplPlayer `敵塗り踏み振動` 등 ELink |
| `spl::RumbleAgent`, `RumbleModuleParam.LimiterParams` 동작 | 클래스 vtable 판독 (2026-10-03 미착수) |
| ~~bnvib 루프·샘플 순서·주파수·진폭 해석~~ | **해소**(2026-10-03 [실행]+[판독]): §7.1. 남은 것: 게임 진동 관리자가 VibrationPlayer를 호출하는 주기(샘플 요청 간격)와 Mixer 압축기(sdk+0x2504dc) 적용 여부 |
| PlayerCamera → 모듈 포저 연결 | 진행(§3.2b): setPoser 0x7101010de0. 6차 정정: 0x710233dbd4 계열·0x710233c414는 촬영(사진·amiibo) 컨트롤러 포저. 다음: 인라인 writer 0x7100fc7654(가상, 요청+0x28 포저)·0x7102121034, PlayerCamera+0x88 포즈를 읽는 포저 |
